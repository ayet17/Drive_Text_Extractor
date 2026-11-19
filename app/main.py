"""Main FastAPI application entry point.

Exposes health check, Drive folder inspection, and single-file text extraction routes,
while serving the static single-page interface.
"""

from pathlib import Path
import tempfile
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.drive import (
    DriveAccessError,
    FileTooLargeError,
    InvalidDriveURLError,
    download_drive_file,
    list_folder_files,
)
from app.extractor import (
    CorruptedFileError,
    EncryptedFileError,
    ExtractionError,
    OCRError,
    UnsupportedFileError,
    extract_document_text,
)
from app.schemas import (
    ErrorResponse,
    ExtractRequest,
    ExtractResponse,
    FileListResponse,
    FolderRequest,
)

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


@app.post(
    "/api/extract",
    response_model=ExtractResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse, "description": "Unsupported file format"},
        status.HTTP_413_CONTENT_TOO_LARGE: {"model": ErrorResponse, "description": "File exceeds size limit"},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse, "description": "Corrupt or encrypted document"},
        status.HTTP_502_BAD_GATEWAY: {"model": ErrorResponse, "description": "Download failed from Google Drive"},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponse, "description": "OCR engine unavailable"},
    },
    summary="Download and extract text from a single Drive file",
)
def extract_file_endpoint(request: ExtractRequest) -> ExtractResponse:
    """Download a single target file into a temporary directory, extract its text, and clean up.

    Processes one file at a time using digital PDF parsing or OCR (images / scanned PDFs).
    """
    # Sanitize file name to avoid directory traversal exploits
    safe_name = Path(request.file_name).name
    if not safe_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A valid file name must be provided.",
        )

    # Isolated temporary workspace ensures no residual files or secrets persist on disk
    with tempfile.TemporaryDirectory(prefix="drive_extractor_") as temp_dir:
        target_path = Path(temp_dir) / safe_name

        # 1. Download target file from Google Drive
        try:
            download_drive_file(request.file_id, target_path)
        except FileTooLargeError as exc:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail=str(exc),
            ) from exc
        except DriveAccessError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(exc),
            ) from exc

        # 2. Extract textual content
        try:
            text, method, page_count = extract_document_text(
                target_path,
                file_type=request.file_type,
            )
        except UnsupportedFileError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc
        except (CorruptedFileError, EncryptedFileError) as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=str(exc),
            ) from exc
        except OCRError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc
        except ExtractionError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Extraction failure: {exc}",
            ) from exc

        return ExtractResponse(
            file_id=request.file_id,
            file_name=safe_name,
            text=text,
            method=method,
            page_count=page_count,
            character_count=len(text),
        )
