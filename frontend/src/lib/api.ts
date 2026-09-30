// 서버 컴포넌트는 rewrite를 거치지 않고 백엔드를 직접 호출한다.
const apiUrl = process.env.API_URL ?? "http://localhost:8000";

export type Market = {
  exchange: string;
  symbol: string;
  timeframe: string;
  candles: number;
  first: string;
  last: string;
};

export type StrategyId = "buy_hold" | "sma_cross" | "macd" | "donchian" | "rsi" | "bollinger";

export type Strategy = {
  id: StrategyId;
  params: Record<string, number>;
};

export type Metrics = {
  total_return: number;
  cagr: number | null;
  volatility: number;
  sharpe: number | null;
  sortino: number | null;
  max_drawdown: number;
  calmar: number | null;
  win_rate: number | null;
  round_trips: number;
  fills: number;
  turnover: number;
  exposure: number;
};

export type RunConfig = {
  symbol: string;
  timeframe: string;
  start: string;
  end: string;
  bars: number;
  fee: number;
  slippage: number;
  min_trade: number;
  initial_cash: number;
  monkeys: number;
};

export type MonkeySummary = {
  runs: number;
  percentile: number;
  exposure: number;
  holding_bars: number;
  quantiles: { p5: number; p25: number; p50: number; p75: number; p95: number };
};

export type CurvePoint = { ts: string; equity: number; benchmark: number; drawdown: number };

export type Fill = {
  ts: string;
  side: "buy" | "sell";
  qty: number;
  price: number;
  notional: number;
  fee: number;
};

export type Backtest = {
  config: RunConfig & { strategy: StrategyId; params: Record<string, number> };
  metrics: Metrics;
  benchmark: Metrics;
  curve: CurvePoint[];
  fills: Fill[];
  monkey: (MonkeySummary & { returns: number[] }) | null;
};

export type Comparison = {
  config: RunConfig;
  strategies: { id: StrategyId; metrics: Metrics; monkey: MonkeySummary | null }[];
};

export type RunQuery = {
  symbol: string;
  start?: string;
  end?: string;
  fee: number;
  slippage: number;
};

// 입력이 잘못되면 백엔드가 422와 설명을 돌려준다. 화면에 그대로 보여준다.
export type Result<T> = { ok: true; data: T } | { ok: false; error: string };

async function request<T>(path: string, init?: RequestInit): Promise<Result<T>> {
  const res = await fetch(`${apiUrl}/api${path}`, { cache: "no-store", ...init });
  if (res.ok) return { ok: true, data: await res.json() };
  if (res.status === 422) {
    const body = await res.json();
    const detail = body.detail;
    return { ok: false, error: typeof detail === "string" ? detail : "Invalid settings." };
  }
  throw new Error(`${init?.method ?? "GET"} /api${path} failed: ${res.status}`);
}

async function unwrap<T>(result: Promise<Result<T>>): Promise<T> {
  const r = await result;
  if (!r.ok) throw new Error(r.error);
  return r.data;
}

export function getMarkets(): Promise<Market[]> {
  return unwrap(request<Market[]>("/markets"));
}

export function getStrategies(): Promise<Strategy[]> {
  return unwrap(request<Strategy[]>("/strategies"));
}

export function runBacktest(query: RunQuery & { strategy: StrategyId }): Promise<Result<Backtest>> {
  return request<Backtest>("/backtests", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(query),
  });
}

export function getComparison(query: RunQuery): Promise<Result<Comparison>> {
  const params = new URLSearchParams({
    symbol: query.symbol,
    fee: String(query.fee),
    slippage: String(query.slippage),
  });
  if (query.start) params.set("start", query.start);
  if (query.end) params.set("end", query.end);
  return request<Comparison>(`/compare?${params}`);
}
