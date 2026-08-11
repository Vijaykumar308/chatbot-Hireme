from fastapi import FastAPI
from dotenv import load_dotenv
import os
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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