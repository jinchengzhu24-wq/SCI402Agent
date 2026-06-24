from sci402_agent import (
    CRITERIA_ORDER,
    RUBRIC_RULES,
    analyze_input,
    count_words,
    find_keyword_matches,
    get_criterion,
    validate_rubric_rules,
)


def test_rubric_has_all_required_criteria_and_fields():
    assert len(CRITERIA_ORDER) == 5
    assert set(CRITERIA_ORDER) == set(RUBRIC_RULES)

    validate_rubric_rules()

    for criterion_id in CRITERIA_ORDER:
        rule = get_criterion(criterion_id)
        assert rule["title"]
        assert rule["checklist"]
        assert rule["missing_feedback"]
        assert rule["blocking_rule"]
        assert rule["keywords"]


def test_input_analyzer_detects_short_confused_input():
    profile = analyze_input("I don't know. Help.")

    assert count_words("I don't know how to start.") == 6
    assert profile["is_short_input"] is True
    assert profile["confusion_detected"] is True
    assert profile["coverage_ratio"] == 0


def test_keyword_matches_identify_ai_ml_formulation():
    matches = find_keyword_matches(
        "This is a regression model with input features and an output target."
    )

    assert "C2_AI_ML_FORMULATION" in matches
    assert "features" in matches["C2_AI_ML_FORMULATION"]
    assert "output" in matches["C2_AI_ML_FORMULATION"]


def test_broad_proposal_covers_all_criteria():
    profile = analyze_input(
        "The scientific problem has a clear research gap and data source. "
        "I will use a regression model with input features and an output target. "
        "The workflow includes preprocessing, training, validation, and metrics. "
        "I will use feature importance and experimental validation for interpretation. "
        "The feasibility section discusses risk, ethics, overfitting, and mitigation."
    )

    assert profile["is_short_input"] is False
    assert profile["matched_criteria"] == list(CRITERIA_ORDER)
    assert profile["missing_criteria"] == []
    assert profile["coverage_ratio"] == 1
