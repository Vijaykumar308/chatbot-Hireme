from fastapi import APIRouter, UploadFile, File, Request
import tempfile
from ..services.parser import extract_text_from_pdf
from ..services.embeddings import get_embedding

router = APIRouter()


@router.post("/upload")
async def upload_resume(request: Request, file: UploadFile = File(...)):
    """Upload a resume (PDF) and index its content into the in-memory vector store."""
    # save uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp.flush()
        path = tmp.name

    text = extract_text_from_pdf(path)

    # simple chunking
    chunk_size = 1000
    chunks = []
    for i in range(0, max(1, len(text)), chunk_size):
        chunk_text = text[i : i + chunk_size]
        emb = get_embedding(chunk_text)
        chunks.append({"id": f"{file.filename}-{i}", "text": chunk_text, "embedding": emb})

    vs = request.app.state.vector_store
    if vs is None:
        return {"success": False, "message": "Vector store not initialized"}

    vs.add_documents(chunks)
    return {"success": True, "message": "Indexed resume", "chunks": len(chunks)}
