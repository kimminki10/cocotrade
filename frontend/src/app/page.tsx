import { copy } from "@/content/copy";
import { getMarkets } from "@/lib/api";

export const dynamic = "force-dynamic";

const t = copy.markets.columns;

function utc(iso: string) {
  return iso.slice(0, 16).replace("T", " ");
}

export default async function Home() {
  const markets = await getMarkets();

  return (
    <>
      <section className="flex max-w-3xl flex-col gap-4 py-10 sm:py-12">
        <h1 className="font-serif text-4xl leading-tight font-normal text-pretty sm:text-5xl">
          {copy.home.title}
        </h1>
        <p className="max-w-2xl text-lg leading-relaxed text-muted">{copy.home.lead}</p>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="font-serif text-2xl font-medium">{copy.markets.heading}</h2>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[520px] border-collapse text-[15px]">
            <thead>
              <tr className="border-b border-ink text-left text-sm text-muted">
                <th className="py-2 font-medium">{t.symbol}</th>
                <th className="py-2 font-medium">{t.timeframe}</th>
                <th className="py-2 text-right font-medium">{t.candles}</th>
                <th className="py-2 text-right font-medium">{t.first}</th>
                <th className="py-2 text-right font-medium">{t.last}</th>
              </tr>
            </thead>
            <tbody className="font-mono tabular-nums">
              {markets.map((m) => (
                <tr key={`${m.exchange}-${m.symbol}-${m.timeframe}`} className="border-b border-rule">
                  <td className="py-2.5 font-sans">{m.symbol}</td>
                  <td className="py-2.5">{m.timeframe}</td>
                  <td className="py-2.5 text-right">{m.candles.toLocaleString("en-US")}</td>
                  <td className="py-2.5 text-right">{utc(m.first)}</td>
                  <td className="py-2.5 text-right">{utc(m.last)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}
