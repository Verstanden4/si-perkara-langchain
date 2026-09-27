"""Koneksi Astra DB + Gemini embeddings (pengganti komponen Langflow)."""
import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()

ASTRA_ENDPOINT = os.getenv("ASTRA_DB_API_ENDPOINT", "")
ASTRA_TOKEN = os.getenv("ASTRA_DB_APPLICATION_TOKEN", "")
ASTRA_KEYSPACE = os.getenv("ASTRA_DB_KEYSPACE", "default_keyspace")
ASTRA_COLLECTION = os.getenv("ASTRA_DB_COLLECTION", "data_kejaksaan")
EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001")
TOP_K = int(os.getenv("TOP_K", "5"))


def is_configured() -> bool:
    return bool(ASTRA_ENDPOINT and ASTRA_TOKEN and os.getenv("GOOGLE_API_KEY"))


def get_embeddings():
    """Lazy import agar backend tetap bisa start tanpa kredensial (mock mode)."""
    from langchain_google_genai import GoogleGenerativeAIEmbeddings

    return GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)


@lru_cache(maxsize=1)
def get_vectorstore():
    """Cache satu instance AstraDBVectorStore."""
    if not (ASTRA_ENDPOINT and ASTRA_TOKEN):
        raise RuntimeError(
            "Astra DB belum dikonfigurasi. Isi ASTRA_DB_API_ENDPOINT dan "
            "ASTRA_DB_APPLICATION_TOKEN di backend/.env"
        )
    from langchain_astradb import AstraDBVectorStore

    return AstraDBVectorStore(
        embedding=get_embeddings(),
        collection_name=ASTRA_COLLECTION,
        api_endpoint=ASTRA_ENDPOINT,
        token=ASTRA_TOKEN,
        namespace=ASTRA_KEYSPACE,
    )


def get_retriever(k: int | None = None):
    vs = get_vectorstore()
    return vs.as_retriever(search_kwargs={"k": k or TOP_K})
