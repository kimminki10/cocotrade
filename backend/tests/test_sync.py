from app.data.sync import fetch_closed_candles, find_gaps, last_closed_end

H = 3_600_000


class FakeExchange:
    """[0, n) 시간의 1시간봉을 가진 거래소. 한 번에 limit개까지 돌려준다."""

    def __init__(self, n: int, missing: set[int] = frozenset()):
        self.rows = [[i * H, 1, 1, 1, 1, 1] for i in range(n) if i not in missing]
        self.calls = 0

    def fetch_ohlcv(self, symbol, timeframe, since, limit):
        self.calls += 1
        return [r for r in self.rows if r[0] >= since][:limit]


def collect(exchange, start, end):
    return [
        r[0]
        for page in fetch_closed_candles(exchange, "BTC/USDT", "1h", start, end)
        for r in page
    ]


def test_last_closed_end_excludes_open_candle():
    assert last_closed_end(5 * H + 123, H) == 5 * H
    assert last_closed_end(5 * H, H) == 5 * H


def test_fetch_paginates_and_stops_at_end():
    exchange = FakeExchange(2500)
    ts = collect(exchange, 0, 2400 * H)
    assert ts == [i * H for i in range(2400)]
    assert exchange.calls == 3


def test_fetch_never_returns_candles_at_or_after_end():
    ts = collect(FakeExchange(10), 0, 5 * H)
    assert max(ts) == 4 * H


def test_fetch_continues_across_exchange_gap():
    ts = collect(FakeExchange(10, missing={3, 4}), 0, 10 * H)
    assert ts == [i * H for i in range(10) if i not in (3, 4)]


def test_find_gaps():
    ts = [0, H, 2 * H, 5 * H, 6 * H]
    assert find_gaps(ts, H) == [(3 * H, 5 * H)]
    assert find_gaps([0, H], H) == []
