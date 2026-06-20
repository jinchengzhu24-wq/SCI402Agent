"""SCI402 rubric-based AI tutor package."""

from .input_analyzer import analyze_input, count_words, find_keyword_matches
from .rules import CRITERIA_ORDER, RUBRIC_RULES, get_criterion, validate_rubric_rules

__all__ = [
    "CRITERIA_ORDER",
    "RUBRIC_RULES",
    "analyze_input",
    "count_words",
    "find_keyword_matches",
    "get_criterion",
    "validate_rubric_rules",
]
