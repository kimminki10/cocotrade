import pytest

from app.data.repo import to_bars
from app.engine.core import run_backtest
from app.engine.types import Costs
from app.strategies.monkey import (
    Monkey,
    TradeProfile,
    compare_with_monkeys,
    trade_profile,
)
from app.strategies.rules import BuyAndHold, SmaCross
from tests.helpers import random_ohlcv


def test_monkey_is_deterministic_per_seed():
    bars = to_bars(random_ohlcv(500))
    profile = TradeProfile(exposure=0.4, holding_bars=12)
    a = run_backtest(bars, Monkey(profile, seed=7))
    b = run_backtest(bars, Monkey(profile, seed=7))
    c = run_backtest(bars, Monkey(profile, seed=8))
    assert a.records == b.records
    assert a.records != c.records


def test_monkey_matches_target_profile():
    bars = to_bars(random_ohlcv(30_000))
    target = TradeProfile(exposure=0.3, holding_bars=24)
    result = run_backtest(
        bars, Monkey(target, seed=1), costs=Costs(fee=0, slippage=0, min_trade=0)
    )
    measured = trade_profile(result)
    assert measured.exposure == pytest.approx(0.3, abs=0.03)
    assert measured.holding_bars == pytest.approx(24, rel=0.1)


def test_full_exposure_monkey_always_holds():
    bars = to_bars(random_ohlcv(200))
    result = run_backtest(
        bars, Monkey(TradeProfile(exposure=1.0, holding_bars=200), seed=0)
    )
    assert trade_profile(result).exposure == pytest.approx(199 / 200)  # 첫 봉만 현금


def test_compare_with_monkeys():
    bars = to_bars(random_ohlcv(1000, seed=3))
    target = run_backtest(bars, SmaCross(24, 168))
    comparison = compare_with_monkeys(bars, target, runs=50, seed=0)
    assert len(comparison.total_returns) == 50
    assert 0 <= comparison.percentile <= 100
    # 같은 seed면 같은 분포
    assert compare_with_monkeys(bars, target, runs=50, seed=0) == comparison


def test_trade_profile():
    bars = to_bars(random_ohlcv(100))
    profile = trade_profile(run_backtest(bars, BuyAndHold()))
    assert profile.exposure == pytest.approx(99 / 100)
    assert profile.holding_bars == 99
