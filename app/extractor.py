"""Document text extraction engine.

Handles digital PDF text parsing via pypdf, optical character recognition (OCR)
for standalone images via pytesseract, and OCR fallback for scanned PDFs
rendered to images using pypdfium2.
"""

import os
from pathlib import Path
import shutil
from typing import Literal
from PIL import Image
import pypdfium2 as pdfium
from pypdf import PdfReader
from pypdf.errors import PyPdfError
import pytesseract

# Supported image and document extensions
PDF_EXTENSIONS: set[str] = {".pdf"}
IMAGE_EXTENSIONS: set[str] = {".png", ".jpg", ".jpeg", ".webp", ".tiff", ".tif"}

# Common fallback paths for Tesseract binary on Windows installations
WINDOWS_TESSERACT_PATHS: list[str] = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
]


class ExtractionError(Exception):
    """Base exception for all document text extraction errors."""


class UnsupportedFileError(ExtractionError):
    """Raised when a file format is not supported for extraction."""


class CorruptedFileError(ExtractionError):
    """Raised when a file is corrupted, truncated, or unreadable."""


class EncryptedFileError(ExtractionError):
    """Raised when a PDF is password-protected and cannot be decrypted."""


class OCRError(ExtractionError):
    """Raised when the OCR engine fails or is not installed."""


def configure_tesseract() -> None:
    """Detect and configure Tesseract executable path if not already on system PATH.

    Supports custom environment variable TESSERACT_CMD or standard Windows directories.
    """
    env_path = os.getenv("TESSERACT_CMD")
    if env_path and Path(env_path).is_file():
        pytesseract.pytesseract.tesseract_cmd = env_path
        return

    # If tesseract is already found in PATH, use default
    if shutil.which("tesseract"):
        return

    # Check common Windows installer default locations
    for standard_path in WINDOWS_TESSERACT_PATHS:
        if Path(standard_path).is_file():
            pytesseract.pytesseract.tesseract_cmd = standard_path
            return


# Initialize tesseract configuration at import time
configure_tesseract()


def extract_digital_pdf_text(file_path: Path | str) -> tuple[str, int]:
    """Extract embedded digital text from a PDF file using pypdf.

    Args:
        file_path: Path to the target PDF file on disk.

    Returns:
        A tuple of (extracted_text, total_pages). If the PDF is scanned or has
        no text layer, extracted_text will be an empty string.

    Raises:
        CorruptedFileError: If the PDF structure is broken or cannot be parsed.
        EncryptedFileError: If the PDF is encrypted with a password.
    """
    path = Path(file_path)

    if not path.is_file():
        raise CorruptedFileError(f"Target file does not exist: {path.name}")

    try:
        reader = PdfReader(str(path))
    except (PyPdfError, OSError, ValueError) as exc:
        raise CorruptedFileError(f"Failed to parse PDF '{path.name}': {exc}") from exc

    if reader.is_encrypted:
        try:
            decrypt_success = reader.decrypt("")
            if not decrypt_success:
                raise EncryptedFileError(f"PDF '{path.name}' is password protected and cannot be read.")
        except Exception as exc:
            raise EncryptedFileError(f"PDF '{path.name}' is password protected.") from exc

    total_pages = len(reader.pages)
    extracted_pages: list[str] = []

    for page in reader.pages:
        try:
            page_text = page.extract_text() or ""
            cleaned = page_text.strip()
            if cleaned:
                extracted_pages.append(cleaned)
        except Exception:
            continue

    combined_text = "\n\n".join(extracted_pages).strip()
    return combined_text, total_pages


def extract_text_from_image(file_path: Path | str) -> str:
    """Perform OCR on an image file (PNG, JPG, WEBP, TIFF) using pytesseract.

    Args:
        file_path: Path to the image file.

    Returns:
        Extracted text string from the image.

    Raises:
        OCRError: If Tesseract OCR is not installed or fails.
        CorruptedFileError: If the image cannot be loaded or opened.
    """
    path = Path(file_path)

    if not path.is_file():
        raise CorruptedFileError(f"Target image does not exist: {path.name}")

    try:
        with Image.open(str(path)) as img:
            # Normalize color mode to RGB for reliable OCR processing
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            text = pytesseract.image_to_string(img)
            return text.strip()
    except pytesseract.TesseractNotFoundError as exc:
        raise OCRError(
            "Tesseract OCR is not installed or not in system PATH. "
            "Please install Tesseract OCR on your machine."
        ) from exc
    except (OSError, ValueError) as exc:
        raise CorruptedFileError(f"Failed to open image file '{path.name}': {exc}") from exc
    except Exception as exc:
        raise OCRError(f"OCR processing failed for image '{path.name}': {exc}") from exc


def extract_text_from_scanned_pdf(file_path: Path | str, render_scale: float = 2.0) -> tuple[str, int]:
    """Render pages of a scanned PDF as bitmap images using pypdfium2 and extract text via OCR.

    Args:
        file_path: Path to the scanned PDF document.
        render_scale: Rendering resolution multiplier (~144 DPI at scale=2.0).

    Returns:
        A tuple of (extracted_text, total_pages).

    Raises:
        OCRError: If Tesseract OCR is not found.
        CorruptedFileError: If the PDF cannot be rendered.
    """
    path = Path(file_path)

    try:
        pdf = pdfium.PdfDocument(str(path))
    except Exception as exc:
        raise CorruptedFileError(f"Failed to load PDF for OCR rendering: {exc}") from exc

    page_texts: list[str] = []
    total_pages = len(pdf)

    try:
        for page_idx in range(total_pages):
            page = pdf[page_idx]
            # Render page to bitmap then convert to PIL Image
            bitmap = page.render(scale=render_scale)
            pil_image = bitmap.to_pil()
            page_text = pytesseract.image_to_string(pil_image)
            cleaned = page_text.strip()
            if cleaned:
                page_texts.append(cleaned)
    except pytesseract.TesseractNotFoundError as exc:
        raise OCRError(
            "Tesseract OCR is not installed or not in system PATH. "
            "Please install Tesseract OCR on your machine."
        ) from exc
    except Exception as exc:
        raise ExtractionError(f"OCR failed on scanned PDF '{path.name}': {exc}") from exc
    finally:
        # Crucial for Windows: release file handle to prevent locking
        pdf.close()

    return "\n\n".join(page_texts).strip(), total_pages


def extract_document_text(
    file_path: Path | str,
    file_type: str | None = None,
) -> tuple[str, Literal["digital", "ocr", "ocr_fallback"], int]:
    """High-level extraction dispatcher.

    For PDFs: attempts digital extraction first; falls back to OCR if no digital text is found.
    For images: performs direct OCR.

    Args:
        file_path: Path to the target file.
        file_type: Optional explicit file type ('pdf' or 'image'). If omitted, inferred from extension.

    Returns:
        A tuple of (extracted_text, extraction_method, page_count).
    """
    path = Path(file_path)
    suffix = path.suffix.lower()

    if not file_type:
        if suffix in PDF_EXTENSIONS:
            file_type = "pdf"
        elif suffix in IMAGE_EXTENSIONS:
            file_type = "image"
        else:
            raise UnsupportedFileError(f"Unsupported file format '{suffix}'. Supported formats: PDF, PNG, JPG, WEBP, TIFF.")

    if file_type == "image":
        text = extract_text_from_image(path)
        return text, "ocr", 1

    if file_type == "pdf":
        digital_text, page_count = extract_digital_pdf_text(path)
        # If the PDF contains a digital text layer, return immediately
        if digital_text:
            return digital_text, "digital", page_count

        # Otherwise, fall back to OCR for scanned or flattened PDF
        ocr_text, ocr_pages = extract_text_from_scanned_pdf(path)
        return ocr_text, "ocr_fallback", ocr_pages

    raise UnsupportedFileError(f"Unknown file classification: {file_type}")
