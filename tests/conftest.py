from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Callable

import pytest


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def openai_settings() -> SimpleNamespace:
    return SimpleNamespace(
        provider="openai",
        api_key="key-123",
        model="gpt-5-mini",
        reasoning_effort="none",
        max_output_tokens=800,
        base_url=None,
    )


@pytest.fixture
def openrouter_settings() -> SimpleNamespace:
    return SimpleNamespace(
        provider="openrouter",
        api_key="router-key",
        model="openrouter/free",
        reasoning_effort="none",
        max_output_tokens=250,
        base_url="https://openrouter.ai/api/v1",
    )


@pytest.fixture
def patch_openai(monkeypatch: pytest.MonkeyPatch) -> Callable[[SimpleNamespace, str], dict]:
    """Patch core.get_settings and core.OpenAI for a single fixed output_text."""

    def _apply(settings: SimpleNamespace, output_text: str) -> dict:
        captured: dict = {}

        class FakeResponses:
            def create(self, **kwargs):
                captured.update(kwargs)
                return SimpleNamespace(output_text=output_text)

        class FakeOpenAI:
            def __init__(self, **kwargs) -> None:
                captured.update(kwargs)
                self.responses = FakeResponses()

        monkeypatch.setattr("email_generator.core.get_settings", lambda: settings)
        monkeypatch.setattr("email_generator.core.OpenAI", FakeOpenAI)
        return captured

    return _apply


@pytest.fixture
def patch_openrouter(monkeypatch: pytest.MonkeyPatch) -> Callable[[SimpleNamespace, str], dict]:
    """Patch core.get_settings and core.OpenAI for OpenRouter with a fixed chat content."""

    def _apply(settings: SimpleNamespace, content_text: str) -> dict:
        captured: dict = {}

        class FakeChatCompletions:
            def create(self, **kwargs):
                captured.update(kwargs)
                message = SimpleNamespace(content=content_text)
                choice = SimpleNamespace(message=message)
                return SimpleNamespace(choices=[choice])

        class FakeOpenAI:
            def __init__(self, **kwargs) -> None:
                captured.update(kwargs)
                self.chat = SimpleNamespace(completions=FakeChatCompletions())

        monkeypatch.setattr("email_generator.core.get_settings", lambda: settings)
        monkeypatch.setattr("email_generator.core.OpenAI", FakeOpenAI)
        return captured

    return _apply
