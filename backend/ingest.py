"""Ingest data perkara ke Astra DB — port dari flow Langflow.

Pemisah & ukuran disamakan dengan README lama:
  Separator  = === PERKARA ===
  Chunk size = 7900, overlap = 0

Cara pakai:
  cd backend
  copy .env.example .env   (lalu isi kredensial)
  pip install -r requirements.txt
  python ingest.py --file ..\\data\\kecil01.txt
"""
import argparse
import os
import re

from dotenv import load_dotenv

load_dotenv()

SEPARATOR = "=== PERKARA ==="
CHUNK_SIZE = 7900

NO_PERKARA_RE = re.compile(r"No\. Perkara:\s*(.+)", re.I)
TERDAKWA_RE = re.compile(r"Terdakwa:\s*(.+)", re.I)
PASAL_RE = re.compile(r"Undang-Undang/Pasal:\s*([\s\S]{1,300})", re.I)
TAHUN_RE = re.compile(r"Tahun:\s*(\d{4})", re.I)
TANGGAL_RE = re.compile(r"(?:Tanggal Surat|SPDP Diterima):\s*(\d{4}-\d{2}-\d{2})", re.I)


def load_chunks(path: str) -> list[str]:
    with open(path, encoding="utf-8", errors="ignore") as f:
        raw = f.read()
    parts = [p.strip() for p in raw.split(SEPARATOR) if p.strip()]
    # Samakan perilaku Split Text lama: gabung sampai CHUNK_SIZE
    chunks: list[str] = []
    buf = ""
    for p in parts:
        block = f"{SEPARATOR}\n{p}"
        if len(buf) + len(block) + 1 <= CHUNK_SIZE:
            buf = f"{buf}\n{block}" if buf else block
        else:
            if buf:
                chunks.append(buf)
            buf = block
    if buf:
        chunks.append(buf)
    return chunks


def extract_meta(text: str) -> dict:
    def g(rx):
        m = rx.search(text)
        return m.group(1).strip().splitlines()[0][:200] if m else "-"

    return {
        "nomor_perkara": g(NO_PERKARA_RE),
        "nama_terdakwa": g(TERDAKWA_RE),
        "pasal": g(PASAL_RE).replace("\n", " ")[:300],
        "tahun": g(TAHUN_RE),
        "tanggal": g(TANGGAL_RE),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default="..\\data\\kecil01.txt")
    ap.add_argument("--collection", default=os.getenv("ASTRA_DB_COLLECTION", "data_kejaksaan"))
    args = ap.parse_args()

    if not os.getenv("GOOGLE_API_KEY"):
        raise SystemExit("GOOGLE_API_KEY kosong di backend/.env")
    if not os.getenv("ASTRA_DB_API_ENDPOINT") or not os.getenv("ASTRA_DB_APPLICATION_TOKEN"):
        raise SystemExit("ASTRA_DB_API_ENDPOINT / TOKEN kosong di backend/.env")

    from langchain_core.documents import Document
    from langchain_astradb import AstraDBVectorStore
    from app.vectorstore import get_embeddings
    import app.vectorstore as vs

    chunks = load_chunks(args.file)
    print(f"[ingest] {len(chunks)} chunk dari {args.file}")
    docs = [
        Document(page_content=c, metadata=extract_meta(c)) for c in chunks
    ]

    store = AstraDBVectorStore(
        embedding=get_embeddings(),
        collection_name=args.collection,
        api_endpoint=os.environ["ASTRA_DB_API_ENDPOINT"],
        token=os.environ["ASTRA_DB_APPLICATION_TOKEN"],
        namespace=os.getenv("ASTRA_DB_KEYSPACE", "default_keyspace"),
    )
    # Hapus dulu biar ingest ulang bersih (opsional, aman untuk demo)
    try:
        store.delete_collection()
        print("[ingest] collection lama dihapus")
    except Exception as e:  # noqa: BLE001
        print(f"[ingest] skip delete: {e}")

    store.add_documents(docs)
    print(f"[ingest] OK — {len(docs)} dokumen masuk ke {vs.ASTRA_KEYSPACE}.{args.collection}")


if __name__ == "__main__":
    main()
