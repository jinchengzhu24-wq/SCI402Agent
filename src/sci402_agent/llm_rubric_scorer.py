"""LLM-based SCI402 rubric scoring with local guardrails."""

from __future__ import annotations

import json
import re
from typing import Any, Callable

from .llm_client import chat_completion
from .proposal_assessor import grade_band
from .rules import CRITERIA_ORDER, RUBRIC_RULES


LLM_SCORING_FALLBACK_REASON = "LLM scoring unavailable; using local rule-based score."
CONFIDENCE_VALUES = {"low", "medium", "high"}


class LLMScoringValidationError(ValueError):
    """Raised when model scoring output cannot be used safely."""


ChatCompletionFn = Callable[..., dict[str, Any]]


def build_llm_scoring_messages(
    student_text: str,
    local_profile: dict[str, Any],
) -> list[dict[str, str]]:
    """Build a strict JSON scoring prompt for SCI402 proposal rubric scoring."""
    system_content = "\n\n".join(
        [
            "You are a SCI402 proposal rubric scoring assistant.",
            "Score only according to the SCI402 rubric and local rule guardrails provided.",
            "Use the student's text as the only evidence source.",
            "Do not invent evidence. Do not use external literature or web knowledge.",
            "Act as an independent second reviewer: read the full student text and make your own semantic judgement.",
            "Use the local precheck only for structural context and hard cap guardrails; it does not contain local evidence or completion decisions.",
            "Return strict JSON only. No markdown, no code fence, no commentary.",
            _format_rubric_for_scoring(),
            _format_required_json_shape(),
        ]
    )
    user_content = "\n\n".join(
        [
            "Student proposal text:",
            student_text,
            "Local deterministic precheck:",
            _format_local_precheck(local_profile),
            "Now produce the JSON scoring result.",
        ]
    )

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]


def score_with_llm(
    student_text: str,
    local_profile: dict[str, Any],
    chat_fn: ChatCompletionFn = chat_completion,
) -> dict[str, Any]:
    """Call the LLM scorer and validate the returned scores."""
    messages = build_llm_scoring_messages(student_text, local_profile)
    response = chat_fn(messages=messages)
    raw_content = response.get("content") or ""
    llm_payload = parse_llm_scoring_json(raw_content)
    validated_scores = validate_llm_scores(student_text, local_profile, llm_payload)
    return build_scoring_response(
        local_profile=local_profile,
        llm_scores=llm_payload["criterion_scores"],
        validated_scores=validated_scores,
        source="llm",
        fallback_reason=None,
    )


def fallback_scoring_response(
    local_profile: dict[str, Any],
    reason: str = LLM_SCORING_FALLBACK_REASON,
) -> dict[str, Any]:
    """Return a scoring response using local rule scores when LLM scoring fails."""
    local_scores = [
        {
            **score,
            "local_score_0_to_5": score["score_0_to_5"],
            "rationale": "Local rule-based fallback score.",
            "semantic_diagnosis": "LLM semantic judgement was unavailable; this card uses the local precheck.",
            "quality_concerns": list(score.get("blocking_flags", [])),
            "scientific_reasoning_concerns": list(score.get("blocking_flags", [])),
            "local_precheck_blind_spots": [
                "AI second review was unavailable, so no semantic blind spots were identified."
            ],
            "why_score_differs_from_local": (
                "No AI second review was available; the local precheck score was used."
            ),
            "revision_focus": (
                score["missing_items"][0]
                if score.get("missing_items")
                else "No local revision focus detected."
            ),
            "confidence": "low",
            "cap_applied": bool(score.get("blocking_flags")),
            "invalid_evidence": [],
            "adjustments": [],
            "source": "local_fallback",
        }
        for score in local_profile["criterion_scores"]
    ]
    return build_scoring_response(
        local_profile=local_profile,
        llm_scores=[],
        validated_scores=local_scores,
        source="local_fallback",
        fallback_reason=reason,
    )


def build_scoring_response(
    local_profile: dict[str, Any],
    llm_scores: list[dict[str, Any]],
    validated_scores: list[dict[str, Any]],
    source: str,
    fallback_reason: str | None,
) -> dict[str, Any]:
    """Build the public hybrid scoring payload."""
    final_total = sum(score["score_0_to_5"] for score in validated_scores)
    return {
        "local_analysis": local_profile,
        "llm_scores": llm_scores,
        "validated_scores": validated_scores,
        "final_total": final_total,
        "final_total_25": final_total,
        "grade_band": grade_band(final_total),
        "source": source,
        "fallback_reason": fallback_reason,
    }


def parse_llm_scoring_json(content: str) -> dict[str, Any]:
    """Parse and validate the top-level LLM scoring JSON payload."""
    try:
        payload = json.loads(_strip_json_fence(content))
    except json.JSONDecodeError as exc:
        raise LLMScoringValidationError("LLM returned invalid JSON.") from exc

    if not isinstance(payload, dict):
        raise LLMScoringValidationError("LLM scoring payload must be a JSON object.")

    scores = payload.get("criterion_scores")
    if not isinstance(scores, list):
        raise LLMScoringValidationError("criterion_scores must be a list.")

    ids = [score.get("id") for score in scores if isinstance(score, dict)]
    if ids != list(CRITERIA_ORDER):
        raise LLMScoringValidationError(
            "criterion_scores must contain the five SCI402 criteria in order."
        )

    for score in scores:
        _validate_llm_score_shape(score)

    return {"criterion_scores": scores}


def validate_llm_scores(
    student_text: str,
    local_profile: dict[str, Any],
    llm_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    """Apply local score guardrails and evidence checks to LLM scores."""
    normalized_text = _normalize_for_evidence(student_text)
    local_by_id = {score["id"]: score for score in local_profile["criterion_scores"]}
    validated_scores = []

    for llm_score in llm_payload["criterion_scores"]:
        criterion_id = llm_score["id"]
        local_score = local_by_id[criterion_id]
        validated_score = {
            "id": criterion_id,
            "title": local_score["title"],
            "score_0_to_5": int(llm_score["score_0_to_5"]),
            "level": _level_for_score(int(llm_score["score_0_to_5"])),
            "local_score_0_to_5": int(local_score["score_0_to_5"]),
            "evidence": list(llm_score["evidence"]),
            "missing_items": list(llm_score["missing_items"]),
            "rationale": llm_score["rationale"],
            "semantic_diagnosis": llm_score["semantic_diagnosis"],
            "quality_concerns": list(llm_score["quality_concerns"]),
            "scientific_reasoning_concerns": list(
                llm_score["scientific_reasoning_concerns"]
            ),
            "local_precheck_blind_spots": list(llm_score["local_precheck_blind_spots"]),
            "why_score_differs_from_local": llm_score["why_score_differs_from_local"],
            "revision_focus": llm_score["revision_focus"],
            "confidence": llm_score["confidence"],
            "cap_applied": bool(llm_score["cap_applied"]),
            "blocking_flags": list(local_score.get("blocking_flags", [])),
            "invalid_evidence": [],
            "adjustments": [],
            "source": "llm",
        }

        for evidence in validated_score["evidence"]:
            if evidence and _normalize_for_evidence(evidence) not in normalized_text:
                validated_score["invalid_evidence"].append(evidence)

        if validated_score["invalid_evidence"]:
            validated_score["adjustments"].append(
                "One or more LLM evidence snippets were not found in the student text."
            )

        cap_max = _cap_max_from_triggered_flags(
            criterion_id,
            validated_score["blocking_flags"],
        )
        if cap_max is not None:
            capped_score = min(validated_score["score_0_to_5"], cap_max)
            if capped_score < validated_score["score_0_to_5"]:
                validated_score["adjustments"].append(
                    f"Local cap rule reduced the LLM score to {cap_max}/5."
                )
            validated_score["score_0_to_5"] = capped_score
            validated_score["cap_applied"] = True

        validated_score["level"] = _level_for_score(validated_score["score_0_to_5"])
        validated_scores.append(validated_score)

    return validated_scores


def _strip_json_fence(content: str) -> str:
    text = content.strip()
    match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, flags=re.DOTALL)
    if match:
        return match.group(1).strip()

    return text


def _validate_llm_score_shape(score: dict[str, Any]) -> None:
    required_fields = (
        "id",
        "score_0_to_5",
        "evidence",
        "missing_items",
        "rationale",
        "semantic_diagnosis",
        "quality_concerns",
        "scientific_reasoning_concerns",
        "local_precheck_blind_spots",
        "why_score_differs_from_local",
        "revision_focus",
        "confidence",
        "cap_applied",
    )
    for field in required_fields:
        if field not in score:
            raise LLMScoringValidationError(f"LLM score missing field: {field}.")

    if not isinstance(score["score_0_to_5"], int) or not 0 <= score["score_0_to_5"] <= 5:
        raise LLMScoringValidationError("score_0_to_5 must be an integer from 0 to 5.")
    if not isinstance(score["evidence"], list):
        raise LLMScoringValidationError("evidence must be a list.")
    if not isinstance(score["missing_items"], list):
        raise LLMScoringValidationError("missing_items must be a list.")
    if not isinstance(score["rationale"], str) or not score["rationale"].strip():
        raise LLMScoringValidationError("rationale must be a non-empty string.")
    if (
        not isinstance(score["semantic_diagnosis"], str)
        or not score["semantic_diagnosis"].strip()
    ):
        raise LLMScoringValidationError(
            "semantic_diagnosis must be a non-empty string."
        )
    if not isinstance(score["quality_concerns"], list):
        raise LLMScoringValidationError("quality_concerns must be a list.")
    if not isinstance(score["scientific_reasoning_concerns"], list):
        raise LLMScoringValidationError(
            "scientific_reasoning_concerns must be a list."
        )
    if not isinstance(score["local_precheck_blind_spots"], list):
        raise LLMScoringValidationError("local_precheck_blind_spots must be a list.")
    if (
        not isinstance(score["why_score_differs_from_local"], str)
        or not score["why_score_differs_from_local"].strip()
    ):
        raise LLMScoringValidationError(
            "why_score_differs_from_local must be a non-empty string."
        )
    if not isinstance(score["revision_focus"], str) or not score["revision_focus"].strip():
        raise LLMScoringValidationError("revision_focus must be a non-empty string.")
    if score["confidence"] not in CONFIDENCE_VALUES:
        raise LLMScoringValidationError("confidence must be low, medium, or high.")
    if not isinstance(score["cap_applied"], bool):
        raise LLMScoringValidationError("cap_applied must be a boolean.")


def _format_rubric_for_scoring() -> str:
    lines = ["SCI402 rubric and local cap rules:"]
    for criterion_id in CRITERIA_ORDER:
        rule = RUBRIC_RULES[criterion_id]
        lines.append(f"{criterion_id}: {rule['title']}")
        lines.extend(f"- Checklist: {item}" for item in rule["checklist"])
        lines.extend(
            f"- Scoring item {item['id']}: {item['label']}"
            for item in rule.get("scoring_items", [])
        )
        lines.extend(
            f"- Cap rule: {cap_rule['message']}"
            for cap_rule in rule.get("cap_rules", [])
        )

    return "\n".join(lines)


def _format_required_json_shape() -> str:
    return (
        "Required JSON shape:\n"
        "{\n"
        '  "criterion_scores": [\n'
        "    {\n"
        '      "id": "C1_SCIENTIFIC_BACKGROUND",\n'
        '      "score_0_to_5": 0,\n'
        '      "evidence": ["exact quote or close snippet from student text"],\n'
        '      "missing_items": ["missing rubric item"],\n'
        '      "rationale": "brief reason grounded in the rubric",\n'
        '      "semantic_diagnosis": "second-review judgement of completion quality",\n'
        '      "quality_concerns": ["legacy field: concise quality concern"],\n'
        '      "scientific_reasoning_concerns": ["scientific logic, validation, interpretation, or feasibility concern"],\n'
        '      "local_precheck_blind_spots": ["what a keyword/checklist precheck may miss"],\n'
        '      "why_score_differs_from_local": "explain how semantic judgement may differ from checklist coverage",\n'
        '      "revision_focus": "one concrete revision focus for this criterion",\n'
        '      "confidence": "low",\n'
        '      "cap_applied": false\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "Return exactly five criterion_scores in SCI402 criterion order."
    )


def _format_local_precheck(local_profile: dict[str, Any]) -> str:
    lines = [
        f"word_count: {local_profile['word_count']}",
        "structure_precheck:",
    ]
    structure_check = local_profile["structure_check"]
    detected_sections = ", ".join(
        section["id"] for section in structure_check["detected_sections"]
    ) or "none"
    lines.extend(
        [
            f"- meets_word_requirement: {structure_check['meets_word_requirement']}",
            f"- has_workflow_diagram: {structure_check['has_workflow_diagram']}",
            f"- sections_in_order: {structure_check['sections_in_order']}",
            f"- detected_sections: {detected_sections}",
            f"- structure_warnings: {', '.join(structure_check['warnings']) or 'none'}",
            "criterion_cap_guardrails:",
        ]
    )
    for score in local_profile["criterion_scores"]:
        cap_flags = score["blocking_flags"] or ["none"]
        lines.append(f"- {score['id']}: triggered_cap_rules={cap_flags}")

    return "\n".join(lines)


def _cap_max_from_triggered_flags(
    criterion_id: str,
    blocking_flags: list[str],
) -> int | None:
    if not blocking_flags:
        return None

    triggered_caps = [
        int(cap_rule["max_score"])
        for cap_rule in RUBRIC_RULES[criterion_id].get("cap_rules", [])
        if cap_rule["message"] in blocking_flags
    ]
    if not triggered_caps:
        return None

    return min(triggered_caps)


def _normalize_for_evidence(text: str) -> str:
    return " ".join(str(text).lower().split())


def _level_for_score(score: int) -> str:
    if score >= 5:
        return "Excellent"
    if score >= 3:
        return "Satisfactory"
    return "Weak"
