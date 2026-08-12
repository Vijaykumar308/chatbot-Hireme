import os

import uvicorn

from src.app import app


def main():
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload_enabled = os.getenv("RELOAD", "false").lower() in {"1", "true", "yes", "on"}

    uvicorn.run(app, host=host, port=port, reload=reload_enabled)


if __name__ == "__main__":
    main()
