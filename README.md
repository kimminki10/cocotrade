# cocotrade

Crypto backtesting and a live track record of decisions made by [Jev](https://docs.typesafe.ai/introduction), TypeSafe AI's decision model.

- Backtest engine with next-bar-open fills, fees and slippage, and no look-ahead
- Jev strategy: Python computes the features, Jev returns up/flat/down probabilities, and a simple policy sizes the position
- Live track record: Jev is asked once per hourly close, and each call is scored 4 hours later (hit rate, calibration, Brier score)

Nothing here is investment advice.

> Work in progress. This project is developed with AI assistance (Claude Code).

## Development

Requirements: Docker, [uv](https://docs.astral.sh/uv/), Node.js 24, pnpm.

```bash
cp .env.example .env                 # set TYPESAFE_API_KEY
docker compose up -d                 # PostgreSQL 16 on 127.0.0.1:5432

cd backend
uv sync
uv run alembic upgrade head
uv run python -m app.data.sync       # BTC/USDT, ETH/USDT 1h candles, last 365 days
uv run python -m app.engine.cli      # compare rule strategies against random "monkey" baselines
uv run uvicorn app.main:app --reload # http://localhost:8000
uv run pytest

cd ../frontend
pnpm install
pnpm dev                             # http://localhost:3000, /api/* is proxied to the backend
```

Market data comes from Binance's public market data endpoint (`data-api.binance.vision`). It is also reachable from regions where `api.binance.com` is blocked.
