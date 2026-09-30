from datetime import UTC, datetime, timedelta

import numpy as np
import pandas as pd

from app.engine.types import Bar

T0 = datetime(2025, 1, 1, tzinfo=UTC)


def make_bars(opens_closes: list[tuple[float, float]]) -> list[Bar]:
    return [
        Bar(T0 + timedelta(hours=i), o, max(o, c), min(o, c), c, 1.0)
        for i, (o, c) in enumerate(opens_closes)
    ]


def random_ohlcv(n: int, seed: int = 0) -> pd.DataFrame:
    """무작위 보행 가격의 1시간봉. 시가는 직전 종가와 같다."""
    rng = np.random.default_rng(seed)
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    open_ = np.concatenate([[100.0], close[:-1]])
    spread = np.abs(rng.normal(0, 0.005, n)) * close
    return pd.DataFrame(
        {
            "open": open_,
            "high": np.maximum(open_, close) + spread,
            "low": np.minimum(open_, close) - spread,
            "close": close,
            "volume": rng.uniform(10, 100, n),
        },
        index=pd.date_range(T0, periods=n, freq="h"),
    )
