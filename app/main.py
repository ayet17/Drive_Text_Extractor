"""Main FastAPI application entry point.

Exposes health check, Drive inspection routes, and serves the static interface.
"""

from pathlib import Path
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.drive import DriveAccessError, InvalidDriveURLError, list_folder_files
from app.schemas import ErrorResponse, FileListResponse, FolderRequest

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


@app.post(
    "/api/files",
    response_model=FileListResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse, "description": "Invalid link format"},
        status.HTTP_502_BAD_GATEWAY: {"model": ErrorResponse, "description": "Drive folder unreachable or private"},
    },
    summary="List files from a public Google Drive folder",
)
def list_files_endpoint(request: FolderRequest) -> FileListResponse:
    """Inspect a public Google Drive folder URL and return detected PDFs and images."""
    try:
        files = list_folder_files(request.url)
        return FileListResponse(files=files, total_count=len(files))
    except InvalidDriveURLError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except DriveAccessError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
