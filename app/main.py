"""Main FastAPI application entry point.

Exposes health check, API routes, and serves the static single-page interface.
"""

from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Absolute path to static assets directory
STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(
    title="Drive Text Extractor",
    description="Extract text and run OCR on documents from public Google Drive folders.",
    version="1.0.0",
)

# Mount static folder for CSS, JavaScript, and static assets
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/health", summary="Health check endpoint")
def health_check() -> dict[str, str]:
    """Return application health status to verify server availability."""
    return {"status": "ok"}


@app.get("/", summary="Serve Web Interface", include_in_schema=False)
def serve_index() -> FileResponse:
    """Serve the root single-page HTML interface."""
    return FileResponse(STATIC_DIR / "index.html")
