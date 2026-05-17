from __future__ import annotations

import pytest

from email_generator.config import get_settings


def test_get_settings_raises_when_api_key_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    with pytest.raises(ValueError, match="No API key found"):
        get_settings()


def test_get_settings_rejects_invalid_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "azure")

    with pytest.raises(ValueError, match="LLM_PROVIDER must be one of"):
        get_settings()


def test_get_settings_requires_openrouter_key_when_forced(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    with pytest.raises(ValueError, match="OPENROUTER_API_KEY is not set"):
        get_settings()


def test_get_settings_requires_openai_key_when_forced(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ValueError, match="OPENAI_API_KEY is not set"):
        get_settings()


def test_get_settings_uses_openai_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_REASONING_EFFORT", raising=False)
    monkeypatch.delenv("MAX_OUTPUT_TOKENS", raising=False)

    settings = get_settings()

    assert settings.provider == "openai"
    assert settings.api_key == "test-key"
    assert settings.model == "gpt-5-mini"
    assert settings.reasoning_effort == "none"
    assert settings.max_output_tokens == 800
    assert settings.base_url is None


def test_get_settings_strips_and_uses_custom_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", " custom-key ")
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_MODEL", " gpt-5 ")
    monkeypatch.setenv("OPENAI_REASONING_EFFORT", " medium ")
    monkeypatch.setenv("MAX_OUTPUT_TOKENS", "1200")

    settings = get_settings()

    assert settings.provider == "openai"
    assert settings.api_key == "custom-key"
    assert settings.model == "gpt-5"
    assert settings.reasoning_effort == "medium"
    assert settings.max_output_tokens == 1200


def test_get_settings_prefers_openrouter_in_auto_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", " router-key ")
    monkeypatch.setenv("OPENAI_API_KEY", " openai-key ")
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("OPENROUTER_BASE_URL", raising=False)
    monkeypatch.delenv("MAX_OUTPUT_TOKENS", raising=False)

    settings = get_settings()

    assert settings.provider == "openrouter"
    assert settings.api_key == "router-key"
    assert settings.model == "openrouter/free"
    assert settings.max_output_tokens == 800
    assert settings.base_url == "https://openrouter.ai/api/v1"


def test_get_settings_supports_openrouter_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "router-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "openai/gpt-4.1-mini")
    monkeypatch.setenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    monkeypatch.setenv("OPENAI_REASONING_EFFORT", "low")
    monkeypatch.setenv("MAX_OUTPUT_TOKENS", "300")

    settings = get_settings()

    assert settings.provider == "openrouter"
    assert settings.api_key == "router-key"
    assert settings.model == "openai/gpt-4.1-mini"
    assert settings.reasoning_effort == "low"
    assert settings.max_output_tokens == 300
    assert settings.base_url == "https://openrouter.ai/api/v1"
