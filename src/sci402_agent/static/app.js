const state = {
  busy: false,
  lastAnalysis: null,
  lastAIReview: null,
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
  scoreButton: document.querySelector("#scoreButton"),
  feedbackButton: document.querySelector("#feedbackButton"),
  clearButton: document.querySelector("#clearButton"),
  sampleButton: document.querySelector("#sampleButton"),
  uploadButton: document.querySelector("#uploadButton"),
  draftFileInput: document.querySelector("#draftFileInput"),
  helpButton: document.querySelector("#helpButton"),
  helpModal: document.querySelector("#helpModal"),
  helpCloseButton: document.querySelector("#helpCloseButton"),
  serviceStatus: document.querySelector("#serviceStatus"),
  feedbackStyleValue: document.querySelector("#feedbackStyleValue"),
  scoreSourceValue: document.querySelector("#scoreSourceValue"),
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

async function postFormData(path, formData) {
  const response = await fetch(path, {
    method: "POST",
    body: formData,
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
  elements.scoreButton.disabled = isBusy;
  elements.feedbackButton.disabled = isBusy;
  elements.sampleButton.disabled = isBusy;
  elements.uploadButton.disabled = isBusy;
  elements.draftFileInput.disabled = isBusy;
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

function openHelpModal() {
  elements.helpModal.hidden = false;
  document.body.classList.add("modal-open");
  elements.helpCloseButton.focus();
}

function closeHelpModal() {
  if (elements.helpModal.hidden) {
    return;
  }
  elements.helpModal.hidden = true;
  document.body.classList.remove("modal-open");
  elements.helpButton.focus();
}

function formatFeedbackStyle(mode) {
  const labels = {
    MODE_1_SUPPORTIVE_INQUIRY: "Supportive",
    MODE_2_STRUCTURED_GUIDANCE: "Guidance",
    MODE_3_EXPERT_CHALLENGE: "Expert",
  };
  return labels[mode] || mode || "None";
}

function renderAnalysis(analysis, { feedbackStyle = null, scoreSource = "Local precheck" } = {}) {
  state.lastAnalysis = analysis;
  const nextFeedbackStyle =
    feedbackStyle === null ? analysis.suggested_feedback_mode : feedbackStyle;
  if (nextFeedbackStyle) {
    elements.feedbackStyleValue.textContent = formatFeedbackStyle(nextFeedbackStyle);
  }
  elements.scoreSourceValue.textContent = scoreSource;
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
  const scores = analysis.validated_scores || analysis.criterion_scores || [];
  const usesAIJudgement =
    Array.isArray(analysis.validated_scores) &&
    scores.some((criterion) => criterion.source === "llm");
  const localScoresById = Object.fromEntries(
    (analysis.criterion_scores || []).map((criterion) => [criterion.id, criterion])
  );
  const structureWarnings = analysis.structure_check?.warnings || [];
  elements.criteriaList.innerHTML = scores
    .map((criterion, index) => {
      const localCriterion = localScoresById[criterion.id] || criterion;
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
      const blockers = criterion.blocking_flags?.length
        ? `<ul class="blocker-list">${criterion.blocking_flags
            .map((flag) => `<li>${escapeHtml(flag)}</li>`)
            .join("")}</ul>`
        : "";
      const rationale = criterion.rationale
        ? `
          <div class="criterion-section">
            <span class="mini-label">AI rationale</span>
            <p class="criterion-detail">${escapeHtml(criterion.rationale)}</p>
          </div>
        `
        : "";
      const semanticDiagnosis = criterion.semantic_diagnosis
        ? `
          <div class="criterion-section">
            <span class="mini-label">AI semantic judgement</span>
            <p class="criterion-detail">${escapeHtml(criterion.semantic_diagnosis)}</p>
          </div>
        `
        : "";
      const qualityConcerns = criterion.quality_concerns?.length
        ? `
          <div class="criterion-section">
            <span class="mini-label">Quality concerns</span>
            ${renderList(criterion.quality_concerns)}
          </div>
        `
        : "";
      const scientificReasoningConcerns = criterion.scientific_reasoning_concerns?.length
        ? `
          <div class="criterion-section">
            <span class="mini-label">Scientific reasoning concerns</span>
            ${renderList(criterion.scientific_reasoning_concerns)}
          </div>
        `
        : "";
      const blindSpots = criterion.local_precheck_blind_spots?.length
        ? `
          <div class="criterion-section">
            <span class="mini-label">Local precheck blind spots</span>
            ${renderList(criterion.local_precheck_blind_spots)}
          </div>
        `
        : "";
      const scoreDifference = criterion.why_score_differs_from_local
        ? `
          <div class="criterion-section">
            <span class="mini-label">Why AI score differs</span>
            <p class="criterion-detail">${escapeHtml(criterion.why_score_differs_from_local)}</p>
          </div>
        `
        : "";
      const revisionFocus = criterion.revision_focus
        ? `
          <div class="criterion-section">
            <span class="mini-label">Revision focus</span>
            <p class="criterion-detail">${escapeHtml(criterion.revision_focus)}</p>
          </div>
        `
        : "";
      const confidence = criterion.confidence
        ? `<span class="criterion-level">Confidence: ${escapeHtml(criterion.confidence)}</span>`
        : `<span class="criterion-level">${escapeHtml(criterion.level)}</span>`;
      const scoreDelta =
        usesAIJudgement && typeof criterion.local_score_0_to_5 === "number"
          ? `<span class="score-delta">Local ${criterion.local_score_0_to_5}/5 -> AI ${criterion.score_0_to_5}/5</span>`
          : '<span class="score-delta">Local precheck</span>';
      const invalidEvidence = criterion.invalid_evidence?.length
        ? `
          <div class="criterion-section">
            <span class="mini-label">Invalid evidence</span>
            ${renderList(criterion.invalid_evidence)}
          </div>
        `
        : "";
      const adjustments = criterion.adjustments?.length
        ? `
          <div class="criterion-section">
            <span class="mini-label">Rule guardrails</span>
            ${renderList(criterion.adjustments)}
          </div>
        `
        : "";
      const localPrecheck = usesAIJudgement
        ? `
          <div class="review-block">
            <span class="mini-label">Local precheck</span>
            <p class="criterion-detail">
              Checklist estimate: ${localCriterion.score_0_to_5}/5.
              Matched: ${escapeHtml(formatListText(localCriterion.matched_items, "none"))}.
              Local gaps: ${escapeHtml(formatListText(localCriterion.missing_items, "none"))}.
            </p>
            <div class="criterion-section">
              <span class="mini-label">Local candidate evidence</span>
              ${renderList(localCriterion.evidence, "No local evidence found.")}
            </div>
            <div class="criterion-section">
              <span class="mini-label">Cap flags</span>
              ${renderList(localCriterion.blocking_flags, "No hard cap triggered.")}
            </div>
            <div class="criterion-section">
              <span class="mini-label">Structure warnings</span>
              ${renderList(structureWarnings, "No structure warning detected.")}
            </div>
          </div>
        `
        : "";
      const aiSecondReview = usesAIJudgement
        ? `
          <div class="review-block">
            <span class="mini-label">AI second review</span>
            ${rationale}
            ${semanticDiagnosis}
            ${qualityConcerns}
            ${scientificReasoningConcerns}
            ${blindSpots}
            ${scoreDifference}
            ${revisionFocus}
            <div class="criterion-section">
              <span class="mini-label">AI evidence</span>
              ${renderList(evidence)}
            </div>
            <div class="criterion-section">
              <span class="mini-label">AI missing items</span>
              ${renderList(missing)}
            </div>
          </div>
        `
        : "";
      const localOnlyDetails = usesAIJudgement
        ? ""
        : `
            ${rationale}
            ${semanticDiagnosis}
            ${qualityConcerns}
            ${revisionFocus}
            <div class="criterion-section">
              <span class="mini-label">Candidate evidence</span>
              ${renderList(evidence)}
            </div>
            <div class="criterion-section">
              <span class="mini-label">Local checklist gaps</span>
              ${renderList(missing)}
            </div>
          `;

      return `
        <article class="criterion-card">
          <button
            class="criterion-card-head"
            type="button"
            aria-expanded="false"
            aria-controls="criterionBody${index}"
          >
            <div>
              <span class="criterion-title">${escapeHtml(criterion.title)}</span>
              ${usesAIJudgement ? scoreDelta : ""}
            </div>
            <span class="criterion-card-actions">
              <span class="score-badge ${scoreClass}">${criterion.score_0_to_5}/5</span>
              <span class="toggle-label">Details</span>
            </span>
          </button>
          <div class="criterion-card-body" id="criterionBody${index}" hidden>
            ${confidence}
            ${usesAIJudgement ? "" : scoreDelta}
            ${localPrecheck}
            ${aiSecondReview}
            ${localOnlyDetails}
            ${invalidEvidence}
            ${adjustments}
            ${blockers}
          </div>
        </article>
      `;
    })
    .join("");
}

function renderList(items, fallback = "No direct evidence found.") {
  const safeItems = Array.isArray(items) && items.length ? items : [fallback];
  return `<ul>${safeItems.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;
}

function formatListText(items, fallback = "none") {
  if (!Array.isArray(items) || !items.length) {
    return fallback;
  }
  return items.join("; ");
}

function toggleCriterionCard(button) {
  const bodyId = button.getAttribute("aria-controls");
  const body = bodyId ? document.getElementById(bodyId) : null;
  if (!body) {
    return;
  }

  const willExpand = body.hidden;
  body.hidden = !willExpand;
  button.setAttribute("aria-expanded", String(willExpand));
  const label = button.querySelector(".toggle-label");
  if (label) {
    label.textContent = willExpand ? "Hide" : "Details";
  }
}

function renderFeedback(text) {
  elements.feedbackBox.innerHTML = renderMarkdown(
    text || "No feedback content returned."
  );
}

function resetAnalysisDisplay() {
  state.lastAnalysis = null;
  state.lastAIReview = null;
  elements.feedbackStyleValue.textContent = "None";
  elements.scoreSourceValue.textContent = "Not scored";
  elements.wordCount.textContent = "0";
  elements.coverageValue.textContent = "0%";
  elements.scoreValue.textContent = "0/25";
  elements.coverageFill.style.width = "0%";
  elements.structureBox.innerHTML =
    '<p class="empty-state">Run analysis to see structure checks.</p>';
  elements.criteriaList.innerHTML =
    '<p class="empty-state">Run analysis to see the five SCI402 rubric areas.</p>';
}

function requestBody({ includeAIReview = false } = {}) {
  const body = {
    student_text: elements.studentText.value,
  };
  if (includeAIReview && Array.isArray(state.lastAIReview)) {
    body.ai_review = state.lastAIReview;
  }
  return body;
}

async function runAnalyze({ silent = false } = {}) {
  state.lastAIReview = null;
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
    const payload = await postJson("/feedback", requestBody({ includeAIReview: true }));
    const analysis = payload.analysis;
    if (Array.isArray(state.lastAIReview)) {
      analysis.validated_scores = state.lastAIReview;
      analysis.estimated_total = state.lastAIReview.reduce(
        (total, criterion) => total + criterion.score_0_to_5,
        0
      );
    }
    renderAnalysis(analysis, {
      feedbackStyle: payload.mode,
      scoreSource: state.lastAIReview ? "AI review" : "Local",
    });
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

async function runUpload(file) {
  if (!file) {
    return;
  }

  const formData = new FormData();
  formData.append("file", file);
  setBusy(true, "Uploading");
  try {
    const payload = await postFormData("/upload-draft", formData);
    elements.studentText.value = payload.extracted_text;
    resetAnalysisDisplay();
    const warningText = payload.warnings.length
      ? `\n\nWarnings:\n${payload.warnings
          .map((warning) => `- ${warning}`)
          .join("\n")}`
      : "";
    renderFeedback(
      `Uploaded \`${payload.filename}\` and extracted ${payload.character_count} characters. Review or edit the draft, then run Analyze or AI score.${warningText}`
    );
    setBusy(false, "Ready");
    elements.studentText.focus();
  } catch (error) {
    setBusy(false, "Ready");
    setErrorStatus("Upload issue");
    renderFeedback(error.message);
  } finally {
    elements.draftFileInput.value = "";
  }
}

async function runLLMScore() {
  setBusy(true, "AI scoring");
  try {
    const payload = await postJson("/llm-score", requestBody());
    const analysis = payload.local_analysis;
    analysis.validated_scores = payload.validated_scores;
    state.lastAnalysis = analysis;
    state.lastAIReview = payload.source === "llm" ? payload.validated_scores : null;
    if (analysis.suggested_feedback_mode) {
      elements.feedbackStyleValue.textContent = formatFeedbackStyle(
        analysis.suggested_feedback_mode
      );
    }
    elements.scoreSourceValue.textContent =
      payload.source === "llm" ? "AI review" : "Fallback";
    elements.wordCount.textContent = String(analysis.word_count);
    elements.scoreValue.textContent = `${payload.final_total}/25`;
    const coverage = Math.round(analysis.coverage_ratio * 100);
    elements.coverageValue.textContent = `${coverage}%`;
    elements.coverageFill.style.width = `${coverage}%`;
    renderStructure({
      ...analysis,
      grade_band: payload.grade_band,
    });
    renderCriterionScores(analysis);

    const fallbackMessage = payload.fallback_reason
      ? `\n\nFallback reason: ${payload.fallback_reason}`
      : "";
    renderFeedback(
      `AI-assisted scoring complete. Scores are formative estimates, not official marks.${fallbackMessage}`
    );
    setBusy(false, "Ready");
  } catch (error) {
    setBusy(false, "Ready");
    setErrorStatus("AI score issue");
    renderFeedback(error.message);
  }
}

function clearWorkspace() {
  elements.studentText.value = "";
  resetAnalysisDisplay();
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

elements.scoreButton.addEventListener("click", () => {
  runLLMScore();
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
  resetAnalysisDisplay();
  state.lastAIReview = null;
  elements.studentText.focus();
});

elements.uploadButton.addEventListener("click", () => {
  if (!state.busy) {
    elements.draftFileInput.click();
  }
});

elements.draftFileInput.addEventListener("change", () => {
  runUpload(elements.draftFileInput.files[0]);
});

elements.studentText.addEventListener("input", () => {
  state.lastAIReview = null;
});

elements.criteriaList.addEventListener("click", (event) => {
  const button = event.target.closest(".criterion-card-head");
  if (button) {
    toggleCriterionCard(button);
  }
});

elements.helpButton.addEventListener("click", () => {
  openHelpModal();
});

elements.helpCloseButton.addEventListener("click", () => {
  closeHelpModal();
});

elements.helpModal.addEventListener("click", (event) => {
  if (event.target === elements.helpModal) {
    closeHelpModal();
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeHelpModal();
  }
});
