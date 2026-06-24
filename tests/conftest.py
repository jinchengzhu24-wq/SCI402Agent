import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


@pytest.fixture(autouse=True)
def isolate_real_dotenv(monkeypatch):
    # Keep local .env secrets from changing unit-test expectations.
    for env_var in (
        "SCI402_LLM_API_BASE",
        "SCI402_LLM_API_KEY",
        "SCI402_LLM_MODEL_ID",
    ):
        monkeypatch.delenv(env_var, raising=False)

    try:
        import sci402_agent.api as api
        import sci402_agent.llm_client as llm_client
    except ImportError:
        yield
        return

    monkeypatch.setattr(api, "load_environment", lambda: False)
    monkeypatch.setattr(llm_client, "load_environment", lambda: False)
    yield
