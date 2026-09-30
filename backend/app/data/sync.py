"""거래소에서 마감된 봉을 받아 저장한다.

uv run python -m app.data.sync --symbols BTC/USDT ETH/USDT --timeframe 1h --days 365
"""

import argparse
import time
from collections.abc import Iterator
from datetime import UTC, datetime
from itertools import pairwise

import ccxt
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.data.exchange import make_binance
from app.data.models import Candle
from app.db import SessionLocal

PAGE_LIMIT = 1000
DAY_MS = 24 * 60 * 60 * 1000


def timeframe_ms(timeframe: str) -> int:
    return ccxt.Exchange.parse_timeframe(timeframe) * 1000


def last_closed_end(now_ms: int, tf_ms: int) -> int:
    """아직 마감되지 않은 봉의 시작 시각. 이보다 앞에서 시작한 봉만 마감된 봉이다."""
    return now_ms // tf_ms * tf_ms


def fetch_closed_candles(
    exchange: ccxt.Exchange, symbol: str, timeframe: str, start_ms: int, end_ms: int
) -> Iterator[list]:
    """[start_ms, end_ms) 구간의 봉을 페이지 단위로 돌려준다."""
    tf_ms = timeframe_ms(timeframe)
    since = start_ms
    while since < end_ms:
        rows = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=PAGE_LIMIT)
        rows = [r for r in rows if since <= r[0] < end_ms]
        if not rows:
            return
        yield rows
        since = rows[-1][0] + tf_ms


def find_gaps(timestamps_ms: list[int], tf_ms: int) -> list[tuple[int, int]]:
    """연속되지 않은 구간을 (빠진 첫 봉, 다음에 있는 봉) 쌍으로 돌려준다."""
    return [
        (prev + tf_ms, cur)
        for prev, cur in pairwise(timestamps_ms)
        if cur - prev != tf_ms
    ]


def _to_dt(ms: int) -> datetime:
    return datetime.fromtimestamp(ms / 1000, tz=UTC)


def _to_ms(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)


def sync_symbol(
    session: Session,
    exchange: ccxt.Exchange,
    symbol: str,
    timeframe: str,
    days: int,
    now_ms: int | None = None,
) -> int:
    """저장된 마지막 봉 다음부터 받는다. 저장된 것이 없으면 최근 days일치를 받는다."""
    tf_ms = timeframe_ms(timeframe)
    end_ms = last_closed_end(
        now_ms if now_ms is not None else int(time.time() * 1000), tf_ms
    )
    key = (
        Candle.exchange == exchange.id,
        Candle.symbol == symbol,
        Candle.timeframe == timeframe,
    )
    latest = session.scalar(select(func.max(Candle.ts)).where(*key))
    start_ms = _to_ms(latest) + tf_ms if latest else end_ms - days * DAY_MS

    inserted = 0
    for rows in fetch_closed_candles(exchange, symbol, timeframe, start_ms, end_ms):
        values = [
            {
                "exchange": exchange.id,
                "symbol": symbol,
                "timeframe": timeframe,
                "ts": _to_dt(ts),
                "open": o,
                "high": h,
                "low": lo,
                "close": c,
                "volume": v,
            }
            for ts, o, h, lo, c, v in rows
        ]
        # 마감된 봉은 바뀌지 않으므로 이미 있으면 건너뛴다.
        session.execute(insert(Candle).values(values).on_conflict_do_nothing())
        session.commit()
        inserted += len(values)
    return inserted


def stored_gaps(
    session: Session, exchange_id: str, symbol: str, timeframe: str
) -> list[tuple[int, int]]:
    ts = session.scalars(
        select(Candle.ts)
        .where(
            Candle.exchange == exchange_id,
            Candle.symbol == symbol,
            Candle.timeframe == timeframe,
        )
        .order_by(Candle.ts)
    ).all()
    return find_gaps([_to_ms(t) for t in ts], timeframe_ms(timeframe))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbols", nargs="+", default=["BTC/USDT", "ETH/USDT"])
    parser.add_argument("--timeframe", default="1h")
    parser.add_argument("--days", type=int, default=365)
    args = parser.parse_args()

    exchange = make_binance()
    with SessionLocal() as session:
        for symbol in args.symbols:
            n = sync_symbol(session, exchange, symbol, args.timeframe, args.days)
            gaps = stored_gaps(session, exchange.id, symbol, args.timeframe)
            print(f"{symbol} {args.timeframe}: {n} new candles, {len(gaps)} gaps")
            for start, end in gaps:
                print(f"  gap {_to_dt(start).isoformat()} .. {_to_dt(end).isoformat()}")


if __name__ == "__main__":
    main()
