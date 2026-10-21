import { useState } from "react";
import { CATEGORY_LABEL, confidenceLabel } from "../format";
import type { Finding } from "../types";
import { ExtLink } from "./ui";

export function EvidenceList({ evidence, max }: { evidence: Finding["evidence"]; max?: number }) {
  const shown = max ? evidence.slice(0, max) : evidence;
  return (
    <ul className="space-y-1.5 text-sm">
      {shown.map((e, i) => (
        <li key={i} className="rounded-md bg-slate-50 px-3 py-2">
          <span className="mr-2 rounded bg-slate-200 px-1.5 py-0.5 text-[11px] font-medium uppercase text-slate-700">
            {e.type}
          </span>
          <span className="text-slate-700">{e.detail}</span>
          {e.url && (
            <div className="mt-0.5 text-xs">
              <ExtLink href={e.url}>{e.url}</ExtLink>
            </div>
          )}
        </li>
      ))}
      {shown.length < evidence.length && (
        <li className="text-xs text-slate-500">+{evidence.length - shown.length} bukti lain (lihat di dashboard)</li>
      )}
    </ul>
  );
}

export function ConfidenceBar({ value }: { value: number }) {
  const { label, cls } = confidenceLabel(value);
  return (
    <div className="flex items-center gap-2">
      <div className="h-2 w-24 overflow-hidden rounded-full bg-slate-100">
        <div className={`h-full ${cls}`} style={{ width: `${Math.round(value * 100)}%` }} />
      </div>
      <span className="text-xs tabular-nums text-slate-600">
        {Math.round(value * 100)}% · {label}
      </span>
    </div>
  );
}

export default function EntityTable({
  findings,
  expandAll = false,
  maxEvidence,
}: {
  findings: Finding[];
  expandAll?: boolean;
  maxEvidence?: number;
}) {
  const [open, setOpen] = useState<number | null>(null);
  return (
    <div className="space-y-2">
      {findings.map((f) => {
        const expanded = expandAll || open === f.id;
        return (
          <div key={f.id} className="card">
            <button
              type="button"
              className="flex w-full flex-wrap items-center gap-3 text-left"
              onClick={() => setOpen(expanded ? null : f.id)}
            >
              <div className="min-w-0 flex-1">
                <div className="font-medium text-slate-900">{f.entity_name}</div>
                <div className="text-xs text-slate-500">
                  {CATEGORY_LABEL[f.category] ?? f.category} ·{" "}
                  {f.method === "ai" ? "Analisis AI" : "Aturan (rule-based)"} · {f.evidence.length} bukti
                </div>
              </div>
              <ConfidenceBar value={f.confidence} />
              <span className="no-print text-slate-400">{expanded ? "▲" : "▼"}</span>
            </button>
            <p className="mt-2 text-sm text-slate-600">{f.rationale}</p>
            {expanded && (
              <div className="mt-3">
                <EvidenceList evidence={f.evidence} max={maxEvidence} />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
