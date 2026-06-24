const state = {
  busy: false,
  lastAnalysis: null,
};

const sampleDraft = [
  "My project studies temperature prediction in lithium-ion batteries.",
  "The scientific problem is that overheating can reduce battery safety and lifetime.",
  "I will use a regression model with input features such as current, voltage, ambient temperature, and charge rate.",
  "The output target is battery surface temperature.",
  "I have not fully planned the preprocessing, workflow diagram, validation metrics, or risk mitigation yet.",
].join(" ");

const elements = {
  apiKeyInput: document.querySelector("#apiKeyInput"),
  studentText: document.querySelector("#studentText"),
  analyzeButton: document.querySelector("#analyzeButton"),
  feedbackButton: document.querySelector("#feedbackButton"),
  clearButton: document.querySelector("#clearButton"),
  sampleButton: document.querySelector("#sampleButton"),
  serviceStatus: document.querySelector("#serviceStatus"),
  modeValue: document.querySelector("#modeValue"),
  wordCount: document.querySelector("#wordCount"),
  coverageValue: document.querySelector("#coverageValue"),
  coverageFill: document.querySelector("#coverageFill"),
  criteriaList: document.querySelector("#criteriaList"),
  feedbackBox: document.querySelector("#feedbackBox"),
};

function apiHeaders() {
  const headers = {
    "Content-Type": "application/json",
  };
  const apiKey = elements.apiKeyInput.value.trim();
  if (apiKey) {
    headers["X-API-Key"] = apiKey;
  }
  return headers;
}

async function postJson(path, body) {
  const response = await fetch(path, {
    method: "POST",
    headers: apiHeaders(),
    body: JSON.stringify(body),
  });
  const text = await response.text();
  const data = text ? JSON.parse(text) : {};
  if (!response.ok) {
    const message = data.detail || `Request failed with status ${response.status}`;
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }
  return data;
}

function setBusy(isBusy, label = "Ready") {
  state.busy = isBusy;
  elements.analyzeButton.disabled = isBusy;
  elements.feedbackButton.disabled = isBusy;
  elements.sampleButton.disabled = isBusy;
  elements.clearButton.disabled = isBusy;
  elements.serviceStatus.textContent = label;
  elements.serviceStatus.classList.toggle("is-busy", isBusy);
  elements.serviceStatus.classList.remove("is-error");
}

function setErrorStatus(message) {
  elements.serviceStatus.textContent = message;
  elements.serviceStatus.classList.remove("is-busy");
  elements.serviceStatus.classList.add("is-error");
}

function renderAnalysis(analysis, mode = "Not selected") {
  state.lastAnalysis = analysis;
  elements.modeValue.textContent = mode;
  elements.wordCount.textContent = String(analysis.word_count);

  const coverage = Math.round(analysis.coverage_ratio * 100);
  elements.coverageValue.textContent = `${coverage}%`;
  elements.coverageFill.style.width = `${coverage}%`;

  elements.criteriaList.innerHTML = analysis.criterion_coverage
    .map((criterion) => {
      const matched = criterion.is_matched;
      const badgeClass = matched ? "is-matched" : "is-missing";
      const badgeText = matched ? "Matched" : "Missing";
      const detail = matched
        ? `Matched keywords: ${criterion.matched_keywords.join(", ")}`
        : criterion.missing_feedback;
      return `
        <article class="criterion-row">
          <div>
            <span class="criterion-title">${escapeHtml(criterion.title)}</span>
            <p class="criterion-detail">${escapeHtml(detail)}</p>
          </div>
          <span class="badge ${badgeClass}">${badgeText}</span>
        </article>
      `;
    })
    .join("");
}

function renderFeedback(text) {
  elements.feedbackBox.textContent = text || "No feedback content returned.";
}

function requestBody() {
  return {
    student_text: elements.studentText.value,
  };
}

async function runAnalyze({ silent = false } = {}) {
  if (!silent) {
    setBusy(true, "Analyzing");
  }
  try {
    const analysis = await postJson("/analyze", requestBody());
    renderAnalysis(analysis);
    if (!silent) {
      renderFeedback("Analysis complete. Generate feedback when you are ready.");
      setBusy(false, "Ready");
    }
    return analysis;
  } catch (error) {
    if (!silent) {
      setBusy(false, "Ready");
      setErrorStatus("Error");
      renderFeedback(error.message);
    }
    throw error;
  }
}

async function runFeedback() {
  setBusy(true, "Generating");
  try {
    const payload = await postJson("/feedback", requestBody());
    renderAnalysis(payload.analysis, payload.mode);
    renderFeedback(payload.feedback);
    setBusy(false, "Ready");
  } catch (error) {
    try {
      const analysis = await runAnalyze({ silent: true });
      renderAnalysis(analysis);
    } catch (_analysisError) {
      state.lastAnalysis = null;
    }
    setBusy(false, "Ready");
    setErrorStatus("LLM issue");
    if (error.status === 503) {
      renderFeedback(
        `${error.message}\n\nRule analysis is still available. Set SCI402_LLM_API_KEY before generating AI feedback.`
      );
      return;
    }
    renderFeedback(error.message);
  }
}

function clearWorkspace() {
  elements.studentText.value = "";
  state.lastAnalysis = null;
  elements.modeValue.textContent = "Not selected";
  elements.wordCount.textContent = "0";
  elements.coverageValue.textContent = "0%";
  elements.coverageFill.style.width = "0%";
  elements.criteriaList.innerHTML =
    '<p class="empty-state">Run analysis to see the five SCI402 rubric areas.</p>';
  renderFeedback("Generate feedback to see the tutor response.");
  elements.serviceStatus.textContent = "Ready";
  elements.serviceStatus.classList.remove("is-error", "is-busy");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

elements.analyzeButton.addEventListener("click", () => {
  runAnalyze();
});

elements.feedbackButton.addEventListener("click", () => {
  runFeedback();
});

elements.clearButton.addEventListener("click", () => {
  clearWorkspace();
  elements.studentText.focus();
});

elements.sampleButton.addEventListener("click", () => {
  elements.studentText.value = sampleDraft;
  elements.studentText.focus();
});
