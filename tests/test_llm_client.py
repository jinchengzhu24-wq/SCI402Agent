import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sci402_agent.llm_client import (
    DEFAULT_LLM_API_BASE,
    DEFAULT_LLM_MODEL_ID,
    LLMConfigurationError,
    LLMConfig,
    chat_completion,
    load_llm_config,
)


def test_load_llm_config_uses_defaults_and_env_key(monkeypatch):
    monkeypatch.setenv("SCI402_LLM_API_KEY", "secret")
    monkeypatch.delenv("SCI402_LLM_API_BASE", raising=False)
    monkeypatch.delenv("SCI402_LLM_MODEL_ID", raising=False)

    config = load_llm_config()

    assert config.api_base == DEFAULT_LLM_API_BASE
    assert config.api_key == "secret"
    assert config.model_id == DEFAULT_LLM_MODEL_ID


def test_load_llm_config_requires_api_key(monkeypatch):
    monkeypatch.delenv("SCI402_LLM_API_KEY", raising=False)

    with pytest.raises(LLMConfigurationError):
        load_llm_config()


def test_chat_completion_sends_messages_and_returns_content():
    captured_request = {}

    class FakeCompletions:
        def create(self, **request):
            captured_request.update(request)
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content="Hello from model.",
                            tool_calls=None,
                        )
                    )
                ]
            )

    class FakeClient:
        chat = SimpleNamespace(completions=FakeCompletions())

    def fake_factory(config):
        assert config.api_key == "secret"
        return FakeClient()

    config = LLMConfig(
        api_base="https://example.test",
        api_key="secret",
        model_id="model-1",
    )

    response = chat_completion(
        messages=[{"role": "user", "content": "Hello!"}],
        config=config,
        client_factory=fake_factory,
    )

    assert captured_request == {
        "model": "model-1",
        "messages": [{"role": "user", "content": "Hello!"}],
    }
    assert response == {"content": "Hello from model.", "tool_calls": []}
