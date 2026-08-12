from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
import os
from ..services.embeddings import get_embedding
from ..services.llm import generate_answer

router = APIRouter()


class Query(BaseModel):
    query: str


@router.post("/chat")
async def chat(request: Request, q: Query):
    """Retrieval + generation: find relevant resume chunks and ask the LLM to answer."""
    vs = request.app.state.vector_store
    if vs is None:
        return {"success": False, "message": "Vector store not initialized"}

    q_emb = get_embedding(q.query)
    hits = vs.similarity_search(q_emb, k=4)

    if not hits:
        hits = vs.keyword_search(q.query, k=4)

    if not hits:
        return {
            "success": False,
            "message": "No resume content is indexed yet. Place a PDF in src/assets or upload one via /api/upload.",
        }

    combined = "\n\n".join([h["doc"]["text"] for h in hits])
    # Ensure Groq key exists
    if not os.getenv("GROQ_API_KEY"):
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not set; chat requires Groq")

    try:
        answer = generate_answer(q.query, combined)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"success": True, "answer": answer, "matches": hits}
