import type { MonkeySummary } from "@/lib/api";
import { pct } from "@/lib/format";
import { ChartFrame, type Label, VIEW_W, linear, niceTicks, pctX } from "./frame";

const ROW = 40; // 왼쪽 이름 줄의 h-10과 같아야 한다
const X_AXIS = 24;

export type ForestRow = { name: string; value: number; monkey: MonkeySummary };

// 전략마다 한 줄: 원숭이 분포(5–95, 25–75, 중앙값) 위에 전략 수익률을 점으로 찍는다.
export function MonkeyForest({ rows, label }: { rows: ForestRow[]; label: string }) {
  const values = rows.flatMap((r) => [r.value, r.monkey.quantiles.p5, r.monkey.quantiles.p95]);
  const lo = Math.min(...values, 0);
  const hi = Math.max(...values, 0);
  const pad = (hi - lo) * 0.05 || 0.01;
  const sx = linear(lo - pad, hi + pad, 0, VIEW_W);
  const ticks = niceTicks(lo - pad, hi + pad, 5);
  const height = rows.length * ROW + X_AXIS;
  const bottom = rows.length * ROW;

  const labels: Label[] = ticks.map((v) => ({ x: sx(v), y: bottom + 8, text: pct(v, 0), align: "middle" }));

  return (
    <div className="grid grid-cols-[minmax(0,9rem)_minmax(0,1fr)] gap-x-4 sm:grid-cols-[11rem_minmax(0,1fr)]">
      <ul className="m-0 list-none p-0" aria-hidden="true">
        {rows.map((r) => (
          <li key={r.name} className="flex h-10 items-center truncate text-[15px]">
            {r.name}
          </li>
        ))}
      </ul>
      <div className="min-w-0">
        <ChartFrame
          height={height}
          label={label}
          labels={labels}
          overlay={rows.map((r, i) => (
            <circle
              key={r.name}
              cx={pctX(sx(r.value))}
              cy={i * ROW + ROW / 2}
              r={5}
              fill="currentColor"
              className="text-accent"
            />
          ))}
        >
          {ticks.map((v) => (
            <line
              key={v}
              x1={sx(v)}
              x2={sx(v)}
              y1={0}
              y2={bottom}
              stroke="currentColor"
              className={v === 0 ? "text-faint" : "text-rule"}
              strokeDasharray={v === 0 ? "3 3" : undefined}
              vectorEffect="non-scaling-stroke"
            />
          ))}
          <line x1={0} x2={VIEW_W} y1={bottom} y2={bottom} stroke="currentColor" className="text-ink" vectorEffect="non-scaling-stroke" />
          {rows.map((r, i) => {
            const y = i * ROW + ROW / 2;
            const q = r.monkey.quantiles;
            return (
              <g key={r.name}>
                <line x1={sx(q.p5)} x2={sx(q.p95)} y1={y} y2={y} stroke="currentColor" className="text-faint" vectorEffect="non-scaling-stroke" />
                <rect x={sx(q.p25)} width={sx(q.p75) - sx(q.p25)} y={y - 6} height={12} fill="currentColor" fillOpacity={0.7} className="text-flat" />
                <line
                  x1={sx(q.p50)}
                  x2={sx(q.p50)}
                  y1={y - 9}
                  y2={y + 9}
                  stroke="currentColor"
                  className="text-ink"
                  strokeWidth={1.5}
                  vectorEffect="non-scaling-stroke"
                />
              </g>
            );
          })}
        </ChartFrame>
      </div>
    </div>
  );
}
