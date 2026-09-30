import type { Market, RunQuery, StrategyId } from "@/lib/api";

// 설정은 URL 검색 매개변수로 주고받는다. 결과 주소를 그대로 공유할 수 있다.
// 수수료와 슬리피지는 URL과 입력란에서 퍼센트(0.1 = 0.1%)로, API에는 비율로 보낸다.

export const DEFAULTS = { symbol: "BTC/USDT", feePct: "0.1", slippagePct: "0.05" } as const;

export const STRATEGY_IDS: StrategyId[] = [
  "buy_hold",
  "sma_cross",
  "macd",
  "donchian",
  "rsi",
  "bollinger",
];

export type RunForm = {
  symbol: string;
  start: string;
  end: string;
  feePct: string;
  slippagePct: string;
};

type SearchParams = Record<string, string | string[] | undefined>;

function one(sp: SearchParams, key: string) {
  const v = sp[key];
  return (Array.isArray(v) ? v[0] : v)?.trim() ?? "";
}

const DATE = /^\d{4}-\d{2}-\d{2}$/;

export function parseRunForm(sp: SearchParams, markets: Market[]): RunForm {
  const symbols = markets.map((m) => m.symbol);
  const symbol = one(sp, "symbol");
  const start = one(sp, "start");
  const end = one(sp, "end");
  const fee = one(sp, "fee");
  const slippage = one(sp, "slippage");
  return {
    symbol: symbols.includes(symbol) ? symbol : DEFAULTS.symbol,
    start: DATE.test(start) ? start : "",
    end: DATE.test(end) ? end : "",
    feePct: fee !== "" && Number.isFinite(Number(fee)) ? fee : DEFAULTS.feePct,
    slippagePct: slippage !== "" && Number.isFinite(Number(slippage)) ? slippage : DEFAULTS.slippagePct,
  };
}

export function parseStrategy(sp: SearchParams): StrategyId {
  const id = one(sp, "strategy") as StrategyId;
  return STRATEGY_IDS.includes(id) ? id : "sma_cross";
}

function fraction(percent: string) {
  return Number((Number(percent) / 100).toFixed(8));
}

export function toQuery(form: RunForm): RunQuery {
  return {
    symbol: form.symbol,
    start: form.start || undefined,
    end: form.end || undefined,
    fee: fraction(form.feePct),
    slippage: fraction(form.slippagePct),
  };
}

export function toSearch(form: RunForm, extra: Record<string, string> = {}) {
  const params = new URLSearchParams(extra);
  params.set("symbol", form.symbol);
  if (form.start) params.set("start", form.start);
  if (form.end) params.set("end", form.end);
  params.set("fee", form.feePct);
  params.set("slippage", form.slippagePct);
  return params.toString();
}
