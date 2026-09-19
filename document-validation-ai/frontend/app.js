/**
 * app.js
 * ------
 * Frontend controller for Document Validation AI Web Desktop GUI.
 */

document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("fileInput");
  const browseBtn = document.getElementById("browseBtn");
  const dropzonePrompt = document.getElementById("dropzonePrompt");
  const fileSelectedState = document.getElementById("fileSelectedState");
  const selectedFileName = document.getElementById("selectedFileName");
  const selectedFileSize = document.getElementById("selectedFileSize");
  const clearFileBtn = document.getElementById("clearFileBtn");

  const docTypeSelect = document.getElementById("docTypeSelect");
  const validateBtn = document.getElementById("validateBtn");
  const btnSpinner = document.getElementById("btnSpinner");

  const emptyState = document.getElementById("emptyState");
  const resultsDashboard = document.getElementById("resultsDashboard");

  // Report DOM elements
  const verdictCard = document.getElementById("verdictCard");
  const verdictBadge = document.getElementById("verdictBadge");
  const reportDocMeta = document.getElementById("reportDocMeta");
  const verdictSummary = document.getElementById("verdictSummary");

  const mlScoreFill = document.getElementById("mlScoreFill");
  const mlScoreVal = document.getElementById("mlScoreVal");
  const wordCountVal = document.getElementById("wordCountVal");
  const wordCountSub = document.getElementById("wordCountSub");
  const orderVal = document.getElementById("orderVal");
  const ruleVal = document.getElementById("ruleVal");

  const checklistTableBody = document.getElementById("checklistTableBody");
  const remarksList = document.getElementById("remarksList");
  const extractedTextCode = document.getElementById("extractedTextCode");

  const tabBtns = document.querySelectorAll(".tab-btn");
  const tabContents = document.querySelectorAll(".tab-content");
  const themeToggle = document.getElementById("themeToggle");
  const themeIcon = themeToggle.querySelector(".theme-icon");
  const themeLabel = themeToggle.querySelector(".theme-label");

  let currentSelectedFile = null;

  applyTheme(localStorage.getItem("document-validation-theme") || "light");
  themeToggle.addEventListener("click", () => {
    const nextTheme = document.body.dataset.theme === "dark" ? "light" : "dark";
    applyTheme(nextTheme);
    localStorage.setItem("document-validation-theme", nextTheme);
  });

  function applyTheme(theme) {
    document.body.dataset.theme = theme;
    const darkMode = theme === "dark";
    themeIcon.textContent = darkMode ? "☀" : "☾";
    themeLabel.textContent = darkMode ? "Light mode" : "Dark mode";
    themeToggle.title = darkMode ? "Switch to light mode" : "Switch to dark mode";
    themeToggle.setAttribute("aria-label", themeToggle.title);
  }

  loadDocumentTypes();

  async function loadDocumentTypes() {
    try {
      const response = await fetch("/api/document-types");
      if (!response.ok) throw new Error("Could not load document templates.");
      const documentTypes = await response.json();
      docTypeSelect.innerHTML = "";
      documentTypes.forEach((documentType) => {
        const option = document.createElement("option");
        option.value = documentType.id;
        option.textContent = documentType.name;
        docTypeSelect.appendChild(option);
      });
      docTypeSelect.value = "frd";
    } catch (error) {
      docTypeSelect.innerHTML = '<option value="ssr">Safety Standard Report (SSR)</option>';
      console.error(error);
    }
  }

  // 1. File Upload & Drag-and-Drop Handlers
  browseBtn.addEventListener("click", () => fileInput.click());
  dropzone.addEventListener("click", (e) => {
    if (e.target !== clearFileBtn && !clearFileBtn.contains(e.target)) {
      if (!currentSelectedFile) fileInput.click();
    }
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      handleFileSelected(e.target.files[0]);
    }
  });

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  });

  dropzone.addEventListener("dragleave", () => {
    dropzone.classList.remove("dragover");
  });

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    if (e.dataTransfer.files.length > 0) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });

  clearFileBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    clearSelectedFile();
  });

  function handleFileSelected(file) {
    const ext = file.name.split(".").pop().toLowerCase();
    if (!["pdf", "docx", "txt"].includes(ext)) {
      alert("Unsupported file format! Please upload a .pdf, .docx, or .txt file.");
      return;
    }

    currentSelectedFile = file;
    selectedFileName.textContent = file.name;
    selectedFileSize.textContent = formatBytes(file.size);

    dropzonePrompt.classList.add("hidden");
    fileSelectedState.classList.remove("hidden");
    validateBtn.disabled = false;
  }

  function clearSelectedFile() {
    currentSelectedFile = null;
    fileInput.value = "";
    selectedFileName.textContent = "";
    selectedFileSize.textContent = "";

    dropzonePrompt.classList.remove("hidden");
    fileSelectedState.classList.add("hidden");
    validateBtn.disabled = true;
  }

  function formatBytes(bytes) {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  }

  // 2. Tab Switching logic
  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetTab = btn.getAttribute("data-tab");
      tabBtns.forEach((b) => b.classList.remove("active"));
      tabContents.forEach((c) => c.classList.remove("active"));

      btn.classList.add("active");
      document.getElementById(targetTab).classList.add("active");
    });
  });

  // 3. Document Validation API Request
  validateBtn.addEventListener("click", async () => {
    if (!currentSelectedFile) return;

    // Show loading state
    validateBtn.disabled = true;
    btnSpinner.classList.remove("hidden");

    const formData = new FormData();
    formData.append("file", currentSelectedFile);
    formData.append("doc_type", docTypeSelect.value);

    try {
      const response = await fetch("/api/validate", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "Validation request failed.");
      }

      const report = await response.json();
      renderValidationReport(report);
    } catch (err) {
      alert("Validation Error: " + err.message);
    } finally {
      validateBtn.disabled = false;
      btnSpinner.classList.add("hidden");
    }
  });

  // 4. Render Validation Results
  function renderValidationReport(report) {
    emptyState.classList.add("hidden");
    resultsDashboard.classList.remove("hidden");

    // Verdict Badge & Class
    verdictBadge.textContent = report.decision;
    verdictBadge.className = "verdict-badge";
    if (report.decision === "ACCEPTED") {
      verdictBadge.classList.add("accepted");
      verdictSummary.textContent = "Document complies with standard format guidelines and AI confidence criteria.";
    } else if (report.decision === "NEEDS MANUAL REVIEW") {
      verdictBadge.classList.add("review");
      verdictSummary.textContent = "Required sections exist, but low confidence or minor flags warrant manual review.";
    } else {
      verdictBadge.classList.add("rejected");
      verdictSummary.textContent = "Document missing mandatory sections/fields or failed formatting checks.";
    }

    reportDocMeta.textContent = `${report.doc_type} (${report.filename})`;

    // Metrics Bar
    const confidencePct = Math.round(report.ml_confidence * 100);
    mlScoreVal.textContent = `${confidencePct}%`;
    mlScoreFill.style.width = `${confidencePct}%`;

    wordCountVal.textContent = report.word_count;
    orderVal.textContent = report.order_ok ? "Correct" : "Shuffled";
    ruleVal.textContent = report.rule_passed ? "PASSED" : "FAILED";

    // Checklist Table
    checklistTableBody.innerHTML = "";

    // Sections
    report.sections.forEach((sec) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong>${sec.name}</strong> (Section)</td>
        <td><span class="tag-status ${sec.found ? "found" : "missing"}">${sec.found ? "✔ FOUND" : "✖ MISSING"}</span></td>
        <td>${sec.found ? `Position char ${sec.position}` : "Required section missing"}</td>
      `;
      checklistTableBody.appendChild(tr);
    });

    // Mandatory Fields
    Object.entries(report.mandatory_fields).forEach(([key, info]) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong>${capitalize(key)}</strong> (Field)</td>
        <td><span class="tag-status ${info.found ? "found" : "missing"}">${info.found ? "✔ FOUND" : "✖ MISSING"}</span></td>
        <td>${info.description}</td>
      `;
      checklistTableBody.appendChild(tr);
    });

    // Actionable Remarks List
    remarksList.innerHTML = "";
    if (report.reasons.length === 0) {
      remarksList.innerHTML = `<li>✔ No compliance issues detected. Format is valid.</li>`;
    } else {
      report.reasons.forEach((reason) => {
        const li = document.createElement("li");
        li.textContent = `• ${reason}`;
        remarksList.appendChild(li);
      });
    }

    // Extracted Text Preview
    extractedTextCode.textContent = report.extracted_text || "No text content.";
  }

  function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
  }
});
