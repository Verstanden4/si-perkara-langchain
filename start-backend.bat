@echo off
title SI PERKARA - LangChain Backend
echo ============================================
echo  Menjalankan backend LangChain (jangan tutup jendela ini)
echo  URL lokal: http://localhost:8000
echo  Health: http://localhost:8000/health
echo ============================================
cd /d "%~dp0backend"
if not exist ".env" (
  echo [INFO] backend\.env belum ada, membuat template...
  (
    echo GOOGLE_API_KEY=GANTI-DENGAN-GOOGLE-API-KEY-KAMU
    echo ASTRA_DB_API_ENDPOINT=https://^^^<ASTRA_DB_ID^^^>-^^^<REGION^^^^>.apps.astra.datastax.com
    echo ASTRA_DB_APPLICATION_TOKEN=AstraCS:...
    echo ASTRA_DB_KEYSPACE=default_keyspace
    echo ASTRA_DB_COLLECTION=data_kejaksaan
    echo GEMINI_CHAT_MODEL=gemini-2.0-flash
    echo GEMINI_EMBEDDING_MODEL=models/gemini-embedding-001
    echo TOP_K=5
    echo PORT=8000
  ) > ".env"
  echo [PENTING] Isi GOOGLE_API_KEY dan ASTRA_DB_* di backend\.env lalu jalankan ulang.
  pause
  exit /b 1
)
if not exist ".venv" (
  echo [INFO] Membuat virtual env pertama kali...
  python -m venv .venv
)
call ".venv\Scripts\activate"
echo [INFO] Install dependencies (skip bila sudah lengkap)...
pip install -r requirements.txt
echo [INFO] Menjalankan FastAPI...
uvicorn app.main:app --host 127.0.0.1 --port 8000
pause
