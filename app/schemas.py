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


class ErrorResponse(BaseModel):
    """Standardized error response payload."""

    detail: str = Field(..., description="Human-readable error explanation.")
