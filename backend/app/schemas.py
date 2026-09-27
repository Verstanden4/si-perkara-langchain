"""Skema request/response backend SI PERKARA."""
from typing import Any, Optional
from pydantic import BaseModel, Field


class QuickSearch(BaseModel):
    jenis_perkara: Optional[str] = None
    nomor_perkara: Optional[str] = None
    nama_terdakwa: Optional[str] = None
    tahun: Optional[str] = None


class ChatRequest(BaseModel):
    input: str = Field(min_length=1, description="Pertanyaan user")
    sessionId: str = Field(default="default")
    quickSearch: Optional[QuickSearch] = None


class ChatResponse(BaseModel):
    answer: str
    sessionId: str
    mode: str = "langchain"
    context_docs: int = 0


class HealthResponse(BaseModel):
    status: str
    astra_connected: bool
    gemini_configured: bool
    detail: dict[str, Any] = {}
