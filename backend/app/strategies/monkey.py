"""원숭이 전략: 비교 대상과 보유 비율, 평균 보유 기간이 같도록 무작위로 사고판다.

대상 전략이 원숭이 여러 마리의 분포에서 몇 번째 백분위인지 보면, 그 성과가 운으로 설명되는지 알 수 있다.
"""

import random
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

from app.engine.core import BacktestResult, run_backtest
from app.engine.types import Bar, Context, Costs


@dataclass(frozen=True)
class TradeProfile:
    exposure: float  # 포지션을 보유한 봉의 비율
    holding_bars: float  # 한 번 진입해서 청산할 때까지의 평균 봉 수


def trade_profile(result: BacktestResult) -> TradeProfile:
    held = [r.qty > 0 for r in result.records]
    entries = sum(1 for prev, cur in zip([False, *held], held) if cur and not prev)
    bars_held = sum(held)
    return TradeProfile(
        exposure=bars_held / len(held),
        holding_bars=bars_held / entries if entries else float(len(held)),
    )


class Monkey:
    """두 상태(현금, 보유)를 무작위로 오간다.

    보유 중에는 매 봉 1/보유기간 확률로 청산하고, 현금일 때는 장기 보유 비율이 목표와 같아지는 확률로 진입한다.
    """

    def __init__(self, profile: TradeProfile, seed: int) -> None:
        exposure = min(max(profile.exposure, 0.0), 1.0)
        if exposure >= 1:
            # 항상 보유: 첫 봉에 진입하고 청산하지 않는다
            self.p_enter, self.p_exit = 1.0, 0.0
        else:
            self.p_exit = 1 / max(profile.holding_bars, 1.0)
            # 정상 상태의 보유 비율 = p_enter / (p_enter + p_exit)
            self.p_enter = min(exposure * self.p_exit / (1 - exposure), 1.0)
        self._rng = random.Random(seed)
        self._holding = False

    def on_bar(self, bar: Bar, context: Context) -> float:
        r = self._rng.random()
        if self._holding:
            self._holding = r >= self.p_exit
        else:
            self._holding = r < self.p_enter
        return 1.0 if self._holding else 0.0


@dataclass(frozen=True)
class MonkeyComparison:
    total_returns: list[float]  # 원숭이별 총수익률
    # 대상 전략보다 성과가 낮은 원숭이의 비율 (0–100). 같은 값은 절반만 센다.
    percentile: float


def monkey_returns(
    bars: Sequence[Bar],
    profile: TradeProfile,
    seeds: Iterable[int],
    costs: Costs | None = None,
    features: Sequence[Mapping[str, float]] | None = None,
) -> list[float]:
    """시드마다 원숭이 한 마리를 돌린 총수익률. 프로세스 풀에 넘길 수 있게 모듈 수준 함수로 둔다."""
    return [
        run_backtest(
            bars, Monkey(profile, seed), costs=costs, features=features
        ).metrics.total_return
        for seed in seeds
    ]


def percentile_of(value: float, returns: Sequence[float]) -> float:
    """value보다 낮은 원숭이의 비율 (0–100). 같은 값은 절반만 센다."""
    below = sum(1 for r in returns if r < value)
    ties = sum(1 for r in returns if r == value)
    return 100 * (below + ties / 2) / len(returns)


def compare_with_monkeys(
    bars: Sequence[Bar],
    target: BacktestResult,
    *,
    runs: int = 1000,
    seed: int = 0,
    costs: Costs | None = None,
    features: Sequence[Mapping[str, float]] | None = None,
) -> MonkeyComparison:
    returns = monkey_returns(
        bars, trade_profile(target), range(seed, seed + runs), costs, features
    )
    return MonkeyComparison(
        returns, percentile_of(target.metrics.total_return, returns)
    )
