import type { Stats } from "../types";

export default function ActivityHeatmap({ stats }: { stats: Stats }) {
  const max = Math.max(1, ...stats.heatmap.flat());
  return (
    <div className="overflow-x-auto">
      <table className="border-separate border-spacing-0.5 text-[10px] text-slate-500">
        <thead>
          <tr>
            <th />
            {Array.from({ length: 24 }, (_, h) => (
              <th key={h} className="w-5 font-normal">
                {h % 3 === 0 ? h : ""}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {stats.heatmap.map((row, d) => (
            <tr key={d}>
              <td className="pr-2 text-right text-xs">{stats.days[d]}</td>
              {row.map((v, h) => (
                <td
                  key={h}
                  title={`${stats.days[d]} ${String(h).padStart(2, "0")}:00 — ${v} aktivitas`}
                  className="h-5 w-5 rounded-sm"
                  style={{
                    background: v ? `rgba(79, 70, 229, ${0.15 + (0.85 * v) / max})` : "#f1f5f9",
                  }}
                />
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-1 text-xs text-slate-500">Jam lokal ({stats.timezone}). Semakin gelap, semakin aktif.</p>
    </div>
  );
}
