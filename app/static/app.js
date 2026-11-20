/**
 * Drive Text Extractor - Frontend Controller
 * Plain vanilla JavaScript interface handling Drive folder inspection,
 * per-file text extraction, clipboard interactions, and a sidebar session history.
 */

document.addEventListener("DOMContentLoaded", () => {
  // Storage key for session history
  const STORAGE_KEY = "drive_text_extractor_history";

  // DOM Elements
  const driveForm = document.getElementById("drive-form");
  const driveUrlInput = document.getElementById("drive-url");
  const btnFetch = document.getElementById("btn-fetch");
  const fetchSpinner = document.getElementById("fetch-spinner");
  const btnFetchText = btnFetch.querySelector(".btn-text");

  const alertBanner = document.getElementById("alert-banner");
  const alertMessage = document.getElementById("alert-message");
  const alertDismiss = document.getElementById("alert-dismiss");

  const filesSection = document.getElementById("files-section");
  const filesList = document.getElementById("files-list");
  const fileCounter = document.getElementById("file-counter");

  const resultSection = document.getElementById("result-section");
  const resultFilename = document.getElementById("result-filename");
  const badgeMethod = document.getElementById("badge-method");
  const metaPages = document.getElementById("meta-pages");
  const metaChars = document.getElementById("meta-chars");
  const extractedTextContent = document.getElementById("extracted-text-content");
  const btnCopy = document.getElementById("btn-copy");
  const copyBtnText = document.getElementById("copy-btn-text");
  const btnDownload = document.getElementById("btn-download");
  const downloadBtnText = document.getElementById("download-btn-text");

  // Sidebar History Elements
  const historyEmpty = document.getElementById("history-empty");
  const historyList = document.getElementById("history-list");
  const historyCounter = document.getElementById("history-counter");
  const btnClearHistory = document.getElementById("btn-clear-history");

  let currentlyExtracting = false;
  let activeHistoryId = null;

  // Icons for files (Inline SVG)
  const SVG_PDF = `
    <svg class="file-row-icon" viewBox="0 0 24 24" fill="none" stroke="#dc2626" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
      <polyline points="14 2 14 8 20 8"></polyline>
      <line x1="9" y1="15" x2="15" y2="15"></line>
    </svg>`;

  const SVG_IMAGE = `
    <svg class="file-row-icon" viewBox="0 0 24 24" fill="none" stroke="#0284c7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
      <circle cx="8.5" cy="8.5" r="1.5"></circle>
      <polyline points="21 15 16 10 5 21"></polyline>
    </svg>`;

  /**
   * Display an alert banner with custom message and styling.
   */
  function showAlert(message, type = "danger") {
    alertBanner.className = `alert ${type}`;
    alertMessage.textContent = message;
    alertBanner.classList.remove("hidden");
  }

  /**
   * Hide the alert banner.
   */
  function hideAlert() {
    alertBanner.classList.add("hidden");
    alertMessage.textContent = "";
  }

  alertDismiss.addEventListener("click", hideAlert);

  /**
   * Fetch and display the list of files from the specified Google Drive folder.
   */
  driveForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    hideAlert();
    resultSection.classList.add("hidden");

    const url = driveUrlInput.value.trim();
    if (!url) {
      showAlert("Please enter a valid Google Drive folder URL.", "danger");
      return;
    }

    // Set loading state
    btnFetch.disabled = true;
    fetchSpinner.classList.remove("hidden");
    btnFetchText.textContent = "Inspecting...";

    try {
      const response = await fetch("/api/files", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to inspect Google Drive folder.");
      }

      renderFilesList(data.files || []);
    } catch (err) {
      filesSection.classList.add("hidden");
      showAlert(err.message, "danger");
    } finally {
      btnFetch.disabled = false;
      fetchSpinner.classList.add("hidden");
      btnFetchText.textContent = "Inspect Folder";
    }
  });

  /**
   * Render the table of detected files in the folder.
   */
  function renderFilesList(files) {
    filesSection.classList.remove("hidden");
    fileCounter.textContent = `${files.length} file${files.length === 1 ? "" : "s"}`;

    if (files.length === 0) {
      filesList.innerHTML = `
        <div class="empty-state">
          <p>No supported PDF or image files found in this folder.</p>
          <p class="form-hint">Make sure the folder is public and contains .pdf, .png, .jpg, .webp, or .tiff files.</p>
        </div>`;
      return;
    }

    let html = `
      <table class="files-table">
        <thead>
          <tr>
            <th>Document</th>
            <th>Type</th>
            <th style="text-align: right;">Action</th>
          </tr>
        </thead>
        <tbody>`;

    files.forEach((file) => {
      const isPdf = file.type === "pdf";
      const icon = isPdf ? SVG_PDF : SVG_IMAGE;
      const typeBadgeClass = isPdf ? "badge-pdf" : "badge-image";
      const typeLabel = isPdf ? "PDF" : "IMAGE";

      html += `
        <tr data-file-id="${escapeHtml(file.id)}">
          <td>
            <div class="file-name-cell">
              ${icon}
              <span title="${escapeHtml(file.name)}">${escapeHtml(file.name)}</span>
            </div>
          </td>
          <td>
            <span class="badge ${typeBadgeClass}">${typeLabel}</span>
          </td>
          <td style="text-align: right;">
            <button
              class="btn btn-secondary btn-sm btn-extract"
              data-id="${escapeHtml(file.id)}"
              data-name="${escapeHtml(file.name)}"
              data-type="${escapeHtml(file.type)}"
            >
              <span class="btn-text">Extract</span>
              <span class="spinner hidden"></span>
            </button>
          </td>
        </tr>`;
    });

    html += `</tbody></table>`;
    filesList.innerHTML = html;

    // Attach event listeners to all Extract buttons
    const extractButtons = filesList.querySelectorAll(".btn-extract");
    extractButtons.forEach((btn) => {
      btn.addEventListener("click", () => handleExtract(btn));
    });
  }

  /**
   * Handle text extraction for an individual file.
   */
  async function handleExtract(button) {
    if (currentlyExtracting) return;

    hideAlert();
    currentlyExtracting = true;

    const fileId = button.dataset.id;
    const fileName = button.dataset.name;
    const fileType = button.dataset.type;

    const btnText = button.querySelector(".btn-text");
    const spinner = button.querySelector(".spinner");

    // Disable all extraction buttons while processing
    const allExtractBtns = filesList.querySelectorAll(".btn-extract");
    allExtractBtns.forEach((b) => (b.disabled = true));

    spinner.classList.remove("hidden");
    btnText.textContent = "Extracting...";

    try {
      const response = await fetch("/api/extract", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          file_id: fileId,
          file_name: fileName,
          file_type: fileType,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || `Failed to extract text from ${fileName}`);
      }

      displayExtractionResult(data);
      saveToHistory(data);
    } catch (err) {
      showAlert(err.message, "danger");
    } finally {
      currentlyExtracting = false;
      allExtractBtns.forEach((b) => (b.disabled = false));
      spinner.classList.add("hidden");
      btnText.textContent = "Extract";
    }
  }

  /**
   * Display extraction results in the preview section.
   */
  function displayExtractionResult(data) {
    activeHistoryId = data.file_id;
    resultFilename.textContent = data.file_name;

    // Render extraction method badge
    const methodLabels = {
      digital: "Digital PDF",
      ocr: "Image OCR",
      ocr_fallback: "Scanned PDF (OCR)",
    };

    badgeMethod.className = `badge badge-method-${data.method}`;
    badgeMethod.textContent = methodLabels[data.method] || data.method.toUpperCase();

    metaPages.textContent = `Pages: ${data.page_count}`;
    metaChars.textContent = `Characters: ${data.character_count.toLocaleString()}`;

    // Show extracted text or placeholder if empty
    if (data.text && data.text.trim().length > 0) {
      extractedTextContent.textContent = data.text;
    } else {
      extractedTextContent.textContent = "[No readable text found in document]";
    }

    resultSection.classList.remove("hidden");
    resultSection.scrollIntoView({ behavior: "smooth", block: "nearest" });

    // Update active highlight in sidebar
    highlightActiveHistoryCard();
  }

  /**
   * Copy extracted text to system clipboard.
   */
  btnCopy.addEventListener("click", async () => {
    const textToCopy = extractedTextContent.textContent;
    if (!textToCopy || textToCopy === "[No readable text found in document]") {
      return;
    }

    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(textToCopy);
      } else {
        // Fallback for older browsers
        const textarea = document.createElement("textarea");
        textarea.value = textToCopy;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
      }

      copyBtnText.textContent = "Copied!";
      btnCopy.classList.add("btn-primary");
      btnCopy.classList.remove("btn-secondary");

      setTimeout(() => {
        copyBtnText.textContent = "Copy Text";
        btnCopy.classList.remove("btn-primary");
        btnCopy.classList.add("btn-secondary");
      }, 2000);
    } catch (err) {
      showAlert("Failed to copy text to clipboard.", "danger");
    }
  });

  /**
   * Download extracted text as a local .txt file.
   */
  btnDownload.addEventListener("click", () => {
    const textToDownload = extractedTextContent.textContent;
    if (!textToDownload || textToDownload === "[No readable text found in document]") {
      return;
    }

    // Determine filename: strip original extension and append _extracted.txt
    const baseName = (resultFilename.textContent || "document").replace(/\.[^/.]+$/, "") || "document";
    const downloadFileName = `${baseName}_extracted.txt`;

    try {
      const blob = new Blob([textToDownload], { type: "text/plain;charset=utf-8" });
      const downloadUrl = URL.createObjectURL(blob);
      const tempLink = document.createElement("a");
      tempLink.href = downloadUrl;
      tempLink.download = downloadFileName;
      document.body.appendChild(tempLink);
      tempLink.click();
      document.body.removeChild(tempLink);
      URL.revokeObjectURL(downloadUrl);

      // Temporary visual confirmation
      downloadBtnText.textContent = "Downloaded!";
      btnDownload.classList.add("btn-primary");
      btnDownload.classList.remove("btn-secondary");

      setTimeout(() => {
        downloadBtnText.textContent = "Download";
        btnDownload.classList.remove("btn-primary");
        btnDownload.classList.add("btn-secondary");
      }, 2000);
    } catch (err) {
      showAlert("Failed to download text file.", "danger");
    }
  });

  // --- Left Sidebar Session History Management ---

  /**
   * Load extraction history from localStorage.
   */
  function getHistory() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      return stored ? JSON.parse(stored) : [];
    } catch (e) {
      return [];
    }
  }

  /**
   * Save a newly completed extraction item into localStorage and update the sidebar.
   */
  function saveToHistory(data) {
    let history = getHistory();

    const historyItem = {
      file_id: data.file_id,
      file_name: data.file_name,
      text: data.text,
      method: data.method,
      page_count: data.page_count,
      character_count: data.character_count,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    // Remove older duplicate if same file_id was previously extracted
    history = history.filter((item) => item.file_id !== data.file_id);

    // Prepend latest extraction to the top
    history.unshift(historyItem);

    // Keep history lean (maximum 20 items)
    if (history.length > 20) {
      history = history.slice(0, 20);
    }

    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
    } catch (e) {
      // Storage quota safety
    }

    activeHistoryId = data.file_id;
    renderHistory();
  }

  /**
   * Render the saved extractions in the left sidebar.
   */
  function renderHistory() {
    const history = getHistory();

    if (history.length === 0) {
      historyEmpty.classList.remove("hidden");
      historyList.classList.add("hidden");
      historyCounter.textContent = "0";
      return;
    }

    historyEmpty.classList.add("hidden");
    historyList.classList.remove("hidden");
    historyCounter.textContent = `${history.length}`;

    const methodLabels = {
      digital: "Digital PDF",
      ocr: "Image OCR",
      ocr_fallback: "Scanned PDF",
    };

    let html = "";
    history.forEach((item, index) => {
      const isPdf = item.file_name.toLowerCase().endsWith(".pdf");
      const icon = isPdf ? SVG_PDF : SVG_IMAGE;
      const methodLabel = methodLabels[item.method] || item.method.toUpperCase();
      const isActive = activeHistoryId === item.file_id ? "active" : "";

      html += `
        <div class="history-card ${isActive}" data-index="${index}" data-file-id="${escapeHtml(item.file_id)}">
          <div class="history-card-top">
            ${icon}
            <span class="history-card-name" title="${escapeHtml(item.file_name)}">${escapeHtml(item.file_name)}</span>
          </div>
          <div class="history-card-bottom">
            <span class="badge badge-method-${escapeHtml(item.method)}">${escapeHtml(methodLabel)}</span>
            <span>${escapeHtml(item.timestamp)}</span>
          </div>
        </div>`;
    });

    historyList.innerHTML = html;

    // Attach click handlers to each history card in the sidebar
    const historyCards = historyList.querySelectorAll(".history-card");
    historyCards.forEach((card) => {
      card.addEventListener("click", () => {
        const itemIndex = parseInt(card.dataset.index, 10);
        const selectedItem = history[itemIndex];
        if (selectedItem) {
          displayExtractionResult(selectedItem);
        }
      });
    });
  }

  /**
   * Highlight the currently viewed item in the left sidebar.
   */
  function highlightActiveHistoryCard() {
    const historyCards = historyList.querySelectorAll(".history-card");
    historyCards.forEach((card) => {
      if (card.dataset.fileId === activeHistoryId) {
        card.classList.add("active");
      } else {
        card.classList.remove("active");
      }
    });
  }

  /**
   * Clear all stored history.
   */
  btnClearHistory.addEventListener("click", () => {
    localStorage.removeItem(STORAGE_KEY);
    activeHistoryId = null;
    renderHistory();
  });

  /**
   * Escape HTML utility to prevent XSS.
   */
  function escapeHtml(string) {
    if (!string) return "";
    const div = document.createElement("div");
    div.innerText = string;
    return div.innerHTML;
  }

  // Initial load: render any previous extractions saved in this browser
  renderHistory();
});
