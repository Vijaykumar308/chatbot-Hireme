FastAPI backend for a resume-based chatbot

Quick start

1. Create a virtual environment and install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

2. Run the server:

```powershell
uvicorn main:app --reload
```

Endpoints

- `GET /` : health
- `POST /api/upload` : upload a PDF resume (form file field `file`)
- `POST /api/chat` : ask a question (json `{ "query": "..." }`)

Notes

- This backend automatically indexes any PDF resumes placed in `src/assets/*.pdf` at startup, so your default personal resume is used without requiring an upload.
- If you keep your resume PDF in `src/assets`, `/api/chat` works immediately for your personal profile.
- It uses an in-memory vector store (`src/services/vector_store.py`) for retrieval.
- Text extraction is handled by `src/services/parser.py` using `pypdf`.
- Embeddings are generated in `src/services/embeddings.py` and currently support Groq when `GROQ_API_KEY` is provided, with a local deterministic fallback.
- The chat response is produced by `src/services/llm.py`, which calls Groq chat completions using your provided system prompt and retrieved resume context.
- The chat endpoint is defined in `src/routes/chat.py` and the upload endpoint is defined in `src/routes/upload.py`.
- `src/app.py` wires the API routes and initializes the vector store on startup.

Requirements

- Python 3.11+
- `fastapi`
- `uvicorn`
- `pypdf`
- `python-dotenv`
- `groq` (for Groq LLM integration)

Usage

1. Create and activate the virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

2. Add `GROQ_API_KEY` to `.env` in the backend directory.

3. Start the server:

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

4. Verify routes:

```powershell
curl http://127.0.0.1:8000/routes
```

5. Test chat:

```powershell
curl -X POST http://127.0.0.1:8000/api/chat -H "Content-Type: application/json" -d '{"query":"Who is this resume about?"}'
```

6. Upload a PDF resume:

```powershell
curl -F "file=@src/assets/resume.pdf" http://127.0.0.1:8000/api/upload
```
