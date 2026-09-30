import pytest

from app.data.repo import to_bars
from app.engine.core import run_backtest
from app.engine.metrics import max_drawdown
from app.engine.report import curve
from app.strategies.rules import BuyAndHold, SmaCross
from tests.helpers import random_ohlcv


@pytest.mark.parametrize("n", [2, 499, 500, 501, 8760])
def test_curve_keeps_endpoints_and_point_limit(n):
    bars = to_bars(random_ohlcv(n))
    result = run_backtest(bars, SmaCross(3, 7))
    benchmark = run_backtest(bars, BuyAndHold())
    points = curve(result, benchmark, max_points=500)

    assert len(points) <= 500
    assert points[0]["ts"] == bars[0].ts
    assert points[0]["equity"] == result.records[0].equity
    assert points[-1]["ts"] == bars[-1].ts
    assert points[-1]["equity"] == result.records[-1].equity
    assert points[-1]["benchmark"] == benchmark.records[-1].equity


def test_curve_keeps_deepest_drawdown():
    bars = to_bars(random_ohlcv(5000, seed=3))
    result = run_backtest(bars, BuyAndHold())
    points = curve(result, result, max_points=50)
    assert min(p["drawdown"] for p in points) == pytest.approx(
        max_drawdown([r.equity for r in result.records])
    )
