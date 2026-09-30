from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.data.models import Candle
from app.db import SessionLocal

app = FastAPI(title="cocotrade")
api = APIRouter(prefix="/api")


def get_session():
    with SessionLocal() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


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


app.include_router(api)
