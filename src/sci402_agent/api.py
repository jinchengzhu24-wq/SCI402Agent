"""HTTP API surface for the SCI402 rubric agent."""

from __future__ import annotations

import hmac
import os
from typing import Any

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

from .input_analyzer import analyze_input
from .llm_client import LLMCallError, LLMConfigurationError, chat_completion
from .rules import CRITERIA_ORDER, RUBRIC_RULES, get_criterion, validate_rubric_rules


API_KEY_ENV_VAR = "SCI402_API_KEY"


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


class AnalyzeResponse(BaseModel):
    """Rule-based analysis profile for student proposal text."""

    word_count: int
    is_blank: bool
    is_short_input: bool
    confusion_detected: bool
    matched_keywords: dict[str, list[str]]
    matched_criteria: list[str]
    missing_criteria: list[str]
    coverage_ratio: float
    criterion_coverage: list[CriterionCoverage]


class HealthResponse(BaseModel):
    """Simple service health payload."""

    status: str
    criteria_count: int


def _require_api_key(expected_api_key: str | None):
    def dependency(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
        if expected_api_key is None:
            return

        if x_api_key is None or not hmac.compare_digest(x_api_key, expected_api_key):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API key.",
            )

    return dependency


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


def _message_to_dict(message: ChatMessage) -> dict[str, Any]:
    if hasattr(message, "model_dump"):
        return message.model_dump()

    return message.dict()


def create_app() -> FastAPI:
    """Create and configure the SCI402 FastAPI application."""
    validate_rubric_rules()
    expected_api_key = os.getenv(API_KEY_ENV_VAR) or None

    app = FastAPI(
        title="SCI402 Agent API",
        version="0.1.0",
        description="Rule-based API for SCI402 proposal rubric analysis.",
    )

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok", criteria_count=len(CRITERIA_ORDER))

    protected_router = APIRouter(
        dependencies=[Depends(_require_api_key(expected_api_key))]
    )

    @protected_router.get("/criteria", response_model=list[CriterionResponse])
    def list_criteria() -> list[CriterionResponse]:
        return [_criterion_response(criterion_id) for criterion_id in CRITERIA_ORDER]

    @protected_router.get("/criteria/{criterion_id}", response_model=CriterionResponse)
    def read_criterion(criterion_id: str) -> CriterionResponse:
        try:
            return _criterion_response(criterion_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @protected_router.post("/analyze", response_model=AnalyzeResponse)
    def analyze_proposal(request: AnalyzeRequest) -> AnalyzeResponse:
        profile = analyze_input(request.student_text)
        return AnalyzeResponse(
            **profile,
            criterion_coverage=_criterion_coverage(profile),
        )

    @protected_router.post("/chat", response_model=ChatResponse)
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

    app.include_router(protected_router)
    return app


app = create_app()
