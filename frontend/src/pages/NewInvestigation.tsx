import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { ErrorBox } from "../components/ui";
import { PLATFORM_LABEL } from "../format";

const PLATFORMS = ["x", "instagram", "threads", "youtube"];

export default function NewInvestigation() {
  const nav = useNavigate();
  const [title, setTitle] = useState("");
  const [subject, setSubject] = useState("");
  const [purpose, setPurpose] = useState("");
  const [demo, setDemo] = useState(false);
  const [ack, setAck] = useState(false);
  const [accounts, setAccounts] = useState([{ platform: "x", handle: "" }]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const update = (i: number, patch: Partial<{ platform: string; handle: string }>) =>
    setAccounts((a) => a.map((x, j) => (j === i ? { ...x, ...patch } : x)));

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const inv = await api.createInvestigation({
        title,
        subject_name: subject,
        purpose,
        demo,
        accounts: accounts.filter((a) => a.handle.trim()),
      });
      await api.collect(inv.id);
      nav(`/investigations/${inv.id}`);
    } catch (err) {
      setError((err as Error).message);
      setBusy(false);
    }
  }

  const fillDemo = () => {
    setTitle("Contoh: Akun demo Budi");
    setSubject("Budi (fiktif)");
    setPurpose("Demonstrasi fitur pelacakan aktivitas publik dan deteksi afiliasi untuk keamanan internet.");
    setAccounts(PLATFORMS.map((p) => ({ platform: p, handle: "budi_demo" })));
    setDemo(true);
  };

  return (
    <form onSubmit={submit} className="mx-auto max-w-2xl space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Investigasi baru</h1>
        <button type="button" className="btn-secondary" onClick={fillDemo}>
          Isi contoh demo
        </button>
      </div>
      {error && <ErrorBox error={error} />}

      <div className="card space-y-4">
        <div>
          <label className="label" htmlFor="title">Judul</label>
          <input id="title" className="input" required value={title} onChange={(e) => setTitle(e.target.value)} />
        </div>
        <div>
          <label className="label" htmlFor="subject">Nama subjek (opsional, membantu riset web)</label>
          <input id="subject" className="input" value={subject} onChange={(e) => setSubject(e.target.value)} />
        </div>
        <div>
          <label className="label" htmlFor="purpose">Tujuan investigasi (wajib)</label>
          <textarea
            id="purpose"
            className="input min-h-24"
            required
            minLength={20}
            placeholder="Mis. verifikasi apakah akun ini bagian dari jaringan penyebar hoaks yang menargetkan pengguna kami."
            value={purpose}
            onChange={(e) => setPurpose(e.target.value)}
          />
          <p className="mt-1 text-xs text-slate-500">Dicatat di log audit. Minimal 20 karakter.</p>
        </div>
      </div>

      <div className="card space-y-3">
        <div className="label">Akun yang dilacak</div>
        {accounts.map((a, i) => (
          <div key={i} className="flex gap-2">
            <select className="input max-w-40" value={a.platform} onChange={(e) => update(i, { platform: e.target.value })}>
              {PLATFORMS.map((p) => (
                <option key={p} value={p}>{PLATFORM_LABEL[p]}</option>
              ))}
            </select>
            <input
              className="input"
              placeholder="@username"
              aria-label="username"
              value={a.handle}
              onChange={(e) => update(i, { handle: e.target.value })}
            />
            {accounts.length > 1 && (
              <button type="button" className="btn-secondary" onClick={() => setAccounts(accounts.filter((_, j) => j !== i))}>
                ✕
              </button>
            )}
          </div>
        ))}
        <button type="button" className="btn-secondary" onClick={() => setAccounts([...accounts, { platform: "instagram", handle: "" }])}>
          + Tambah akun
        </button>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={demo} onChange={(e) => setDemo(e.target.checked)} />
          Mode demo (pakai data contoh fiktif, tanpa memanggil API platform)
        </label>
      </div>

      <label className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
        <input type="checkbox" className="mt-1" checked={ack} onChange={(e) => setAck(e.target.checked)} />
        <span>
          Saya memahami bahwa Lacak hanya mengolah data publik, hasil afiliasi adalah <b>indikasi</b> yang perlu
          diverifikasi, dan saya menggunakannya untuk tujuan yang sah (keamanan, riset, perlindungan) — bukan untuk
          menguntit, melecehkan, atau mendiskriminasi seseorang.
        </span>
      </label>

      <button className="btn-primary" disabled={busy || !ack || !accounts.some((a) => a.handle.trim())}>
        {busy ? "Memproses…" : "Buat & mulai kumpulkan data"}
      </button>
    </form>
  );
}
