import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { Empty, ErrorBox, PlatformBadge, Section, StatusBadge } from "../components/ui";
import { fmtDate } from "../format";
import type { ConnectorStatus, InvestigationSummary } from "../types";

export default function InvestigationList() {
  const [items, setItems] = useState<InvestigationSummary[] | null>(null);
  const [status, setStatus] = useState<ConnectorStatus | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.listInvestigations().then(setItems).catch((e) => setError(e.message));
    api.connectorStatus().then(setStatus).catch(() => {});
  }, []);

  return (
    <div className="space-y-8">
      <Section title="Investigasi">
        {error && <ErrorBox error={error} />}
        {items && items.length === 0 && (
          <Empty>
            Belum ada investigasi. <Link to="/new" className="text-indigo-700 underline">Buat yang pertama</Link>{" "}
            (coba mode demo bila API key belum diisi).
          </Empty>
        )}
        <div className="grid gap-3 md:grid-cols-2">
          {items?.map((inv) => (
            <Link key={inv.id} to={`/investigations/${inv.id}`} className="card block transition hover:border-indigo-300">
              <div className="flex items-start justify-between gap-2">
                <div className="font-semibold text-slate-900">{inv.title}</div>
                <div className="flex gap-1">
                  {inv.demo && <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-800">Demo</span>}
                  <StatusBadge status={inv.status} />
                </div>
              </div>
              {inv.subject_name && <div className="text-sm text-slate-600">Subjek: {inv.subject_name}</div>}
              <p className="mt-1 line-clamp-2 text-sm text-slate-500">{inv.purpose}</p>
              <div className="mt-2 text-xs text-slate-400">
                Dibuat {fmtDate(inv.created_at)} · Dikumpulkan {fmtDate(inv.collected_at)}
              </div>
            </Link>
          ))}
        </div>
      </Section>

      {status && (
        <Section title="Status konektor">
          <div className="grid gap-3 md:grid-cols-2">
            {status.connectors.map((c) => (
              <div key={c.platform} className="card">
                <div className="flex items-center justify-between">
                  <PlatformBadge platform={c.platform} />
                  <span className={`text-xs font-medium ${c.configured ? "text-emerald-700" : "text-slate-500"}`}>
                    {c.configured ? "● Terkonfigurasi" : "○ Belum dikonfigurasi"}
                  </span>
                </div>
                <p className="mt-2 text-xs text-slate-600">{c.limitations}</p>
              </div>
            ))}
            <div className="card">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">AI (Claude)</span>
                <span className={`text-xs font-medium ${status.ai.configured ? "text-emerald-700" : "text-slate-500"}`}>
                  {status.ai.configured ? `● ${status.ai.model}` : "○ Nonaktif (ANTHROPIC_API_KEY kosong)"}
                </span>
              </div>
              <p className="mt-2 text-xs text-slate-600">
                Riset web publik, analisis afiliasi berbukti, klasifikasi topik/sentimen, dan ringkasan laporan.
              </p>
            </div>
          </div>
        </Section>
      )}
    </div>
  );
}
