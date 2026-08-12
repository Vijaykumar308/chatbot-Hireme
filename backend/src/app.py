from urllib.parse import urlsplit

from fastapi import FastAPI
from dotenv import load_dotenv
import os
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()


def normalize_origin(raw_origin: str) -> str:
    value = raw_origin.strip()
    if not value:
        return ""
    if value.startswith("http://") or value.startswith("https://"):
        parsed = urlsplit(value)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"
        return value
    return value


app = FastAPI(title="HireMe AI Career Assistant")

allowed_origins = []
raw_origins = os.getenv("ALLOWED_ORIGINS", "")
if raw_origins:
    allowed_origins.extend(
        normalized_origin
        for origin in raw_origins.split(",")
        if (normalized_origin := normalize_origin(origin))
    )

allowed_origins.extend(
    [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ]
)

# de-duplicate while preserving order
seen = set()
unique_origins = []
for origin in allowed_origins:
    if origin not in seen:
        seen.add(origin)
        unique_origins.append(origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=unique_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"success": True, "message": "This is a Home route"}


@app.get("/check")
def check():
    groq_api_key = os.getenv("GROQ_API_KEY")
    return {"success": True, "message": f" Groq API key is {groq_api_key} "}


@app.get("/routes")
def list_routes():
    """Return the list of registered FastAPI route paths for quick inspection."""
    paths = []
    for route in app.routes:
        try:
            paths.append({"path": route.path, "name": route.name})
        except Exception:
            pass
    return {"success": True, "routes": paths}


# import and include routers (upload, chat)
try:
    from .routes import upload, chat

    app.include_router(upload.router, prefix="/api")
    app.include_router(chat.router, prefix="/api")
    app.add_api_route("/chat", chat.chat, methods=["POST"])
except Exception:
    # routers may not exist yet during initial scaffolding
    pass


# initialize a simple in-memory vector store on startup
@app.on_event("startup")
def startup_event():
    try:
        from .services.vector_store import InMemoryVectorStore
        app.state.vector_store = InMemoryVectorStore()
        # attempt to automatically index any PDFs in src/assets
        try:
            from .services.indexer import index_assets

            total = index_assets(app.state.vector_store)
            if total:
                print(f"Indexed {total} chunks from src/assets PDFs")
        except Exception:
            pass
    except Exception:
        app.state.vector_store = None