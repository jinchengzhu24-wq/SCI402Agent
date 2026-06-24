from sci402_agent import analyze_input
from sci402_agent.feedback_agent import (
    MODE_1_SUPPORTIVE_INQUIRY,
    MODE_2_STRUCTURED_GUIDANCE,
    MODE_3_EXPERT_CHALLENGE,
    build_feedback_messages,
    select_mode,
)
from sci402_agent.rules import CRITERIA_ORDER, RUBRIC_RULES


def test_feedback_mode_selection_uses_input_profile():
    assert select_mode(analyze_input("help")) == MODE_1_SUPPORTIVE_INQUIRY

    incomplete_profile = analyze_input(
        "My project will use a regression model with input features and an "
        "output target for a dataset, but the workflow and validation are not "
        "planned yet."
    )
    assert select_mode(incomplete_profile) == MODE_2_STRUCTURED_GUIDANCE

    broad_profile = analyze_input(
        "The scientific problem has a clear research gap and data source. "
        "I will use a regression model with input features and an output target. "
        "The workflow includes preprocessing, training, validation, and metrics. "
        "I will use feature importance and experimental validation for interpretation. "
        "The feasibility section discusses risk, ethics, overfitting, and mitigation."
    )
    assert select_mode(broad_profile) == MODE_3_EXPERT_CHALLENGE


def test_feedback_prompt_includes_rubric_and_mode_instructions():
    messages = build_feedback_messages(
        "help",
        analyze_input("help"),
        MODE_1_SUPPORTIVE_INQUIRY,
    )
    system_prompt = messages[0]["content"]

    for criterion_id in CRITERIA_ORDER:
        rule = RUBRIC_RULES[criterion_id]
        assert rule["title"] in system_prompt
        assert rule["blocking_rule"] in system_prompt

    assert "exactly one low-pressure open question" in system_prompt
    assert "Do not use external literature" in system_prompt
    assert "Do not give generic praise" in system_prompt
    assert "Do not write the complete proposal" in system_prompt


def test_feedback_prompt_changes_with_guidance_mode():
    guidance_prompt = build_feedback_messages(
        "This regression project has input features and an output target, but "
        "the workflow is unfinished.",
        analyze_input(
            "This regression project has input features and an output target, "
            "but the workflow is unfinished."
        ),
        MODE_2_STRUCTURED_GUIDANCE,
    )[0]["content"]
    expert_prompt = build_feedback_messages(
        "A complete proposal draft.",
        analyze_input("A complete proposal draft."),
        MODE_3_EXPERT_CHALLENGE,
    )[0]["content"]

    assert "concrete missing items" in guidance_prompt
    assert "step-by-step supplement requirements" in guidance_prompt
    assert "limitations" in expert_prompt
    assert "experimental validation" in expert_prompt
    assert "failure points" in expert_prompt
