"""Pydantic schemas for request and response models."""

from typing import Literal
from pydantic import BaseModel, Field


class FolderRequest(BaseModel):
    """Request payload containing the Google Drive folder link."""

    url: str = Field(
        ...,
        description="Public Google Drive folder URL or folder ID.",
        examples=["https://drive.google.com/drive/folders/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs"],
    )


class DriveFileItem(BaseModel):
    """Metadata for an individual file detected in the Google Drive folder."""

    id: str = Field(..., description="Unique Google Drive file identifier.")
    name: str = Field(..., description="Original file name including extension.")
    type: Literal["pdf", "image"] = Field(
        ...,
        description="Categorized file type ('pdf' for documents, 'image' for visual media).",
    )
    size: int | None = Field(
        default=None,
        description="File size in bytes if available from metadata.",
    )


class FileListResponse(BaseModel):
    """Response payload returning filtered files found in the folder."""

    files: list[DriveFileItem] = Field(
        default_factory=list,
        description="List of supported PDF and image files found.",
    )
    total_count: int = Field(
        ...,
        description="Total number of supported files found.",
    )


class ExtractRequest(BaseModel):
    """Request payload to extract text from a single Google Drive file."""

    file_id: str = Field(..., description="Google Drive file ID to download and process.")
    file_name: str = Field(..., description="Original name of the target file.")
    file_type: Literal["pdf", "image"] | None = Field(
        default=None,
        description="Pre-classified file type if known, or inferred from filename.",
    )


class ExtractResponse(BaseModel):
    """Result of document text extraction and OCR."""

    file_id: str = Field(..., description="Processed Google Drive file ID.")
    file_name: str = Field(..., description="Name of the processed file.")
    text: str = Field(..., description="Extracted textual content.")
    method: Literal["digital", "ocr", "ocr_fallback"] = Field(
        ...,
        description="Extraction pipeline utilized: 'digital', 'ocr', or 'ocr_fallback'.",
    )
    page_count: int = Field(..., description="Total pages or images parsed.")
    character_count: int = Field(..., description="Character count of extracted text.")


class ErrorResponse(BaseModel):
    """Standardized error response payload."""

    detail: str = Field(..., description="Human-readable error explanation.")
