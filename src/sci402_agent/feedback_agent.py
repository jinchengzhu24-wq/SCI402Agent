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

    if input_profile.get("estimated_total", 0) >= 20:
        return MODE_3_EXPERT_CHALLENGE

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
    ai_review: list[dict[str, Any]] | None = None,
) -> list[dict[str, str]]:
    """Build LLM messages for rubric-bound SCI402 feedback."""
    has_ai_review = bool(ai_review)
    system_content = "\n\n".join(
        [
            "You are a SCI402 rubric-based AI tutor.",
            "Use only the SCI402 proposal rubric below as the source of feedback.",
            (
                "When an AI second review is provided, use it as the primary "
                "revision diagnosis. Do not restate the Rubric Check; turn the "
                "second-review findings into a concrete revision plan."
            )
            if has_ai_review
            else "No AI second review is available; use the local precheck profile.",
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
            _format_input_profile(
                input_profile,
                include_candidate_evidence=not has_ai_review,
            ),
            "AI second review:",
            _format_ai_review(ai_review or []),
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
        lines.append("Scoring items:")
        lines.extend(
            f"- {item['id']}: {item['label']}"
            for item in rule.get("scoring_items", [])
        )
        lines.append("Score cap rules:")
        lines.extend(
            f"- {cap_rule['message']}"
            for cap_rule in rule.get("cap_rules", [])
        )
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
            "The student has covered most rubric areas or has a high formative "
            "score estimate. Act as a revision coach for a stronger draft: "
            "challenge the scientific logic, limitations, edge cases, "
            "experimental validation, failure points, and risk mitigation. "
            "Do not repeat the full rubric check. Do not rewrite the proposal."
        )

    return (
        "Mode Instruction: MODE_2_STRUCTURED_GUIDANCE\n"
        "The student has a proposal idea but the structure is incomplete. "
        "Act as a revision coach: identify the most important next revision, "
        "then explain what to add and why it matters scientifically. Prioritize "
        "features, output variables, workflow, metrics, scientific "
        "interpretation, validation, and risk mitigation when they are absent. "
        "Do not repeat the full rubric check."
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
        "Overall diagnosis:\n"
        "<one short paragraph on the draft's main revision need>\n"
        "Priority rewrite targets:\n"
        "- <highest-impact area to rewrite>\n"
        "- <second priority if needed>\n"
        "- <third priority if needed>\n"
        "Criterion-specific revision plan:\n"
        "- <criterion>: <specific change, using AI second-review findings when provided>\n"
        "- <criterion>: <specific change, using AI second-review findings when provided>\n"
        "Scientific reasoning upgrade:\n"
        "<explain how to improve causal logic, validation, interpretation, or feasibility>\n"
        "Example sentence patterns:\n"
        "- <reusable sentence frame, not a completed proposal paragraph>\n"
        "- <reusable sentence frame, not a completed proposal paragraph>\n"
        "What not to waste time on:\n"
        "<one brief note about a low-priority edit>"
    )


def _prohibited_behavior() -> str:
    return (
        "Prohibited Behavior:\n"
        "- Do not use external literature, web search, or scientific knowledge "
        "outside the provided SCI402 rubric.\n"
        "- Do not give generic praise such as \"looks good\" or \"good job\" "
        "unless all five criteria are complete.\n"
        "- Do not write the complete proposal for the student.\n"
        "- Do not add suggestions unrelated to the SCI402 rubric.\n"
        "- Treat numeric scores as formative estimates, not official marks.\n"
        "- Do not repeat the Rubric Check as a five-criterion score table.\n"
        "- Do not mark a criterion complete unless the assessor profile or AI "
        "second review gives evidence for it."
    )


def _format_input_profile(
    input_profile: dict[str, Any],
    include_candidate_evidence: bool = True,
) -> str:
    lines = [
        f"word_count: {input_profile['word_count']}",
        f"is_blank: {input_profile['is_blank']}",
        f"is_short_input: {input_profile['is_short_input']}",
        f"confusion_detected: {input_profile['confusion_detected']}",
        f"matched_criteria: {', '.join(input_profile['matched_criteria']) or 'none'}",
        f"missing_criteria: {', '.join(input_profile['missing_criteria']) or 'none'}",
        f"coverage_ratio: {input_profile['coverage_ratio']:.2f}",
    ]

    structure_check = input_profile.get("structure_check")
    if structure_check:
        detected_sections = ", ".join(
            section["id"] for section in structure_check["detected_sections"]
        ) or "none"
        lines.extend(
            [
                f"meets_word_requirement: {structure_check['meets_word_requirement']}",
                f"has_workflow_diagram: {structure_check['has_workflow_diagram']}",
                f"detected_sections: {detected_sections}",
                "structure_warnings: "
                + (", ".join(structure_check["warnings"]) or "none"),
            ]
        )

    criterion_scores = input_profile.get("criterion_scores", [])
    if criterion_scores and include_candidate_evidence:
        lines.append("candidate_evidence_and_guardrails:")
        for score in criterion_scores:
            evidence = "; ".join(score["evidence"][:2]) or "not found"
            blockers = "; ".join(score["blocking_flags"]) or "none"
            lines.append(
                f"- {score['id']}: candidate_evidence: {evidence}; "
                f"cap_flags: {blockers}"
            )

    priority_revisions = input_profile.get("priority_revisions", [])
    if priority_revisions:
        lines.append("priority_revisions:")
        lines.extend(f"- {revision}" for revision in priority_revisions[:5])

    return "\n".join(lines)


def _format_ai_review(ai_review: list[dict[str, Any]]) -> str:
    if not ai_review:
        return "not provided"

    lines = []
    for score in ai_review:
        lines.extend(
            [
                f"- {score.get('id', 'UNKNOWN')}: "
                f"AI score {score.get('score_0_to_5', 'n/a')}/5; "
                f"local precheck {score.get('local_score_0_to_5', 'n/a')}/5",
                f"  semantic_diagnosis: {score.get('semantic_diagnosis', 'not provided')}",
                "  scientific_reasoning_concerns: "
                + _format_list(score.get("scientific_reasoning_concerns")),
                "  local_precheck_blind_spots: "
                + _format_list(score.get("local_precheck_blind_spots")),
                "  why_score_differs_from_local: "
                + str(score.get("why_score_differs_from_local", "not provided")),
                f"  revision_focus: {score.get('revision_focus', 'not provided')}",
                "  evidence: " + _format_list(score.get("evidence")),
                "  guardrail_adjustments: " + _format_list(score.get("adjustments")),
            ]
        )

    return "\n".join(lines)


def _format_list(items: Any) -> str:
    if not items:
        return "none"
    if not isinstance(items, list):
        return str(items)
    return "; ".join(str(item) for item in items) or "none"
