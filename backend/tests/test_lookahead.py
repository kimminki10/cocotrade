"""시점 t 이후의 데이터를 바꿔도 t까지의 피처와 판단이 변하지 않아야 한다."""

import numpy as np
import pandas as pd

from app.data.repo import to_bars
from app.engine.core import run_backtest
from app.features.indicators import (
    PEER_COLUMNS,
    compute_features,
    compute_peer_features,
)
from app.strategies.rules import RULE_STRATEGIES
from tests.helpers import random_ohlcv

N, T = 1500, 1000


def perturb_after(df: pd.DataFrame, t: int, seed: int = 99) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    out = df.copy()
    factor = rng.uniform(0.5, 1.5, len(df) - t - 1)
    for col in ["open", "high", "low", "close", "volume"]:
        out.iloc[t + 1 :, out.columns.get_loc(col)] *= factor
    return out


class FeatureStrategy:
    """피처를 쓰는 전략. 판단 기록을 남긴다."""

    def on_bar(self, bar, context):
        f = context.features
        if any(np.isnan(v) for v in f.values()):
            return 0.0
        score = (
            -f["price_vs_sma_24"] * 10
            + (50 - f["rsi_14"]) / 50
            + f["volatility_vs_30d"] * 0.1
        )
        return float(np.clip(score, 0, 1))


def test_features_do_not_look_ahead():
    df = random_ohlcv(N)
    before = compute_features(df).iloc[: T + 1]
    after = compute_features(perturb_after(df, T)).iloc[: T + 1]
    pd.testing.assert_frame_equal(before, after)
    # 워밍업이 끝난 뒤에는 값이 있어야 의미 있는 테스트다
    assert before.iloc[T].notna().all()


def test_decisions_do_not_look_ahead():
    df = random_ohlcv(N)
    changed = perturb_after(df, T)

    for make in (*RULE_STRATEGIES.values(), FeatureStrategy):
        a = run_backtest(
            to_bars(df), make(), features=compute_features(df).to_dict("records")
        )
        b = run_backtest(
            to_bars(changed),
            make(),
            features=compute_features(changed).to_dict("records"),
        )
        assert a.records[: T + 1] == b.records[: T + 1]
        # 바꾼 뒤로는 결과가 달라져야 한다 (테스트가 실제로 무언가를 바꿨는지 확인)
        assert a.records[-1].equity != b.records[-1].equity, make


def test_peer_features_do_not_look_ahead():
    df = random_ohlcv(N, seed=1)
    peer = random_ohlcv(N, seed=2)
    before = compute_peer_features(df, peer).iloc[: T + 1]
    after = compute_peer_features(df, perturb_after(peer, T)).iloc[: T + 1]
    pd.testing.assert_frame_equal(before, after)
    assert before.iloc[T].notna().all()
    assert list(before.columns) == PEER_COLUMNS
