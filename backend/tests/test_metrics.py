import math

import numpy as np
import pytest

from app.engine.metrics import (
    PERIODS_PER_YEAR,
    bar_returns,
    cagr,
    max_drawdown,
    round_trips,
    sharpe,
    sortino,
)
from app.engine.types import Fill
from tests.helpers import T0

EQUITY = [100.0, 110.0, 99.0, 108.9]  # 수익률 +10%, −10%, +10%


def test_bar_returns():
    assert bar_returns(EQUITY) == pytest.approx([0.1, -0.1, 0.1])


def test_max_drawdown():
    assert max_drawdown(EQUITY) == pytest.approx(99 / 110 - 1)
    assert max_drawdown([1.0, 2.0, 3.0]) == 0.0


def test_cagr():
    # 2기간에 21% → 기간당 10%
    assert cagr(100, 121, 2, periods_per_year=1) == pytest.approx(0.1)
    assert cagr(100, 121, 2, periods_per_year=2) == pytest.approx(0.21)


def test_sharpe_and_sortino_by_hand():
    r = np.array([0.1, -0.1, 0.1])
    mean = 0.1 / 3
    std = math.sqrt(((0.1 - mean) ** 2 * 2 + (-0.1 - mean) ** 2) / 2)  # 표본 표준편차
    downside = math.sqrt(0.01 / 3)  # 음수 수익률 −0.1 하나, 전체 3기간으로 나눈다
    assert sharpe(r) == pytest.approx(mean / std * math.sqrt(PERIODS_PER_YEAR))
    assert sortino(r) == pytest.approx(mean / downside * math.sqrt(PERIODS_PER_YEAR))
    assert sharpe(np.zeros(3)) is None
    assert sortino(np.array([0.01, 0.02])) is None


def fill(side, qty, price, fee_rate=0.001):
    return Fill(T0, side, qty, price, qty * price, qty * price * fee_rate)


def test_round_trips_group_partial_fills():
    fills = [
        fill("buy", 1, 100),
        fill("buy", 1, 100),
        fill("sell", 1, 110),
        fill("sell", 1, 90),  # 여기서 포지션 0 → 거래 1건
        fill("buy", 1, 100),  # 끝나지 않은 거래는 세지 않는다
    ]
    trips = round_trips(fills)
    assert len(trips) == 1
    assert trips[0].pnl == pytest.approx((110 + 90) * 0.999 - 200 * 1.001)


def test_cagr_on_tiny_window_is_none_instead_of_overflow():
    assert cagr(100, 120, 2) is None
