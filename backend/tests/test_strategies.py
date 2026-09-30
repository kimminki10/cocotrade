import pandas as pd
import pytest

from app.data.repo import to_bars
from app.engine.types import Context
from app.features.indicators import rsi
from app.strategies.rules import Bollinger, Donchian, Ema, Macd, Rsi
from tests.helpers import make_bars, random_ohlcv

CTX = Context(cash=0.0, qty=0.0, equity=0.0, weight=0.0, features={})


def targets(strategy, bars):
    return [strategy.on_bar(b, CTX) for b in bars]


def test_ema_matches_pandas():
    closes = random_ohlcv(200)["close"]
    ema = Ema(12)
    ours = [ema.update(c) for c in closes]
    expected = closes.ewm(span=12, adjust=False).mean()
    assert ours == pytest.approx(expected.tolist())


def test_incremental_rsi_matches_feature_rsi():
    df = random_ohlcv(300)
    strategy = Rsi()
    ours = []
    for bar in to_bars(df):
        strategy.on_bar(bar, CTX)
        ours.append(strategy.value())
    expected = rsi(df["close"])
    for mine, theirs in zip(ours, expected, strict=True):
        if pd.isna(theirs):
            assert mine is None
        else:
            assert mine == pytest.approx(theirs)


def test_rsi_enters_when_oversold_and_exits_when_overbought():
    falling = [(100 - i, 100 - i - 1) for i in range(20)]
    rising = [(80 + i, 80 + i + 1) for i in range(40)]
    result = targets(Rsi(), make_bars(falling + rising))
    assert result[14] == 1.0  # 14봉 연속 하락 → RSI 0 → 진입
    assert result[-1] == 0.0  # 계속 오르면 RSI가 70을 넘어 청산
    assert 1.0 in result[20:30]  # 반등 초기에는 아직 보유


def test_donchian_breakout_and_exit():
    flat = [(100, 100)] * 20  # 고가 100, 저가 100
    bars = make_bars([*flat, (100, 101), (101, 100), (100, 99)])
    result = targets(Donchian(entry=20, exit=10), bars)
    assert result[:20] == [0.0] * 20
    assert result[20] == 1.0  # 직전 20봉 최고가 100을 넘음
    assert result[21] == 1.0  # 100은 직전 10봉 최저가(100)보다 작지 않음
    assert result[22] == 0.0  # 99 < 100 → 청산


def test_bollinger_buys_below_lower_band_and_sells_at_middle():
    wiggle = [(100, 100 + (1 if i % 2 else -1)) for i in range(20)]
    bars = make_bars([*wiggle, (100, 95), (95, 97), (97, 101)])
    result = targets(Bollinger(), bars)
    assert result[20] == 1.0  # 95는 하단 밴드 아래
    assert result[21] == 1.0  # 아직 평균 아래
    assert result[22] == 0.0  # 평균 위로 복귀


def test_macd_waits_for_warmup():
    bars = to_bars(random_ohlcv(100))
    result = targets(Macd(), bars)
    assert result[: 26 + 9 - 1] == [0.0] * 34
    assert set(result) <= {0.0, 1.0}
