import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from app.engine.types import BarRecord, Fill

# 가상자산은 24시간 거래된다. 1시간봉 기준 연환산 계수.
PERIODS_PER_YEAR = 24 * 365


@dataclass(frozen=True)
class RoundTrip:
    """진입부터 포지션이 0이 될 때까지의 거래 하나."""

    pnl: float  # 매도 대금 − 매수 대금 (수수료 포함)


@dataclass(frozen=True)
class Metrics:
    total_return: float
    cagr: float | None
    volatility: float
    sharpe: float | None
    sortino: float | None
    max_drawdown: float  # 0 이하
    calmar: float | None
    win_rate: float | None
    round_trips: int
    fills: int
    turnover: float
    exposure: float


def bar_returns(equity: Sequence[float]) -> np.ndarray:
    e = np.asarray(equity, dtype=float)
    return e[1:] / e[:-1] - 1


def max_drawdown(equity: Sequence[float]) -> float:
    e = np.asarray(equity, dtype=float)
    return float(np.min(e / np.maximum.accumulate(e) - 1))


def cagr(
    initial: float, final: float, periods: int, periods_per_year: int = PERIODS_PER_YEAR
) -> float | None:
    """연환산 수익률. 구간이 너무 짧아 값이 발산하면 None."""
    if final <= 0:
        return -1.0
    exponent = math.log(final / initial) * periods_per_year / periods
    return math.expm1(exponent) if exponent < 700 else None


def sharpe(
    returns: np.ndarray, periods_per_year: int = PERIODS_PER_YEAR
) -> float | None:
    std = returns.std(ddof=1)
    return (
        float(returns.mean() / std * math.sqrt(periods_per_year)) if std > 0 else None
    )


def sortino(
    returns: np.ndarray, periods_per_year: int = PERIODS_PER_YEAR
) -> float | None:
    # 하방 편차: 0보다 작은 수익률만 남기고 전체 봉 수로 나눈 제곱 평균의 제곱근
    downside = math.sqrt(np.mean(np.minimum(returns, 0.0) ** 2))
    return (
        float(returns.mean() / downside * math.sqrt(periods_per_year))
        if downside > 0
        else None
    )


def round_trips(fills: Sequence["Fill"], eps: float = 1e-12) -> list[RoundTrip]:
    """체결 내역을 진입부터 청산까지의 거래로 묶는다. 끝나지 않은 거래는 넣지 않는다."""
    trips: list[RoundTrip] = []
    qty = 0.0
    flow = 0.0
    for f in fills:
        if f.side == "buy":
            qty += f.qty
            flow -= f.notional + f.fee
        else:
            qty -= f.qty
            flow += f.notional - f.fee
        if qty <= eps and f.side == "sell":
            trips.append(RoundTrip(pnl=flow))
            qty, flow = 0.0, 0.0
    return trips


def compute_metrics(
    records: Sequence["BarRecord"], fills: Sequence["Fill"], initial_cash: float
) -> Metrics:
    # 자산 곡선은 봉마다의 종가 평가액이다. 첫 봉에는 체결이 없으므로 첫 값은 초기 자본과 같다.
    if not records:
        raise ValueError("no bars")
    equity = [r.equity for r in records]
    returns = bar_returns(equity)
    final = equity[-1]
    mdd = max_drawdown(equity)
    growth = cagr(initial_cash, final, len(returns)) if returns.size else None
    trips = round_trips(fills)
    wins = sum(1 for t in trips if t.pnl > 0)

    return Metrics(
        total_return=final / initial_cash - 1,
        cagr=growth,
        volatility=float(returns.std(ddof=1) * math.sqrt(PERIODS_PER_YEAR))
        if returns.size > 1
        else 0.0,
        sharpe=sharpe(returns) if returns.size > 1 else None,
        sortino=sortino(returns) if returns.size > 1 else None,
        max_drawdown=mdd,
        calmar=growth / abs(mdd) if growth is not None and mdd < 0 else None,
        win_rate=wins / len(trips) if trips else None,
        round_trips=len(trips),
        fills=len(fills),
        turnover=sum(f.notional for f in fills) / float(np.mean(equity)),
        exposure=sum(1 for r in records if r.qty > 0) / len(records),
    )
