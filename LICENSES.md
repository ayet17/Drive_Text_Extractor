# Dependency License Compliance

This project adheres strictly to permissive open-source licensing. Every direct dependency and external tool is distributed under a business-friendly, permissive license (**MIT**, **BSD**, or **Apache 2.0**).

> **License Compliance Notice:**  
> Copyleft and AGPL-licensed libraries (such as *PyMuPDF* / *fitz*) were deliberately avoided to ensure full compliance with commercial and corporate distribution policies. Scanned PDF page rendering is achieved via **pypdfium2** (Apache 2.0 / BSD) and text extraction via **pypdf** (BSD-3-Clause).

---

## Dependency Inventory

| Component | Category | Version | License | Upstream Project / Repository |
| :--- | :--- | :--- | :--- | :--- |
| **FastAPI** | Backend Framework | `>=0.110.0` | MIT | [github.com/fastapi/fastapi](https://github.com/fastapi/fastapi) |
| **Uvicorn** | ASGI Web Server | `>=0.28.0` | BSD-3-Clause | [github.com/encode/uvicorn](https://github.com/encode/uvicorn) |
| **Pydantic** | Validation & Schemas | `>=2.6.0` | MIT | [github.com/pydantic/pydantic](https://github.com/pydantic/pydantic) |
| **gdown** | Public Drive Downloader | `>=5.1.0` | MIT | [github.com/wkentaro/gdown](https://github.com/wkentaro/gdown) |
| **pypdf** | Digital PDF Text Extractor | `>=4.1.0` | BSD-3-Clause | [github.com/py-pdf/pypdf](https://github.com/py-pdf/pypdf) |
| **pytesseract** | Python Tesseract Wrapper | `>=0.3.10` | Apache-2.0 | [github.com/madmaze/pytesseract](https://github.com/madmaze/pytesseract) |
| **Pillow** | Image Processing | `>=10.2.0` | HPND (MIT-like) | [github.com/python-pillow/Pillow](https://github.com/python-pillow/Pillow) |
| **pypdfium2** | PDF-to-Bitmap Renderer | `>=4.28.0` | Apache-2.0 / BSD | [github.com/pypdfium2-team/pypdfium2](https://github.com/pypdfium2-team/pypdfium2) |
| **pytest** | Test Framework (Dev) | `>=8.0.0` | MIT | [github.com/pytest-dev/pytest](https://github.com/pytest-dev/pytest) |
| **httpx** | HTTP Client (Dev) | `>=0.27.0` | BSD-3-Clause | [github.com/encode/httpx](https://github.com/encode/httpx) |
| **Tesseract OCR** | External OCR Engine | `>=5.0.0` | Apache-2.0 | [github.com/tesseract-ocr/tesseract](https://github.com/tesseract-ocr/tesseract) |

---

## License Summary

- **MIT License**: FastAPI, Pydantic, gdown, pytest
- **BSD-3-Clause**: Uvicorn, pypdf, httpx
- **Apache 2.0**: pytesseract, Tesseract OCR, pypdfium2
- **HPND (Permissive)**: Pillow
- **AGPL / Strong Copyleft**: None (0%)
