import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { TYPE_LABEL } from "../format";
import type { Stats } from "../types";

export function DailyChart({ stats, height = 200 }: { stats: Stats; height?: number }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={stats.daily ?? []} margin={{ top: 4, right: 8, bottom: 0, left: -20 }}>
        <CartesianGrid vertical={false} stroke="#e2e8f0" />
        <XAxis dataKey="date" tick={{ fontSize: 10 }} minTickGap={24} />
        <YAxis allowDecimals={false} tick={{ fontSize: 10 }} />
        <Tooltip formatter={(v) => [v, "aktivitas"]} />
        <Bar dataKey="count" fill="#6366f1" radius={[3, 3, 0, 0]} isAnimationActive={false} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function TypeBreakdown({ stats }: { stats: Stats }) {
  const entries = Object.entries(stats.by_type ?? {});
  const total = entries.reduce((s, [, v]) => s + v, 0) || 1;
  return (
    <div className="space-y-1.5">
      {entries.map(([k, v]) => (
        <div key={k} className="flex items-center gap-2 text-sm">
          <span className="w-20 text-slate-600">{TYPE_LABEL[k] ?? k}</span>
          <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
            <div className="h-full bg-indigo-500" style={{ width: `${(100 * v) / total}%` }} />
          </div>
          <span className="w-16 text-right tabular-nums text-slate-600">
            {v} ({Math.round((100 * v) / total)}%)
          </span>
        </div>
      ))}
    </div>
  );
}
