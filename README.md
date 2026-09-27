# SI PERKARA — Chatbot Pencari Perkara Kejaksaan (Versi LangChain)

Aplikasi web chatbot AI untuk mencari dan memahami informasi perkara pada Kejaksaan.
Dibangun dengan **Next.js + Python LangChain (FastAPI)**, data perkara di **Astra DB**, AI pakai **Gemini**.

> **Tidak perlu API key pemilik repo.** Data contoh sudah termasuk di repo ini,
> jadi kamu bisa jalan dalam Mode Demo tanpa key apa pun.
> Mau AI beneran? Daftar key **gratis** milikmu sendiri (caranya di bawah, ±10 menit).

---

## Daftar Isi

1. [Gambaran arsitektur](#1-gambaran-arsitektur)
2. [Yang perlu disiapkan](#2-yang-perlu-disiapkan)
3. [Cara 1 — Mode Demo, tanpa API key (±5 menit)](#3-cara-1--mode-demo-tanpa-api-key-5-menit)
4. [Cara 2 — Full RAG dengan key gratis milikmu (±20 menit)](#4-cara-2--full-rag-dengan-key-gratis-milikmu-20-menit)
5. [Menjalankan sehari-hari](#5-menjalankan-sehari-hari)
6. [Struktur folder](#6-struktur-folder)
7. [Troubleshooting](#7-troubleshooting)
8. [FAQ](#8-faq)
9. [Teknologi](#9-teknologi)

---

## 1. Gambaran arsitektur

```
Browser (http://localhost:3000)
        |  HTTP POST (SSE streaming, efek mengetik)
        v
Next.js API Route  /api/chat          <- src/app/api/chat/route.ts
        |  POST /chat/stream (SSE) + fallback POST /chat
        v
FastAPI LangChain (http://localhost:8000)  <- backend/app/main.py
  ├── RAG chain (backend/app/rag_chain.py)  <- ambil konteks + tanya Gemini
  ├── vectorstore Astra DB (backend/app/vectorstore.py)
  ├── memori sesi (backend/app/session.py)
        |  vector search
        v
Astra DB (collection: data_kejaksaan) <- data perkara (data/kecil01.txt, 50 perkara)
```

- **Mode Demo:** browser → Next.js saja (tanpa backend). Jawaban dari data contoh lokal.
- **Mode Full:** browser → Next.js → backend Python → Astra DB + Gemini.

---

## 2. Yang perlu disiapkan

| Kebutuhan | Cara cek / download | Wajib untuk |
|---|---|---|
| Git | `git --version` → [git-scm.com](https://git-scm.com) | Semua cara |
| Node.js 20+ | `node --version` → [nodejs.org](https://nodejs.org) | Semua cara |
| Python 3.10–3.12 | `python --version` → [python.org](https://www.python.org/downloads/) | Hanya Cara 2 |
| Akun Google (gratis) | untuk key Gemini | Hanya Cara 2 |
| Akun Astra DB (gratis) | [astra.datastax.com](https://astra.datastax.com) | Hanya Cara 2 |

> Python 3.14 kadang bermasalah dengan LangChain — kalau error saat install, pakai Python 3.11/3.12.

Clone dulu reponya:

```bash
git clone https://github.com/Verstanden4/si-perkara-langchain.git
cd si-perkara-langchain
```

---

## 3. Cara 1 — Mode Demo, tanpa API key (±5 menit)

Cocok untuk: lihat tampilan, demo ke dosen/teman, oprek UI. **Tanpa Python, tanpa daftar akun apa pun.**

**Langkah 1 — Install dependency web:**

```bash
npm install
```

Tunggu sampai selesai (±1 menit, muncul `added ... packages`).

**Langkah 2 — Buat file `.env` di folder utama** (sejajar `package.json`), isi persis ini:

```env
LANGCHAIN_BACKEND_URL=http://localhost:8000
MOCK_MODE=true
```

> `MOCK_MODE=true` artinya: "jangan cari backend, pakai data contoh lokal".

**Langkah 3 — Jalankan:**

```bash
npm run dev
```

**Langkah 4 — Buka http://localhost:3000.** 🎉

Coba ketik: `Cari perkara korupsi tahun 2025` → harus muncul jawaban + **kartu perkara**
(PDM-05/TPK/3/2025). Coba juga form **pencarian perkara** di atas chat dan tombol **Sesi Baru**.

Kalau ini jalan, berarti instalasi dasarmu beres. Lanjut ke Cara 2 kalau mau AI beneran.

---

## 4. Cara 2 — Full RAG dengan key gratis milikmu (±20 menit)

Di cara ini kamu pakai **key gratis atas nama akunmu sendiri** — bukan key pemilik repo
(repo ini memang tidak menyimpan key siapa pun).

### 4a. Daftar & ambil key Gemini (gratis)

1. Buka [aistudio.google.com/apikey](https://aistudio.google.com/apikey), login akun Google.
2. Klik **Create API Key** → copy key-nya (diawali `AIza...`). Simpan di notepad sementara.

### 4b. Daftar Astra DB & siapkan database (gratis)

1. Daftar/login di [astra.datastax.com](https://astra.datastax.com).
2. Buat database **Serverless (Vector)** — region bebas, keyspace biarkan `default_keyspace`.
3. Setelah jadi, buka halaman database → catat **API Endpoint**
   (bentuknya `https://xxxx-yyyy.apps.astra.datastax.com`).
4. Buka **Settings / Application Tokens** → **Generate Token** (role bawaan cukup)
   → copy token-nya (diawali `AstraCS:...`). Token hanya ditampilkan sekali, jadi langsung simpan.

### 4c. Install backend Python

```bat
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 4d. Isi `backend/.env`

Buat file `backend/.env` (sejajar folder `backend/app`), isi dengan key milikmu:

```env
GOOGLE_API_KEY=AIza... (key dari langkah 4a)
ASTRA_DB_API_ENDPOINT=https://xxxx-yyyy.apps.astra.datastax.com (dari langkah 4b)
ASTRA_DB_APPLICATION_TOKEN=AstraCS:... (dari langkah 4b)
ASTRA_DB_KEYSPACE=default_keyspace
ASTRA_DB_COLLECTION=data_kejaksaan
GEMINI_CHAT_MODEL=gemini-2.0-flash
GEMINI_EMBEDDING_MODEL=models/gemini-embedding-001
TOP_K=5
PORT=8000
```

> Windows: dobel-klik `start-backend.bat` — file `.env` template dibuat otomatis
> kalau belum ada, tinggal isi 3 baris key-nya.

### 4e. Nyalakan backend & cek kesehatan

```bat
start-backend.bat
```

atau manual:

```bat
cd backend
.venv\Scripts\activate
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Buka **http://localhost:8000/health** — harus terlihat:

```json
{"status":"ok","astra_connected":true,"gemini_configured":true}
```

Kalau masih `degraded`, berarti ada key yang salah/kosong — cek lagi langkah 4d.

### 4f. Masukkan data perkara ke Astra (sekali saja)

File `data/kecil01.txt` berisi 50 perkara, format pemisah `=== PERKARA ===`.
Perintah ini memotong, meng-embed, dan mengunggahnya ke collection `data_kejaksaan`:

```bat
cd backend
.venv\Scripts\activate
python ingest.py --file ..\data\kecil01.txt
```

Tunggu sampai muncul `[ingest] OK — ... dokumen masuk`.
Verifikasi di dashboard Astra DB → **Data Explorer** → collection `data_kejaksaan`:
tiap record harus punya field `$vector`.

### 4g. Jalankan aplikasi web dalam mode full

Pastikan file `.env` di folder utama berisi:

```env
LANGCHAIN_BACKEND_URL=http://localhost:8000
MOCK_MODE=false
```

```bash
npm install
npm run build
npm run start
```

Buka **http://localhost:3000** — header harus bertuliskan **"Terhubung ke LangChain"**
(bukan "Mode Demo"). Coba tanya soal perkara yang ada di `kecil01.txt`. 🎉

---

## 5. Menjalankan sehari-hari

| Kebutuhan | Perintah |
|---|---|
| Semua sekaligus (backend + web) | dobel-klik `start-all.bat` |
| Backend saja | dobel-klik `start-backend.bat` |
| Web saja | `npm run dev` (develop) atau `npm run start` (produksi) |
| Web bisa diakses teman satu Wi-Fi | `npx next start -H 0.0.0.0 -p 3000`, lalu buka `http://<IP-komputermu>:3000` |

Urutan nyala yang benar: **backend dulu** (port 8000), baru web (port 3000).

---

## 6. Struktur folder

```
si-perkara-langchain/
├── src/                        # Frontend Next.js (chat, form pencarian, kartu perkara)
│   ├── app/api/chat/route.ts   # API route: teruskan ke backend, stream SSE ke browser
│   └── lib/langchain.ts        # Klien ke backend (SSE + fallback JSON + mock)
├── backend/                    # Backend Python (pengganti Langflow)
│   ├── app/main.py             # FastAPI: /health, /chat, /chat/stream
│   ├── app/rag_chain.py        # RAG: retriever Astra + prompt + Gemini
│   ├── app/vectorstore.py      # Koneksi Astra DB + embeddings
│   ├── app/session.py          # Memori chat per sesi
│   └── ingest.py               # Upload data/kecil01.txt ke Astra
├── data/kecil01.txt            # 50 contoh perkara (sudah termasuk)
├── start-backend.bat / start-app.bat / start-all.bat
└── .env                        # Config web (BUAT SENDIRI, tidak ikut ke-git)
    backend/.env                # Key milikmu (BUAT SENDIRI, tidak ikut ke-git)
```

Yang TIDAK berubah dari versi Langflow: parser `perkara.ts`, data mock, semua komponen UI,
dan format jawaban `###DATA### ... ###END###`.

---

## 7. Troubleshooting

| Gejala | Penyebab & solusi |
|---|---|
| `/health` = `degraded` | `backend/.env` belum diisi / salah — cek 3 key (langkah 4d) |
| Web: "Gagal menghubungi server" | Backend belum nyala, atau `LANGCHAIN_BACKEND_URL` salah |
| Header tertulis "Mode Demo" padahal mau full | `.env` utama masih `MOCK_MODE=true` → ganti `false`, restart web |
| 429 `RESOURCE_EXHAUSTED` | Kuota gratis Gemini habis — tunggu ±1 menit, ulangi |
| `Document size limitation violated` | Jangan ubah CHUNK_SIZE 7900 di `ingest.py` |
| `EADDRINUSE :3000` / `:8000` | Port dipakai proses lain — tutup dulu atau ganti port |
| Jawaban "tidak ditemukan" padahal data ada | Cek ingest: `$vector` terisi? collection = `data_kejaksaan`? |
| `pip install` error di Python 3.14 | Pakai Python 3.11/3.12 |
| `Invalid JSON body` dari `/api/chat` | Body request kosong — pastikan kirim `{"input":"..."}` |

---

## 8. FAQ

**Q: Apakah perlu minta API key ke pemilik repo?**
Tidak. Mode Demo jalan tanpa key. Mode full pakai key gratis milikmu sendiri (langkah 4a–4b).

**Q: Datanya dari mana?**
Sudah termasuk: `data/kecil01.txt` (50 perkara, dipakai mode full) dan data demo
di `src/lib/mockData.ts` (dipakai mode demo). Punya file perkara lain dengan format sama?
Tinggal `python ingest.py --file <namafile>`.

**Q: Apakah key saya aman?**
Ya, selama di file `.env` / `backend/.env` — keduanya di-ignore git dan tidak akan ke-push.
Jangan pernah paste key ke file lain atau ke issue/PR.

**Q: Bisa jalan di HP / laptop teman?**
Bisa, selama satu Wi-Fi: jalankan web dengan `npx next start -H 0.0.0.0 -p 3000`,
lalu buka `http://<IP-komputermu>:3000` dari perangkat lain.

---

## 9. Teknologi

- **Next.js 16** (App Router) + **TypeScript** + **Tailwind CSS v4** — frontend
- **Python FastAPI + LangChain + langchain-google-genai + langchain-astradb** — backend
- **Astra DB** — vector search (`gemini-embedding-001`, dim 3072)
- **Gemini `gemini-2.0-flash`** — chat (ganti via `GEMINI_CHAT_MODEL`)
