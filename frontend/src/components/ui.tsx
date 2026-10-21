import type { ReactNode } from "react";
import { LEVEL_CLASS, LEVEL_LABEL, PLATFORM_COLOR, PLATFORM_LABEL, STATUS_LABEL } from "../format";

export function PlatformBadge({ platform }: { platform: string }) {
  return (
    <span
      className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium text-white"
      style={{ background: PLATFORM_COLOR[platform] ?? "#64748b" }}
    >
      {PLATFORM_LABEL[platform] ?? platform}
    </span>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const cls: Record<string, string> = {
    new: "bg-slate-100 text-slate-700",
    running: "bg-blue-100 text-blue-800 animate-pulse",
    done: "bg-emerald-100 text-emerald-800",
    error: "bg-red-100 text-red-800",
  };
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${cls[status] ?? ""}`}>
      {STATUS_LABEL[status] ?? status}
    </span>
  );
}

export function LevelBadge({ level }: { level: string }) {
  return (
    <span className={`rounded-full border px-2 py-0.5 text-xs font-medium ${LEVEL_CLASS[level]}`}>
      {LEVEL_LABEL[level] ?? level}
    </span>
  );
}

export function StatTile({ label, value, hint }: { label: string; value: ReactNode; hint?: string }) {
  return (
    <div className="card">
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-1 text-2xl font-semibold tabular-nums text-slate-900">{value}</div>
      {hint && <div className="mt-0.5 text-xs text-slate-500">{hint}</div>}
    </div>
  );
}

export function Section({ title, children, action }: { title: string; children: ReactNode; action?: ReactNode }) {
  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between gap-2">
        <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
        {action}
      </div>
      {children}
    </section>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return <div className="card text-center text-sm text-slate-500">{children}</div>;
}

export function ErrorBox({ error }: { error: string }) {
  return <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800">{error}</div>;
}

export function ExtLink({ href, children }: { href: string; children: ReactNode }) {
  if (!href) return <>{children}</>;
  return (
    <a href={href} target="_blank" rel="noopener noreferrer" className="text-indigo-700 hover:underline break-all">
      {children}
    </a>
  );
}
