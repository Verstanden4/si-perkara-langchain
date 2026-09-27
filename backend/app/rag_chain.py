"""RAG chain LangChain pengganti flow Langflow SI PERKARA.

Alur: retriever Astra DB -> prompt -> Gemini -> output teks + blok ###DATA###
Format blok WAJIB dipertahankan agar parser frontend (perkara.ts) tetap jalan.
"""
import json
import os
import re

from dotenv import load_dotenv

load_dotenv()

CHAT_MODEL = os.getenv("GEMINI_CHAT_MODEL", "gemini-2.0-flash")

SYSTEM_PROMPT = """Kamu adalah asisten SI PERKARA — pencari informasi perkara Kejaksaan Indonesia.
Jawab HANYA berdasarkan KONTEKS di bawah. Jika tidak ada di konteks, katakan terus terang tidak ditemukan dan sarankan ubah kata kunci.

Aturan format jawaban:
1. Bahasa Indonesia, ringkas, sebut nomor perkara, nama terdakwa/terlapor, pasal, tanggal, dan ringkasan.
2. Jika ada filter [quick_search], prioritaskan dokumen yang cocok dengan filter itu.
3. SELALU akhiri jawaban dengan blok JSON persis seperti ini (untuk di-parse frontend):
###DATA###
{{"quickSearch": {{...filter...}}, "perkaraList": [{{"nomor_perkara": "...", "nama_terdakwa": "...", "pasal": "...", "jenis_perkara": "...", "status": "Tahap Penyidikan", "tanggal": "...", "pihak": "...", "ringkasan": "..."}}], "total": N}}
###END###
Status hanya boleh salah satu: P21, Tahap Penyidikan, Tahap Penuntutan, Pemeriksaan Sidang, Eksekusi, SP3.
Jika tidak ada hasil, tulis perkaraList kosong: [] dan total 0.
JANGAN tulis penjelasan di luar blok setelah ###END###.
"""

DATA_RE = re.compile(r"###DATA###\s*(\{[\s\S]*?\})\s*###END###")


def build_query(user_input: str, quick_search: dict | None) -> str:
    if not quick_search:
        return user_input
    # Samakan dengan perilaku lama: tempel filter ke query agar retriever fokus
    return f"{user_input}\n\n[quick_search] {json.dumps(quick_search, ensure_ascii=False)}"


def format_docs(docs) -> str:
    parts: list[str] = []
    for i, d in enumerate(docs, 1):
        text = (d.page_content or "")[:4000]
        parts.append(f"--- Dokumen {i} ---\n{text}")
    return "\n\n".join(parts) if parts else "(tidak ada dokumen relevan)"


def get_llm():
    from langchain_google_genai import ChatGoogleGenerativeAI

    if not os.getenv("GOOGLE_API_KEY"):
        raise RuntimeError("GOOGLE_API_KEY belum diisi di backend/.env")
    return ChatGoogleGenerativeAI(model=CHAT_MODEL, temperature=0.2)


async def run_rag(
    user_input: str,
    quick_search: dict | None = None,
    chat_history: str = "",
) -> tuple[str, int]:
    """Jalankan RAG. Return (jawaban_full_text, jumlah_dokumen)."""
    from . import vectorstore

    query = build_query(user_input, quick_search)

    try:
        retriever = vectorstore.get_retriever()
        docs = await retriever.ainvoke(query)
    except Exception as e:
        # Fallback ramah bila Astra belum dikonfigurasi / offline
        raise RuntimeError(f"Gagal mengambil konteks Astra DB: {e}") from e

    context = format_docs(docs)
    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"RIWAYAT SINGKAT:\n{chat_history or '-'}\n\n"
        f"KONTEKS PERKARA:\n{context}\n\n"
        f"FILTER: {json.dumps(quick_search or {}, ensure_ascii=False)}\n"
        f"PERTANYAAN: {query}\nJAWABAN:"
    )

    llm = get_llm()
    result = await llm.ainvoke(prompt)
    answer = result.content if isinstance(result.content, str) else str(result.content)
    return answer, len(docs)


async def stream_rag(user_input: str, quick_search: dict | None = None, chat_history: str = ""):
    """Generator streaming token per token (dipakai endpoint /chat/stream)."""
    from . import vectorstore

    query = build_query(user_input, quick_search)

    retriever = vectorstore.get_retriever()
    docs = await retriever.ainvoke(query)
    context = format_docs(docs)
    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"RIWAYAT SINGKAT:\n{chat_history or '-'}\n\n"
        f"KONTEKS PERKARA:\n{context}\n\n"
        f"FILTER: {json.dumps(quick_search or {}, ensure_ascii=False)}\n"
        f"PERTANYAAN: {query}\nJAWABAN:"
    )

    llm = get_llm()
    async for chunk in llm.astream(prompt):
        text = chunk.content if isinstance(chunk.content, str) else str(chunk.content)
        if text:
            yield text
