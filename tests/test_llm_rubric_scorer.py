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
                "semantic_diagnosis": "The draft is semantically adequate for this criterion.",
                "quality_concerns": ["The scientific logic needs sharper detail."],
                "scientific_reasoning_concerns": [
                    "The scientific reasoning needs sharper detail."
                ],
                "local_precheck_blind_spots": [
                    "Checklist coverage may not prove scientific coherence."
                ],
                "why_score_differs_from_local": (
                    "The AI score reflects semantic quality rather than keyword coverage."
                ),
                "revision_focus": "Add a more specific scientific justification.",
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
    assert "Local deterministic precheck" in user_prompt
    assert "criterion_cap_guardrails" in user_prompt
    combined_prompt = system_prompt + "\n" + user_prompt
    assert "estimated_local_total" not in combined_prompt
    assert "local_score=" not in combined_prompt
    assert "candidate_evidence" not in combined_prompt
    assert "missing=" not in user_prompt
    assert "State the MSc research topic" not in user_prompt


def test_parse_llm_scoring_json_rejects_invalid_json():
    with pytest.raises(LLMScoringValidationError):
        parse_llm_scoring_json("not json")


def test_validator_keeps_llm_score_when_no_cap_rule_is_triggered():
    text = "I will use a regression model with input features and an output target."
    profile = assess_proposal(text)

    validated = validate_llm_scores(
        text,
        profile,
        llm_payload(score=4, evidence=text),
    )
    c2 = next(score for score in validated if score["id"] == "C2_AI_ML_FORMULATION")

    assert c2["score_0_to_5"] == 4
    assert c2["local_score_0_to_5"] == 3
    assert c2["semantic_diagnosis"]
    assert c2["scientific_reasoning_concerns"]
    assert c2["local_precheck_blind_spots"]
    assert c2["why_score_differs_from_local"]
    assert c2["revision_focus"]


def test_validator_applies_cap_max_not_local_heuristic_score():
    text = (
        "Potential risks include overfitting and data bias. "
        "Ethical issues include privacy and transparent reporting."
    )
    profile = assess_proposal(text)

    validated = validate_llm_scores(text, profile, llm_payload(score=5))
    c5 = next(score for score in validated if score["id"] == "C5_FEASIBILITY_ETHICS_RISK")

    assert c5["local_score_0_to_5"] < 3
    assert c5["score_0_to_5"] == 3
    assert c5["cap_applied"] is True
    assert "Local cap rule reduced the LLM score to 3/5." in c5["adjustments"]


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
    assert parsed["criterion_scores"][0]["semantic_diagnosis"]
    assert parsed["criterion_scores"][0]["scientific_reasoning_concerns"]
    assert parsed["criterion_scores"][0]["local_precheck_blind_spots"]
