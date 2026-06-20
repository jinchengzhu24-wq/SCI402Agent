import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sci402_agent import analyze_input, count_words, find_keyword_matches


def test_count_words_handles_simple_text():
    assert count_words("I don't know how to start.") == 6


def test_analyze_short_confused_input():
    profile = analyze_input("I don't know. Help.")

    assert profile["is_short_input"] is True
    assert profile["confusion_detected"] is True
    assert profile["coverage_ratio"] == 0


def test_keyword_matches_identify_relevant_criteria():
    matches = find_keyword_matches(
        "This is a regression model with input features and an output target."
    )

    assert "C2_AI_ML_FORMULATION" in matches
    assert "features" in matches["C2_AI_ML_FORMULATION"]
    assert "output" in matches["C2_AI_ML_FORMULATION"]


def test_analyze_broad_proposal_covers_all_criteria():
    profile = analyze_input(
        "The scientific problem has a clear research gap and data source. "
        "I will use a regression model with input features and an output target. "
        "The workflow includes preprocessing, training, validation, and metrics. "
        "I will use feature importance and experimental validation for interpretation. "
        "The feasibility section discusses risk, ethics, overfitting, and mitigation."
    )

    assert profile["is_short_input"] is False
    assert profile["matched_criteria"] == [
        "C1_SCIENTIFIC_BACKGROUND",
        "C2_AI_ML_FORMULATION",
        "C3_METHODOLOGY_WORKFLOW",
        "C4_SCIENTIFIC_INTEGRATION",
        "C5_FEASIBILITY_ETHICS_RISK",
    ]
    assert profile["missing_criteria"] == []
    assert profile["coverage_ratio"] == 1
