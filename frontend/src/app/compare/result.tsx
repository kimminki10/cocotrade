import Link from "next/link";
import { MonkeyForest } from "@/components/charts/monkey-forest";
import { Figure, Notice } from "@/components/report";
import { copy } from "@/content/copy";
import { getComparison } from "@/lib/api";
import { int, longDate, ordinal, pct, ratio } from "@/lib/format";
import { type RunForm, toQuery, toSearch } from "@/lib/run-form";

const t = copy.compare;

export async function ComparisonResult({ form }: { form: RunForm }) {
  const res = await getComparison(toQuery(form));
  if (!res.ok) return <Notice tone="error">{res.error}</Notice>;

  const { config, strategies } = res.data;
  const caption = t.fig(config.symbol, longDate(config.start), longDate(config.end));
  const rows = strategies.flatMap((s) =>
    s.monkey ? [{ name: copy.strategies[s.id].name, value: s.metrics.total_return, monkey: s.monkey }] : [],
  );

  return (
    <div className="flex flex-col gap-12">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[720px] border-collapse text-[15px]">
          <thead>
            <tr className="border-b border-ink text-left text-[13px] text-muted">
              <th className="py-2 font-medium">{t.columns.strategy}</th>
              <th className="py-2 text-right font-medium">{t.columns.total_return}</th>
              <th className="py-2 text-right font-medium">{t.columns.cagr}</th>
              <th className="py-2 text-right font-medium">{t.columns.sharpe}</th>
              <th className="py-2 text-right font-medium">{t.columns.max_drawdown}</th>
              <th className="py-2 text-right font-medium">{t.columns.fills}</th>
              <th className="py-2 text-right font-medium">{t.columns.exposure}</th>
              <th className="py-2 text-right font-medium">{t.columns.percentile}</th>
            </tr>
          </thead>
          <tbody className="font-mono tabular-nums">
            {strategies.map(({ id, metrics, monkey }) => (
              <tr key={id} className="border-b border-rule">
                <th scope="row" className="py-2.5 text-left font-sans font-normal">
                  <Link href={`/backtest?${toSearch(form, { strategy: id })}`} className="text-ink hover:text-accent">
                    {copy.strategies[id].name}
                  </Link>
                </th>
                <td className="py-2.5 text-right">{pct(metrics.total_return)}</td>
                <td className="py-2.5 text-right">{pct(metrics.cagr)}</td>
                <td className="py-2.5 text-right">{ratio(metrics.sharpe)}</td>
                <td className="py-2.5 text-right">{pct(metrics.max_drawdown)}</td>
                <td className="py-2.5 text-right">{int(metrics.fills)}</td>
                <td className="py-2.5 text-right">{pct(metrics.exposure, 0, false)}</td>
                <td className="py-2.5 text-right">{monkey ? ordinal(monkey.percentile) : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {rows.length ? (
        <Figure n={1} caption={caption}>
          <MonkeyForest rows={rows} label={caption} />
        </Figure>
      ) : null}
    </div>
  );
}
