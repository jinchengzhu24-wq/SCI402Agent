import sys
from pathlib import Path

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sci402_agent.api import create_app
from sci402_agent.feedback_agent import MODE_2_STRUCTURED_GUIDANCE
from sci402_agent.llm_client import LLMCallError, LLMConfigurationError


def test_health_endpoint_reports_service_status(monkeypatch):
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "criteria_count": 5}


def test_index_page_is_served(monkeypatch):
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "SCI402 Feedback Agent" in response.text


def test_static_app_script_is_served(monkeypatch):
    client = TestClient(create_app())

    response = client.get("/static/app.js")

    assert response.status_code == 200
    assert "runFeedback" in response.text


def test_criteria_endpoint_returns_ordered_rubric_rules(monkeypatch):
    client = TestClient(create_app())

    response = client.get("/criteria")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 5
    assert payload[0]["id"] == "C1_SCIENTIFIC_BACKGROUND"
    assert payload[0]["title"] == "Scientific Background & Problem Definition"


def test_single_criterion_endpoint_returns_404_for_unknown_id(monkeypatch):
    client = TestClient(create_app())

    response = client.get("/criteria/UNKNOWN")

    assert response.status_code == 404
    assert "Unknown criterion id" in response.json()["detail"]


def test_analyze_endpoint_returns_profile_and_criterion_coverage(monkeypatch):
    client = TestClient(create_app())

    response = client.post(
        "/analyze",
        json={
            "student_text": (
                "I will use a regression model with input features and an output target."
            )
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["word_count"] == 13
    assert payload["matched_criteria"] == ["C2_AI_ML_FORMULATION"]
    assert payload["criterion_coverage"][1]["id"] == "C2_AI_ML_FORMULATION"
    assert payload["criterion_coverage"][1]["is_matched"] is True
    assert payload["criterion_coverage"][0]["missing_feedback"]


def test_chat_endpoint_returns_model_content(monkeypatch):
    def fake_chat_completion(messages, tools=None):
        assert messages == [{"role": "user", "content": "Hello!"}]
        assert tools is None
        return {"content": "Hi there.", "tool_calls": []}

    monkeypatch.setattr("sci402_agent.api.chat_completion", fake_chat_completion)
    client = TestClient(create_app())

    response = client.post(
        "/chat",
        json={"messages": [{"role": "user", "content": "Hello!"}]},
    )

    assert response.status_code == 200
    assert response.json() == {"content": "Hi there.", "tool_calls": []}


def test_feedback_endpoint_returns_mode_analysis_and_feedback(monkeypatch):
    captured_request = {}

    def fake_chat_completion(messages, tools=None):
        captured_request["messages"] = messages
        assert tools is None
        return {
            "content": "Mode: MODE_2_STRUCTURED_GUIDANCE\nFeedback: Add workflow details.",
            "tool_calls": [],
        }

    monkeypatch.setattr("sci402_agent.api.chat_completion", fake_chat_completion)
    client = TestClient(create_app())

    response = client.post(
        "/feedback",
        json={
            "student_text": (
                "My project will use a regression model with input features "
                "and an output target for a dataset, but the workflow and "
                "validation are not planned yet."
            )
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == MODE_2_STRUCTURED_GUIDANCE
    assert payload["analysis"]["matched_criteria"] == [
        "C2_AI_ML_FORMULATION",
        "C3_METHODOLOGY_WORKFLOW",
    ]
    assert payload["feedback"] == (
        "Mode: MODE_2_STRUCTURED_GUIDANCE\nFeedback: Add workflow details."
    )
    assert captured_request["messages"][0]["role"] == "system"
    assert "SCI402 Rubric Rules" in captured_request["messages"][0]["content"]


def test_feedback_endpoint_returns_503_for_missing_llm_config(monkeypatch):
    def fake_chat_completion(messages, tools=None):
        raise LLMConfigurationError("Missing SCI402_LLM_API_KEY.")

    monkeypatch.setattr("sci402_agent.api.chat_completion", fake_chat_completion)
    client = TestClient(create_app())

    response = client.post(
        "/feedback",
        json={"student_text": "This is a proposal draft with enough words to analyze."},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Missing SCI402_LLM_API_KEY."


def test_feedback_endpoint_returns_502_for_llm_call_error(monkeypatch):
    def fake_chat_completion(messages, tools=None):
        raise LLMCallError("Model call failed.")

    monkeypatch.setattr("sci402_agent.api.chat_completion", fake_chat_completion)
    client = TestClient(create_app())

    response = client.post(
        "/feedback",
        json={"student_text": "This is a proposal draft with enough words to analyze."},
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "Model call failed."
