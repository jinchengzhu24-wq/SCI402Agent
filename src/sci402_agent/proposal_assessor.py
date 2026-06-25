"""Rubric-aware formative assessment for SCI402 proposal drafts."""

from __future__ import annotations

import re
from typing import Any

from .input_analyzer import analyze_input, keyword_in_text, normalize_text
from .rules import CRITERIA_ORDER, RUBRIC_RULES


REQUIRED_WORD_COUNT = 3000
MAX_EVIDENCE_PER_CRITERION = 3

SECTION_PATTERNS: dict[str, tuple[str, ...]] = {
    "C1_SCIENTIFIC_BACKGROUND": (
        "scientific background",
        "problem definition",
        "background and problem",
    ),
    "C2_AI_ML_FORMULATION": (
        "ai / ml problem formulation",
        "ai/ml problem formulation",
        "machine learning problem formulation",
        "ml problem formulation",
    ),
    "C3_METHODOLOGY_WORKFLOW": (
        "methodology",
        "workflow design",
        "methodology and workflow",
    ),
    "C4_SCIENTIFIC_INTEGRATION": (
        "scientific integration",
        "interpretation",
        "scientific integration and interpretation",
    ),
    "C5_FEASIBILITY_ETHICS_RISK": (
        "feasibility",
        "ethics",
        "risk assessment",
        "feasibility ethics",
    ),
}

DIAGRAM_MARKERS = (
    "workflow diagram",
    "system architecture",
    "flowchart",
    "visual workflow",
    "visual framework",
)

ARROW_MARKERS = ("->", "=>", "-->", "→")


def split_sentences(text: str) -> list[str]:
    """Split proposal text into compact evidence-sized snippets."""
    normalized_newlines = re.sub(r"\r\n?", "\n", text.strip())
    raw_chunks = re.split(r"(?<=[.!?])\s+|\n+", normalized_newlines)
    sentences = []
    for chunk in raw_chunks:
        sentence = " ".join(chunk.split())
        if sentence:
            sentences.append(sentence)

    return sentences


def _shorten_snippet(sentence: str, max_chars: int = 240) -> str:
    if len(sentence) <= max_chars:
        return sentence

    return sentence[: max_chars - 3].rstrip() + "..."


def _contains_any_keyword(text: str, keywords: list[str]) -> bool:
    normalized_text = normalize_text(text)
    return any(keyword_in_text(keyword, normalized_text) for keyword in keywords)


def _matching_sentences(sentences: list[str], keywords: list[str]) -> list[str]:
    matches = []
    seen = set()
    for sentence in sentences:
        if not _contains_any_keyword(sentence, keywords):
            continue

        snippet = _shorten_snippet(sentence)
        if snippet in seen:
            continue

        matches.append(snippet)
        seen.add(snippet)
        if len(matches) >= MAX_EVIDENCE_PER_CRITERION:
            break

    return matches


def has_workflow_diagram_marker(text: str) -> bool:
    """Detect whether the proposal declares a workflow diagram or architecture."""
    normalized_text = normalize_text(text)
    if any(marker in normalized_text for marker in DIAGRAM_MARKERS):
        return True

    has_workflow_label = "workflow" in normalized_text
    has_arrow_sequence = any(marker in text for marker in ARROW_MARKERS)
    return has_workflow_label and has_arrow_sequence


def detect_sections(text: str) -> dict[str, Any]:
    """Detect expected SCI402 proposal section headings and their order."""
    detected_sections = []
    lines = [line.strip() for line in re.split(r"\r\n?|\n", text) if line.strip()]

    for line_number, line in enumerate(lines, start=1):
        normalized_line = normalize_text(line)
        for criterion_id, patterns in SECTION_PATTERNS.items():
            if any(pattern in normalized_line for pattern in patterns):
                if criterion_id not in [section["id"] for section in detected_sections]:
                    detected_sections.append(
                        {
                            "id": criterion_id,
                            "title": RUBRIC_RULES[criterion_id]["title"],
                            "line": line_number,
                        }
                    )

    detected_ids = [section["id"] for section in detected_sections]
    missing_sections = [
        criterion_id for criterion_id in CRITERIA_ORDER if criterion_id not in detected_ids
    ]
    section_positions = [
        detected_ids.index(criterion_id)
        for criterion_id in CRITERIA_ORDER
        if criterion_id in detected_ids
    ]
    sections_in_order = section_positions == sorted(section_positions)

    return {
        "detected_sections": detected_sections,
        "missing_sections": missing_sections,
        "sections_in_order": sections_in_order,
    }


def build_structure_check(text: str, word_count: int) -> dict[str, Any]:
    """Build proposal-level checks required by the SCI402 brief."""
    section_check = detect_sections(text)
    has_diagram = has_workflow_diagram_marker(text)
    warnings = []

    if word_count < REQUIRED_WORD_COUNT:
        warnings.append(
            f"Proposal is below the required {REQUIRED_WORD_COUNT} words."
        )
    if section_check["missing_sections"]:
        warnings.append("One or more required proposal sections are missing.")
    if not section_check["sections_in_order"]:
        warnings.append("Required proposal sections are not in rubric order.")
    if not has_diagram:
        warnings.append(
            "Workflow diagram or system architecture is not declared in the text."
        )

    return {
        "required_word_count": REQUIRED_WORD_COUNT,
        "meets_word_requirement": word_count >= REQUIRED_WORD_COUNT,
        "has_workflow_diagram": has_diagram,
        "warnings": warnings,
        **section_check,
    }


def _score_from_matches(matched_count: int, total_items: int) -> int:
    if matched_count == 0:
        return 0

    return max(1, min(5, round((matched_count / total_items) * 5)))


def _score_level(score: int) -> str:
    if score >= 5:
        return "Excellent"
    if score >= 3:
        return "Satisfactory"
    return "Weak"


def assess_criterion(
    criterion_id: str,
    text: str,
    sentences: list[str],
    structure_check: dict[str, Any],
) -> dict[str, Any]:
    """Score one proposal criterion with evidence and cap rules."""
    rule = RUBRIC_RULES[criterion_id]
    scoring_items = rule["scoring_items"]
    matched_items = []
    missing_items = []
    evidence = []

    for item in scoring_items:
        item_keywords = item["keywords"]
        item_evidence = _matching_sentences(sentences, item_keywords)
        if item_evidence:
            matched_items.append(item["id"])
            for snippet in item_evidence:
                if snippet not in evidence:
                    evidence.append(snippet)
                    break
        else:
            missing_items.append(item["missing"])

    score = _score_from_matches(len(matched_items), len(scoring_items))
    blocking_flags = []
    matched_item_set = set(matched_items)

    for cap_rule in rule["cap_rules"]:
        required_item = cap_rule.get("requires")
        required_external = cap_rule.get("requires_external")
        rule_passed = True

        if required_item:
            rule_passed = required_item in matched_item_set
        if required_external:
            rule_passed = bool(structure_check.get(required_external))

        if rule_passed:
            continue

        score = min(score, cap_rule["max_score"])
        blocking_flags.append(cap_rule["message"])

    return {
        "id": criterion_id,
        "title": rule["title"],
        "score_0_to_5": score,
        "level": _score_level(score),
        "matched_items": matched_items,
        "missing_items": missing_items,
        "evidence": evidence[:MAX_EVIDENCE_PER_CRITERION],
        "blocking_flags": blocking_flags,
    }


def grade_band(total_score: int) -> str:
    """Return the SCI402 proposal grade band for a 25-point estimate."""
    if total_score >= 22:
        return "22-25 Excellent integration of AI and science"
    if total_score >= 17:
        return "17-21 Satisfactory proposal with minor limitations"
    if total_score >= 12:
        return "12-16 Adequate but lacks methodological clarity"
    return "0-11 Poorly formulated proposal"


def build_priority_revisions(
    structure_check: dict[str, Any],
    criterion_scores: list[dict[str, Any]],
) -> list[str]:
    """Choose the most important revisions from structure and rubric gaps."""
    revisions = []

    if not structure_check["meets_word_requirement"]:
        revisions.append("Expand the proposal to at least 3,000 words.")
    if structure_check["missing_sections"]:
        missing_titles = [
            RUBRIC_RULES[criterion_id]["title"]
            for criterion_id in structure_check["missing_sections"]
        ]
        revisions.append("Add the missing required sections: " + ", ".join(missing_titles) + ".")
    if not structure_check["has_workflow_diagram"]:
        revisions.append("Add or clearly reference a workflow diagram or system architecture.")

    ordered_scores = sorted(
        criterion_scores,
        key=lambda item: (item["score_0_to_5"], CRITERIA_ORDER.index(item["id"])),
    )
    for score in ordered_scores:
        if score["blocking_flags"]:
            revisions.append(score["blocking_flags"][0])
        elif score["missing_items"]:
            revisions.append(f"{score['title']}: {score['missing_items'][0]}")

        if len(revisions) >= 5:
            break

    return revisions[:5]


def assess_proposal(student_text: str) -> dict[str, Any]:
    """Return the legacy input profile plus rubric-aware proposal assessment."""
    base_profile = analyze_input(student_text)
    sentences = split_sentences(student_text)
    structure_check = build_structure_check(student_text, base_profile["word_count"])
    criterion_scores = [
        assess_criterion(criterion_id, student_text, sentences, structure_check)
        for criterion_id in CRITERIA_ORDER
    ]
    estimated_total = sum(
        criterion_score["score_0_to_5"] for criterion_score in criterion_scores
    )

    return {
        **base_profile,
        "structure_check": structure_check,
        "criterion_scores": criterion_scores,
        "estimated_total": estimated_total,
        "estimated_total_25": estimated_total,
        "grade_band": grade_band(estimated_total),
        "priority_revisions": build_priority_revisions(
            structure_check,
            criterion_scores,
        ),
    }
