import type { Metadata } from "next";
import { Suspense } from "react";
import { PageIntro, Notice } from "@/components/report";
import { RunSettings } from "@/components/run-settings";
import { copy } from "@/content/copy";
import { getMarkets } from "@/lib/api";
import { parseRunForm, parseStrategy } from "@/lib/run-form";
import { BacktestResult } from "./result";

export const metadata: Metadata = { title: `${copy.backtest.eyebrow} · ${copy.site.name}` };

export default async function BacktestPage({ searchParams }: PageProps<"/backtest">) {
  const sp = await searchParams;
  const markets = await getMarkets();
  const form = parseRunForm(sp, markets);
  const strategy = parseStrategy(sp);

  return (
    <>
      <PageIntro eyebrow={copy.backtest.eyebrow} title={copy.backtest.title} lead={copy.backtest.lead} />
      <RunSettings form={form} markets={markets} strategy={strategy} submit={copy.form.runBacktest} />
      <div className="mt-10">
        <Suspense key={JSON.stringify([strategy, form])} fallback={<Notice>{copy.backtest.loading}</Notice>}>
          <BacktestResult strategy={strategy} form={form} />
        </Suspense>
      </div>
    </>
  );
}
