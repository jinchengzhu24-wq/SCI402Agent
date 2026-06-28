"""HTTP API surface for the SCI402 rubric agent."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .env import load_environment
from .feedback_agent import build_feedback_messages, select_mode
from .llm_client import LLMCallError, LLMConfigurationError, chat_completion
from .llm_rubric_scorer import (
    LLMScoringValidationError,
    fallback_scoring_response,
    score_with_llm,
)
from .proposal_assessor import assess_proposal
from .rules import CRITERIA_ORDER, RUBRIC_RULES, get_criterion, validate_rubric_rules


STATIC_DIR = Path(__file__).resolve().parent / "static"


class AnalyzeRequest(BaseModel):
    """Input payload for proposal analysis."""

    student_text: str = Field(..., description="Student proposal text to analyze.")


class ChatMessage(BaseModel):
    """One message in a chat-completion request."""

    role: str
    content: str


class ChatRequest(BaseModel):
    """Input payload for direct model chat."""

    messages: list[ChatMessage]
    tools: list[dict[str, Any]] | None = None


class ChatResponse(BaseModel):
    """Model response returned by the Ark-compatible client."""

    content: str | None
    tool_calls: list[dict[str, Any]]


class CriterionResponse(BaseModel):
    """Public representation of one rubric criterion."""

    id: str
    title: str
    checklist: list[str]
    missing_feedback: str
    blocking_rule: str
    keywords: list[str]


class CriterionCoverage(BaseModel):
    """Criterion-level analysis returned with an input profile."""

    id: str
    title: str
    matched_keywords: list[str]
    is_matched: bool
    missing_feedback: str | None


class DetectedSection(BaseModel):
    """Detected required proposal section."""

    id: str
    title: str
    line: int


class StructureCheck(BaseModel):
    """Proposal-level structure checks from the SCI402 brief."""

    required_word_count: int
    meets_word_requirement: bool
    has_workflow_diagram: bool
    detected_sections: list[DetectedSection]
    missing_sections: list[str]
    sections_in_order: bool
    warnings: list[str]


class CriterionScore(BaseModel):
    """Rubric-aware estimated score for one criterion."""

    id: str
    title: str
    score_0_to_5: int
    level: str
    matched_items: list[str]
    missing_items: list[str]
    evidence: list[str]
    blocking_flags: list[str]


class AnalyzeResponse(BaseModel):
    """Rule-based analysis profile for student proposal text."""

    suggested_feedback_mode: str
    word_count: int
    is_blank: bool
    is_short_input: bool
    confusion_detected: bool
    matched_keywords: dict[str, list[str]]
    matched_criteria: list[str]
    missing_criteria: list[str]
    coverage_ratio: float
    criterion_coverage: list[CriterionCoverage]
    structure_check: StructureCheck
    criterion_scores: list[CriterionScore]
    estimated_total: int
    estimated_total_25: int
    grade_band: str
    priority_revisions: list[str]


class FeedbackResponse(BaseModel):
    """Adaptive SCI402 tutor feedback generated from rubric-bound prompts."""

    mode: str
    analysis: AnalyzeResponse
    feedback: str


class RawLLMScore(BaseModel):
    """One raw score returned by the model before local guardrail validation."""

    id: str
    score_0_to_5: int
    evidence: list[str]
    missing_items: list[str]
    rationale: str
    semantic_diagnosis: str
    quality_concerns: list[str]
    scientific_reasoning_concerns: list[str]
    local_precheck_blind_spots: list[str]
    why_score_differs_from_local: str
    revision_focus: str
    confidence: str
    cap_applied: bool


class ValidatedLLMScore(BaseModel):
    """One LLM score after local cap and evidence validation."""

    id: str
    title: str
    score_0_to_5: int
    level: str
    local_score_0_to_5: int
    evidence: list[str]
    missing_items: list[str]
    rationale: str
    semantic_diagnosis: str
    quality_concerns: list[str]
    scientific_reasoning_concerns: list[str]
    local_precheck_blind_spots: list[str]
    why_score_differs_from_local: str
    revision_focus: str
    confidence: str
    cap_applied: bool
    blocking_flags: list[str]
    invalid_evidence: list[str]
    adjustments: list[str]
    source: str


class FeedbackRequest(AnalyzeRequest):
    """Feedback request with optional AI second-review context."""

    ai_review: list[ValidatedLLMScore] | None = None


class LLMScoreResponse(BaseModel):
    """Hybrid scoring payload using LLM judgment with local guardrails."""

    local_analysis: AnalyzeResponse
    llm_scores: list[RawLLMScore]
    validated_scores: list[ValidatedLLMScore]
    final_total: int
    final_total_25: int
    grade_band: str
    source: str
    fallback_reason: str | None


class HealthResponse(BaseModel):
    """Simple service health payload."""

    status: str
    criteria_count: int


def _criterion_response(criterion_id: str) -> CriterionResponse:
    rule = get_criterion(criterion_id)
    return CriterionResponse(
        id=criterion_id,
        title=rule["title"],
        checklist=list(rule["checklist"]),
        missing_feedback=rule["missing_feedback"],
        blocking_rule=rule["blocking_rule"],
        keywords=list(rule["keywords"]),
    )


def _criterion_coverage(profile: dict[str, Any]) -> list[CriterionCoverage]:
    matched_keywords = profile["matched_keywords"]

    coverage = []
    for criterion_id in CRITERIA_ORDER:
        rule = RUBRIC_RULES[criterion_id]
        keyword_hits = matched_keywords.get(criterion_id, [])
        coverage.append(
            CriterionCoverage(
                id=criterion_id,
                title=rule["title"],
                matched_keywords=keyword_hits,
                is_matched=bool(keyword_hits),
                missing_feedback=None if keyword_hits else rule["missing_feedback"],
            )
        )

    return coverage


def _analyze_response_from_profile(profile: dict[str, Any]) -> AnalyzeResponse:
    return AnalyzeResponse(
        **profile,
        suggested_feedback_mode=select_mode(profile),
        criterion_coverage=_criterion_coverage(profile),
    )


def _message_to_dict(message: ChatMessage) -> dict[str, Any]:
    if hasattr(message, "model_dump"):
        return message.model_dump()

    return message.dict()


def create_app() -> FastAPI:
    """Create and configure the SCI402 FastAPI application."""
    load_environment()
    validate_rubric_rules()

    app = FastAPI(
        title="SCI402 Agent API",
        version="0.1.0",
        description="Rule-based API for SCI402 proposal rubric analysis.",
    )
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/", response_class=FileResponse)
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok", criteria_count=len(CRITERIA_ORDER))

    @app.get("/criteria", response_model=list[CriterionResponse])
    def list_criteria() -> list[CriterionResponse]:
        return [_criterion_response(criterion_id) for criterion_id in CRITERIA_ORDER]

    @app.get("/criteria/{criterion_id}", response_model=CriterionResponse)
    def read_criterion(criterion_id: str) -> CriterionResponse:
        try:
            return _criterion_response(criterion_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/analyze", response_model=AnalyzeResponse)
    def analyze_proposal(request: AnalyzeRequest) -> AnalyzeResponse:
        profile = assess_proposal(request.student_text)
        return _analyze_response_from_profile(profile)

    @app.post("/feedback", response_model=FeedbackResponse)
    def feedback(request: FeedbackRequest) -> FeedbackResponse:
        profile = assess_proposal(request.student_text)
        mode = select_mode(profile)
        messages = build_feedback_messages(
            student_text=request.student_text,
            input_profile=profile,
            selected_mode=mode,
            ai_review=[
                score.model_dump() if hasattr(score, "model_dump") else score.dict()
                for score in request.ai_review or []
            ],
        )

        try:
            response = chat_completion(messages=messages)
        except LLMConfigurationError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc
        except LLMCallError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(exc),
            ) from exc

        return FeedbackResponse(
            mode=mode,
            analysis=_analyze_response_from_profile(profile),
            feedback=response.get("content") or "",
        )

    @app.post("/llm-score", response_model=LLMScoreResponse)
    def llm_score(request: AnalyzeRequest) -> LLMScoreResponse:
        profile = assess_proposal(request.student_text)
        try:
            payload = score_with_llm(request.student_text, profile)
        except (LLMConfigurationError, LLMCallError, LLMScoringValidationError) as exc:
            payload = fallback_scoring_response(profile, str(exc))

        payload["local_analysis"] = _analyze_response_from_profile(profile)
        return LLMScoreResponse(**payload)

    @app.post("/chat", response_model=ChatResponse)
    def chat(request: ChatRequest) -> ChatResponse:
        try:
            response = chat_completion(
                messages=[_message_to_dict(message) for message in request.messages],
                tools=request.tools,
            )
        except LLMConfigurationError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc
        except LLMCallError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(exc),
            ) from exc

        return ChatResponse(**response)

    return app


app = create_app()
