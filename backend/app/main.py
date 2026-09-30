from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from sqlalchemy import func, select

from app.api import backtests
from app.api.deps import SessionDep
from app.data.models import Candle


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    backtests.shutdown_pool()


app = FastAPI(title="cocotrade", lifespan=lifespan)
api = APIRouter(prefix="/api")


@app.get("/health")
def health() -> dict:
    """준비 프로브용. DB를 읽지 않는다."""
    return {"status": "ok"}


@api.get("/markets")
def markets(session: SessionDep) -> list[dict]:
    rows = session.execute(
        select(
            Candle.exchange,
            Candle.symbol,
            Candle.timeframe,
            func.count(),
            func.min(Candle.ts),
            func.max(Candle.ts),
        ).group_by(Candle.exchange, Candle.symbol, Candle.timeframe)
    ).all()
    return [
        {
            "exchange": e,
            "symbol": s,
            "timeframe": tf,
            "candles": n,
            "first": first,
            "last": last,
        }
        for e, s, tf, n, first, last in rows
    ]


api.include_router(backtests.router)
app.include_router(api)
