"""Unit tests for document text extraction and error handling."""

from pathlib import Path
from unittest.mock import MagicMock, patch
from pypdf import PdfWriter
import pytest

from app.extractor import (
    CorruptedFileError,
    OCRError,
    UnsupportedFileError,
    extract_digital_pdf_text,
    extract_document_text,
)


@pytest.fixture
def digital_pdf_file(tmp_path: Path) -> Path:
    """Generate a minimal valid PDF containing digital text."""
    pdf_content = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
        b"4 0 obj\n<< /Length 55 >>\nstream\n"
        b"BT\n/F1 18 Tf\n50 100 Td\n(Dixpertia Assessment Demo) Tj\nET\n"
        b"endstream\nendobj\n"
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        b"xref\n0 6\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"0000000244 00000 n \n"
        b"0000000350 00000 n \n"
        b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n433\n%%EOF\n"
    )
    pdf_path = tmp_path / "sample_digital.pdf"
    pdf_path.write_bytes(pdf_content)
    return pdf_path


@pytest.fixture
def blank_pdf_file(tmp_path: Path) -> Path:
    """Generate a blank PDF with no textual content."""
    pdf_path = tmp_path / "blank.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    with open(pdf_path, "wb") as f:
        writer.write(f)
    return pdf_path


class TestDigitalPDFExtraction:
    """Tests for extracting text layers from digital PDF files."""

    def test_extract_digital_pdf_with_text(self, digital_pdf_file: Path) -> None:
        text, pages = extract_digital_pdf_text(digital_pdf_file)
        assert pages == 1
        assert "Dixpertia Assessment Demo" in text

    def test_extract_blank_pdf(self, blank_pdf_file: Path) -> None:
        text, pages = extract_digital_pdf_text(blank_pdf_file)
        assert pages == 1
        assert text == ""

    def test_extract_corrupted_file(self, tmp_path: Path) -> None:
        corrupted = tmp_path / "broken.pdf"
        corrupted.write_text("This is plain text, not a valid PDF.")

        with pytest.raises(CorruptedFileError):
            extract_digital_pdf_text(corrupted)

    def test_extract_non_existent_file(self, tmp_path: Path) -> None:
        missing = tmp_path / "missing.pdf"
        with pytest.raises(CorruptedFileError):
            extract_digital_pdf_text(missing)


class TestExtractorDispatcher:
    """Tests for the high-level extract_document_text coordinator."""

    def test_extract_document_text_digital_pdf(self, digital_pdf_file: Path) -> None:
        text, method, pages = extract_document_text(digital_pdf_file)
        assert method == "digital"
        assert "Dixpertia Assessment Demo" in text
        assert pages == 1

    def test_extract_document_text_unsupported_extension(self, tmp_path: Path) -> None:
        unsupported = tmp_path / "archive.zip"
        unsupported.write_bytes(b"PK\x03\x04")

        with pytest.raises(UnsupportedFileError):
            extract_document_text(unsupported)

    @patch("app.extractor.extract_digital_pdf_text")
    @patch("app.extractor.extract_text_from_scanned_pdf")
    def test_extract_document_text_ocr_fallback(
        self,
        mock_ocr_pdf: MagicMock,
        mock_digital_pdf: MagicMock,
        tmp_path: Path,
    ) -> None:
        # Simulate a PDF with zero digital text
        mock_digital_pdf.return_value = ("", 2)
        mock_ocr_pdf.return_value = ("Extracted OCR text", 2)

        sample_pdf = tmp_path / "scanned.pdf"
        sample_pdf.write_bytes(b"%PDF-dummy")

        text, method, pages = extract_document_text(sample_pdf)

        assert method == "ocr_fallback"
        assert text == "Extracted OCR text"
        assert pages == 2
        mock_ocr_pdf.assert_called_once_with(sample_pdf)
