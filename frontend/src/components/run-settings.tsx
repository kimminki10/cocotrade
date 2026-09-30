import Form from "next/form";
import type { ReactNode } from "react";
import { copy } from "@/content/copy";
import type { Market, StrategyId } from "@/lib/api";
import { utcDate } from "@/lib/format";
import { type RunForm, STRATEGY_IDS } from "@/lib/run-form";

const t = copy.form;

const input =
  "h-10 w-full border-0 border-b border-ink bg-transparent px-0 font-mono text-[15px] tabular-nums text-ink focus:border-accent focus:outline-none";

function Field({ label, children, className = "" }: { label: string; children: ReactNode; className?: string }) {
  return (
    <label className={`flex min-w-0 flex-col gap-1 ${className}`}>
      <span className="text-[13px] text-muted">{label}</span>
      {children}
    </label>
  );
}

// GET 폼이라 제출하면 설정이 URL에 들어간다. 자바스크립트가 없어도 동작한다.
export function RunSettings({
  form,
  markets,
  strategy,
  submit,
}: {
  form: RunForm;
  markets: Market[];
  strategy?: StrategyId;
  submit: string;
}) {
  const market = markets.find((m) => m.symbol === form.symbol) ?? markets[0];
  const min = market ? utcDate(market.first) : undefined;
  const max = market ? utcDate(market.last) : undefined;

  return (
    <Form action="" className="grid grid-cols-2 items-end gap-x-6 gap-y-5 sm:grid-cols-3 lg:grid-cols-[repeat(6,minmax(0,1fr))_auto]">
      {strategy ? (
        <Field label={t.strategy} className="col-span-2 sm:col-span-1">
          <select name="strategy" defaultValue={strategy} className={`${input} font-sans`}>
            {STRATEGY_IDS.map((id) => (
              <option key={id} value={id}>
                {copy.strategies[id].name}
              </option>
            ))}
          </select>
        </Field>
      ) : null}
      <Field label={t.symbol}>
        <select name="symbol" defaultValue={form.symbol} className={`${input} font-sans`}>
          {markets.map((m) => (
            <option key={m.symbol} value={m.symbol}>
              {m.symbol}
            </option>
          ))}
        </select>
      </Field>
      <Field label={t.start}>
        <input type="date" name="start" defaultValue={form.start || min} min={min} max={max} className={input} />
      </Field>
      <Field label={t.end}>
        <input type="date" name="end" defaultValue={form.end || max} min={min} max={max} className={input} />
      </Field>
      <Field label={t.fee}>
        <input type="number" name="fee" defaultValue={form.feePct} min={0} max={1} step={0.01} className={input} />
      </Field>
      <Field label={t.slippage}>
        <input
          type="number"
          name="slippage"
          defaultValue={form.slippagePct}
          min={0}
          max={1}
          step={0.01}
          className={input}
        />
      </Field>
      <button
        type="submit"
        className={`col-span-2 h-10 cursor-pointer bg-ink px-5 text-[15px] font-medium text-paper hover:bg-accent sm:col-span-1 ${strategy ? "" : "lg:col-start-7"}`}
      >
        {submit}
      </button>
    </Form>
  );
}
