import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import ActivityHeatmap from "../components/ActivityHeatmap";
import AffiliationGraph from "../components/AffiliationGraph";
import { DailyChart, TypeBreakdown } from "../components/Charts";
import EntityTable from "../components/EntityTable";
import SignalList from "../components/SignalList";
import { ErrorBox, ExtLink, PlatformBadge } from "../components/ui";
import { PLATFORM_LABEL, TYPE_LABEL, fmtDate, fmtNumber } from "../format";
import type { Report } from "../types";

function H({ n, children }: { n: number; children: React.ReactNode }) {
  return (
    <h2 className="mb-3 mt-8 border-b border-slate-300 pb-1 text-lg font-semibold text-slate-900">
      {n}. {children}
    </h2>
  );
}

export default function ReportPrint() {
  const id = Number(useParams().id);
  const [r, setR] = useState<Report | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.report(id).then(setR).catch((e) => setError(e.message));
  }, [id]);

  if (error) return <div className="p-6"><ErrorBox error={error} /></div>;
  if (!r) return <p className="p-6 text-slate-500">Menyusun laporan…</p>;

  const inv = r.investigation;
  const s = r.stats;
  let n = 0;
  return (
    <div className="mx-auto max-w-4xl bg-white px-8 py-8 text-[13px] leading-relaxed print:px-0">
      <div className="no-print mb-6 flex gap-2">
        <Link to={`/investigations/${id}`} className="btn-secondary">← Kembali</Link>
        <button className="btn-primary" onClick={() => window.print()}>🖨 Cetak / Simpan PDF</button>
      </div>

      <header className="border-b-2 border-slate-900 pb-4">
        <div className="text-xs uppercase tracking-widest text-slate-500">Laporan OSINT · Aktivitas Publik · RAHASIA</div>
        <h1 className="mt-1 text-2xl font-bold text-slate-900">{inv.title}</h1>
        {inv.subject_name && <div className="text-slate-700">Subjek: {inv.subject_name}</div>}
        <div className="mt-2 grid grid-cols-2 gap-x-6 text-xs text-slate-600">
          <span>Dibuat laporan: {fmtDate(r.generated_at)}</span>
          <span>Data dikumpulkan: {fmtDate(inv.collected_at)}</span>
          <span>No. investigasi: #{inv.id}</span>
          <span>Mode: {inv.demo ? "DEMO (data fiktif)" : "Data nyata"}</span>
        </div>
        <p className="mt-3 rounded bg-slate-100 p-2"><b>Tujuan:</b> {inv.purpose}</p>
      </header>

      <H n={++n}>Ringkasan eksekutif</H>
      {r.ai ? (
        <p className="whitespace-pre-wrap">{r.ai.summary}</p>
      ) : (
        <p className="text-slate-600">
          Ringkasan AI tidak tersedia{r.ai_error ? ` (${r.ai_error})` : ""}. Laporan ini berisi hasil analisis
          berbasis aturan: {s.total ?? 0} aktivitas publik dari {r.accounts.length} akun, {r.findings.length} indikasi
          afiliasi, dan tingkat indikator perilaku <b>{r.signals.overall ?? "-"}</b>.
        </p>
      )}

      <H n={++n}>Profil akun</H>
      <table className="w-full border-collapse text-left">
        <thead>
          <tr className="border-b border-slate-300 text-xs text-slate-500">
            <th className="py-1">Platform</th><th>Akun</th><th>Pengikut</th><th>Dibuat</th><th>Aktivitas</th>
          </tr>
        </thead>
        <tbody>
          {r.accounts.map((a) => (
            <tr key={a.id} className="border-b border-slate-100 align-top">
              <td className="py-1.5"><PlatformBadge platform={a.platform} /></td>
              <td>
                <ExtLink href={a.profile_url}>@{a.handle}</ExtLink> {a.display_name && `— ${a.display_name}`}
                {a.bio && <div className="text-xs text-slate-600">{a.bio}</div>}
                {a.error && <div className="text-xs text-red-700">{a.error}</div>}
              </td>
              <td className="tabular-nums">{fmtNumber(a.followers)}</td>
              <td>{fmtDate(a.created_at_platform, false)}</td>
              <td className="tabular-nums">{a.activity_count}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {s.total > 0 && (
        <>
          <H n={++n}>Pola aktivitas</H>
          <p>
            {s.total} aktivitas dalam {s.span_days} hari ({fmtDate(s.first, false)} – {fmtDate(s.last, false)}),
            rata-rata {s.avg_per_day}/hari. Paling aktif hari <b>{s.most_active_day}</b> sekitar pukul{" "}
            <b>{String(s.most_active_hour).padStart(2, "0")}:00</b> ({s.timezone}). Per platform:{" "}
            {Object.entries(s.by_platform ?? {}).map(([p, v]) => `${PLATFORM_LABEL[p] ?? p} ${v}`).join(", ")}.
          </p>
          <div className="mt-3 grid grid-cols-2 gap-6">
            <ActivityHeatmap stats={s} />
            <TypeBreakdown stats={s} />
          </div>
          <div className="mt-3"><DailyChart stats={s} height={160} /></div>
        </>
      )}

      <H n={++n}>Indikator perilaku</H>
      <SignalList signals={r.signals} />

      <div className="print-break" />
      <H n={++n}>Jaringan interaksi</H>
      {r.graph.top.length > 0 ? (
        <>
          <AffiliationGraph data={r.graph} height={380} />
          <table className="mt-3 w-full text-left">
            <thead>
              <tr className="border-b border-slate-300 text-xs text-slate-500"><th className="py-1">Akun</th><th>Interaksi</th><th>Platform</th><th className="text-right">Total</th></tr>
            </thead>
            <tbody>
              {r.graph.top.slice(0, 15).map((t) => (
                <tr key={t.handle} className="border-b border-slate-100">
                  <td className="py-1">@{t.handle} {t.entity && <span className="text-xs text-red-700">({t.entity})</span>}</td>
                  <td className="text-xs">{Object.entries(t.kinds).map(([k, v]) => `${TYPE_LABEL[k] ?? k} ${v}`).join(", ")}</td>
                  <td className="text-xs">{t.platforms.map((p) => PLATFORM_LABEL[p] ?? p).join(", ")}</td>
                  <td className="text-right tabular-nums">{t.weight}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      ) : (
        <p className="text-slate-600">Tidak ada interaksi terdeteksi.</p>
      )}

      <H n={++n}>Indikasi afiliasi organisasi</H>
      {r.findings.length > 0 ? <EntityTable findings={r.findings} expandAll maxEvidence={5} /> : <p className="text-slate-600">Tidak ada indikasi afiliasi.</p>}

      {r.ai && r.ai.topics.length > 0 && (
        <>
          <H n={++n}>Topik & sentimen</H>
          <ul className="list-disc pl-5">
            {r.ai.topics.map((t) => <li key={t.topic}><b>{t.topic}</b> — {t.share_percent}%, sentimen {t.sentiment}</li>)}
          </ul>
          {r.ai.notable_activities.length > 0 && (
            <>
              <h3 className="mt-3 font-medium">Aktivitas menonjol</h3>
              <ul className="list-disc pl-5">
                {r.ai.notable_activities.map((a) => <li key={a.url}>{a.reason} — <ExtLink href={a.url}>{a.url}</ExtLink></li>)}
              </ul>
            </>
          )}
        </>
      )}

      {(r.ai_research || r.web_findings.length > 0) && (
        <>
          <H n={++n}>Riset web publik</H>
          {r.ai_research && <p className="whitespace-pre-wrap">{r.ai_research}</p>}
          <ol className="mt-2 list-decimal space-y-1 pl-5 text-xs">
            {r.web_findings.map((w) => <li key={w.id}>{w.title} — <ExtLink href={w.url}>{w.url}</ExtLink></li>)}
          </ol>
        </>
      )}

      <H n={++n}>Sampel aktivitas terbaru</H>
      <table className="w-full text-left text-xs">
        <tbody>
          {r.recent_activities.map((a) => (
            <tr key={a.id} className="border-b border-slate-100 align-top">
              <td className="whitespace-nowrap py-1 pr-2">{fmtDate(a.created_at)}</td>
              <td className="pr-2">{PLATFORM_LABEL[a.platform]} · {TYPE_LABEL[a.type] ?? a.type}</td>
              <td>{a.text.slice(0, 200)} {a.url && <ExtLink href={a.url}>↗</ExtLink>}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <H n={++n}>Metodologi & keterbatasan</H>
      <ul className="list-disc space-y-1 pl-5">
        <li>Data hanya berasal dari sumber publik: API resmi platform, file yang di-import analis, dan riset web publik (AI).</li>
        <li>Status “online/last seen” tidak tersedia dari API mana pun; yang dianalisis adalah pola waktu aktivitas publik.</li>
        <li>Skor afiliasi adalah indikasi berbasis bukti (tautan profil, bio, interaksi, penyebutan), bukan bukti hubungan formal.</li>
        <li>Indikator perilaku bersifat statistik dan dapat menghasilkan positif palsu; verifikasi manual diperlukan.</li>
        {r.limitations.map((l) => <li key={l.platform}><b>{PLATFORM_LABEL[l.platform]}:</b> {l.text}</li>)}
        {r.ai_caveats.map((c) => <li key={c}>{c}</li>)}
      </ul>
      <p className="mt-6 border-t border-slate-300 pt-3 text-xs text-slate-500">
        Dokumen ini memuat data pribadi. Simpan dan bagikan hanya kepada pihak yang berwenang sesuai tujuan di atas
        dan ketentuan UU No. 27 Tahun 2022 tentang Pelindungan Data Pribadi.
      </p>
    </div>
  );
}
