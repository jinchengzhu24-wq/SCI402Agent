import sys
from pathlib import Path

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sci402_agent.api import create_app


def test_health_endpoint_does_not_require_api_key(monkeypatch):
    monkeypatch.setenv("SCI402_API_KEY", "secret")
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "criteria_count": 5}


def test_health_endpoint_reports_service_status(monkeypatch):
    monkeypatch.delenv("SCI402_API_KEY", raising=False)
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "criteria_count": 5}


def test_criteria_endpoint_returns_ordered_rubric_rules(monkeypatch):
    monkeypatch.delenv("SCI402_API_KEY", raising=False)
    client = TestClient(create_app())

    response = client.get("/criteria")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 5
    assert payload[0]["id"] == "C1_SCIENTIFIC_BACKGROUND"
    assert payload[0]["title"] == "Scientific Background & Problem Definition"


def test_single_criterion_endpoint_returns_404_for_unknown_id(monkeypatch):
    monkeypatch.delenv("SCI402_API_KEY", raising=False)
    client = TestClient(create_app())

    response = client.get("/criteria/UNKNOWN")

    assert response.status_code == 404
    assert "Unknown criterion id" in response.json()["detail"]


def test_protected_endpoints_reject_missing_api_key(monkeypatch):
    monkeypatch.setenv("SCI402_API_KEY", "secret")
    client = TestClient(create_app())

    response = client.get("/criteria")

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing API key."


def test_protected_endpoints_accept_valid_api_key(monkeypatch):
    monkeypatch.setenv("SCI402_API_KEY", "secret")
    client = TestClient(create_app())

    response = client.get("/criteria", headers={"X-API-Key": "secret"})

    assert response.status_code == 200
    assert response.json()[0]["id"] == "C1_SCIENTIFIC_BACKGROUND"


def test_analyze_endpoint_returns_profile_and_criterion_coverage(monkeypatch):
    monkeypatch.delenv("SCI402_API_KEY", raising=False)
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
    monkeypatch.delenv("SCI402_API_KEY", raising=False)

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
