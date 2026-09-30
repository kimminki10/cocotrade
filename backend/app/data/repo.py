from datetime import datetime

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data.models import Candle
from app.engine.types import Bar


def load_candles(
    session: Session,
    symbol: str,
    timeframe: str = "1h",
    *,
    exchange: str = "binance",
    start: datetime | None = None,
    end: datetime | None = None,
) -> pd.DataFrame:
    """저장된 봉을 시간순 DataFrame(index=ts)으로 읽는다. end는 포함하지 않는다."""
    query = select(
        Candle.ts, Candle.open, Candle.high, Candle.low, Candle.close, Candle.volume
    ).where(
        Candle.exchange == exchange,
        Candle.symbol == symbol,
        Candle.timeframe == timeframe,
    )
    if start is not None:
        query = query.where(Candle.ts >= start)
    if end is not None:
        query = query.where(Candle.ts < end)
    rows = session.execute(query.order_by(Candle.ts)).all()
    return pd.DataFrame(
        rows, columns=["ts", "open", "high", "low", "close", "volume"]
    ).set_index("ts")


def to_bars(df: pd.DataFrame) -> list[Bar]:
    return [Bar(ts, o, h, lo, c, v) for ts, o, h, lo, c, v in df.itertuples(name=None)]
