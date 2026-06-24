import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sci402_agent import env


def test_load_environment_loads_project_dotenv(monkeypatch, tmp_path):
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text("SCI402_TEST_DOTENV=value-from-file\n", encoding="utf-8")
    monkeypatch.setattr(env, "DOTENV_PATH", dotenv_path)
    monkeypatch.delenv("SCI402_TEST_DOTENV", raising=False)

    loaded = env.load_environment()

    assert loaded is True
    assert env.load_environment() is True
    assert os.getenv("SCI402_TEST_DOTENV") == "value-from-file"


def test_load_environment_does_not_override_existing_environment(monkeypatch, tmp_path):
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text("SCI402_TEST_DOTENV=value-from-file\n", encoding="utf-8")
    monkeypatch.setattr(env, "DOTENV_PATH", dotenv_path)
    monkeypatch.setenv("SCI402_TEST_DOTENV", "value-from-env")

    loaded = env.load_environment()

    assert loaded is True
    assert os.getenv("SCI402_TEST_DOTENV") == "value-from-env"
