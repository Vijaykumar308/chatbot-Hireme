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

    If `GROQ_API_KEY` is present and the `groq` package is available, attempt
    to fetch embeddings from Groq. Otherwise fall back to a deterministic
    local pseudo-embedding so the app works offline.
    """
    try:
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            try:
                import groq

                client = groq.GroqClient(api_key=groq_key)
                # the exact client call may vary depending on the installed
                # `groq` package version; wrap in try/except to fall back.
                try:
                    resp = client.embeddings.create(model="embed-1", input=text)
                    # typical shape: {'data': [{'embedding': [...]}, ...]}
                    return resp["data"][0]["embedding"]
                except Exception:
                    # fall through to pseudo embedding
                    pass
            except Exception:
                # groq import failed: fall back
                pass
    except Exception:
        pass

    return _pseudo_embedding(text, dim)
