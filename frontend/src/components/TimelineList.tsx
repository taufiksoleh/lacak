import { TYPE_LABEL, fmtDate } from "../format";
import type { Activity } from "../types";
import { ExtLink, PlatformBadge } from "./ui";

export default function TimelineList({ items }: { items: Activity[] }) {
  return (
    <ol className="relative space-y-3 border-l border-slate-200 pl-4">
      {items.map((a) => (
        <li key={a.id} className="card relative">
          <span className="absolute -left-[1.4rem] top-5 h-2.5 w-2.5 rounded-full bg-indigo-500 ring-4 ring-slate-50" />
          <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
            <PlatformBadge platform={a.platform} />
            <span className="rounded bg-slate-100 px-1.5 py-0.5 font-medium text-slate-700">
              {TYPE_LABEL[a.type] ?? a.type}
            </span>
            <span>@{a.handle}</span>
            <span>·</span>
            <time dateTime={a.created_at}>{fmtDate(a.created_at)}</time>
            {a.source !== "api" && <span className="rounded bg-amber-50 px-1.5 text-amber-700">{a.source}</span>}
          </div>
          <p className="mt-2 whitespace-pre-wrap text-sm text-slate-800">{a.text || <em>(tanpa teks)</em>}</p>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-xs">
            {a.targets.map((t) => (
              <span key={t.kind + t.handle} className="rounded-full bg-indigo-50 px-2 py-0.5 text-indigo-700">
                {TYPE_LABEL[t.kind] ?? t.kind} @{t.handle}
              </span>
            ))}
            {a.url && (
              <span className="ml-auto">
                <ExtLink href={a.url}>Lihat sumber ↗</ExtLink>
              </span>
            )}
          </div>
        </li>
      ))}
    </ol>
  );
}
