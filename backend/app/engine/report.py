"""백테스트 결과를 화면에 보낼 형태로 줄인다."""

import math
from dataclasses import asdict

import numpy as np

from app.engine.core import BacktestResult


def curve(
    result: BacktestResult, benchmark: BacktestResult, max_points: int = 500
) -> list[dict]:
    """자산 곡선, 기준 곡선, 낙폭을 최대 max_points개 점으로 줄인다.

    점마다 구간 마지막 봉의 평가액과 구간 안에서 가장 깊은 낙폭을 쓴다. 줄여도 최대 낙폭은 그대로 남는다.
    """
    records = result.records
    n = len(records)
    if len(benchmark.records) != n:
        raise ValueError("benchmark must cover the same bars")

    equity = np.array([r.equity for r in records])
    bench = np.array([r.equity for r in benchmark.records])
    drawdown = equity / np.maximum.accumulate(equity) - 1

    size = max(1, math.ceil((n - 1) / (max_points - 1)))
    ends = list(range(0, n, size))
    if ends[-1] != n - 1:
        ends.append(n - 1)

    points = []
    prev = -1
    for end in ends:
        points.append(
            {
                "ts": records[end].ts,
                "equity": float(equity[end]),
                "benchmark": float(bench[end]),
                "drawdown": float(drawdown[prev + 1 : end + 1].min()),
            }
        )
        prev = end
    return points


def fills(result: BacktestResult) -> list[dict]:
    return [asdict(f) for f in result.fills]


def quantiles(values: list[float], qs: tuple[float, ...]) -> dict[str, float]:
    return {f"p{round(q * 100)}": float(np.quantile(values, q)) for q in qs}
