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
  const resultCoach = document.getElementById("resultCoach");
  const resultCoachIcon = document.getElementById("resultCoachIcon");
  const resultCoachTitle = document.getElementById("resultCoachTitle");
  const resultCoachText = document.getElementById("resultCoachText");
  const railCoachTitle = document.getElementById("railCoachTitle");
  const railCoachText = document.getElementById("railCoachText");
  const coachForm = document.getElementById("coachForm");
  const coachQuestion = document.getElementById("coachQuestion");
  const coachAnswer = document.getElementById("coachAnswer");

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
  const templateHelperTitle = document.getElementById("templateHelperTitle");
  const templateHelperSummary = document.getElementById("templateHelperSummary");
  const templateSectionCount = document.getElementById("templateSectionCount");
  const templateSectionsList = document.getElementById("templateSectionsList");
  const templateFieldsList = document.getElementById("templateFieldsList");
  const templateRequirements = document.getElementById("templateRequirements");
  const templateRequirementsPreview = document.getElementById("templateRequirementsPreview");
  const copyTemplateBtn = document.getElementById("copyTemplateBtn");
  const copyFeedback = document.getElementById("copyFeedback");
  const exportReportBtn = document.getElementById("exportReportBtn");

  let currentSelectedFile = null;
  let currentTemplate = "";
  let latestReport = null;

  exportReportBtn.addEventListener("click", exportReport);

  applyTheme(localStorage.getItem("document-validation-theme") || "light");
  themeToggle.addEventListener("click", () => {
    const nextTheme = document.body.dataset.theme === "dark" ? "light" : "dark";
    applyTheme(nextTheme);
    localStorage.setItem("document-validation-theme", nextTheme);
  });

  function applyTheme(theme) {
    document.body.dataset.theme = theme;
    document.documentElement.dataset.theme = theme;
    const darkMode = theme === "dark";
    document.documentElement.style.colorScheme = darkMode ? "dark" : "light";
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
      await loadTemplateHelper();
    } catch (error) {
      docTypeSelect.innerHTML = '<option value="ssr">Safety Standard Report (SSR)</option>';
      console.error(error);
    }
  }

  docTypeSelect.addEventListener("change", loadTemplateHelper);

  coachForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const question = coachQuestion.value.trim();
    coachAnswer.textContent = buildCoachAnswer(question, latestReport);
    coachAnswer.classList.remove("hidden");
    coachQuestion.select();
  });

  async function loadTemplateHelper() {
    const selectedOption = docTypeSelect.options[docTypeSelect.selectedIndex];
    if (!selectedOption || !docTypeSelect.value) return;

    templateHelperTitle.textContent = "Prepare your document";
    templateHelperSummary.innerHTML = "<strong>Tip:</strong> Use clear numbered headings and keep them in the same order as the selected template.";
    templateSectionCount.textContent = "Loading...";
    copyTemplateBtn.disabled = true;

    try {
      const response = await fetchWithTimeout(`/api/templates/${encodeURIComponent(docTypeSelect.value)}`);
      if (!response.ok) throw new Error("Template requirements could not be loaded.");
      const template = await response.json();
      currentTemplate = template.template;
      templateSectionCount.textContent = `${template.required_sections.length} sections`;
      templateHelperSummary.innerHTML = "<strong>Tip:</strong> Check the required sections below before uploading your document.";
      templateRequirementsPreview.textContent = `${template.required_sections.slice(0, 3).join(" • ")}${template.required_sections.length > 3 ? " • ..." : ""}`;
      templateRequirements.classList.remove("hidden");
      copyTemplateBtn.disabled = false;
    } catch (error) {
      templateHelperSummary.innerHTML = "<strong>Tip:</strong> Upload a PDF, DOCX, or TXT file to receive specific document suggestions.";
      templateSectionCount.textContent = shortDocumentName(selectedOption.textContent);
      templateRequirements.classList.add("hidden");
      console.error(error);
    }
  }

  async function fetchWithTimeout(url) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000);
    try {
      return await fetch(url, { signal: controller.signal });
    } finally {
      clearTimeout(timeout);
    }
  }

  function renderTemplateList(list, items, emptyMessage) {
    list.innerHTML = "";
    const visibleItems = items.slice(0, 4);
    visibleItems.forEach((item) => {
      const listItem = document.createElement("li");
      listItem.textContent = item.replaceAll("_", " ");
      list.appendChild(listItem);
    });
    if (items.length > visibleItems.length) {
      const moreItem = document.createElement("li");
      moreItem.className = "template-more";
      moreItem.textContent = `+ ${items.length - visibleItems.length} more`;
      list.appendChild(moreItem);
    } else if (visibleItems.length === 0) {
      const emptyItem = document.createElement("li");
      emptyItem.className = "template-more";
      emptyItem.textContent = emptyMessage;
      list.appendChild(emptyItem);
    }
  }

  function shortDocumentName(name) {
    return name.replace(/\s*\([^)]*\)/, "").replace("Document", "Doc");
  }

  copyTemplateBtn.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(currentTemplate);
      copyFeedback.textContent = "Starter template copied";
      setTimeout(() => { copyFeedback.textContent = ""; }, 2200);
    } catch (error) {
      copyFeedback.textContent = "Copy failed. Open the template endpoint instead.";
    }
  });

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
    latestReport = report;
    exportReportBtn.disabled = false;
    exportReportBtn.title = "Download the validation report";
    emptyState.classList.add("hidden");
    resultsDashboard.classList.remove("hidden");

    // Verdict Badge & Class
    verdictBadge.textContent = report.decision;
    verdictBadge.className = "verdict-badge";
    if (report.decision === "ACCEPTED") {
      verdictBadge.classList.add("accepted");
      verdictSummary.textContent = "Your document matches the selected format and is ready for the next step.";
      showResultCoach("accepted", "Great work!", "Your document is in good shape. You can submit it, share it, or keep a copy of this validation report.", "✓");
      showRailCoach("Ready to submit", "Your document matches the selected template. Keep this report with your final document.");
    } else if (report.decision === "NEEDS MANUAL REVIEW") {
      verdictBadge.classList.add("review");
      verdictSummary.textContent = "The structure looks close, but a quick human review is recommended before submission.";
      showResultCoach("review", "Almost there", "Review the highlighted details below, then upload the updated file if anything needs correcting.", "!");
      showRailCoach("Review before sending", "The structure is close. Check the highlighted items and confirm the document with a reviewer.");
    } else {
      verdictBadge.classList.add("rejected");
      verdictSummary.textContent = "A few format checks need attention before this document can pass.";
      showResultCoach("rejected", "A little tune-up will help", "Check the missing items below, add the required headings or fields, and upload the revised file again.", "↻");
      showRailCoach("A few items need attention", "Start with the missing items below. Add them to your document, then run validation again.");
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
    coachAnswer.textContent = "Your report is ready. Ask about missing sections, required fields, score, or next steps.";
    coachAnswer.classList.remove("hidden");
  }

  function exportReport() {
    if (!latestReport) return;

    const report = latestReport;
    const confidence = Math.round(report.ml_confidence * 100);
    const sections = report.sections
      .map((section) => `- ${section.name}: ${section.found ? `FOUND (position ${section.position})` : "MISSING"}`)
      .join("\n");
    const fields = Object.entries(report.mandatory_fields)
      .map(([name, info]) => `- ${capitalize(name.replaceAll("_", " "))}: ${info.found ? "FOUND" : "MISSING"} - ${info.description}`)
      .join("\n");
    const reasons = report.reasons.length
      ? report.reasons.map((reason) => `- ${reason}`).join("\n")
      : "- No compliance issues detected.";
    const content = [
      "DOCUMENT VALIDATION REPORT",
      "===========================",
      `Document: ${report.filename}`,
      `Format: ${report.doc_type}`,
      `Decision: ${report.decision}`,
      `AI confidence: ${confidence}%`,
      `Word count: ${report.word_count}`,
      `Section order: ${report.order_ok ? "Correct" : "Needs review"}`,
      `Rule check: ${report.rule_passed ? "PASSED" : "FAILED"}`,
      "",
      "REQUIRED SECTIONS",
      "------------------",
      sections,
      "",
      "MANDATORY FIELDS",
      "----------------",
      fields,
      "",
      "REASONS AND NEXT STEPS",
      "----------------------",
      reasons,
      "",
      "Generated by Document Validation AI",
    ].join("\n");

    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const downloadUrl = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = downloadUrl;
    link.download = `${shortDocumentName(report.filename.replace(/\.[^/.]+$/, ""))}-validation-report.txt`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(downloadUrl);
  }

  function buildCoachAnswer(question, report) {
    if (!question) return "Type a question about the document and I will point you to the most useful next step.";
    if (!report) return "Upload and validate a document first. Then I can explain its missing sections, fields, score, and next steps.";

    const normalizedQuestion = question.toLowerCase();
    const missingSections = report.sections.filter((section) => !section.found).map((section) => section.name);
    const missingFields = Object.entries(report.mandatory_fields)
      .filter(([, info]) => !info.found)
      .map(([name]) => capitalize(name.replaceAll("_", " ")));

    if (normalizedQuestion.includes("missing") || normalizedQuestion.includes("fix") || normalizedQuestion.includes("improve")) {
      const missing = [...missingSections, ...missingFields];
      return missing.length ? `Start with: ${missing.join(", ")}. Add these items, then validate the revised document again.` : "No required sections or fields are missing. Review the remarks and keep the document in the expected order.";
    }
    if (normalizedQuestion.includes("score") || normalizedQuestion.includes("confidence") || normalizedQuestion.includes("pass")) {
      return `The document is ${report.decision.toLowerCase()} with ${Math.round(report.ml_confidence * 100)}% AI confidence and ${report.rule_passed ? "a passing" : "a failing"} rule check.`;
    }
    if (normalizedQuestion.includes("section") || normalizedQuestion.includes("heading") || normalizedQuestion.includes("order")) {
      return `${missingSections.length ? `Missing sections: ${missingSections.join(", ")}. ` : "All required sections were found. "}${report.order_ok ? "Their order is correct." : "Their order needs review."}`;
    }
    if (normalizedQuestion.includes("field") || normalizedQuestion.includes("date") || normalizedQuestion.includes("signature")) {
      return missingFields.length ? `These mandatory fields need attention: ${missingFields.join(", ")}.` : "All mandatory fields were found in the document.";
    }
    return report.reasons.length ? `The most important next step is to address: ${report.reasons[0]}` : "The document passed the main checks. You can export the report or submit the document.";
  }

  function showResultCoach(type, title, text, icon) {
    resultCoach.className = `result-coach ${type}`;
    resultCoachIcon.textContent = icon;
    resultCoachTitle.textContent = title;
    resultCoachText.textContent = text;
  }

  function showRailCoach(title, text) {
    railCoachTitle.textContent = title;
    railCoachText.textContent = text;
  }

  function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
  }
});
