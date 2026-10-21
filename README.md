# Lacak — Dashboard OSINT Aktivitas Publik Media Sosial

[![CI](https://github.com/taufiksoleh/lacak/actions/workflows/ci.yml/badge.svg)](https://github.com/taufiksoleh/lacak/actions/workflows/ci.yml)

Lacak membantu analis keamanan menelusuri **aktivitas publik** sebuah akun di **X/Twitter, Instagram,
Threads, dan YouTube**, lalu menyusun laporan yang komprehensif:

- **Timeline aktivitas publik** — postingan, balasan/komentar, repost, quote; filter & pencarian.
- **Pola waktu** — heatmap jam × hari (zona waktu lokal), aktivitas per hari, jenis aktivitas.
- **Graf afiliasi akun** — akun yang paling sering di-mention/di-reply/di-repost, dikelompokkan per komunitas.
- **Indikasi afiliasi organisasi** — pemerintah, partai, perusahaan, media, LSM; setiap indikasi punya
  skor dan **bukti berupa tautan sumber**.
- **Indikator perilaku** — rasio repost, teks berulang, konsentrasi jam posting, aktivitas dini hari,
  volume vs umur akun (indikasi pola terkoordinasi/otomatis).
- **AI (Claude)** — riset web publik dengan sumber, analisis afiliasi (klaim tanpa bukti dibuang),
  klasifikasi topik & sentimen, dan ringkasan laporan dalam Bahasa Indonesia.
- **Laporan** siap cetak / simpan PDF dari browser.

## Prinsip & batasan (penting)

- **Hanya data publik**: API resmi platform, file import dari analis, dan riset web publik. Tidak ada
  scraping dengan login, bypass privasi, atau akses akun privat.
- **Status "online / last seen" tidak tersedia** di API mana pun dan tidak dibuat. Yang dianalisis
  adalah pola waktu aktivitas publik.
- **Afiliasi = indikasi, bukan vonis.** Interaksi saja (repost/mention akun lembaga) dibatasi maksimal
  skor 45% ("Sedang"); skor tinggi butuh bukti di profil (tautan resmi, bio).
- **Akuntabilitas**: tujuan investigasi wajib diisi, semua aksi (buat, kumpulkan, import, lihat
  laporan, hapus) tercatat di **Log Audit**, dan data investigasi dapat dihapus total.
- Gunakan secara sah dan proporsional sesuai UU No. 27/2022 tentang Pelindungan Data Pribadi.
  Jangan gunakan untuk menguntit, melecehkan, atau mendiskriminasi.

### Cakupan per platform

| Platform | Sumber | Yang bisa diambil | Keterbatasan |
|---|---|---|---|
| X / Twitter | X API v2 (Bearer token, tier berbayar) | profil, tweet, reply, quote, repost, mention | like & akun privat tidak tersedia |
| YouTube | YouTube Data API v3 | profil channel, video yang diunggah, mention di deskripsi | API tidak bisa mendaftar semua komentar yang ditulis sebuah akun |
| Instagram | Graph API Business Discovery | profil & postingan akun Business/Creator | akun pribadi, komentar di postingan orang lain, story tidak tersedia |
| Threads | Threads API (`threads_profile_discovery`) | profil & postingan publik | balasan di thread orang lain terbatas |

Untuk data yang tidak tersedia lewat API (mis. komentar), gunakan **Import JSON/CSV**.

## Menjalankan

### Cepat dengan Docker

```bash
cp .env.example .env      # isi kredensial yang dimiliki (semuanya opsional)
docker compose up --build
# buka http://localhost:8000
```

### Pengembangan lokal

Backend (Python ≥ 3.11):

```bash
cd backend
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
cp ../.env.example .env   # opsional
uvicorn app.main:app --reload --port 8000
```

Frontend (Node ≥ 20):

```bash
cd frontend
npm install
npm run dev               # http://localhost:5173 (proxy /api ke :8000)
```

Tanpa API key apa pun, buat investigasi dengan tombol **"Isi contoh demo"** untuk mencoba semua fitur
dengan data fiktif.

### Tes & lint

```bash
cd backend && pytest && ruff check .
cd frontend && npm run lint && npm run build
```

Pengecekan yang sama berjalan otomatis di GitHub Actions (`.github/workflows/ci.yml`) untuk setiap
pull request dan push ke `main`, ditambah build image Docker dan smoke test `/api/health`.

## Format import

JSON (`list` atau `{"activities": [...]}`) atau CSV dengan kolom:

| kolom | wajib | contoh |
|---|---|---|
| `platform` | ya | `x`, `instagram`, `threads`, `youtube` |
| `handle` | ya | `budi_demo` (akun yang menulis) |
| `type` | ya | `post`, `reply`, `comment`, `repost`, `quote` |
| `created_at` | ya | `2026-10-01T10:00:00Z` (ISO 8601) |
| `text`, `url`, `id` | tidak | |
| `targets` | tidak | CSV: `reply:andi;mention:rina` · JSON: `[{"handle":"andi","kind":"reply"}]` |

Mention `@handle` di teks otomatis dideteksi. Akun yang belum ada di investigasi akan ditambahkan.

```csv
platform,handle,type,text,url,created_at,targets
youtube,budi_demo,comment,Mantap @kopisenja_id,https://youtube.com/watch?v=x,2026-10-01T10:00:00Z,
x,budi_demo,reply,Setuju,https://x.com/budi_demo/status/1,2026-10-02T10:00:00Z,reply:kemkomdigi
```

## Daftar entitas (organisasi)

Deteksi afiliasi berbasis aturan memakai `backend/data/entities.yaml` (dimuat ke database saat pertama
kali dijalankan) dan bisa ditambah lewat menu **Daftar Entitas**. Setiap entitas memiliki `handles`,
`domains` resmi, dan `keywords` spesifik. Tautan ke domain `.go.id`/`.mil.id` yang tidak terdaftar
dikelompokkan sebagai "Instansi pemerintah (domain .go.id)". **Verifikasi handle sebelum dipakai untuk
keputusan penting** — handle bisa berbeda antar platform dan bisa berubah.

Bobot bukti: tautan resmi di profil (0,5) > disebut di bio (0,4) > repost/quote/reply/mention
(0,04–0,05 per kejadian, maks. 0,3) > membagikan tautan domain resmi > menyebut nama. Skor digabung
secara probabilistik; tanpa bukti profil skor dibatasi 0,45.

## Arsitektur

```
backend/   FastAPI + SQLAlchemy (SQLite default, Postgres via DATABASE_URL)
  app/connectors/  youtube, x, instagram, threads, importer, demo  → format aktivitas seragam
  app/analysis/    activity (statistik & heatmap), graph (networkx), entities (aturan), signals
  app/ai/          client (Claude, fallback otomatis, lanjut pause_turn), research (web search),
                   affiliation & summarize (structured output, URL divalidasi terhadap data)
  app/services/    collector (pipeline), report_builder, audit
frontend/  React + Vite + TypeScript + Tailwind, Recharts, Cytoscape.js
```

Keamanan AI: semua teks dari media sosial/web dibungkus sebagai data tidak terpercaya (mitigasi
prompt injection), dan setiap URL bukti dari AI harus ada di data masukan; jika tidak, klaim dibuang.

## API ringkas

| Metode | Path | Fungsi |
|---|---|---|
| `POST` | `/api/investigations` | buat investigasi (`title`, `purpose`, `accounts`, `demo`) |
| `POST` | `/api/investigations/{id}/collect?use_ai=true` | kumpulkan data & analisis (background) |
| `POST` | `/api/investigations/{id}/import` | upload JSON/CSV |
| `GET` | `/api/investigations/{id}/timeline` | `platform`, `type`, `q`, `limit`, `offset` |
| `GET` | `/api/investigations/{id}/graph` · `/affiliations` · `/web-findings` · `/report` | hasil analisis |
| `DELETE` | `/api/investigations/{id}` | hapus semua data investigasi |
| `GET/POST/DELETE` | `/api/entities` | kelola daftar organisasi |
| `GET` | `/api/connectors/status` · `/api/audit` | status konektor, log audit |

Dokumentasi interaktif: `http://localhost:8000/docs`.
