# Drive Text Extractor (POC)

A clean, lightweight Proof-of-Concept (POC) web application that inspects public Google Drive folders, lists documents and images, and extracts their textual content using native PDF parsing and Optical Character Recognition (OCR).


---

## What It Does

1. **Folder Inspection**: Takes any public Google Drive folder link (*"Anyone with the link can view"*), parses the folder ID, and retrieves file metadata without requiring Google Cloud API keys.
2. **Format Filtering**: Automatically filters folder contents to supported documents and images:
   - **PDF**: `.pdf`
   - **Images**: `.png`, `.jpg`, `.jpeg`, `.webp`, `.tiff`, `.tif`
3. **Smart Text Extraction**:
   - **Digital PDFs**: Extracts existing digital text layers directly with `pypdf`.
   - **Scanned PDFs (Fallback)**: If no digital text layer is detected, pages are rendered into high-resolution images via `pypdfium2` and OCR is performed page-by-page.
   - **Standalone Images**: Extracts text using Tesseract OCR via `pytesseract`.
4. **Single-Page UI**: Clean, responsive vanilla HTML/CSS/JavaScript web interface with real-time extraction feedback, method indicators, and one-click clipboard copying.

---

## Architecture Overview

```text
+-------------------------------------------------------------------------+
|                              Web Browser                                |
|  - HTML5 / CSS3 / Vanilla JS (no build step, no framework overhead)    |
+-------------------------------------------------------------------------+
                                    |
                    REST Requests   |   Static Assets
                    (JSON / Fetch)  |   (HTML, CSS, JS)
                                    v
+-------------------------------------------------------------------------+
|                          FastAPI Application                            |
|                          (app/main.py)                                  |
|   GET  /          -> Serves index.html                                  |
|   GET  /health    -> Health check status                                |
|   POST /api/files -> Inspect folder contents                            |
|   POST /api/extract -> Download & extract single file                   |
+-------------------------------------------------------------------------+
            |                                           |
            v                                           v
+-------------------------+                 +-------------------------+
|      app/drive.py       |                 |    app/extractor.py     |
| - URL regex validation  |                 | - pypdf (Digital PDF)   |
| - Folder ID extraction  |                 | - pypdfium2 (Renderer)  |
| - gdown metadata query  |                 | - pytesseract (OCR)     |
| - Download with size cap|                 | - Fallback coordinator  |
+-------------------------+                 +-------------------------+
            |                                           |
            +--------------------+----------------------+
                                 |
                                 v
                +---------------------------------+
                |   Temporary Isolated Storage    |
                | - tempfile.TemporaryDirectory() |
                | - Guaranteed automatic cleanup  |
                +---------------------------------+
```

### Design Principles
- **Minimal & Explainable**: Simple, readable code over complex abstractions.
- **Resource Protection**: Max 50 files listed per folder; 25 MB max file size limit.
- **Privacy & Security**: Files are processed in isolated temporary directories and deleted immediately upon request completion. No secrets or client files are retained.
- **100% Permissive Licensing**: Strictly MIT, BSD, and Apache-2.0 dependencies. PyMuPDF was excluded due to its copyleft AGPL license.

---

## Prerequisites

- **Python 3.11+**
- **Tesseract OCR Engine** installed on the host system:
  - **Windows**: Download and run the [UB-Mannheim Tesseract Installer](https://github.com/UB-Mannheim/tesseract/wiki).
    - Default path: `C:\Program Files\Tesseract-OCR\tesseract.exe` (automatically detected).
    - Or via Winget: `winget install UB-Mannheim.TesseractOCR`
  - **macOS**: `brew install tesseract`
  - **Linux (Ubuntu/Debian)**: `sudo apt-get update && sudo apt-get install -y tesseract-ocr`

---

## Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Drive_Text_Extractor
   ```

2. **Create and activate a virtual environment**:
   - **Windows (PowerShell)**:
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
   - **Windows (CMD)**:
     ```cmd
     python -m venv .venv
     .\.venv\Scripts\activate.bat
     ```
   - **macOS / Linux**:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify Tesseract installation (optional)**:
   If Tesseract is installed in a non-standard path, set the environment variable:
   ```bash
   export TESSERACT_CMD="/path/to/tesseract"
   # Windows PowerShell:
   $env:TESSERACT_CMD = "C:\CustomPath\tesseract.exe"
   ```

---

## Running the Application

Start the FastAPI server using Uvicorn:

```bash
uvicorn app.main:app --reload --port 8000
```

Navigate to [http://localhost:8000](http://localhost:8000) in your web browser.

Interactive OpenAPI documentation is available at [http://localhost:8000/docs](http://localhost:8000/docs).

---

## Usage Guide

1. Paste a public Google Drive folder URL (e.g. `https://drive.google.com/drive/folders/...`) into the input box.
2. Click **Inspect Folder**. The application fetches metadata and displays all detected PDFs and images with file type badges.
3. Click **Extract** next to any file. The server will download the file into a temporary sandbox, parse its text, and return the result.
4. Review the extracted text in the preview pane, check the extraction method (`Digital PDF`, `Image OCR`, or `Scanned PDF (OCR)`), and click **Copy Text** to copy to your clipboard.
5. arabic text extraction is not supported yet

---

## Running Tests

Run the test suite with pytest:

```bash
pytest -v
```

The test suite covers:
- Google Drive URL regex parsing and ID extraction.
- File extension classification and whitelist filtering.
- Digital PDF text extraction on real PDF samples.
- Blank and corrupted file handling.
- FastAPI endpoint responses and error status code mappings (400, 413, 502).

---

## Known Limitations

- **Public Folders Only**: Private folders requiring OAuth2 credentials or Google login cannot be accessed.
- **Google Drive Rate Limiting**: Very rapid repeated requests against public Drive folders may trigger Google's unauthenticated rate limits.
- **OCR Accuracy**: OCR performance depends on image resolution, lighting, and scanned page orientation.
- **Synchronous Extraction**: Large multi-page documents are processed synchronously within the HTTP request cycle; processing very large documents (>50 pages) may take several seconds.

---

## Future Improvements

- **Table & Layout Preservation**: Integrate layout-aware extraction to preserve tabular data in financial documents and forms.
- **arabic language to be added in the extraction 
- **Result Caching**: Cache extracted text by file hash / ID in Redis to avoid re-downloading unchanged documents.
- **Batch Export**: Provide a "Download All as ZIP" option to export extracted `.txt` files for every document in the folder.

---

## License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) and [LICENSES.md](LICENSES.md) for full compliance details.
