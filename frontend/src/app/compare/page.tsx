import type { Metadata } from "next";
import { Suspense } from "react";
import { Notice, PageIntro } from "@/components/report";
import { RunSettings } from "@/components/run-settings";
import { copy } from "@/content/copy";
import { getMarkets } from "@/lib/api";
import { parseRunForm } from "@/lib/run-form";
import { ComparisonResult } from "./result";

export const metadata: Metadata = { title: `${copy.nav.compare} · ${copy.site.name}` };

export default async function ComparePage({ searchParams }: PageProps<"/compare">) {
  const sp = await searchParams;
  const markets = await getMarkets();
  const form = parseRunForm(sp, markets);

  return (
    <>
      <PageIntro eyebrow={copy.compare.eyebrow} title={copy.compare.title} lead={copy.compare.lead} />
      <RunSettings form={form} markets={markets} submit={copy.form.runCompare} />
      <div className="mt-10">
        <Suspense key={JSON.stringify(form)} fallback={<Notice>{copy.compare.loading}</Notice>}>
          <ComparisonResult form={form} />
        </Suspense>
      </div>
    </>
  );
}
