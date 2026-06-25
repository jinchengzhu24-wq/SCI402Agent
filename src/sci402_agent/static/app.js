const state = {
  busy: false,
  lastAnalysis: null,
};

const sampleDraft = [
  "1. Scientific Background & Problem Definition",
  "My project studies temperature prediction in lithium-ion batteries.",
  "The scientific problem is that overheating can reduce battery safety and lifetime.",
  "The research gap is the lack of fast prediction methods compared with computationally expensive traditional thermal simulations.",
  "Experimental cycling datasets provide current, voltage, ambient temperature, and state of charge measurements.",
  "2. AI / ML Problem Formulation",
  "I will use a regression model with input features such as current, voltage, ambient temperature, and charge rate.",
  "The output target is battery surface temperature.",
  "Random Forest Regression is suitable because it can model nonlinear relationships in battery operating data.",
  "3. Methodology and Workflow Design",
  "Workflow diagram: Data Collection -> Data Cleaning -> Feature Engineering -> Model Training -> Validation -> Evaluation.",
  "I have not fully planned the preprocessing, validation metrics, reproducibility, or risk mitigation yet.",
].join(" ");

const elements = {
  studentText: document.querySelector("#studentText"),
  analyzeButton: document.querySelector("#analyzeButton"),
  feedbackButton: document.querySelector("#feedbackButton"),
  clearButton: document.querySelector("#clearButton"),
  sampleButton: document.querySelector("#sampleButton"),
  serviceStatus: document.querySelector("#serviceStatus"),
  modeValue: document.querySelector("#modeValue"),
  wordCount: document.querySelector("#wordCount"),
  coverageValue: document.querySelector("#coverageValue"),
  scoreValue: document.querySelector("#scoreValue"),
  coverageFill: document.querySelector("#coverageFill"),
  structureBox: document.querySelector("#structureBox"),
  criteriaList: document.querySelector("#criteriaList"),
  feedbackBox: document.querySelector("#feedbackBox"),
};

async function postJson(path, body) {
  const response = await fetch(path, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
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
  elements.scoreValue.textContent =
    typeof analysis.estimated_total === "number"
      ? `${analysis.estimated_total}/25`
      : "0/25";

  const coverage = Math.round(analysis.coverage_ratio * 100);
  elements.coverageValue.textContent = `${coverage}%`;
  elements.coverageFill.style.width = `${coverage}%`;

  renderStructure(analysis);
  if (Array.isArray(analysis.criterion_scores)) {
    renderCriterionScores(analysis);
    return;
  }

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

function renderStructure(analysis) {
  const structure = analysis.structure_check;
  if (!structure) {
    elements.structureBox.innerHTML =
      '<p class="empty-state">Run analysis to see structure checks.</p>';
    return;
  }

  const checks = [
    {
      label: `At least ${structure.required_word_count} words`,
      ok: structure.meets_word_requirement,
    },
    {
      label: "Required sections",
      ok: structure.missing_sections.length === 0 && structure.sections_in_order,
    },
    {
      label: "Workflow diagram",
      ok: structure.has_workflow_diagram,
    },
  ];
  const warningHtml = structure.warnings.length
    ? `<ul class="warning-list">${structure.warnings
        .map((warning) => `<li>${escapeHtml(warning)}</li>`)
        .join("")}</ul>`
    : '<p class="structure-ok">No structure warnings detected.</p>';

  elements.structureBox.innerHTML = `
    <div class="grade-band">${escapeHtml(analysis.grade_band || "No grade band")}</div>
    <div class="structure-checks">
      ${checks
        .map(
          (check) => `
            <span class="check-pill ${check.ok ? "is-ok" : "is-warning"}">
              ${check.ok ? "Pass" : "Check"}: ${escapeHtml(check.label)}
            </span>
          `
        )
        .join("")}
    </div>
    ${warningHtml}
  `;
}

function renderCriterionScores(analysis) {
  elements.criteriaList.innerHTML = analysis.criterion_scores
    .map((criterion) => {
      const scoreClass =
        criterion.score_0_to_5 >= 5
          ? "is-excellent"
          : criterion.score_0_to_5 >= 3
            ? "is-satisfactory"
            : "is-weak";
      const evidence = criterion.evidence.length
        ? criterion.evidence
        : ["No direct evidence found."];
      const missing = criterion.missing_items.length
        ? criterion.missing_items
        : ["No major missing item detected."];
      const blockers = criterion.blocking_flags.length
        ? `<ul class="blocker-list">${criterion.blocking_flags
            .map((flag) => `<li>${escapeHtml(flag)}</li>`)
            .join("")}</ul>`
        : "";

      return `
        <article class="criterion-card">
          <div class="criterion-card-head">
            <div>
              <span class="criterion-title">${escapeHtml(criterion.title)}</span>
              <span class="criterion-level">${escapeHtml(criterion.level)}</span>
            </div>
            <span class="score-badge ${scoreClass}">${criterion.score_0_to_5}/5</span>
          </div>
          <div class="criterion-section">
            <span class="mini-label">Evidence</span>
            <ul>
              ${evidence.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
            </ul>
          </div>
          <div class="criterion-section">
            <span class="mini-label">Missing checklist</span>
            <ul>
              ${missing.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
            </ul>
          </div>
          ${blockers}
        </article>
      `;
    })
    .join("");
}

function renderFeedback(text) {
  elements.feedbackBox.innerHTML = renderMarkdown(
    text || "No feedback content returned."
  );
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
  elements.scoreValue.textContent = "0/25";
  elements.coverageFill.style.width = "0%";
  elements.structureBox.innerHTML =
    '<p class="empty-state">Run analysis to see structure checks.</p>';
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

function escapeAttribute(value) {
  return escapeHtml(value).replaceAll("`", "&#096;");
}

function sanitizeUrl(value) {
  const url = String(value).replaceAll("&amp;", "&").trim();
  if (/^(https?:|mailto:)/i.test(url)) {
    return url;
  }
  return "";
}

function renderInlineMarkdown(value) {
  const codeSpans = [];
  let html = escapeHtml(value).replace(/`([^`]+)`/g, (_match, code) => {
    const index = codeSpans.length;
    codeSpans.push(`<code>${code}</code>`);
    return `\u0000CODE${index}\u0000`;
  });

  html = html
    .replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, (_match, label, url) => {
      const safeUrl = sanitizeUrl(url);
      if (!safeUrl) {
        return `${label} (${url})`;
      }
      return `<a href="${escapeAttribute(safeUrl)}" target="_blank" rel="noopener noreferrer">${label}</a>`;
    })
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/(^|[\s(])\*([^*\n]+)\*/g, "$1<em>$2</em>");

  codeSpans.forEach((codeHtml, index) => {
    html = html.replaceAll(`\u0000CODE${index}\u0000`, codeHtml);
  });

  return html;
}

function renderMarkdown(markdown) {
  const lines = String(markdown).replace(/\r\n?/g, "\n").split("\n");
  const blocks = [];
  let paragraphLines = [];
  let listItems = [];
  let isOrderedList = false;

  function flushParagraph() {
    if (!paragraphLines.length) {
      return;
    }
    blocks.push(`<p>${renderInlineMarkdown(paragraphLines.join(" "))}</p>`);
    paragraphLines = [];
  }

  function flushList() {
    if (!listItems.length) {
      return;
    }
    const tag = isOrderedList ? "ol" : "ul";
    blocks.push(`<${tag}>${listItems.join("")}</${tag}>`);
    listItems = [];
  }

  lines.forEach((line) => {
    const trimmed = line.trim();
    if (!trimmed) {
      flushParagraph();
      flushList();
      return;
    }

    const heading = trimmed.match(/^(#{1,3})\s+(.+)$/);
    if (heading) {
      flushParagraph();
      flushList();
      const level = heading[1].length + 2;
      blocks.push(`<h${level}>${renderInlineMarkdown(heading[2])}</h${level}>`);
      return;
    }

    const unorderedItem = trimmed.match(/^[-*]\s+(.+)$/);
    const orderedItem = trimmed.match(/^\d+[.)]\s+(.+)$/);
    if (unorderedItem || orderedItem) {
      flushParagraph();
      const nextIsOrdered = Boolean(orderedItem);
      if (listItems.length && isOrderedList !== nextIsOrdered) {
        flushList();
      }
      isOrderedList = nextIsOrdered;
      listItems.push(
        `<li>${renderInlineMarkdown(
          unorderedItem ? unorderedItem[1] : orderedItem[1]
        )}</li>`
      );
      return;
    }

    flushList();
    paragraphLines.push(trimmed);
  });

  flushParagraph();
  flushList();

  return blocks.join("");
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
