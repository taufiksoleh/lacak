import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import ActivityHeatmap from "../components/ActivityHeatmap";
import AffiliationGraph from "../components/AffiliationGraph";
import { DailyChart, TypeBreakdown } from "../components/Charts";
import EntityTable from "../components/EntityTable";
import SignalList from "../components/SignalList";
import TimelineList from "../components/TimelineList";
import { Empty, ErrorBox, ExtLink, PlatformBadge, Section, StatTile, StatusBadge } from "../components/ui";
import { CATEGORY_LABEL, PLATFORM_LABEL, TYPE_LABEL, fmtDate, fmtNumber } from "../format";
import type { Activity, Finding, GraphData, Investigation, WebFinding } from "../types";

const TABS = ["Ringkasan", "Timeline", "Graf Afiliasi", "Organisasi", "Riset Web"] as const;
type Tab = (typeof TABS)[number];

export default function InvestigationDetail() {
  const id = Number(useParams().id);
  const nav = useNavigate();
  const [inv, setInv] = useState<Investigation | null>(null);
  const [tab, setTab] = useState<Tab>("Ringkasan");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const load = useCallback(() => api.getInvestigation(id).then(setInv).catch((e) => setError(e.message)), [id]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (inv?.status !== "running") return;
    const t = setInterval(load, 2000);
    return () => clearInterval(t);
  }, [inv?.status, load]);

  if (error) return <ErrorBox error={error} />;
  if (!inv) return <p className="text-slate-500">Memuat…</p>;

  const recollect = async () => {
    setNotice("");
    try {
      await api.collect(id);
      load();
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const onImport = async (file: File) => {
    try {
      const r = await api.importFile(id, file);
      setNotice(`Import: ${r.imported} aktivitas masuk, ${r.skipped} dilewati.${r.errors.length ? " Catatan: " + r.errors.slice(0, 3).join("; ") : ""}`);
      load();
    } catch (e) {
      setNotice(`Import gagal: ${(e as Error).message}`);
    }
  };

  const remove = async () => {
    if (!confirm("Hapus investigasi ini beserta seluruh data yang dikumpulkan?")) return;
    await api.deleteInvestigation(id);
    nav("/");
  };

  const ready = inv.status !== "running";

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-semibold text-slate-900">{inv.title}</h1>
            <StatusBadge status={inv.status} />
            {inv.demo && <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-800">Demo</span>}
          </div>
          <p className="mt-1 max-w-3xl text-sm text-slate-600">
            <b>Tujuan:</b> {inv.purpose}
          </p>
          <p className="text-xs text-slate-400">Terakhir dikumpulkan: {fmtDate(inv.collected_at)}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button className="btn-secondary" disabled={!ready} onClick={recollect}>
            ↻ Kumpulkan ulang
          </button>
          <button className="btn-secondary" disabled={!ready} onClick={() => fileRef.current?.click()}>
            ⇪ Import JSON/CSV
          </button>
          <input
            ref={fileRef}
            type="file"
            accept=".json,.csv"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) onImport(f);
              e.target.value = "";
            }}
          />
          <Link className="btn-primary" to={`/investigations/${id}/report`}>
            📄 Laporan
          </Link>
          <button className="btn-danger" onClick={remove}>
            Hapus
          </button>
        </div>
      </div>

      {inv.status === "running" && (
        <div className="rounded-lg border border-blue-200 bg-blue-50 p-3 text-sm text-blue-800">
          {inv.status_detail || "Sedang memproses…"}
        </div>
      )}
      {inv.status !== "running" && inv.status_detail && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">{inv.status_detail}</div>
      )}
      {notice && <div className="rounded-lg border border-slate-200 bg-white p-3 text-sm">{notice}</div>}

      <div className="flex gap-1 overflow-x-auto border-b border-slate-200">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`whitespace-nowrap border-b-2 px-3 py-2 text-sm ${tab === t ? "border-indigo-600 font-medium text-indigo-700" : "border-transparent text-slate-500 hover:text-slate-800"}`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "Ringkasan" && <Overview inv={inv} />}
      {tab === "Timeline" && <TimelineTab inv={inv} />}
      {tab === "Graf Afiliasi" && <GraphTab id={id} key={inv.collected_at} />}
      {tab === "Organisasi" && <OrgTab id={id} key={inv.collected_at} />}
      {tab === "Riset Web" && <WebTab inv={inv} key={inv.collected_at} />}
    </div>
  );
}

function Overview({ inv }: { inv: Investigation }) {
  const s = inv.analysis.stats;
  const ai = inv.analysis.ai;
  return (
    <div className="space-y-6">
      <Section title="Akun">
        <div className="grid gap-3 md:grid-cols-2">
          {inv.accounts.map((a) => (
            <div key={a.id} className="card">
              <div className="flex items-center gap-2">
                <PlatformBadge platform={a.platform} />
                <ExtLink href={a.profile_url}>@{a.handle}</ExtLink>
                {a.verified && <span title="Terverifikasi">✔</span>}
                <span className="ml-auto text-xs text-slate-500">{a.activity_count} aktivitas</span>
              </div>
              {a.display_name && <div className="mt-1 font-medium">{a.display_name}</div>}
              {a.bio && <p className="mt-1 text-sm text-slate-600">{a.bio}</p>}
              <div className="mt-2 flex flex-wrap gap-x-4 text-xs text-slate-500">
                <span>Pengikut: {fmtNumber(a.followers)}</span>
                <span>Mengikuti: {fmtNumber(a.following)}</span>
                <span>Dibuat: {fmtDate(a.created_at_platform, false)}</span>
              </div>
              {a.links.length > 0 && (
                <div className="mt-1 space-y-0.5 text-xs">
                  {a.links.map((l) => (
                    <div key={l}><ExtLink href={l}>{l}</ExtLink></div>
                  ))}
                </div>
              )}
              {a.error && <p className="mt-2 rounded bg-red-50 p-2 text-xs text-red-700">{a.error}</p>}
            </div>
          ))}
        </div>
      </Section>

      {s && s.total > 0 ? (
        <>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <StatTile label="Total aktivitas" value={fmtNumber(s.total)} hint={`${s.span_days} hari`} />
            <StatTile label="Rata-rata / hari" value={s.avg_per_day} />
            <StatTile label="Jam paling aktif" value={`${String(s.most_active_hour).padStart(2, "0")}:00`} hint={s.timezone} />
            <StatTile label="Hari paling aktif" value={s.most_active_day} />
          </div>
          <div className="grid gap-4 lg:grid-cols-2">
            <div className="card">
              <h3 className="mb-2 font-medium">Pola waktu aktivitas publik</h3>
              <ActivityHeatmap stats={s} />
            </div>
            <div className="card space-y-4">
              <div>
                <h3 className="mb-2 font-medium">Jenis aktivitas</h3>
                <TypeBreakdown stats={s} />
              </div>
              <div>
                <h3 className="mb-1 font-medium">Per platform</h3>
                <div className="flex flex-wrap gap-3 text-sm">
                  {Object.entries(s.by_platform ?? {}).map(([p, v]) => (
                    <span key={p}>{PLATFORM_LABEL[p] ?? p}: <b>{v}</b></span>
                  ))}
                </div>
              </div>
            </div>
          </div>
          <div className="card">
            <h3 className="mb-2 font-medium">Aktivitas per hari</h3>
            <DailyChart stats={s} />
          </div>
        </>
      ) : (
        <Empty>Belum ada aktivitas. Kumpulkan data atau import file JSON/CSV.</Empty>
      )}

      <Section title="Indikator perilaku">
        <div className="card">
          <SignalList signals={inv.analysis.signals} />
        </div>
      </Section>

      <Section title="Ringkasan AI">
        {inv.analysis.ai_error && <ErrorBox error={inv.analysis.ai_error} />}
        {ai ? (
          <div className="card space-y-4">
            <p className="whitespace-pre-wrap text-sm leading-relaxed">{ai.summary}</p>
            {ai.topics.length > 0 && (
              <div>
                <h3 className="mb-2 font-medium">Topik</h3>
                <div className="grid gap-2 md:grid-cols-2">
                  {ai.topics.map((t) => (
                    <div key={t.topic} className="rounded-lg border border-slate-200 p-2 text-sm">
                      <div className="flex justify-between">
                        <b>{t.topic}</b>
                        <span className="text-slate-500">{t.share_percent}% · {t.sentiment}</span>
                      </div>
                      {t.example_urls.map((u) => (
                        <div key={u} className="text-xs"><ExtLink href={u}>{u}</ExtLink></div>
                      ))}
                    </div>
                  ))}
                </div>
              </div>
            )}
            {ai.notable_activities.length > 0 && (
              <div>
                <h3 className="mb-1 font-medium">Aktivitas menonjol</h3>
                <ul className="list-disc space-y-1 pl-5 text-sm">
                  {ai.notable_activities.map((n) => (
                    <li key={n.url}>{n.reason} — <ExtLink href={n.url}>sumber</ExtLink></li>
                  ))}
                </ul>
              </div>
            )}
            {ai.risk_notes.length > 0 && (
              <ul className="list-disc pl-5 text-sm text-amber-900">
                {ai.risk_notes.map((r) => <li key={r}>{r}</li>)}
              </ul>
            )}
          </div>
        ) : (
          <Empty>
            {inv.analysis.ai_enabled
              ? "Ringkasan AI akan muncul setelah pengumpulan data selesai."
              : "AI nonaktif. Isi ANTHROPIC_API_KEY di .env backend untuk riset web & ringkasan otomatis."}
          </Empty>
        )}
      </Section>
    </div>
  );
}

function TimelineTab({ inv }: { inv: Investigation }) {
  const [platform, setPlatform] = useState("");
  const [type, setType] = useState("");
  const [q, setQ] = useState("");
  const [page, setPage] = useState(0);
  const [data, setData] = useState<{ total: number; items: Activity[] } | null>(null);
  const size = 30;

  useEffect(() => {
    const t = setTimeout(() => {
      api.timeline(inv.id, { platform, type, q, limit: size, offset: page * size }).then(setData);
    }, 250);
    return () => clearTimeout(t);
  }, [inv.id, inv.collected_at, platform, type, q, page]);

  const platforms = [...new Set(inv.accounts.map((a) => a.platform))];
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        <select className="input max-w-44" value={platform} onChange={(e) => { setPlatform(e.target.value); setPage(0); }}>
          <option value="">Semua platform</option>
          {platforms.map((p) => <option key={p} value={p}>{PLATFORM_LABEL[p]}</option>)}
        </select>
        <select className="input max-w-44" value={type} onChange={(e) => { setType(e.target.value); setPage(0); }}>
          <option value="">Semua jenis</option>
          {Object.entries(TYPE_LABEL).filter(([k]) => k !== "mention").map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <input className="input max-w-xs" placeholder="Cari teks…" value={q} onChange={(e) => { setQ(e.target.value); setPage(0); }} />
        {data && <span className="self-center text-sm text-slate-500">{data.total} aktivitas</span>}
      </div>
      {data && data.items.length === 0 && <Empty>Tidak ada aktivitas yang cocok.</Empty>}
      {data && <TimelineList items={data.items} />}
      {data && data.total > size && (
        <div className="flex items-center justify-center gap-3">
          <button className="btn-secondary" disabled={page === 0} onClick={() => setPage(page - 1)}>← Sebelumnya</button>
          <span className="text-sm text-slate-500">Hal. {page + 1} / {Math.ceil(data.total / size)}</span>
          <button className="btn-secondary" disabled={(page + 1) * size >= data.total} onClick={() => setPage(page + 1)}>Berikutnya →</button>
        </div>
      )}
    </div>
  );
}

function GraphTab({ id }: { id: number }) {
  const [g, setG] = useState<GraphData | null>(null);
  useEffect(() => {
    api.graph(id).then(setG);
  }, [id]);
  if (!g) return <p className="text-slate-500">Memuat graf…</p>;
  if (g.top.length === 0) return <Empty>Belum ada interaksi (mention/reply/repost) yang terdeteksi.</Empty>;
  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <div className="lg:col-span-2">
        <AffiliationGraph data={g} />
      </div>
      <div className="card">
        <h3 className="mb-2 font-medium">Akun paling sering berinteraksi</h3>
        <table className="w-full text-sm">
          <tbody>
            {g.top.map((t) => (
              <tr key={t.handle} className="border-t border-slate-100">
                <td className="py-1.5">
                  <div className="font-medium">@{t.handle}</div>
                  {t.entity && <div className="text-xs text-red-700">{t.entity}</div>}
                  <div className="text-xs text-slate-500">
                    {Object.entries(t.kinds).map(([k, v]) => `${TYPE_LABEL[k] ?? k} ${v}`).join(" · ")}
                  </div>
                </td>
                <td className="text-right font-semibold tabular-nums">{t.weight}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function OrgTab({ id }: { id: number }) {
  const [findings, setFindings] = useState<Finding[] | null>(null);
  const [cat, setCat] = useState("");
  useEffect(() => {
    api.affiliations(id).then(setFindings);
  }, [id]);
  if (!findings) return <p className="text-slate-500">Memuat…</p>;
  const shown = findings.filter((f) => !cat || f.category === cat);
  return (
    <div className="space-y-3">
      <div className="rounded-lg border border-slate-200 bg-white p-3 text-sm text-slate-600">
        Skor menunjukkan <b>kekuatan indikasi</b> dari bukti publik, bukan kepastian afiliasi. Interaksi (repost/mention)
        dengan akun resmi lembaga bernilai rendah; tautan resmi di profil dan pernyataan di bio bernilai lebih tinggi.
        Kelola daftar organisasi di menu <Link className="text-indigo-700 underline" to="/entities">Daftar Entitas</Link>.
      </div>
      <div className="flex flex-wrap gap-1">
        {["", ...Object.keys(CATEGORY_LABEL)].map((c) => (
          <button key={c} onClick={() => setCat(c)} className={`rounded-full border px-3 py-1 text-xs ${cat === c ? "border-indigo-500 bg-indigo-50 text-indigo-700" : "border-slate-200 bg-white"}`}>
            {c ? CATEGORY_LABEL[c] : "Semua"}
          </button>
        ))}
      </div>
      {shown.length === 0 ? <Empty>Tidak ada indikasi afiliasi yang terdeteksi.</Empty> : <EntityTable findings={shown} />}
    </div>
  );
}

function WebTab({ inv }: { inv: Investigation }) {
  const [items, setItems] = useState<WebFinding[] | null>(null);
  useEffect(() => {
    api.webFindings(inv.id).then(setItems);
  }, [inv.id]);
  return (
    <div className="space-y-4">
      {inv.analysis.ai_research ? (
        <div className="card">
          <h3 className="mb-2 font-medium">Ringkasan riset web (AI)</h3>
          <p className="whitespace-pre-wrap text-sm leading-relaxed">{inv.analysis.ai_research}</p>
        </div>
      ) : (
        <Empty>Riset web membutuhkan AI aktif (ANTHROPIC_API_KEY).</Empty>
      )}
      {items && items.length > 0 && (
        <div className="space-y-2">
          <h3 className="font-medium">Sumber ({items.length})</h3>
          {items.map((w) => (
            <div key={w.id} className="card">
              <ExtLink href={w.url}>{w.title || w.url}</ExtLink>
              {w.snippet && <p className="mt-1 text-sm text-slate-600">“{w.snippet}”</p>}
              <div className="text-xs text-slate-400">{w.url}</div>
            </div>
          ))}
        </div>
      )}
      {inv.analysis.ai_caveats && inv.analysis.ai_caveats.length > 0 && (
        <div className="card text-sm">
          <h3 className="mb-1 font-medium">Catatan keterbatasan dari AI</h3>
          <ul className="list-disc pl-5">{inv.analysis.ai_caveats.map((c) => <li key={c}>{c}</li>)}</ul>
        </div>
      )}
    </div>
  );
}
