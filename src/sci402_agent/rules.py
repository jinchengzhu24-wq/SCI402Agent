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

RUBRIC_LEVELS = {
    "excellent": "Excellent (5): complete, specific, and logically justified.",
    "satisfactory": "Satisfactory (3-4): mostly present but missing detail or depth.",
    "weak": "Weak (0-2): vague, incomplete, or disconnected from the rubric.",
}


PROPOSAL_SCORING_RULES: dict[str, dict[str, Any]] = {
    "C1_SCIENTIFIC_BACKGROUND": {
        "rubric_levels": RUBRIC_LEVELS,
        "scoring_items": [
            {
                "id": "topic",
                "label": "Clear scientific topic or research area",
                "missing": "State the MSc research topic and specific scientific problem.",
                "keywords": [
                    "research topic",
                    "scientific problem",
                    "project studies",
                    "challenge",
                    "problem",
                ],
            },
            {
                "id": "importance",
                "label": "Scientific importance or motivation",
                "missing": "Explain why the problem matters scientifically or practically.",
                "keywords": [
                    "important",
                    "safety",
                    "degradation",
                    "understanding",
                    "scientifically important",
                    "major challenge",
                ],
            },
            {
                "id": "research_gap",
                "label": "Clear research gap",
                "missing": "Identify the scientific gap or limitation in current approaches.",
                "keywords": [
                    "research gap",
                    "gap",
                    "lack of",
                    "insufficient",
                    "limitation",
                    "limits",
                ],
            },
            {
                "id": "method_limitation",
                "label": "Why current methodology is insufficient",
                "missing": "Explain why current experiments, simulations, or manual methods are insufficient.",
                "keywords": [
                    "traditional",
                    "current methodology",
                    "existing method",
                    "manual",
                    "simulation",
                    "computational time",
                    "parameter calibration",
                ],
            },
            {
                "id": "data_context",
                "label": "Available data type or source",
                "missing": "Describe the available data source or expected data type.",
                "keywords": [
                    "data source",
                    "data",
                    "dataset",
                    "experimental",
                    "simulation",
                    "omics",
                    "imaging",
                    "time-series",
                    "measurements",
                ],
            },
        ],
        "cap_rules": [
            {
                "id": "missing_research_gap",
                "requires": "research_gap",
                "max_score": 2,
                "message": "Research gap is not clearly stated, so C1 is capped at 2/5.",
            }
        ],
    },
    "C2_AI_ML_FORMULATION": {
        "rubric_levels": RUBRIC_LEVELS,
        "scoring_items": [
            {
                "id": "task_type",
                "label": "Specific ML task type",
                "missing": "State whether the problem is regression, classification, clustering, inverse design, optimization, or generative modeling.",
                "keywords": [
                    "regression",
                    "classification",
                    "clustering",
                    "inverse design",
                    "optimization",
                    "generative",
                    "supervised",
                    "unsupervised",
                ],
            },
            {
                "id": "input_features",
                "label": "Input features",
                "missing": "Define the input features the model will use.",
                "keywords": [
                    "input features",
                    "features",
                    "feature",
                    "input variable",
                    "variables",
                    "current",
                    "voltage",
                ],
            },
            {
                "id": "output_variable",
                "label": "Output variable or target",
                "missing": "Define the output variable, target label, or prediction target.",
                "keywords": [
                    "output",
                    "target",
                    "label",
                    "predict",
                    "prediction target",
                    "surface temperature",
                ],
            },
            {
                "id": "algorithm_justification",
                "label": "Algorithm choice justified",
                "missing": "Justify why the selected algorithm family fits the scientific data and objective.",
                "keywords": [
                    "because",
                    "suitable",
                    "appropriate",
                    "justify",
                    "can model",
                    "nonlinear",
                    "chosen model",
                ],
            },
            {
                "id": "data_amount",
                "label": "Realistic data amount or sufficiency",
                "missing": "Estimate how much data is available and whether it is sufficient.",
                "keywords": [
                    "sample size",
                    "observations",
                    "several thousand",
                    "569",
                    "dataset contains",
                    "data sufficiency",
                    "how much data",
                ],
            },
        ],
        "cap_rules": [
            {
                "id": "missing_input_features",
                "requires": "input_features",
                "max_score": 2,
                "message": "Input features are undefined, so C2 is capped at 2/5.",
            },
            {
                "id": "missing_output_variable",
                "requires": "output_variable",
                "max_score": 2,
                "message": "Output variable or target is undefined, so C2 is capped at 2/5.",
            },
        ],
    },
    "C3_METHODOLOGY_WORKFLOW": {
        "rubric_levels": RUBRIC_LEVELS,
        "scoring_items": [
            {
                "id": "data_pipeline",
                "label": "End-to-end data pipeline",
                "missing": "Outline the pipeline from data collection to final evaluation.",
                "keywords": [
                    "pipeline",
                    "workflow",
                    "data collection",
                    "data acquisition",
                    "data cleaning",
                    "model validation",
                ],
            },
            {
                "id": "preprocessing",
                "label": "Preprocessing or feature engineering",
                "missing": "Explain cleaning, preprocessing, scaling, normalization, or feature engineering.",
                "keywords": [
                    "preprocessing",
                    "cleaning",
                    "missing values",
                    "normalization",
                    "scaling",
                    "feature engineering",
                ],
            },
            {
                "id": "model_training",
                "label": "Model training plan",
                "missing": "Describe how models will be trained.",
                "keywords": [
                    "training",
                    "train",
                    "trained",
                    "model training",
                ],
            },
            {
                "id": "validation_strategy",
                "label": "Training-validation strategy",
                "missing": "Define a validation strategy such as cross-validation or a train/test split.",
                "keywords": [
                    "validation",
                    "cross-validation",
                    "data splitting",
                    "train-test",
                    "70-30",
                    "test set",
                    "holdout",
                ],
            },
            {
                "id": "metrics",
                "label": "Performance metrics",
                "missing": "Specify suitable performance metrics.",
                "keywords": [
                    "metrics",
                    "rmse",
                    "mae",
                    "r2",
                    "accuracy",
                    "precision",
                    "recall",
                    "f1",
                    "auc",
                ],
            },
            {
                "id": "reproducibility",
                "label": "Reproducibility plan",
                "missing": "Describe how code, data, or settings will be documented for reproducibility.",
                "keywords": [
                    "reproducibility",
                    "reproducible",
                    "documented",
                    "code",
                    "datasets",
                    "version",
                    "random seed",
                ],
            },
        ],
        "cap_rules": [
            {
                "id": "missing_workflow_diagram",
                "requires_external": "has_workflow_diagram",
                "max_score": 4,
                "message": "Workflow diagram or system architecture is not declared, so C3 is capped at 4/5.",
            },
            {
                "id": "missing_validation_strategy",
                "requires": "validation_strategy",
                "max_score": 3,
                "message": "Training-validation strategy is missing, so C3 is capped at 3/5.",
            },
        ],
    },
    "C4_SCIENTIFIC_INTEGRATION": {
        "rubric_levels": RUBRIC_LEVELS,
        "scoring_items": [
            {
                "id": "scientific_understanding",
                "label": "How ML results improve scientific understanding",
                "missing": "Explain what the AI results mean scientifically, not only what they predict.",
                "keywords": [
                    "scientific understanding",
                    "advance",
                    "contribution",
                    "support",
                    "influence",
                    "thermal behavior",
                    "what the findings mean",
                ],
            },
            {
                "id": "interpretation_method",
                "label": "Model interpretation method",
                "missing": "Include interpretation methods such as feature importance, SHAP, or sensitivity analysis.",
                "keywords": [
                    "interpretation",
                    "feature importance",
                    "sensitivity analysis",
                    "shap",
                    "explainable",
                ],
            },
            {
                "id": "experimental_validation",
                "label": "Experimental or real-world validation",
                "missing": "Describe how predictions will be validated experimentally or against real-world measurements.",
                "keywords": [
                    "experimental validation",
                    "validated experimentally",
                    "experimentally measured",
                    "measured",
                    "laboratory",
                    "real-world validation",
                    "compare with",
                ],
            },
            {
                "id": "domain_constraints",
                "label": "Domain knowledge or physical constraints",
                "missing": "Explain any physical constraints, domain knowledge, or scientific laws embedded in the model.",
                "keywords": [
                    "domain knowledge",
                    "physical constraint",
                    "physical constraints",
                    "scientific law",
                    "physics",
                    "thermal energy balance",
                ],
            },
            {
                "id": "beyond_accuracy",
                "label": "Beyond accuracy-only reporting",
                "missing": "Clarify why the result matters scientifically beyond predictive accuracy.",
                "keywords": [
                    "not only accuracy",
                    "rather than just",
                    "not just prediction",
                    "scientific result",
                    "scientific meaning",
                ],
            },
        ],
        "cap_rules": [
            {
                "id": "missing_scientific_understanding",
                "requires": "scientific_understanding",
                "max_score": 2,
                "message": "Scientific understanding is not explained, so C4 is capped at 2/5.",
            },
            {
                "id": "missing_interpretation_method",
                "requires": "interpretation_method",
                "max_score": 4,
                "message": "Model interpretation method is missing, so C4 cannot exceed 4/5.",
            },
            {
                "id": "missing_experimental_validation",
                "requires": "experimental_validation",
                "max_score": 4,
                "message": "Experimental validation is missing, so C4 cannot exceed 4/5.",
            },
        ],
    },
    "C5_FEASIBILITY_ETHICS_RISK": {
        "rubric_levels": RUBRIC_LEVELS,
        "scoring_items": [
            {
                "id": "data_availability",
                "label": "Data availability",
                "missing": "Evaluate whether the required data is available.",
                "keywords": [
                    "data availability",
                    "available",
                    "dataset",
                    "data source",
                    "laboratory experiments",
                ],
            },
            {
                "id": "sample_size",
                "label": "Sample size or data limitation",
                "missing": "Discuss sample size limitations or data sufficiency.",
                "keywords": [
                    "sample size",
                    "limited dataset",
                    "several thousand",
                    "569",
                    "observations",
                    "data limits",
                ],
            },
            {
                "id": "computational_requirements",
                "label": "Computational requirements",
                "missing": "Describe computational resources or time constraints.",
                "keywords": [
                    "computational",
                    "resources",
                    "time constraints",
                    "moderate computational",
                    "hardware",
                    "gpu",
                ],
            },
            {
                "id": "failure_points",
                "label": "Risks or failure points",
                "missing": "Identify risks such as overfitting, bias, model failure, or data quality problems.",
                "keywords": [
                    "risk",
                    "failure point",
                    "overfitting",
                    "bias",
                    "data quality",
                    "limited",
                ],
            },
            {
                "id": "ethics",
                "label": "Ethics or responsible AI",
                "missing": "Address ethical, privacy, transparency, or responsible reporting issues.",
                "keywords": [
                    "ethics",
                    "ethical",
                    "privacy",
                    "transparent",
                    "responsible",
                    "limitations",
                ],
            },
            {
                "id": "mitigation_strategy",
                "label": "Mitigation strategies",
                "missing": "Provide specific mitigation strategies for the major risks.",
                "keywords": [
                    "mitigation",
                    "mitigated",
                    "cross-validation",
                    "regularization",
                    "reduce",
                    "address",
                    "manage",
                ],
            },
        ],
        "cap_rules": [
            {
                "id": "missing_mitigation_strategy",
                "requires": "mitigation_strategy",
                "max_score": 3,
                "message": "Risks are not paired with mitigation strategies, so C5 is capped at 3/5.",
            }
        ],
    },
}

for _criterion_id, _scoring_rule in PROPOSAL_SCORING_RULES.items():
    RUBRIC_RULES[_criterion_id].update(_scoring_rule)


REQUIRED_RULE_FIELDS = (
    "title",
    "checklist",
    "missing_feedback",
    "blocking_rule",
    "keywords",
    "rubric_levels",
    "scoring_items",
    "cap_rules",
)


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

        if not rule["scoring_items"]:
            raise ValueError(f"{criterion_id} must have at least one scoring item")

        for item in rule["scoring_items"]:
            for field in ("id", "label", "missing", "keywords"):
                if field not in item:
                    raise ValueError(
                        f"{criterion_id} scoring item is missing field: {field}"
                    )
            if not item["keywords"]:
                raise ValueError(
                    f"{criterion_id} scoring item {item['id']} must have keywords"
                )

        for cap_rule in rule["cap_rules"]:
            for field in ("id", "max_score", "message"):
                if field not in cap_rule:
                    raise ValueError(
                        f"{criterion_id} cap rule is missing field: {field}"
                    )
