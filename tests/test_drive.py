"""Unit tests for Google Drive validation and listing functionality."""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from app.drive import (
    DriveAccessError,
    FileTooLargeError,
    InvalidDriveURLError,
    categorize_file,
    download_drive_file,
    extract_folder_id,
    list_folder_files,
)


class TestDriveURLValidation:
    """Tests for validating Drive folder links and extracting IDs."""

    def test_extract_folder_id_standard_url(self) -> None:
        url = "https://drive.google.com/drive/folders/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs"
        assert extract_folder_id(url) == "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs"

    def test_extract_folder_id_with_user_index(self) -> None:
        url = "https://drive.google.com/drive/u/1/folders/1a2b3c4d5e6f7g8h9i0j_klm-NOP"
        assert extract_folder_id(url) == "1a2b3c4d5e6f7g8h9i0j_klm-NOP"

    def test_extract_folder_id_open_parameter(self) -> None:
        url = "https://drive.google.com/open?id=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs"
        assert extract_folder_id(url) == "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs"

    def test_extract_folder_id_bare_id(self) -> None:
        folder_id = "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs"
        assert extract_folder_id(folder_id) == folder_id

    @pytest.mark.parametrize(
        "invalid_input",
        [
            "",
            "   ",
            "https://example.com/not-drive",
            "https://drive.google.com/file/d/123",
            "short",
            "invalid!characters@#$%",
        ],
    )
    def test_extract_folder_id_invalid(self, invalid_input: str) -> None:
        with pytest.raises(InvalidDriveURLError):
            extract_folder_id(invalid_input)


class TestFileCategorization:
    """Tests for file extension classification."""

    @pytest.mark.parametrize(
        "filename",
        ["document.pdf", "REPORT.PDF", "path/to/invoice.pdf"],
    )
    def test_categorize_pdf(self, filename: str) -> None:
        assert categorize_file(filename) == "pdf"

    @pytest.mark.parametrize(
        "filename",
        ["image.png", "photo.jpg", "pic.jpeg", "banner.webp", "scan.tiff", "doc.tif"],
    )
    def test_categorize_images(self, filename: str) -> None:
        assert categorize_file(filename) == "image"

    @pytest.mark.parametrize(
        "filename",
        ["data.csv", "notes.txt", "archive.zip", "program.exe", "doc.docx"],
    )
    def test_categorize_unsupported(self, filename: str) -> None:
        assert categorize_file(filename) is None


class TestDriveListingAndDownload:
    """Tests for folder file queries and download limits."""

    @patch("app.drive.gdown.download_folder")
    def test_list_folder_files_success(self, mock_download_folder: MagicMock) -> None:
        # Mock item returned by gdown with id and path
        item1 = MagicMock(id="id-1", path="document.pdf")
        item2 = MagicMock(id="id-2", path="photo.png")
        item3 = MagicMock(id="id-3", path="ignore.csv")
        mock_download_folder.return_value = [item1, item2, item3]

        files = list_folder_files("https://drive.google.com/drive/folders/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs")

        assert len(files) == 2
        assert files[0].id == "id-1"
        assert files[0].name == "document.pdf"
        assert files[0].type == "pdf"
        assert files[1].id == "id-2"
        assert files[1].name == "photo.png"
        assert files[1].type == "image"

    @patch("app.drive.gdown.download_folder")
    def test_list_folder_files_drive_access_error(self, mock_download_folder: MagicMock) -> None:
        mock_download_folder.side_effect = RuntimeError("Drive network failure")

        with pytest.raises(DriveAccessError):
            list_folder_files("https://drive.google.com/drive/folders/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs")

    @patch("app.drive.gdown.download")
    def test_download_file_size_limit_exceeded(self, mock_download: MagicMock, tmp_path: Path) -> None:
        target_file = tmp_path / "oversized.pdf"
        # Write dummy file of 100 bytes but enforce limit of 50 bytes
        target_file.write_bytes(b"x" * 100)
        mock_download.return_value = str(target_file)

        with pytest.raises(FileTooLargeError):
            download_drive_file("fake-id", target_file, max_bytes=50)

        # Ensure oversized file was removed to save space
        assert not target_file.exists()
