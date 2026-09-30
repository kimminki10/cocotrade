"""백테스트 실행과 전략 비교.

결과는 저장하지 않고 요청마다 계산한다. 같은 입력과 같은 봉이면 메모리 캐시에서 돌려준다.
원숭이 전략은 수백 번 돌려야 해서 프로세스 풀에 나눠 맡긴다.
"""

import inspect
from collections import OrderedDict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from datetime import UTC, date, datetime, time, timedelta
from threading import Lock
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.api.deps import SessionDep
from app.config import settings
from app.data.repo import load_candles, to_bars
from app.engine import report
from app.engine.core import BacktestResult, run_backtest
from app.engine.types import Bar, Costs
from app.strategies.monkey import (
    TradeProfile,
    monkey_returns,
    percentile_of,
    trade_profile,
)
from app.strategies.rules import RULE_STRATEGIES, BuyAndHold

router = APIRouter()

INITIAL_CASH = 10_000.0
# 가장 긴 규칙 전략(SMA 168)이 판단을 시작하고도 남는 길이
MIN_BARS = 336
QUANTILES = (0.05, 0.25, 0.5, 0.75, 0.95)


class MarketQuery(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    symbol: str = "BTC/USDT"
    # 지표의 연환산 계수(8,760)가 1시간봉 기준이다.
    timeframe: Literal["1h"] = "1h"
    start: date | None = None
    end: date | None = None  # 이 날짜까지 포함 (UTC)
    fee: float = Field(0.001, ge=0, le=0.01)
    slippage: float = Field(0.0005, ge=0, le=0.01)
    monkeys: int = Field(200, ge=0, le=1000)

    def costs(self) -> Costs:
        return Costs(fee=self.fee, slippage=self.slippage)


class BacktestRequest(MarketQuery):
    strategy: str


def _params(factory: type) -> dict:
    return {
        name: p.default
        for name, p in inspect.signature(factory).parameters.items()
        if p.default is not inspect.Parameter.empty
    }


@router.get("/strategies")
def strategies() -> list[dict]:
    return [
        {"id": key, "params": _params(factory)}
        for key, factory in RULE_STRATEGIES.items()
    ]


@router.post("/backtests")
def create_backtest(body: BacktestRequest, session: SessionDep) -> dict:
    if body.strategy not in RULE_STRATEGIES:
        raise HTTPException(422, f"unknown strategy: {body.strategy}")
    bars = _load_bars(session, body)
    return _cached(
        ("backtest", body, len(bars), bars[-1].ts), lambda: _backtest(bars, body)
    )


@router.get("/compare")
def compare(query: Annotated[MarketQuery, Query()], session: SessionDep) -> dict:
    bars = _load_bars(session, query)
    return _cached(
        ("compare", query, len(bars), bars[-1].ts), lambda: _compare(bars, query)
    )


def _load_bars(session: Session, query: MarketQuery) -> list[Bar]:
    start = datetime.combine(query.start, time(), UTC) if query.start else None
    end = (
        datetime.combine(query.end + timedelta(days=1), time(), UTC)
        if query.end
        else None
    )
    if start and end and start >= end:
        raise HTTPException(422, "start must be before end")
    df = load_candles(session, query.symbol, query.timeframe, start=start, end=end)
    if len(df) < MIN_BARS:
        raise HTTPException(
            422, f"need at least {MIN_BARS} candles, found {len(df)} for this range"
        )
    return to_bars(df)


def _config(bars: list[Bar], query: MarketQuery) -> dict:
    return {
        "symbol": query.symbol,
        "timeframe": query.timeframe,
        "start": bars[0].ts,
        "end": bars[-1].ts,
        "bars": len(bars),
        "fee": query.fee,
        "slippage": query.slippage,
        "min_trade": query.costs().min_trade,
        "initial_cash": INITIAL_CASH,
        "monkeys": query.monkeys,
    }


def _run(bars: list[Bar], strategy_id: str, costs: Costs) -> BacktestResult:
    return run_backtest(
        bars, RULE_STRATEGIES[strategy_id](), costs=costs, initial_cash=INITIAL_CASH
    )


def _backtest(bars: list[Bar], body: BacktestRequest) -> dict:
    costs = body.costs()
    result = _run(bars, body.strategy, costs)
    benchmark = run_backtest(bars, BuyAndHold(), costs=costs, initial_cash=INITIAL_CASH)
    monkey = None
    if body.monkeys:
        profile = trade_profile(result)
        (returns,) = _monkeys(bars, [profile], body.monkeys, costs)
        monkey = _monkey_summary(result, profile, returns) | {
            "returns": sorted(returns)
        }
    return {
        "config": _config(bars, body)
        | {
            "strategy": body.strategy,
            "params": _params(RULE_STRATEGIES[body.strategy]),
        },
        "metrics": asdict(result.metrics),
        "benchmark": asdict(benchmark.metrics),
        "curve": report.curve(result, benchmark),
        "fills": report.fills(result),
        "monkey": monkey,
    }


def _compare(bars: list[Bar], query: MarketQuery) -> dict:
    costs = query.costs()
    results = {key: _run(bars, key, costs) for key in RULE_STRATEGIES}
    profiles = [trade_profile(r) for r in results.values()]
    returns = (
        _monkeys(bars, profiles, query.monkeys, costs)
        if query.monkeys
        else [None] * len(results)
    )
    return {
        "config": _config(bars, query),
        "strategies": [
            {
                "id": key,
                "metrics": asdict(result.metrics),
                "monkey": _monkey_summary(result, profile, r) if r else None,
            }
            for (key, result), profile, r in zip(
                results.items(), profiles, returns, strict=True
            )
        ],
    }


def _monkey_summary(
    result: BacktestResult, profile: TradeProfile, returns: list[float]
) -> dict:
    return {
        "runs": len(returns),
        "percentile": percentile_of(result.metrics.total_return, returns),
        "exposure": profile.exposure,
        "holding_bars": profile.holding_bars,
        "quantiles": report.quantiles(returns, QUANTILES),
    }


# ---------------------------------------------------------------- 원숭이 병렬 실행

_pool: ProcessPoolExecutor | None = None


def _executor() -> ProcessPoolExecutor:
    global _pool
    if _pool is None:
        _pool = ProcessPoolExecutor(max_workers=settings.backtest_workers)
    return _pool


def shutdown_pool() -> None:
    if _pool is not None:
        _pool.shutdown(cancel_futures=True)


def _monkeys(
    bars: list[Bar], profiles: list[TradeProfile], runs: int, costs: Costs
) -> list[list[float]]:
    """프로필마다 원숭이 runs마리(시드 0..runs−1)의 총수익률. 시드를 작업자 수만큼 나눠 동시에 돌린다."""
    workers = settings.backtest_workers
    futures = [
        [
            _executor().submit(
                monkey_returns, bars, profile, range(i, runs, workers), costs
            )
            for i in range(min(workers, runs))
        ]
        for profile in profiles
    ]
    return [[r for f in parts for r in f.result()] for parts in futures]


# ---------------------------------------------------------------- 결과 캐시

_CACHE_SIZE = 64
_cache: OrderedDict[tuple, dict] = OrderedDict()
_cache_lock = Lock()


def _cached(key: tuple, compute) -> dict:
    """마지막 봉 시각이 키에 들어가므로 새 봉이 들어오면 자연히 다시 계산한다."""
    with _cache_lock:
        if key in _cache:
            _cache.move_to_end(key)
            return _cache[key]
    value = compute()
    with _cache_lock:
        _cache[key] = value
        while len(_cache) > _CACHE_SIZE:
            _cache.popitem(last=False)
    return value
