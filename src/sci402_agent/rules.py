"""Structured SCI402 proposal rubric rules.

This module is the first layer of the agent: it turns the human marking
criteria into data that later modules can inspect, score lightly, and pass into
prompt templates.
"""

from __future__ import annotations

from typing import Any


CRITERIA_ORDER = (
    "C1_SCIENTIFIC_BACKGROUND",
    "C2_AI_ML_FORMULATION",
    "C3_METHODOLOGY_WORKFLOW",
    "C4_SCIENTIFIC_INTEGRATION",
    "C5_FEASIBILITY_ETHICS_RISK",
)


RUBRIC_RULES: dict[str, dict[str, Any]] = {
    "C1_SCIENTIFIC_BACKGROUND": {
        "title": "Scientific Background & Problem Definition",
        "checklist": [
            "Defines the scientific topic or research area.",
            "Explains why the problem is scientifically important.",
            "Identifies a clear research gap or limitation in current methods.",
            "Mentions available data sources or expected data type.",
            "Discusses basic limitations of the data or existing approach.",
        ],
        "missing_feedback": (
            "Clarify the scientific problem, why it matters, the research gap, "
            "and what data source will support the project."
        ),
        "blocking_rule": (
            "Do not mark this criterion as complete if the research gap is not "
            "clearly stated."
        ),
        "keywords": [
            "scientific problem",
            "research gap",
            "background",
            "data source",
            "limitation",
            "traditional method",
        ],
    },
    "C2_AI_ML_FORMULATION": {
        "title": "AI/ML Problem Formulation",
        "checklist": [
            "States the ML task type, such as regression or classification.",
            "Defines input features.",
            "Defines the output variable or target label.",
            "Explains why the chosen model family fits the task.",
            "Mentions sample size or data sufficiency.",
        ],
        "missing_feedback": (
            "Define the ML task type, input features, output or target variable, "
            "and why the selected algorithm is appropriate."
        ),
        "blocking_rule": (
            "Do not give positive completion feedback if input features or "
            "output variables are undefined."
        ),
        "keywords": [
            "regression",
            "classification",
            "clustering",
            "features",
            "input",
            "output",
            "target",
            "label",
            "model",
        ],
    },
    "C3_METHODOLOGY_WORKFLOW": {
        "title": "Methodology & Workflow Design",
        "checklist": [
            "Describes data collection or data acquisition.",
            "Explains cleaning, preprocessing, or feature engineering.",
            "Specifies model training and validation strategy.",
            "Chooses suitable evaluation metrics.",
            "Includes a reproducibility plan.",
            "Mentions the required workflow diagram or system architecture.",
        ],
        "missing_feedback": (
            "Add a complete workflow covering data collection, preprocessing, "
            "training, validation, metrics, reproducibility, and a workflow diagram."
        ),
        "blocking_rule": (
            "Flag the methodology as incomplete if the workflow diagram or "
            "training-validation strategy is missing."
        ),
        "keywords": [
            "workflow",
            "pipeline",
            "preprocessing",
            "cleaning",
            "training",
            "validation",
            "evaluation",
            "metrics",
            "reproducibility",
            "diagram",
        ],
    },
    "C4_SCIENTIFIC_INTEGRATION": {
        "title": "Scientific Integration & Interpretation",
        "checklist": [
            "Explains how ML results support scientific understanding.",
            "Includes interpretation methods such as feature importance.",
            "Connects predictions to domain knowledge or physical constraints.",
            "Plans experimental or real-world validation.",
            "Avoids treating accuracy as the only scientific result.",
        ],
        "missing_feedback": (
            "Explain how the model output will improve scientific understanding, "
            "how results will be interpreted, and how predictions will be validated."
        ),
        "blocking_rule": (
            "Do not mark this criterion as strong if the proposal only reports "
            "prediction accuracy without scientific interpretation."
        ),
        "keywords": [
            "interpretation",
            "feature importance",
            "sensitivity analysis",
            "domain knowledge",
            "physical constraint",
            "experimental validation",
            "scientific understanding",
        ],
    },
    "C5_FEASIBILITY_ETHICS_RISK": {
        "title": "Feasibility, Ethics & Risk Assessment",
        "checklist": [
            "Assesses whether the data is available and sufficient.",
            "Discusses sample size, bias, or data quality risks.",
            "Mentions overfitting and model failure points.",
            "Considers computational resources and time constraints.",
            "Identifies ethical or privacy issues where relevant.",
            "Provides mitigation strategies for major risks.",
        ],
        "missing_feedback": (
            "Add feasibility, risk, and ethics discussion, including data limits, "
            "overfitting, bias, resources, ethical issues, and mitigation strategies."
        ),
        "blocking_rule": (
            "Do not mark this criterion as complete if risks are listed without "
            "mitigation strategies."
        ),
        "keywords": [
            "feasibility",
            "risk",
            "ethics",
            "bias",
            "overfitting",
            "privacy",
            "mitigation",
            "sample size",
            "computational resources",
        ],
    },
}


REQUIRED_RULE_FIELDS = ("title", "checklist", "missing_feedback", "blocking_rule", "keywords")


def get_criterion(criterion_id: str) -> dict[str, Any]:
    """Return one rubric criterion by id."""
    try:
        return RUBRIC_RULES[criterion_id]
    except KeyError as exc:
        known_ids = ", ".join(CRITERIA_ORDER)
        raise KeyError(f"Unknown criterion id: {criterion_id}. Known ids: {known_ids}") from exc


def validate_rubric_rules() -> None:
    """Raise ValueError if the rubric rule store is incomplete."""
    missing_criteria = [criterion_id for criterion_id in CRITERIA_ORDER if criterion_id not in RUBRIC_RULES]
    if missing_criteria:
        raise ValueError(f"Missing rubric criteria: {', '.join(missing_criteria)}")

    for criterion_id, rule in RUBRIC_RULES.items():
        missing_fields = [field for field in REQUIRED_RULE_FIELDS if field not in rule]
        if missing_fields:
            raise ValueError(f"{criterion_id} is missing fields: {', '.join(missing_fields)}")

        if not rule["checklist"]:
            raise ValueError(f"{criterion_id} must have at least one checklist item")

        if not rule["keywords"]:
            raise ValueError(f"{criterion_id} must have at least one keyword")
