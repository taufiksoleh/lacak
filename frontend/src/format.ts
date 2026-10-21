export const PLATFORM_LABEL: Record<string, string> = {
  instagram: "Instagram",
  threads: "Threads",
  x: "X / Twitter",
  youtube: "YouTube",
};

export const PLATFORM_COLOR: Record<string, string> = {
  instagram: "#d6249f",
  threads: "#111827",
  x: "#0f766e",
  youtube: "#dc2626",
};

export const CATEGORY_LABEL: Record<string, string> = {
  government: "Pemerintah",
  party: "Partai politik",
  company: "Perusahaan",
  ngo: "LSM / Organisasi",
  media: "Media",
  other: "Lainnya",
};

export const TYPE_LABEL: Record<string, string> = {
  post: "Posting",
  reply: "Balasan",
  comment: "Komentar",
  repost: "Repost",
  quote: "Quote",
  mention: "Mention",
};

export const STATUS_LABEL: Record<string, string> = {
  new: "Baru",
  running: "Berjalan",
  done: "Selesai",
  error: "Gagal",
};

export const LEVEL_LABEL: Record<string, string> = {
  low: "Rendah",
  medium: "Sedang",
  high: "Tinggi",
  insufficient: "Data kurang",
};

export const LEVEL_CLASS: Record<string, string> = {
  low: "bg-emerald-50 text-emerald-700 border-emerald-200",
  medium: "bg-amber-50 text-amber-800 border-amber-200",
  high: "bg-red-50 text-red-700 border-red-200",
  insufficient: "bg-slate-50 text-slate-600 border-slate-200",
};

export function fmtDate(iso: string | null | undefined, withTime = true): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleString("id-ID", {
    dateStyle: "medium",
    ...(withTime ? { timeStyle: "short" } : {}),
  });
}

export function fmtNumber(n: number | null | undefined): string {
  return n == null ? "—" : n.toLocaleString("id-ID");
}

export function confidenceLabel(c: number): { label: string; cls: string } {
  if (c >= 0.6) return { label: "Kuat", cls: "bg-red-500" };
  if (c >= 0.3) return { label: "Sedang", cls: "bg-amber-500" };
  return { label: "Lemah", cls: "bg-slate-400" };
}
