"""Ark-compatible chat completion client for SCI402 tutor responses."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Callable

from .env import load_environment


DEFAULT_LLM_API_BASE = "https://aiagent.xjtlu.edu.cn/api/aigw/v1"
DEFAULT_LLM_MODEL_ID = "d6sfcv1u680jfadtkgn0"
LLM_API_BASE_ENV_VAR = "SCI402_LLM_API_BASE"
LLM_API_KEY_ENV_VAR = "SCI402_LLM_API_KEY"
LLM_MODEL_ID_ENV_VAR = "SCI402_LLM_MODEL_ID"


class LLMConfigurationError(RuntimeError):
    """Raised when model client configuration is incomplete."""


class LLMCallError(RuntimeError):
    """Raised when the model provider call fails."""


@dataclass(frozen=True)
class LLMConfig:
    """Configuration required to create an Ark client."""

    api_base: str
    api_key: str
    model_id: str
    timeout: int = 60


ArkClientFactory = Callable[[LLMConfig], Any]


def load_llm_config() -> LLMConfig:
    """Load model configuration from environment variables."""
    load_environment()
    api_key = os.getenv(LLM_API_KEY_ENV_VAR)
    if not api_key:
        raise LLMConfigurationError(
            f"Missing {LLM_API_KEY_ENV_VAR}. Set it before calling the model."
        )

    return LLMConfig(
        api_base=os.getenv(LLM_API_BASE_ENV_VAR, DEFAULT_LLM_API_BASE),
        api_key=api_key,
        model_id=os.getenv(LLM_MODEL_ID_ENV_VAR, DEFAULT_LLM_MODEL_ID),
    )


def create_ark_client(config: LLMConfig) -> Any:
    """Create the SDK client lazily so tests and rule endpoints do not require it."""
    try:
        from volcenginesdkarkruntime import Ark
    except ImportError as exc:
        raise LLMConfigurationError(
            "Missing volcenginesdkarkruntime. Install it with: "
            "pip install 'volcengine-python-sdk[ark]'"
        ) from exc

    return Ark(base_url=config.api_base, api_key=config.api_key, timeout=config.timeout)


def _model_or_dict_to_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value

    if hasattr(value, "model_dump"):
        return value.model_dump()

    if hasattr(value, "dict"):
        return value.dict()

    return {
        key: getattr(value, key)
        for key in ("id", "type", "function")
        if hasattr(value, key)
    }


def _serialize_tool_calls(tool_calls: Any) -> list[dict[str, Any]]:
    if not tool_calls:
        return []

    return [_model_or_dict_to_dict(tool_call) for tool_call in tool_calls]


def chat_completion(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
    config: LLMConfig | None = None,
    client_factory: ArkClientFactory = create_ark_client,
) -> dict[str, Any]:
    """Call the configured Ark-compatible chat completion model."""
    active_config = config or load_llm_config()
    client = client_factory(active_config)

    request: dict[str, Any] = {
        "model": active_config.model_id,
        "messages": messages,
    }
    if tools is not None:
        request["tools"] = tools

    try:
        response = client.chat.completions.create(**request)
    except Exception as exc:
        raise LLMCallError(f"Model call failed: {exc}") from exc

    message = response.choices[0].message
    return {
        "content": getattr(message, "content", None),
        "tool_calls": _serialize_tool_calls(getattr(message, "tool_calls", None)),
    }
