import type { ReactNode } from "react";

// 차트는 가로로만 늘어난다. 도형은 안쪽 SVG(viewBox 가로 1000 × 세로 height px)에 그리고
// preserveAspectRatio="none"으로 폭에 맞춘다. 선 굵기는 non-scaling-stroke로 유지한다.
// 글자와 점은 늘어나면 찌그러지므로 바깥 SVG에 가로 퍼센트, 세로 px 좌표로 그린다.
// 인라인 style 속성은 쓰지 않는다. 프록시나 CDN이 CSP로 막으면 차트가 통째로 사라진다.
// 색은 fill/stroke 클래스 대신 currentColor와 text-* 클래스로 준다. 브라우저 강제 다크 모드나
// 다크 모드 확장은 글자색은 제대로 바꾸지만 SVG의 fill/stroke 값은 잘못 바꾸는 일이 많다.

export const VIEW_W = 1000;

export type Label = { x: number; y: number; text: string; align?: "start" | "middle" | "end" };

export function linear(d0: number, d1: number, r0: number, r1: number) {
  const k = d1 === d0 ? 0 : (r1 - r0) / (d1 - d0);
  return (v: number) => r0 + (v - d0) * k;
}

// 1, 2, 2.5, 5 × 10^n 간격의 눈금
export function niceTicks(lo: number, hi: number, count = 4): number[] {
  const span = hi - lo;
  if (!(span > 0)) return [lo];
  const raw = span / count;
  const mag = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => s >= raw) ?? 10 * mag;
  // 정수 배수로 만들어야 0이 −0.00000001 같은 값이 되지 않는다.
  const ticks: number[] = [];
  for (let k = Math.ceil(lo / step - 1e-9); k * step <= hi + step * 1e-9; k++) {
    ticks.push(Number((k * step).toPrecision(12)) || 0);
  }
  return ticks;
}

// 월초 눈금. 기간이 길면 몇 달씩 건너뛴다.
export function monthTicks(startMs: number, endMs: number, max = 7) {
  const months: number[] = [];
  const d = new Date(startMs);
  let t = Date.UTC(d.getUTCFullYear(), d.getUTCMonth() + 1, 1);
  while (t <= endMs) {
    months.push(t);
    const n = new Date(t);
    t = Date.UTC(n.getUTCFullYear(), n.getUTCMonth() + 1, 1);
  }
  const every = Math.max(1, Math.ceil(months.length / max));
  return months.filter((_, i) => i % every === 0);
}

export function monthLabel(ms: number) {
  const d = new Date(ms);
  const month = d.toLocaleDateString("en-US", { month: "short", timeZone: "UTC" });
  return d.getUTCMonth() === 0 ? `${month} ${d.getUTCFullYear()}` : month;
}

// 가운데 정렬 글자가 차트 밖으로 삐져나가지 않게 가장자리에서는 안쪽으로 붙인다.
function edgeAlign(l: Label): Label["align"] {
  if (l.align !== "middle") return l.align;
  if (l.x < VIEW_W * 0.03) return "start";
  if (l.x > VIEW_W * 0.97) return "end";
  return "middle";
}

export function pctX(x: number) {
  return `${(x / VIEW_W) * 100}%`;
}

const ANCHOR = { start: "start", middle: "middle", end: "end" } as const;

export function ChartFrame({
  height,
  label,
  labels,
  overlay,
  children,
}: {
  height: number;
  label: string;
  labels: Label[];
  overlay?: ReactNode; // 바깥 SVG 좌표(가로 %, 세로 px)로 그릴 것
  children: ReactNode;
}) {
  return (
    <svg width="100%" height={height} className="block overflow-visible" role="img" aria-label={label}>
      <svg
        width="100%"
        height={height}
        viewBox={`0 0 ${VIEW_W} ${height}`}
        preserveAspectRatio="none"
        className="overflow-visible"
      >
        {children}
      </svg>
      {overlay}
      {labels.map((l, i) => (
        <text
          key={i}
          aria-hidden="true"
          x={pctX(l.x)}
          y={l.y + 9}
          textAnchor={ANCHOR[edgeAlign(l) ?? "start"]}
          fill="currentColor"
          className="font-mono text-[11px] text-muted tabular-nums"
        >
          {l.text}
        </text>
      ))}
    </svg>
  );
}

export function polyline(xs: number[], ys: number[]) {
  return xs.map((x, i) => `${x.toFixed(2)},${ys[i].toFixed(2)}`).join(" ");
}
