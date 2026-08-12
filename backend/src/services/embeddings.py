import hashlib
import math
import os
from typing import List


def _pseudo_embedding(text: str, dim: int = 512) -> List[float]:
    h = hashlib.sha256(text.encode("utf-8")).digest()
    arr = list(h)
    if not arr:
        arr = [1] * 32
    reps = (dim + len(arr) - 1) // len(arr)
    vec = (arr * reps)[:dim]
    vec = [float(x) for x in vec]
    norm = math.sqrt(sum(x * x for x in vec)) + 1e-12
    vec = [x / norm for x in vec]
    return vec


def get_embedding(text: str, dim: int = 512):
    """Return an embedding for `text`.

    Prefer real Groq embeddings when configured. Use a deterministic hash-based
    fallback only if the SDK or API is unavailable.
    """
    try:
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            try:
                import groq

                client = None
                try:
                    client = groq.Groq(api_key=groq_key)
                except Exception:
                    try:
                        client = groq.Client(api_key=groq_key)
                    except Exception:
                        pass

                if client is not None:
                    for model_name in ("text-embedding-3-small", "all-minilm-l6-v2", "embed-1"):
                        try:
                            resp = client.embeddings.create(model=model_name, input=text)
                            data = getattr(resp, "data", None)
                            if data:
                                emb = data[0].embedding
                                if emb:
                                    return emb
                            if isinstance(resp, dict) and resp.get("data"):
                                emb = resp["data"][0].get("embedding")
                                if emb:
                                    return emb
                        except Exception:
                            continue
            except Exception:
                pass
    except Exception:
        pass

    return _pseudo_embedding(text, dim)
