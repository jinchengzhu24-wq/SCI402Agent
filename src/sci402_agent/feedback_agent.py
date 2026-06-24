"""Mode selection and prompt assembly for SCI402 feedback."""

from __future__ import annotations

from typing import Any

from .rules import CRITERIA_ORDER, RUBRIC_RULES


MODE_1_SUPPORTIVE_INQUIRY = "MODE_1_SUPPORTIVE_INQUIRY"
MODE_2_STRUCTURED_GUIDANCE = "MODE_2_STRUCTURED_GUIDANCE"
MODE_3_EXPERT_CHALLENGE = "MODE_3_EXPERT_CHALLENGE"

EXPERT_REQUIRED_CRITERIA = (
    "C3_METHODOLOGY_WORKFLOW",
    "C4_SCIENTIFIC_INTEGRATION",
    "C5_FEASIBILITY_ETHICS_RISK",
)


def select_mode(input_profile: dict[str, Any]) -> str:
    """Select the adaptive feedback mode from a rule-based input profile."""
    if (
        input_profile["is_blank"]
        or input_profile["is_short_input"]
        or input_profile["confusion_detected"]
    ):
        return MODE_1_SUPPORTIVE_INQUIRY

    matched_keywords = input_profile["matched_keywords"]
    has_expert_coverage = input_profile["coverage_ratio"] >= 0.8 and all(
        matched_keywords.get(criterion_id)
        for criterion_id in EXPERT_REQUIRED_CRITERIA
    )
    if has_expert_coverage:
        return MODE_3_EXPERT_CHALLENGE

    return MODE_2_STRUCTURED_GUIDANCE


def build_feedback_messages(
    student_text: str,
    input_profile: dict[str, Any],
    selected_mode: str,
) -> list[dict[str, str]]:
    """Build LLM messages for rubric-bound SCI402 feedback."""
    system_content = "\n\n".join(
        [
            "You are a SCI402 rubric-based AI tutor.",
            "Use only the SCI402 proposal rubric below as the source of feedback.",
            _format_rubric_rules(),
            _mode_instruction(selected_mode),
            _output_format(selected_mode),
            _prohibited_behavior(),
        ]
    )
    user_content = "\n\n".join(
        [
            "Student input:",
            student_text,
            "Rule-based input profile:",
            _format_input_profile(input_profile),
            "Generate the feedback now.",
        ]
    )

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]


def _format_rubric_rules() -> str:
    lines = ["SCI402 Rubric Rules:"]
    for criterion_id in CRITERIA_ORDER:
        rule = RUBRIC_RULES[criterion_id]
        lines.append(f"{criterion_id}: {rule['title']}")
        lines.append("Checklist:")
        lines.extend(f"- {item}" for item in rule["checklist"])
        lines.append(f"Missing feedback: {rule['missing_feedback']}")
        lines.append(f"Blocking rule: {rule['blocking_rule']}")
        lines.append(f"Keywords: {', '.join(rule['keywords'])}")

    return "\n".join(lines)


def _mode_instruction(selected_mode: str) -> str:
    if selected_mode == MODE_1_SUPPORTIVE_INQUIRY:
        return (
            "Mode Instruction: MODE_1_SUPPORTIVE_INQUIRY\n"
            "The student is at an early or confused stage. Do not score, "
            "criticize, or list many missing criteria. Ask exactly one "
            "low-pressure open question that helps the student begin. Include "
            "one brief sentence explaining why that question is a useful first "
            "step."
        )

    if selected_mode == MODE_3_EXPERT_CHALLENGE:
        return (
            "Mode Instruction: MODE_3_EXPERT_CHALLENGE\n"
            "The student has covered most rubric areas. Provide advanced "
            "challenge questions and improvement advice about limitations, "
            "edge cases, experimental validation, failure points, and risk "
            "mitigation. Do not rewrite the proposal."
        )

    return (
        "Mode Instruction: MODE_2_STRUCTURED_GUIDANCE\n"
        "The student has a proposal idea but the structure is incomplete. "
        "Use the rubric to identify concrete missing items, then give "
        "step-by-step supplement requirements. Prioritize features, output "
        "variables, workflow, metrics, scientific interpretation, validation, "
        "and risk mitigation when they are absent."
    )


def _output_format(selected_mode: str) -> str:
    if selected_mode == MODE_1_SUPPORTIVE_INQUIRY:
        return (
            "Required Output Format:\n"
            f"Mode: {MODE_1_SUPPORTIVE_INQUIRY}\n"
            "Question: <one low-pressure open question>\n"
            "Why this helps: <one brief sentence>"
        )

    return (
        "Required Output Format:\n"
        f"Mode: {selected_mode}\n"
        "Rubric Check:\n"
        "- C1 Scientific Background: <Complete / Partially complete / Missing>\n"
        "- C2 AI/ML Formulation: <Complete / Partially complete / Missing>\n"
        "- C3 Methodology: <Complete / Partially complete / Missing>\n"
        "- C4 Scientific Integration: <Complete / Partially complete / Missing>\n"
        "- C5 Feasibility/Ethics/Risk: <Complete / Partially complete / Missing>\n"
        "Feedback:\n"
        "1. <specific rubric-based improvement>\n"
        "2. <specific rubric-based improvement>\n"
        "Next action:\n"
        "<the single most important revision to do next>"
    )


def _prohibited_behavior() -> str:
    return (
        "Prohibited Behavior:\n"
        "- Do not use external literature, web search, or scientific knowledge "
        "outside the provided SCI402 rubric.\n"
        "- Do not give generic praise such as \"looks good\" or \"good job\" "
        "unless all five criteria are complete.\n"
        "- Do not write the complete proposal for the student.\n"
        "- Do not add suggestions unrelated to the SCI402 rubric."
    )


def _format_input_profile(input_profile: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"word_count: {input_profile['word_count']}",
            f"is_blank: {input_profile['is_blank']}",
            f"is_short_input: {input_profile['is_short_input']}",
            f"confusion_detected: {input_profile['confusion_detected']}",
            f"matched_criteria: {', '.join(input_profile['matched_criteria']) or 'none'}",
            f"missing_criteria: {', '.join(input_profile['missing_criteria']) or 'none'}",
            f"coverage_ratio: {input_profile['coverage_ratio']:.2f}",
        ]
    )
