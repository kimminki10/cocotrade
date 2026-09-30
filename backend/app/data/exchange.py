import ccxt

from app.config import settings


def make_binance() -> ccxt.binance:
    exchange = ccxt.binance(
        {
            "enableRateLimit": True,
            # 선물(fapi, dapi) 시장 목록은 불러오지 않는다. 공개 시세 도메인은 현물만 제공한다.
            "options": {"defaultType": "spot", "fetchMarkets": {"types": ["spot"]}},
        }
    )
    exchange.urls["api"]["public"] = settings.binance_public_url
    return exchange
