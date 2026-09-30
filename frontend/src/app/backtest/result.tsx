import { DrawdownChart, EquityChart } from "@/components/charts/equity-chart";
import { MonkeyHistogram } from "@/components/charts/monkey-histogram";
import { Figure, Notice, Stat } from "@/components/report";
import { copy } from "@/content/copy";
import { type Metrics, type StrategyId, runBacktest } from "@/lib/api";
import { int, longDate, money, ordinal, pct, price, qty, ratio, utcDateTime } from "@/lib/format";
import { type RunForm, toQuery } from "@/lib/run-form";

const t = copy.backtest;
const m = copy.metrics;
const FILLS_SHOWN = 50;

// 표 1에 나란히 놓는 지표: [이름, 값 표기]
const TABLE: [keyof Metrics, (v: Metrics) => string][] = [
  ["total_return", (v) => pct(v.total_return)],
  ["cagr", (v) => pct(v.cagr)],
  ["volatility", (v) => pct(v.volatility, 1, false)],
  ["sharpe", (v) => ratio(v.sharpe)],
  ["sortino", (v) => ratio(v.sortino)],
  ["max_drawdown", (v) => pct(v.max_drawdown)],
  ["calmar", (v) => ratio(v.calmar)],
  ["win_rate", (v) => pct(v.win_rate, 0, false)],
  ["round_trips", (v) => int(v.round_trips)],
  ["fills", (v) => int(v.fills)],
  ["turnover", (v) => `${v.turnover.toFixed(1)}×`],
  ["exposure", (v) => pct(v.exposure, 0, false)],
];

export async function BacktestResult({ strategy, form }: { strategy: StrategyId; form: RunForm }) {
  const res = await runBacktest({ ...toQuery(form), strategy });
  if (!res.ok) return <Notice tone="error">{res.error}</Notice>;

  const { config, metrics, benchmark, curve, fills, monkey } = res.data;
  const name = copy.strategies[strategy].name;
  const from = longDate(config.start);
  const to = longDate(config.end);
  const params = Object.entries(config.params);
  const shown = fills.slice(-FILLS_SHOWN).reverse();

  return (
    <div className="flex flex-col gap-12">
      <section className="flex flex-col gap-2 border-t-2 border-ink pt-5">
        <h2 className="font-serif text-3xl font-medium">
          {name} <span className="text-muted">· {config.symbol}</span>
        </h2>
        <p className="max-w-2xl text-[15px] text-muted">
          {copy.strategies[strategy].summary}
          {params.length ? (
            <span className="font-mono text-[13px]">
              {" "}
              ({params.map(([k, v]) => `${k}=${v}`).join(", ")})
            </span>
          ) : null}
        </p>
      </section>

      <dl className="m-0 grid grid-cols-2 gap-6 sm:grid-cols-3 lg:grid-cols-5">
        <Stat label={m.total_return} value={pct(metrics.total_return)} note={m.versus(pct(benchmark.total_return))} />
        <Stat label={m.sharpe} value={ratio(metrics.sharpe)} note={m.versus(ratio(benchmark.sharpe))} />
        <Stat
          label={m.max_drawdown}
          value={pct(metrics.max_drawdown)}
          note={m.versus(pct(benchmark.max_drawdown))}
        />
        <Stat label={m.exposure} value={pct(metrics.exposure, 0, false)} note={t.fillsNote(int(metrics.fills))} />
        {monkey ? (
          <Stat
            label={copy.monkey.percentile}
            value={ordinal(monkey.percentile)}
            note={copy.monkey.percentileNote(monkey.runs)}
          />
        ) : null}
      </dl>

      <div className="grid gap-10 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <div className="flex min-w-0 flex-col gap-8">
          <Figure n={1} caption={t.fig.equity(name, config.symbol, from, to)}>
            <EquityChart points={curve} label={t.fig.equity(name, config.symbol, from, to)} />
          </Figure>
          <Figure n={2} caption={t.fig.drawdown}>
            <DrawdownChart points={curve} label={t.fig.drawdown} />
          </Figure>
        </div>

        <table className="w-full self-start border-collapse text-[15px]">
          <caption className="pb-2 text-left text-sm text-muted">
            <strong className="font-semibold text-ink">Table 1.</strong> {t.table(name)}
          </caption>
          <thead>
            <tr className="border-b border-ink text-left text-[13px] text-muted">
              <th className="py-2 font-medium" />
              <th className="py-2 text-right font-medium">{name}</th>
              <th className="py-2 text-right font-medium">{copy.strategies.buy_hold.name}</th>
            </tr>
          </thead>
          <tbody>
            {TABLE.map(([key, show]) => (
              <tr key={key} className="border-b border-rule">
                <th scope="row" className="py-2 text-left font-normal text-muted">
                  {m[key]}
                </th>
                <td className="py-2 text-right font-mono tabular-nums">{show(metrics)}</td>
                <td className="py-2 text-right font-mono text-muted tabular-nums">{show(benchmark)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {monkey ? (
        <Figure
          n={3}
          caption={t.fig.monkeys(monkey.runs, pct(monkey.exposure, 0, false), t.hours(Math.round(monkey.holding_bars)))}
        >
          <MonkeyHistogram
            returns={monkey.returns}
            value={metrics.total_return}
            valueLabel={t.fig.marker(name, pct(metrics.total_return), ordinal(monkey.percentile))}
            label={t.fig.monkeys(monkey.runs, pct(monkey.exposure, 0, false), t.hours(Math.round(monkey.holding_bars)))}
          />
        </Figure>
      ) : null}

      <section className="flex flex-col gap-3">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 className="font-serif text-2xl font-medium">{t.trades.heading}</h2>
          <p className="text-sm text-muted">
            {fills.length ? t.trades.showing(shown.length, fills.length) : t.trades.none}
          </p>
        </div>
        {fills.length ? (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] border-collapse text-[15px]">
              <thead>
                <tr className="border-b border-ink text-left text-[13px] text-muted">
                  <th className="py-2 font-medium">{t.trades.columns.ts}</th>
                  <th className="py-2 font-medium">{t.trades.columns.side}</th>
                  <th className="py-2 text-right font-medium">{t.trades.columns.price}</th>
                  <th className="py-2 text-right font-medium">{t.trades.columns.qty}</th>
                  <th className="py-2 text-right font-medium">{t.trades.columns.notional}</th>
                  <th className="py-2 text-right font-medium">{t.trades.columns.fee}</th>
                </tr>
              </thead>
              <tbody className="font-mono tabular-nums">
                {shown.map((f) => (
                  <tr key={`${f.ts}-${f.side}`} className="border-b border-rule">
                    <td className="py-2">{utcDateTime(f.ts)}</td>
                    <td className={`py-2 font-sans ${f.side === "buy" ? "text-up" : "text-down"}`}>
                      {t.trades.side[f.side]}
                    </td>
                    <td className="py-2 text-right">{price(f.price)}</td>
                    <td className="py-2 text-right">{qty(f.qty)}</td>
                    <td className="py-2 text-right">{money(f.notional, 2)}</td>
                    <td className="py-2 text-right">{money(f.fee, 2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>

      <p className="max-w-3xl text-sm leading-relaxed text-muted">
        {t.assumptions(pct(config.fee, 2, false), pct(config.slippage, 2, false))}
      </p>
    </div>
  );
}
