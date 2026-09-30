import type { ReactNode } from "react";

// 리서치 노트 형식의 공통 조각: 머리말, 그림과 설명, 지표 한 칸.

export function PageIntro({ eyebrow, title, lead }: { eyebrow: string; title: string; lead: string }) {
  return (
    <section className="flex max-w-3xl flex-col gap-4 pt-10 pb-8 sm:pt-12">
      <div className="text-sm tracking-[0.08em] text-muted uppercase">{eyebrow}</div>
      <h1 className="font-serif text-4xl leading-tight font-normal text-pretty sm:text-5xl">{title}</h1>
      <p className="max-w-2xl text-lg leading-relaxed text-muted">{lead}</p>
    </section>
  );
}

export function Figure({ n, caption, children }: { n: number; caption: string; children: ReactNode }) {
  return (
    <figure className="m-0 flex min-w-0 flex-col gap-3">
      {children}
      <figcaption className="text-sm leading-normal text-muted">
        <strong className="font-semibold text-ink">Fig. {n}.</strong> {caption}
      </figcaption>
    </figure>
  );
}

export function Stat({ label, value, note }: { label: string; value: string; note?: string }) {
  return (
    <div className="min-w-0">
      <dt className="text-[13px] text-muted">{label}</dt>
      <dd className="m-0 mt-1.5 font-mono text-[26px] leading-tight tabular-nums sm:text-3xl">{value}</dd>
      {note ? <dd className="m-0 mt-1 text-[13px] text-muted">{note}</dd> : null}
    </div>
  );
}

export function Notice({ tone = "muted", children }: { tone?: "muted" | "error"; children: ReactNode }) {
  return (
    <p
      className={`border-l-2 py-1 pl-4 text-[15px] ${tone === "error" ? "border-down text-down" : "border-rule text-muted"}`}
      role={tone === "error" ? "alert" : "status"}
    >
      {children}
    </p>
  );
}
