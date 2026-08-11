import os
from typing import List
from .parser import extract_text_from_pdf
from .embeddings import get_embedding


def _read_text_asset(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except UnicodeDecodeError:
        with open(path, "r", encoding="latin-1", errors="ignore") as fh:
            return fh.read()


def index_assets(vector_store) -> int:
    """Scan `src/assets/*.(pdf|txt|md)`, extract text, chunk, embed and add to `vector_store`.

    Returns the number of chunks indexed.
    """
    base = os.path.dirname(os.path.dirname(__file__))
    assets_dir = os.path.join(base, "assets")
    if not os.path.isdir(assets_dir):
        return 0

    total = 0
    for fname in os.listdir(assets_dir):
        lower = fname.lower()
        path = os.path.join(assets_dir, fname)

        if lower.endswith(".pdf"):
            try:
                text = extract_text_from_pdf(path)
            except Exception:
                continue
        elif lower.endswith(".txt") or lower.endswith(".md"):
            try:
                text = _read_text_asset(path)
            except Exception:
                continue
        else:
            continue

        if not text:
            continue

        chunk_size = 1000
        chunks = []
        for i in range(0, max(1, len(text)), chunk_size):
            chunk_text = text[i : i + chunk_size]
            emb = get_embedding(chunk_text)
            chunks.append({"id": f"{fname}-{i}", "text": chunk_text, "embedding": emb})

        vector_store.add_documents(chunks)
        total += len(chunks)

    return total
