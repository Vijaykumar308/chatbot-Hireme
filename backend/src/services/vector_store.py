from typing import List, Dict
import math


class InMemoryVectorStore:
    def __init__(self):
        self.docs: List[Dict] = []

    def add_documents(self, docs: List[Dict]):
        self.docs.extend(docs)

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
