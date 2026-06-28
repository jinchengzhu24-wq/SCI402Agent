import json

import pytest

from sci402_agent.llm_rubric_scorer import (
    LLMScoringValidationError,
    build_llm_scoring_messages,
    parse_llm_scoring_json,
    validate_llm_scores,
)
from sci402_agent.proposal_assessor import assess_proposal
from sci402_agent.rules import CRITERIA_ORDER


def llm_payload(score=5, evidence="This is a supervised regression task."):
    return {
        "criterion_scores": [
            {
                "id": criterion_id,
                "score_0_to_5": score,
                "evidence": [evidence],
                "missing_items": [],
                "rationale": "The draft appears to address this criterion.",
                "confidence": "medium",
                "cap_applied": False,
            }
            for criterion_id in CRITERIA_ORDER
        ]
    }


def test_llm_scoring_prompt_includes_rubric_and_local_precheck():
    profile = assess_proposal("This is a supervised regression task.")

    messages = build_llm_scoring_messages(
        "This is a supervised regression task.",
        profile,
    )

    system_prompt = messages[0]["content"]
    user_prompt = messages[1]["content"]
    assert "Return strict JSON only" in system_prompt
    assert "C1_SCIENTIFIC_BACKGROUND" in system_prompt
    assert "Cap rule" in system_prompt
    assert "Local rule-based precheck" in user_prompt
    assert "criterion_prechecks" in user_prompt


def test_parse_llm_scoring_json_rejects_invalid_json():
    with pytest.raises(LLMScoringValidationError):
        parse_llm_scoring_json("not json")


def test_validator_applies_local_cap_rule_to_high_llm_score():
    text = (
        "This is a supervised regression task. Random Forest is suitable because "
        "it can model nonlinear relationships in scientific data."
    )
    profile = assess_proposal(text)

    validated = validate_llm_scores(text, profile, llm_payload(score=5))
    c2 = next(score for score in validated if score["id"] == "C2_AI_ML_FORMULATION")

    assert c2["score_0_to_5"] <= 2
    assert c2["cap_applied"] is True
    assert "Local cap rule reduced the LLM score." in c2["adjustments"]


def test_validator_flags_evidence_not_found_in_student_text():
    text = "This is a supervised regression task."
    profile = assess_proposal(text)

    validated = validate_llm_scores(
        text,
        profile,
        llm_payload(score=2, evidence="This sentence does not exist in the draft."),
    )

    assert validated[0]["invalid_evidence"] == [
        "This sentence does not exist in the draft."
    ]
    assert "not found in the student text" in validated[0]["adjustments"][0]


def test_parse_llm_scoring_json_accepts_strict_payload():
    payload = llm_payload(score=3)

    parsed = parse_llm_scoring_json(json.dumps(payload))

    assert parsed["criterion_scores"][0]["id"] == "C1_SCIENTIFIC_BACKGROUND"
    assert parsed["criterion_scores"][0]["score_0_to_5"] == 3
