import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sci402_agent import analyze_input
from sci402_agent.feedback_agent import (
    MODE_1_SUPPORTIVE_INQUIRY,
    MODE_2_STRUCTURED_GUIDANCE,
    MODE_3_EXPERT_CHALLENGE,
    build_feedback_messages,
    select_mode,
)
from sci402_agent.rules import CRITERIA_ORDER, RUBRIC_RULES


def test_select_mode_uses_supportive_inquiry_for_help():
    profile = analyze_input("help")

    assert select_mode(profile) == MODE_1_SUPPORTIVE_INQUIRY


def test_select_mode_uses_structured_guidance_for_incomplete_proposal():
    profile = analyze_input(
        "My project will use a regression model with input features and an "
        "output target for a dataset, but the workflow and validation are not "
        "planned yet."
    )

    assert select_mode(profile) == MODE_2_STRUCTURED_GUIDANCE


def test_select_mode_uses_expert_challenge_for_broad_proposal():
    profile = analyze_input(
        "The scientific problem has a clear research gap and data source. "
        "I will use a regression model with input features and an output target. "
        "The workflow includes preprocessing, training, validation, and metrics. "
        "I will use feature importance and experimental validation for interpretation. "
        "The feasibility section discusses risk, ethics, overfitting, and mitigation."
    )

    assert select_mode(profile) == MODE_3_EXPERT_CHALLENGE


def test_prompt_includes_rubric_titles_and_blocking_rules():
    profile = analyze_input("help")
    messages = build_feedback_messages("help", profile, MODE_1_SUPPORTIVE_INQUIRY)
    system_prompt = messages[0]["content"]

    for criterion_id in CRITERIA_ORDER:
        rule = RUBRIC_RULES[criterion_id]
        assert rule["title"] in system_prompt
        assert rule["blocking_rule"] in system_prompt


def test_prompt_includes_mode_specific_instructions():
    mode_1_prompt = build_feedback_messages(
        "help",
        analyze_input("help"),
        MODE_1_SUPPORTIVE_INQUIRY,
    )[0]["content"]
    mode_2_prompt = build_feedback_messages(
        "This regression project has input features and an output target, but "
        "the workflow is unfinished.",
        analyze_input(
            "This regression project has input features and an output target, "
            "but the workflow is unfinished."
        ),
        MODE_2_STRUCTURED_GUIDANCE,
    )[0]["content"]
    mode_3_prompt = build_feedback_messages(
        "A complete proposal draft.",
        analyze_input("A complete proposal draft."),
        MODE_3_EXPERT_CHALLENGE,
    )[0]["content"]

    assert "exactly one low-pressure open question" in mode_1_prompt
    assert "concrete missing items" in mode_2_prompt
    assert "step-by-step supplement requirements" in mode_2_prompt
    assert "limitations" in mode_3_prompt
    assert "experimental validation" in mode_3_prompt
    assert "failure points" in mode_3_prompt


def test_prompt_includes_prohibited_behavior():
    profile = analyze_input("help")
    messages = build_feedback_messages("help", profile, MODE_1_SUPPORTIVE_INQUIRY)
    system_prompt = messages[0]["content"]

    assert "Do not use external literature" in system_prompt
    assert "Do not give generic praise" in system_prompt
    assert "Do not write the complete proposal" in system_prompt
