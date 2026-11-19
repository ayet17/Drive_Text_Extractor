"""Google Drive interaction module.

Validates public folder links, queries folder contents using gdown,
and filters items to supported document and image formats.
"""

from pathlib import Path
import re
from typing import Literal
import gdown
from app.schemas import DriveFileItem

# Supported file extensions for document text extraction and OCR
PDF_EXTENSIONS: set[str] = {".pdf"}
IMAGE_EXTENSIONS: set[str] = {".png", ".jpg", ".jpeg", ".webp", ".tiff", ".tif"}
SUPPORTED_EXTENSIONS: set[str] = PDF_EXTENSIONS | IMAGE_EXTENSIONS

# Regular expressions to extract folder IDs from various Google Drive URL formats
# e.g., https://drive.google.com/drive/folders/<ID>, open?id=<ID>, or bare ID
FOLDER_URL_PATTERN = re.compile(
    r"(?:https?://)?(?:drive\.google\.com/(?:drive/(?:u/\d+/)?folders/|open\?id=))([a-zA-Z0-9_-]{15,})",
    re.IGNORECASE,
)
BARE_FOLDER_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{15,45}$")

# Maximum number of files processed per folder request to protect resource usage
MAX_FOLDER_FILES: int = 50


class DriveError(Exception):
    """Base exception for Google Drive operations."""


class InvalidDriveURLError(DriveError):
    """Raised when the provided Google Drive link or ID is malformed."""


class DriveAccessError(DriveError):
    """Raised when a folder cannot be accessed (private, deleted, or network failure)."""


def extract_folder_id(url_or_id: str) -> str:
    """Extract and validate the Google Drive folder ID from a URL or raw ID string.

    Args:
        url_or_id: Full Google Drive folder URL or raw alphanumeric folder ID.

    Returns:
        The validated alphanumeric folder ID string.

    Raises:
        InvalidDriveURLError: If the input does not match expected folder patterns.
    """
    clean_input = url_or_id.strip()

    # Match full URL pattern
    match = FOLDER_URL_PATTERN.search(clean_input)
    if match:
        return match.group(1)

    # Match raw folder ID if the user pasted the ID directly
    if BARE_FOLDER_ID_PATTERN.match(clean_input):
        return clean_input

    raise InvalidDriveURLError(
        "Invalid Google Drive folder link. Please provide a link in the format: "
        "https://drive.google.com/drive/folders/<FOLDER_ID>"
    )


def categorize_file(filename: str) -> Literal["pdf", "image"] | None:
    """Classify a file based on its extension into 'pdf', 'image', or None if unsupported.

    Args:
        filename: Name or path of the target file.

    Returns:
        'pdf', 'image', or None if not supported.
    """
    suffix = Path(filename).suffix.lower()
    if suffix in PDF_EXTENSIONS:
        return "pdf"
    if suffix in IMAGE_EXTENSIONS:
        return "image"
    return None


def list_folder_files(url_or_id: str, max_files: int = MAX_FOLDER_FILES) -> list[DriveFileItem]:
    """Retrieve metadata of supported PDF and image files from a public Drive folder.

    Uses gdown with skip_download=True to inspect folder contents without downloading the payload.

    Args:
        url_or_id: Public Google Drive folder link or ID.
        max_files: Guardrail limit on the number of files to process.

    Returns:
        List of DriveFileItem objects with ID, file name, and categorized type.

    Raises:
        InvalidDriveURLError: If the folder URL format is invalid.
        DriveAccessError: If the folder is private, missing, or inaccessible.
    """
    folder_id = extract_folder_id(url_or_id)

    try:
        # skip_download=True inspects folder contents without downloading the payload
        items = gdown.download_folder(
            id=folder_id,
            skip_download=True,
            quiet=True,
            use_cookies=False,
        )
    except Exception as exc:
        raise DriveAccessError(
            f"Unable to access Google Drive folder. Please verify the folder is set to "
            f"'Anyone with the link can view'. Details: {exc}"
        ) from exc

    if not items:
        return []

    filtered_files: list[DriveFileItem] = []

    for item in items:
        raw_name = Path(item.path).name
        file_type = categorize_file(raw_name)

        if file_type is not None:
            filtered_files.append(
                DriveFileItem(
                    id=item.id,
                    name=raw_name,
                    type=file_type,
                )
            )

        # Enforce maximum file limit guardrail
        if len(filtered_files) >= max_files:
            break

    return filtered_files
