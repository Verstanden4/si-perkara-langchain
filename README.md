# SI PERKARA — Chatbot Pencari Perkara Kejaksaan (Versi LangChain)

Aplikasi web chatbot AI untuk mencari dan memahami informasi perkara pada Kejaksaan.
Versi ini adalah **duplikat** dari projek `projek akhir`, dengan lapisan **Langflow diganti
backend Python LangChain (FastAPI)**. UI Next.js, fitur, dan database **Astra DB tetap sama**.

## Arsitektur

```
Browser (http://localhost:3000)
        |  HTTP POST (SSE streaming)
        v
Next.js API Route  /api/chat          <- src/app/api/chat/route.ts
        |  POST /chat/stream (SSE) + fallback POST /chat
        v
FastAPI LangChain (http://localhost:8000)  <- backend/app/main.py
  ├── RAG chain (backend/app/rag_chain.py)  <- retriever + prompt + Gemini
  ├── vectorstore Astra DB (backend/app/vectorstore.py)
  ├── session memory (backend/app/session.py)
        |  vector search
        v
Astra DB  (collection: data_kejaksaan) <- data perkara ter-embed
```

- Jawaban AI disalurkan bertahap (efek mengetik) ke UI.
- Riwayat chat tersimpan di browser (localStorage) + memori sesi di backend.
- Format jawaban `###DATA### ... ###END###` dipertahankan agar kartu perkara tetap muncul.

## Fitur (full port dari versi Langflow)

- Chat AI streaming dengan indikator mengetik
- Form pencarian perkara: jenis perkara, nomor perkara, nama terdakwa/korporasi, tahun
- Multi-sesi percakapan + riwayat tersimpan di localStorage
- Backend `/chat/stream` (SSE) dengan fallback `/chat` (JSON)
- Mock mode bila backend belum dikonfigurasi
- Script ingest Python (`backend/ingest.py`) pengganti komponen Langflow

## Prasyarat

| Tools | Keterangan |
|---|---|
| Node.js 20+ | untuk aplikasi web ([nodejs.org](https://nodejs.org)) |
| Python 3.10–3.12* | untuk backend LangChain (*3.14 bisa dicoba, bila error pakai 3.11/3.12) |
| Akun Google AI | API key Gemini gratis → [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| Akun Astra DB | database vector gratis → [astra.datastax.com](https://astra.datastax.com) |

## Langkah Setup

### 1. Install backend Python

```bat
cd backend
REM buat file .env berisi:
REM   GOOGLE_API_KEY=...
REM   ASTRA_DB_API_ENDPOINT=https://...apps.astra.datastax.com
REM   ASTRA_DB_APPLICATION_TOKEN=AstraCS:...
REM   ASTRA_DB_KEYSPACE=default_keyspace
REM   ASTRA_DB_COLLECTION=data_kejaksaan
REM   GEMINI_CHAT_MODEL=gemini-2.0-flash
REM   GEMINI_EMBEDDING_MODEL=models/gemini-embedding-001
REM   TOP_K=5
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Windows: dobel-klik `start-backend.bat` (otomatis buat venv + install + jalan di port 8000).

Cek: buka http://localhost:8000/health — harus `status: ok` bila kredensial benar,
`degraded` bila belum diisi (aplikasi jalan dalam mock mode).

### 2. Ingest data perkara (sekali saja)

Sama seperti dulu: `data/kecil01.txt`, separator `=== PERKARA ===`, chunk 7900 / overlap 0.

```bat
cd backend
.venv\Scripts\activate
python ingest.py --file ..\data\kecil01.txt
```

Verifikasi di dashboard Astra DB: record punya field `$vector`, collection `data_kejaksaan`.
Kalau collection lama dari projek Langflow masih ada, bisa langsung dipakai tanpa ingest ulang.

### 3. Jalankan aplikasi web

Buat file `.env` di folder proyek (dibuat otomatis saat clone? tidak — buat manual):

```env
LANGCHAIN_BACKEND_URL=http://localhost:8000
MOCK_MODE=false
```

```bash
npm install
npm run build
npm run start
```

Buka **http://localhost:3000** — chatbot siap dipakai. 🎉

> Sekali klik semua: dobel-klik `start-all.bat` (menyalakan backend + web sekaligus).

## File penting (perbandingan dengan versi Langflow)

| Versi Langflow | Versi LangChain ini |
|---|---|
| `src/lib/langflow.ts` (A2A JSON-RPC) | `src/lib/langchain.ts` (fetch FastAPI SSE + fallback JSON) |
| `langflow/flow-siperkara.json` + server `:7860` | `backend/app/*.py` + server `:8000` |
| Split Text + Astra ingest di UI Langflow | `backend/ingest.py` (CLI) |
| `contextIdMap` (memory) | `backend/app/session.py` (in-memory history) |
| `LANGFLOW_*` env | `LANGCHAIN_BACKEND_URL` env + `backend/.env` |
| `start-langflow.bat` | `start-backend.bat` / `start-all.bat` |

Yang TIDAK berubah: `src/lib/perkara.ts`, `src/lib/mockData.ts`, `src/lib/types.ts`,
`src/hooks/useChat.ts` (selain label), semua komponen UI, `data/kecil01.txt`.

## Troubleshooting

| Gejala | Penyebab & Solusi |
|---|---|
| `/health` = degraded | `backend/.env` belum diisi — cek GOOGLE_API_KEY dan ASTRA_* |
| Aplikasi: "Gagal menghubungi server" | Backend tidak jalan, atau `LANGCHAIN_BACKEND_URL` salah |
| 429 `RESOURCE_EXHAUSTED` | Kuota Gemini habis — tunggu ±1 menit lalu ulangi |
| `Document size limitation violated` | Jangan ubah CHUNK_SIZE 7900 di ingest.py |
| `EADDRINUSE :3000 / :8000` | Port dipakai proses lain — matikan dulu atau ganti port |
| Jawaban "tidak ditemukan" padahal data ada | Cek ingest (`$vector` terisi?) dan collection = `data_kejaksaan` |
| Python 3.14 error install | Pakai Python 3.11/3.12 untuk LangChain paling stabil |

## Teknologi

- **Next.js 16** (App Router) + **TypeScript** + **Tailwind CSS v4** (frontend, reuse)
- **Python FastAPI + LangChain + langchain-google-genai + langchain-astradb** (backend, pengganti Langflow)
- **Astra DB** (vector search, embedding `gemini-embedding-001`, dim 3072)
- **Gemini** `gemini-2.0-flash` (chat, bisa diganti via `GEMINI_CHAT_MODEL`)
