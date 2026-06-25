from sci402_agent.proposal_assessor import assess_proposal


SAMPLE_SOLUTION_STYLE_PROPOSAL = """
Section 1: Scientific Background & Problem Definition
Lithium-ion batteries are widely used in electric vehicles and renewable energy storage systems. A major engineering challenge is predicting battery temperature rise during high-power operation because excessive temperature accelerates degradation and may lead to thermal runaway. Traditional electrochemical thermal models provide accurate predictions but require significant computational time and detailed parameter calibration. This limits their applicability in real-time battery management systems. The scientific gap lies in the lack of fast and scalable prediction methods capable of estimating battery temperature under varying operating conditions. Experimental battery cycling datasets containing measurements of current, voltage, ambient temperature, and state of charge are available.

Section 2: AI / ML Problem Formulation
The scientific problem is formulated as a supervised regression task. The input features include battery current, voltage, ambient temperature, and state of charge. The output variable is battery surface temperature. Random Forest Regression, Gaussian Process Regression, and Artificial Neural Networks are suitable because they can model nonlinear relationships. The dataset is expected to contain several thousand experimental observations.

Section 3: Methodology & Workflow Design
The methodology begins with data collection and preprocessing, including removal of missing values and normalization. Feature engineering may generate additional descriptors. The dataset will be divided into training and validation subsets using a 70-30 split. Machine learning models will be trained using cross-validation. Model performance will be evaluated using RMSE, MAE, and R2. All code and datasets will be documented to ensure reproducibility. Workflow diagram: Data Collection -> Data Cleaning -> Feature Engineering -> Model Training -> Model Validation -> Performance Evaluation.

Section 4: Scientific Integration & Interpretation
Machine learning predictions will enable rapid estimation of battery temperature, supporting real-time battery management systems. The model can help identify how operating conditions influence thermal behavior through feature importance and sensitivity analysis. Predictions will be validated by comparing ML outputs with experimentally measured temperature data from battery tests. Integrating physical constraints such as thermal energy balance equations can improve model reliability. This will show scientific meaning rather than just prediction accuracy.

Section 5: Feasibility, Ethics & Risk Assessment
The proposed study is feasible because battery cycling datasets are typically available from laboratory experiments and machine learning models require moderate computational resources. Potential risks include limited dataset size and overfitting. These challenges can be mitigated through cross-validation and regularization techniques. Ethical considerations include transparent reporting of model limitations and ensuring reproducible research practices by sharing code and datasets where possible.
"""


def score_for(profile, criterion_id):
    return next(
        score
        for score in profile["criterion_scores"]
        if score["id"] == criterion_id
    )


def test_sample_solution_style_proposal_scores_high_with_evidence():
    profile = assess_proposal(SAMPLE_SOLUTION_STYLE_PROPOSAL)

    assert profile["estimated_total"] >= 22
    assert profile["grade_band"].startswith("22-25")
    assert profile["structure_check"]["has_workflow_diagram"] is True
    assert profile["structure_check"]["missing_sections"] == []
    assert profile["structure_check"]["sections_in_order"] is True

    for criterion_score in profile["criterion_scores"]:
        assert criterion_score["score_0_to_5"] >= 4
        assert criterion_score["evidence"]


def test_keyword_stuffing_does_not_score_as_complete_proposal():
    profile = assess_proposal(
        "regression features output workflow validation metrics ethics mitigation"
    )

    assert profile["estimated_total"] < 17
    assert profile["structure_check"]["missing_sections"]
    assert profile["structure_check"]["has_workflow_diagram"] is False


def test_c1_is_capped_when_research_gap_is_missing():
    profile = assess_proposal(
        "The scientific problem is battery heating. It is important for safety. "
        "Experimental dataset measurements are available."
    )

    c1 = score_for(profile, "C1_SCIENTIFIC_BACKGROUND")
    assert c1["score_0_to_5"] <= 2
    assert any("Research gap" in flag for flag in c1["blocking_flags"])


def test_c2_is_capped_when_inputs_or_outputs_are_missing():
    profile = assess_proposal(
        "This is a supervised regression task. Random Forest is suitable because "
        "it can model nonlinear relationships in scientific data."
    )

    c2 = score_for(profile, "C2_AI_ML_FORMULATION")
    assert c2["score_0_to_5"] <= 2
    assert any("Input features" in flag for flag in c2["blocking_flags"])
    assert any("Output variable" in flag for flag in c2["blocking_flags"])


def test_c3_is_capped_when_validation_strategy_is_missing():
    profile = assess_proposal(
        "Section 3: Methodology & Workflow Design\n"
        "Workflow diagram: Data Collection -> Data Cleaning -> Feature Engineering "
        "-> Model Training -> Performance Evaluation. The pipeline includes "
        "preprocessing, missing values removal, normalization, training, RMSE, "
        "MAE, R2, documented code, datasets, and reproducibility."
    )

    c3 = score_for(profile, "C3_METHODOLOGY_WORKFLOW")
    assert c3["score_0_to_5"] <= 3
    assert any("Training-validation strategy" in flag for flag in c3["blocking_flags"])


def test_c5_is_capped_when_mitigation_is_missing():
    profile = assess_proposal(
        "Data availability is realistic because the dataset is available from "
        "laboratory experiments with several thousand observations. Computational "
        "resources are moderate. The risk is limited dataset size, overfitting, "
        "bias, and transparent ethical reporting of limitations."
    )

    c5 = score_for(profile, "C5_FEASIBILITY_ETHICS_RISK")
    assert c5["score_0_to_5"] <= 3
    assert any("mitigation" in flag.lower() for flag in c5["blocking_flags"])


def test_structure_check_detects_missing_order_and_diagram_warnings():
    profile = assess_proposal(
        "Section 2: AI / ML Problem Formulation\n"
        "This is a regression task with input features and an output target.\n"
        "Section 1: Scientific Background & Problem Definition\n"
        "The scientific problem is important, but the research gap is unclear."
    )

    structure = profile["structure_check"]
    assert structure["meets_word_requirement"] is False
    assert structure["sections_in_order"] is False
    assert structure["has_workflow_diagram"] is False
    assert "C3_METHODOLOGY_WORKFLOW" in structure["missing_sections"]
    assert structure["warnings"]
