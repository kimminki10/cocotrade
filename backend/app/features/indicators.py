"""봉마다 지표를 계산한다. 모든 값은 해당 봉까지의 데이터만 쓴다 (rolling, ewm은 과거 방향으로만 본다)."""

import pandas as pd

FEATURE_COLUMNS = [
    "sma_24",
    "sma_168",
    "price_vs_sma_24",
    "price_vs_sma_168",
    "rsi_14",
    "atr_14_pct",
    "return_4h",
    "return_24h",
    "volatility_vs_30d",
    "volume_vs_24h",
]


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Wilder 방식 RSI (0–100)."""
    delta = close.diff()
    gain = (
        delta.clip(lower=0)
        .ewm(alpha=1 / period, adjust=False, min_periods=period)
        .mean()
    )
    loss = (
        (-delta.clip(upper=0))
        .ewm(alpha=1 / period, adjust=False, min_periods=period)
        .mean()
    )
    return 100 - 100 / (1 + gain / loss)


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Wilder 방식 ATR."""
    prev_close = df["close"].shift(1)
    true_range = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return true_range.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()


def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """OHLCV(시간순, 1시간봉)에서 피처를 계산한다. 앞쪽 워밍업 구간은 NaN이다."""
    close = df["close"]
    out = pd.DataFrame(index=df.index)
    out["sma_24"] = close.rolling(24).mean()
    out["sma_168"] = close.rolling(168).mean()
    out["price_vs_sma_24"] = close / out["sma_24"] - 1
    out["price_vs_sma_168"] = close / out["sma_168"] - 1
    out["rsi_14"] = rsi(close)
    out["atr_14_pct"] = atr(df) / close
    out["return_4h"] = close.pct_change(4)
    out["return_24h"] = close.pct_change(24)
    vol_24h = close.pct_change().rolling(24).std()
    out["volatility_vs_30d"] = vol_24h / vol_24h.rolling(24 * 30).mean()
    out["volume_vs_24h"] = df["volume"] / df["volume"].rolling(24).mean()
    return out[FEATURE_COLUMNS]
