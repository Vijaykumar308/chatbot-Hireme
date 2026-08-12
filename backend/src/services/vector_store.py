import math
import re
from typing import Dict, List


class InMemoryVectorStore:
    def __init__(self):
        self.docs: List[Dict] = []

    def add_documents(self, docs: List[Dict]):
        self.docs.extend(docs)

    def keyword_search(self, query: str, k: int = 4):
        if not self.docs or not query:
            return []

        normalized_query = query.lower().strip()
        query_tokens = {t for t in re.findall(r"[a-z0-9+/.-]+", normalized_query) if t and len(t) > 2}
        if not query_tokens:
            return []

        scored = []
        for doc in self.docs:
            text = (doc.get("text") or "").lower()
            score = 0.0
            if normalized_query in text:
                score += 12.0
            for token in query_tokens:
                if token in text:
                    score += 3.0
                if token.replace("+", " ") in text:
                    score += 1.0
            if score > 0:
                scored.append({"doc": doc, "score": float(score)})

        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:k]

    def similarity_search(self, query_embedding: List[float], k: int = 3):
        if not self.docs:
            return []

        def dot(a, b):
            return sum(x * y for x, y in zip(a, b))

        def norm(a):
            return math.sqrt(sum(x * x for x in a)) + 1e-12

        qn = [x / norm(query_embedding) for x in query_embedding]
        sims = []
        for d in self.docs:
            emb = d["embedding"]
            en = [x / norm(emb) for x in emb]
            sims.append(dot(en, qn))

        idxs = sorted(range(len(sims)), key=lambda i: sims[i], reverse=True)[:k]
        results = []
        for i in idxs:
            results.append({"doc": self.docs[int(i)], "score": float(sims[int(i)])})
        return results
