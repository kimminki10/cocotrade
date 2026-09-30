import { pct } from "@/lib/format";
import { ChartFrame, type Label, VIEW_W, linear, niceTicks } from "./frame";

const X_AXIS = 22;
const BINS = 30;

export function MonkeyHistogram({
  returns,
  value,
  valueLabel,
  label,
  height = 180,
}: {
  returns: number[];
  value: number;
  valueLabel: string;
  label: string;
  height?: number;
}) {
  const lo = Math.min(...returns, value);
  const hi = Math.max(...returns, value);
  const pad = (hi - lo) * 0.04 || 0.01;
  const d0 = lo - pad;
  const d1 = hi + pad;
  const width = (d1 - d0) / BINS;
  const counts = new Array<number>(BINS).fill(0);
  for (const r of returns) counts[Math.min(BINS - 1, Math.floor((r - d0) / width))] += 1;

  const bottom = height - X_AXIS;
  const top = 26; // 전략 표시 글자 자리
  const sx = linear(d0, d1, 0, VIEW_W);
  const sy = linear(0, Math.max(...counts), bottom, top);
  const binW = VIEW_W / BINS;
  const x = sx(value);

  const labels: Label[] = [
    ...niceTicks(d0, d1, 5).map((v) => ({ x: sx(v), y: bottom + 8, text: pct(v, 0), align: "middle" as const })),
    { x, y: 4, text: valueLabel, align: x > VIEW_W * 0.75 ? "end" : x < VIEW_W * 0.25 ? "start" : "middle" },
  ];

  return (
    <ChartFrame height={height} label={label} labels={labels}>
      {counts.map((c, i) =>
        c ? (
          <rect key={i} x={i * binW + 1} width={binW - 2} y={sy(c)} height={bottom - sy(c)} fill="currentColor" className="text-flat" />
        ) : null,
      )}
      <line x1={0} x2={VIEW_W} y1={bottom} y2={bottom} stroke="currentColor" className="text-ink" vectorEffect="non-scaling-stroke" />
      {d0 < 0 && d1 > 0 ? (
        <line
          x1={sx(0)}
          x2={sx(0)}
          y1={top}
          y2={bottom}
          stroke="currentColor"
          className="text-faint"
          strokeDasharray="3 3"
          vectorEffect="non-scaling-stroke"
        />
      ) : null}
      <line x1={x} x2={x} y1={20} y2={bottom} stroke="currentColor" className="text-ink" strokeWidth={2} vectorEffect="non-scaling-stroke" />
    </ChartFrame>
  );
}
