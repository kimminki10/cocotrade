"""저장된 봉으로 규칙 전략을 모두 돌리고, 원숭이 전략 분포와 비교한다.

python -m app.engine.cli --symbol BTC/USDT --monkeys 200
"""

import argparse
import time

from app.data.repo import load_candles, to_bars
from app.db import SessionLocal
from app.engine.core import run_backtest
from app.strategies.monkey import compare_with_monkeys
from app.strategies.rules import RULE_STRATEGIES


def pct(value: float | None) -> str:
    return "-" if value is None else f"{value * 100:+.1f}%"


def num(value: float | None) -> str:
    return "-" if value is None else f"{value:+.2f}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="BTC/USDT")
    parser.add_argument("--timeframe", default="1h")
    parser.add_argument(
        "--monkeys", type=int, default=200, help="원숭이 수 (0이면 비교하지 않음)"
    )
    args = parser.parse_args()

    with SessionLocal() as session:
        df = load_candles(session, args.symbol, args.timeframe)
    bars = to_bars(df)
    print(
        f"{args.symbol} {args.timeframe}  {bars[0].ts:%Y-%m-%d} – {bars[-1].ts:%Y-%m-%d}  {len(bars)} bars"
    )
    print(
        f"{'strategy':<11}{'return':>9}{'CAGR':>9}{'sharpe':>8}{'MDD':>9}"
        f"{'fills':>7}{'exposure':>10}{'monkey pct':>12}"
    )

    started = time.perf_counter()
    for name, make in RULE_STRATEGIES.items():
        result = run_backtest(bars, make())
        m = result.metrics
        monkey = (
            f"{compare_with_monkeys(bars, result, runs=args.monkeys).percentile:.0f}"
            if args.monkeys
            else "-"
        )
        print(
            f"{name:<11}{pct(m.total_return):>9}{pct(m.cagr):>9}{num(m.sharpe):>8}"
            f"{pct(m.max_drawdown):>9}{m.fills:>7}{m.exposure:>10.2f}{monkey:>12}"
        )
    print(f"elapsed {time.perf_counter() - started:.1f} s")


if __name__ == "__main__":
    main()
