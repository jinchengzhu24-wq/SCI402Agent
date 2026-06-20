"""Lightweight analysis for student proposal text."""

from __future__ import annotations

import re
from typing import Any

from .rules import CRITERIA_ORDER, RUBRIC_RULES


SHORT_INPUT_WORD_LIMIT = 15
CONFUSION_PHRASES = (
    "help",
    "i don't know",
    "i do not know",
    "not sure",
    "confused",
    "no idea",
)

WORD_PATTERN = re.compile(r"[a-zA-Z0-9]+(?:'[a-zA-Z0-9]+)?")


def normalize_text(text: str) -> str:
    """Lowercase text and collapse repeated whitespace."""
    return " ".join(text.lower().split())


def count_words(text: str) -> int:
    """Count simple English words and numbers in a text string."""
    return len(WORD_PATTERN.findall(text))


def keyword_in_text(keyword: str, normalized_text: str) -> bool:
    """Return True when a keyword or phrase appears in normalized text."""
    normalized_keyword = normalize_text(keyword)
    if not normalized_keyword:
        return False

    if " " in normalized_keyword:
        return normalized_keyword in normalized_text

    pattern = rf"\b{re.escape(normalized_keyword)}\b"
    return re.search(pattern, normalized_text) is not None


def find_keyword_matches(student_text: str) -> dict[str, list[str]]:
    """Find rubric keywords that appear in the student input."""
    normalized_text = normalize_text(student_text)
    matches: dict[str, list[str]] = {}

    for criterion_id in CRITERIA_ORDER:
        keywords = RUBRIC_RULES[criterion_id]["keywords"]
        matched_keywords = [
            keyword for keyword in keywords if keyword_in_text(keyword, normalized_text)
        ]
        if matched_keywords:
            matches[criterion_id] = matched_keywords

    return matches


def analyze_input(student_text: str) -> dict[str, Any]:
    """Build a rule-based profile of a student's proposal text."""
    normalized_text = normalize_text(student_text)
    word_count = count_words(student_text)
    matched_keywords = find_keyword_matches(student_text)
    matched_criteria = list(matched_keywords)
    missing_criteria = [
        criterion_id for criterion_id in CRITERIA_ORDER if criterion_id not in matched_keywords
    ]

    return {
        "word_count": word_count,
        "is_blank": not normalized_text,
        "is_short_input": word_count < SHORT_INPUT_WORD_LIMIT,
        "confusion_detected": any(
            phrase in normalized_text for phrase in CONFUSION_PHRASES
        ),
        "matched_keywords": matched_keywords,
        "matched_criteria": matched_criteria,
        "missing_criteria": missing_criteria,
        "coverage_ratio": len(matched_criteria) / len(CRITERIA_ORDER),
    }
