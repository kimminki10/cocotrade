import { getMarkets } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function Home() {
  const markets = await getMarkets();

  return (
    <main className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="text-2xl font-semibold">cocotrade</h1>
      <p className="mt-2 text-sm text-neutral-500">
        Backtests and live track record of Jev decisions on crypto markets. Not investment advice.
      </p>

      <h2 className="mt-10 text-lg font-medium">Market data</h2>
      <table className="mt-3 w-full text-left text-sm">
        <thead className="text-neutral-500">
          <tr>
            <th className="py-1">Symbol</th>
            <th>Timeframe</th>
            <th>Candles</th>
            <th>First</th>
            <th>Last</th>
          </tr>
        </thead>
        <tbody>
          {markets.map((m) => (
            <tr key={`${m.exchange}-${m.symbol}-${m.timeframe}`} className="border-t border-neutral-200">
              <td className="py-1">{m.symbol}</td>
              <td>{m.timeframe}</td>
              <td>{m.candles.toLocaleString()}</td>
              <td>{m.first.slice(0, 16).replace("T", " ")}</td>
              <td>{m.last.slice(0, 16).replace("T", " ")}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
