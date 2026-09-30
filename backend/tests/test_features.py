import numpy as np

from app.features.indicators import compute_features, compute_peer_features
from tests.helpers import random_ohlcv


def test_peer_features_align_by_timestamp():
    df = random_ohlcv(400, seed=1)
    peer = random_ohlcv(400, seed=2)
    # peer에서 한 봉이 빠지면 그 시각은 NaN이고, 앞 값으로 채우지 않는다
    missing = df.index[300]
    out = compute_peer_features(df, peer.drop(missing))

    assert out.index.equals(df.index)
    assert out.loc[missing].isna().all()
    expected = compute_features(peer)["return_24h"]
    assert np.isclose(out["peer_return_24h"].iloc[250], expected.iloc[250])


def test_peer_features_ignore_extra_peer_bars():
    df = random_ohlcv(400, seed=1).iloc[200:]
    peer = random_ohlcv(400, seed=2)
    out = compute_peer_features(df, peer)
    # peer는 df보다 앞선 봉까지 있으므로 df의 첫 봉부터 장기 지표가 채워져 있다
    assert out.index.equals(df.index)
    assert out.iloc[0].notna().all()
