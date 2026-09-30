import math

import pytest

from app.data.repo import to_bars
from app.engine.core import run_backtest, step
from app.engine.types import Account, Costs
from app.strategies.rules import BuyAndHold
from tests.helpers import make_bars, random_ohlcv

NO_COSTS = Costs(fee=0.0, slippage=0.0)


class Targets:
    """정해진 목표 비중을 차례로 반환한다."""

    def __init__(self, *targets: float) -> None:
        self.targets = list(targets)

    def on_bar(self, bar, context):
        return self.targets.pop(0)


def test_buy_fills_at_next_open_with_slippage_and_fee():
    bars = make_bars([(100, 100), (100, 110)])
    result = run_backtest(
        bars, BuyAndHold(), costs=Costs(fee=0.001, slippage=0.0005), initial_cash=10_000
    )

    notional = 10_000 / 1.001  # 수수료까지 현금 안에서 낸다
    qty = notional / 100.05
    fill = result.fills[0]
    assert fill.ts == bars[1].ts
    assert fill.price == pytest.approx(100.05)
    assert fill.qty == pytest.approx(qty)
    assert fill.fee == pytest.approx(notional * 0.001)
    assert result.final_account.cash == pytest.approx(0.0, abs=1e-9)
    assert result.records[1].equity == pytest.approx(qty * 110)
    # 첫 봉에는 체결이 없다
    assert result.records[0].fill is None
    assert result.records[0].equity == 10_000


def test_sell_to_zero_leaves_no_position():
    bars = make_bars([(100, 100), (100, 100), (120, 120)])
    result = run_backtest(
        bars, Targets(1.0, 0.0, 0.0), costs=Costs(fee=0.001, slippage=0.0005)
    )

    buy, sell = result.fills
    assert sell.side == "sell"
    assert sell.qty == pytest.approx(buy.qty)
    assert sell.price == pytest.approx(120 * (1 - 0.0005))
    assert result.final_account.qty == 0
    assert result.final_account.cash == pytest.approx(sell.notional - sell.fee)


def test_last_decision_is_not_executed():
    bars = make_bars([(100, 100), (100, 100)])
    result = run_backtest(bars, Targets(0.0, 1.0), costs=NO_COSTS)

    assert result.fills == []
    assert result.final_account.qty == 0
    assert result.final_account.pending_target == 1.0


def test_small_rebalance_is_skipped():
    bars = make_bars([(100, 100)] * 4)
    result = run_backtest(bars, Targets(0.5, 0.505, 0.6, 0.6), costs=NO_COSTS)

    # 0.5 → 0.505는 최소 거래 단위(1%p)보다 작아서 건너뛴다
    assert [f.ts for f in result.fills] == [bars[1].ts, bars[3].ts]
    assert result.records[-1].weight == pytest.approx(0.6)


def test_target_is_clamped_and_nan_rejected():
    bars = make_bars([(100, 100), (100, 100)])
    result = run_backtest(bars, Targets(1.7, -1.0), costs=NO_COSTS)
    assert result.records[0].target == 1.0
    assert result.records[1].target == 0.0

    with pytest.raises(ValueError, match="NaN"):
        run_backtest(bars, Targets(math.nan, 0.0), costs=NO_COSTS)


def test_buy_and_hold_without_costs_matches_price_change():
    df = random_ohlcv(500, seed=1)
    bars = to_bars(df)
    result = run_backtest(bars, BuyAndHold(), costs=NO_COSTS)

    # 첫 봉 종가에 판단하고 둘째 봉 시가에 산다
    expected = bars[-1].close / bars[1].open - 1
    assert result.metrics.total_return == pytest.approx(expected, rel=1e-12)


def test_stepwise_continuation_matches_single_run():
    """실시간 가상 계좌처럼 계좌 상태를 저장했다가 이어서 처리해도 한 번에 돌린 것과 같다."""
    df = random_ohlcv(300, seed=2)
    bars = to_bars(df)
    features = [{"r": c / o - 1} for o, c in zip(df["open"], df["close"], strict=True)]

    class Momentum:
        def on_bar(self, bar, context):
            return 1.0 if context.features["r"] > 0 else 0.3

    costs = Costs()
    full = run_backtest(bars, Momentum(), features=features, costs=costs)

    account = Account(cash=10_000.0)
    records = []
    for bar, row in zip(bars, features, strict=True):
        # 매 봉마다 상태를 새 객체로 다시 만든다 (DB에 저장했다가 읽는 것과 같다)
        account = Account(account.cash, account.qty, account.pending_target)
        account, record = step(account, bar, row, Momentum(), costs)
        records.append(record)

    assert records == full.records
    assert account == full.final_account
