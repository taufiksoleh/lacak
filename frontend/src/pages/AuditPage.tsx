import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { Section } from "../components/ui";
import { fmtDate } from "../format";
import type { AuditEntry } from "../types";

export default function AuditPage() {
  const [items, setItems] = useState<AuditEntry[]>([]);
  useEffect(() => {
    api.audit().then(setItems);
  }, []);
  return (
    <Section title="Log audit">
      <p className="text-sm text-slate-600">Setiap pembuatan investigasi, pengumpulan data, import, akses laporan, dan penghapusan tercatat di sini.</p>
      <div className="card overflow-x-auto p-0">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-xs text-slate-500">
            <tr><th className="p-2">Waktu</th><th>Aksi</th><th>Investigasi</th><th>Detail</th></tr>
          </thead>
          <tbody>
            {items.map((a) => (
              <tr key={a.id} className="border-t border-slate-100">
                <td className="whitespace-nowrap p-2 text-xs">{fmtDate(a.created_at)}</td>
                <td className="font-mono text-xs">{a.action}</td>
                <td>{a.investigation_id ? <Link className="text-indigo-700" to={`/investigations/${a.investigation_id}`}>#{a.investigation_id}</Link> : "—"}</td>
                <td className="text-xs text-slate-600">{a.detail}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Section>
  );
}
