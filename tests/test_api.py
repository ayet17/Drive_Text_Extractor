"""Unit tests for FastAPI endpoints and HTTP exception mappings."""

from unittest.mock import MagicMock, patch
from fastapi import HTTPException
import pytest

from app.drive import DriveAccessError, FileTooLargeError
from app.main import (
    extract_file_endpoint,
    health_check,
    list_files_endpoint,
)
from app.schemas import DriveFileItem, ExtractRequest, FolderRequest


class TestAPIEndpoints:
    """Tests for core API handlers."""

    def test_health_check_endpoint(self) -> None:
        result = health_check()
        assert result == {"status": "ok"}

    def test_list_files_endpoint_invalid_url(self) -> None:
        req = FolderRequest(url="invalid-url")
        with pytest.raises(HTTPException) as exc_info:
            list_files_endpoint(req)
        assert exc_info.value.status_code == 400
        assert "Invalid Google Drive folder link" in exc_info.value.detail

    @patch("app.main.list_folder_files")
    def test_list_files_endpoint_success(self, mock_list_files: MagicMock) -> None:
        mock_list_files.return_value = [
            DriveFileItem(id="doc1", name="doc.pdf", type="pdf"),
            DriveFileItem(id="img1", name="image.png", type="image"),
        ]

        req = FolderRequest(url="https://drive.google.com/drive/folders/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs")
        response = list_files_endpoint(req)

        assert response.total_count == 2
        assert len(response.files) == 2
        assert response.files[0].name == "doc.pdf"

    @patch("app.main.list_folder_files")
    def test_list_files_endpoint_drive_failure(self, mock_list_files: MagicMock) -> None:
        mock_list_files.side_effect = DriveAccessError("Folder not accessible")

        req = FolderRequest(url="https://drive.google.com/drive/folders/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs")
        with pytest.raises(HTTPException) as exc_info:
            list_files_endpoint(req)
        assert exc_info.value.status_code == 502

    def test_extract_file_endpoint_empty_filename(self) -> None:
        req = ExtractRequest(file_id="id123", file_name="")
        with pytest.raises(HTTPException) as exc_info:
            extract_file_endpoint(req)
        assert exc_info.value.status_code == 400

    @patch("app.main.download_drive_file")
    @patch("app.main.extract_document_text")
    def test_extract_file_endpoint_success(
        self,
        mock_extract_text: MagicMock,
        mock_download: MagicMock,
    ) -> None:
        mock_extract_text.return_value = ("Sample extracted text", "digital", 1)

        req = ExtractRequest(file_id="file-123", file_name="sample.pdf", file_type="pdf")
        response = extract_file_endpoint(req)

        assert response.file_id == "file-123"
        assert response.file_name == "sample.pdf"
        assert response.text == "Sample extracted text"
        assert response.method == "digital"
        assert response.page_count == 1
        assert response.character_count == len("Sample extracted text")

    @patch("app.main.download_drive_file")
    def test_extract_file_endpoint_file_too_large(self, mock_download: MagicMock) -> None:
        mock_download.side_effect = FileTooLargeError("File exceeds 25 MB limit")

        req = ExtractRequest(file_id="large-id", file_name="huge.pdf", file_type="pdf")
        with pytest.raises(HTTPException) as exc_info:
            extract_file_endpoint(req)
        assert exc_info.value.status_code == 413
        assert "File exceeds 25 MB limit" in exc_info.value.detail

    @patch("app.main.download_drive_file")
    def test_extract_file_endpoint_download_failed(self, mock_download: MagicMock) -> None:
        mock_download.side_effect = DriveAccessError("File unreachable")

        req = ExtractRequest(file_id="bad-id", file_name="file.pdf", file_type="pdf")
        with pytest.raises(HTTPException) as exc_info:
            extract_file_endpoint(req)
        assert exc_info.value.status_code == 502
