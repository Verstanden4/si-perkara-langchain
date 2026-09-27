"""FastAPI backend SI PERKARA (LangChain) — pengganti Langflow :7860."""
import json
import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

load_dotenv()

from .rag_chain import run_rag, stream_rag
from .schemas import ChatRequest, ChatResponse, HealthResponse
from .session import add_turn, clear_session, history_text
from . import vectorstore

app = FastAPI(title="SI PERKARA LangChain Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health():
    astra_ok = bool(vectorstore.ASTRA_ENDPOINT and vectorstore.ASTRA_TOKEN)
    gemini_ok = bool(os.getenv("GOOGLE_API_KEY"))
    # Coba koneksi ringan bila sudah dikonfigurasi
    detail: dict = {}
    if astra_ok:
        try:
            vs = vectorstore.get_vectorstore()
            # akses collection untuk validasi (tanpa query berat)
            detail["collection"] = vectorstore.ASTRA_COLLECTION
            detail["keyspace"] = vectorstore.ASTRA_KEYSPACE
        except Exception as e:  # noqa: BLE001
            astra_ok = False
            detail["error"] = str(e)[:300]
    return HealthResponse(
        status="ok" if (astra_ok and gemini_ok) else "degraded",
        astra_connected=astra_ok,
        gemini_configured=gemini_ok,
        detail=detail,
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Non-streaming (dipakai Next.js sebagai fallback, mirip message/send)."""
    if not req.input.strip():
        raise HTTPException(status_code=400, detail="Missing input")
    qs = req.quickSearch.model_dump(exclude_none=True) if req.quickSearch else None
    try:
        answer, n_docs = await run_rag(
            req.input, qs, chat_history=history_text(req.sessionId)
        )
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    add_turn(req.sessionId, req.input, answer)
    return ChatResponse(answer=answer, sessionId=req.sessionId, context_docs=n_docs)


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    """Streaming SSE (dipakai Next.js sebagai jalur utama, mirip message/stream)."""
    if not req.input.strip():
        raise HTTPException(status_code=400, detail="Missing input")
    qs = req.quickSearch.model_dump(exclude_none=True) if req.quickSearch else None

    async def generator():
        acc: list[str] = []
        try:
            async for token in stream_rag(
                req.input, qs, chat_history=history_text(req.sessionId)
            ):
                acc.append(token)
                yield {"event": "message", "data": json.dumps({"type": "token", "content": token}, ensure_ascii=False)}
            full = "".join(acc)
            add_turn(req.sessionId, req.input, full)
            yield {"event": "message", "data": json.dumps({"type": "done", "content": full, "mode": "langchain"}, ensure_ascii=False)}
        except Exception as e:  # noqa: BLE001
            yield {"event": "message", "data": json.dumps({"type": "error", "content": str(e)[:500]}, ensure_ascii=False)}

    return EventSourceResponse(generator())


@app.post("/session/clear")
def session_clear(sessionId: str = "default"):
    clear_session(sessionId)
    return JSONResponse({"ok": True, "sessionId": sessionId})
