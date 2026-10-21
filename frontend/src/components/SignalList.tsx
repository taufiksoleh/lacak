import type { Signals } from "../types";
import { LevelBadge } from "./ui";

export default function SignalList({ signals }: { signals?: Signals }) {
  if (!signals || !signals.indicators?.length) {
    return <p className="text-sm text-slate-500">{signals?.note ?? "Belum ada data."}</p>;
  }
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 text-sm">
        <span className="font-medium">Indikasi pola terkoordinasi/otomatis:</span>
        <LevelBadge level={signals.overall} />
      </div>
      <div className="grid gap-2 sm:grid-cols-2">
        {signals.indicators.map((i) => (
          <div key={i.key} className="rounded-lg border border-slate-200 p-3">
            <div className="flex items-center justify-between gap-2">
              <span className="text-sm font-medium">{i.label}</span>
              <LevelBadge level={i.level} />
            </div>
            <div className="mt-1 text-lg font-semibold tabular-nums">{i.display}</div>
            <p className="text-xs text-slate-500">{i.description}</p>
          </div>
        ))}
      </div>
      <p className="text-xs italic text-slate-500">{signals.note}</p>
    </div>
  );
}
