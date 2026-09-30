import type { CurvePoint } from "@/lib/api";
import { money, pct } from "@/lib/format";
import {
  ChartFrame,
  type Label,
  VIEW_W,
  linear,
  monthLabel,
  monthTicks,
  niceTicks,
  polyline,
} from "./frame";

const X_AXIS = 22; // 아래 월 표시 자리

function timeScale(points: CurvePoint[]) {
  const t = points.map((p) => Date.parse(p.ts));
  return { t, sx: linear(t[0], t[t.length - 1], 0, VIEW_W) };
}

function monthAxis(t: number[], sx: (v: number) => number, bottom: number): Label[] {
  return monthTicks(t[0], t[t.length - 1]).map((m) => ({
    x: sx(m),
    y: bottom + 8,
    text: monthLabel(m),
    align: "middle",
  }));
}

export function EquityChart({ points, label, height = 260 }: { points: CurvePoint[]; label: string; height?: number }) {
  const { t, sx } = timeScale(points);
  const values = points.flatMap((p) => [p.equity, p.benchmark]);
  const lo = Math.min(...values);
  const hi = Math.max(...values);
  const pad = (hi - lo) * 0.06 || hi * 0.01;
  const bottom = height - X_AXIS;
  const sy = linear(lo - pad, hi + pad, bottom, 8);
  const ticks = niceTicks(lo - pad, hi + pad, 4);
  const xs = t.map(sx);

  const labels: Label[] = [
    ...ticks.map((v) => ({ x: 0, y: sy(v) - 15, text: money(v) })),
    ...monthAxis(t, sx, bottom),
  ];

  return (
    <ChartFrame height={height} label={label} labels={labels}>
      {ticks.map((v) => (
        <line key={v} x1={0} x2={VIEW_W} y1={sy(v)} y2={sy(v)} stroke="currentColor" className="text-rule" vectorEffect="non-scaling-stroke" />
      ))}
      <polyline
        points={polyline(xs, points.map((p) => sy(p.benchmark)))}
        fill="none"
        stroke="currentColor"
        className="text-faint"
        strokeWidth={1.5}
        strokeDasharray="5 4"
        vectorEffect="non-scaling-stroke"
      />
      <polyline
        points={polyline(xs, points.map((p) => sy(p.equity)))}
        fill="none"
        stroke="currentColor"
        className="text-ink"
        strokeWidth={2}
        strokeLinejoin="round"
        vectorEffect="non-scaling-stroke"
      />
    </ChartFrame>
  );
}

export function DrawdownChart({ points, label, height = 140 }: { points: CurvePoint[]; label: string; height?: number }) {
  const { t, sx } = timeScale(points);
  const deepest = Math.min(...points.map((p) => p.drawdown), -0.01);
  const bottom = height - X_AXIS;
  const sy = linear(deepest * 1.08, 0, bottom, 4);
  const ticks = niceTicks(deepest * 1.08, 0, 3).filter((v) => v < 0);
  const xs = t.map(sx);
  const ys = points.map((p) => sy(p.drawdown));
  const area = `${polyline(xs, ys)} ${VIEW_W},${sy(0)} 0,${sy(0)}`;

  const labels: Label[] = [
    ...ticks.map((v) => ({ x: 0, y: sy(v) - 15, text: pct(v, 0) })),
    ...monthAxis(t, sx, bottom),
  ];

  return (
    <ChartFrame height={height} label={label} labels={labels}>
      {ticks.map((v) => (
        <line key={v} x1={0} x2={VIEW_W} y1={sy(v)} y2={sy(v)} stroke="currentColor" className="text-rule" vectorEffect="non-scaling-stroke" />
      ))}
      <polygon points={area} fill="currentColor" fillOpacity={0.15} className="text-down" />
      <polyline points={polyline(xs, ys)} fill="none" stroke="currentColor" className="text-down" strokeWidth={1.25} vectorEffect="non-scaling-stroke" />
      <line x1={0} x2={VIEW_W} y1={sy(0)} y2={sy(0)} stroke="currentColor" className="text-ink" vectorEffect="non-scaling-stroke" />
    </ChartFrame>
  );
}
