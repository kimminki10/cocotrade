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

export async function getMarkets(): Promise<Market[]> {
  const res = await fetch(`${apiUrl}/api/markets`, { cache: "no-store" });
  if (!res.ok) throw new Error(`GET /api/markets failed: ${res.status}`);
  return res.json();
}
