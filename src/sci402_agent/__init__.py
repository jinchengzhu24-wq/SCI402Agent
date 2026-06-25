"""SCI402 rubric-based AI tutor package."""

from .feedback_agent import build_feedback_messages, select_mode
from .input_analyzer import analyze_input, count_words, find_keyword_matches
from .proposal_assessor import assess_proposal
from .rules import CRITERIA_ORDER, RUBRIC_RULES, get_criterion, validate_rubric_rules

__all__ = [
    "CRITERIA_ORDER",
    "RUBRIC_RULES",
    "analyze_input",
    "assess_proposal",
    "build_feedback_messages",
    "count_words",
    "find_keyword_matches",
    "get_criterion",
    "select_mode",
    "validate_rubric_rules",
]
