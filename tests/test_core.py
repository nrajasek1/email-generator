from __future__ import annotations

from types import SimpleNamespace

import pytest

from email_generator.core import _normalize_text, generate_email
from email_generator.prompt import build_user_prompt
from email_generator.providers import (
    _chat_message_to_text,
    _extract_json,
    _generate_with_openai,
    _generate_with_openrouter,
)
from email_generator.schemas import EmailRequest


def test_build_user_prompt_includes_all_fields() -> None:
    prompt = build_user_prompt(
        EmailRequest(
            purpose="Follow up after meeting",
            tone="Friendly",
            context="Mention the timeline and next steps.",
        )
    )

    assert "Purpose: Follow up after meeting" in prompt
    assert "Tone: Friendly" in prompt
    assert "Context: Mention the timeline and next steps." in prompt
    assert "Only use facts present in the context." in prompt
    assert "Treat the context as the source of truth" in prompt
    assert "Every specific claim in the email must be traceable to the context." in prompt
    assert "Do not ask the recipient for information" in prompt
    assert "Avoid generic openings and vague closers." in prompt
    assert "End with a clear, appropriate next step" in prompt
    assert "If the context is sparse, write a shorter and more general email" in prompt
    assert "If the context names topics to cover, explicitly address those topics" in prompt
    assert "Do not add template placeholders" in prompt
    assert "Do not make up pricing tiers" in prompt
    assert "Do not use markdown headings" in prompt
    assert "If exact pricing details are not given" in prompt


def test_system_instructions_include_non_invention_guardrails() -> None:
    from email_generator.prompt import SYSTEM_INSTRUCTIONS

    assert "Do not invent facts" in SYSTEM_INSTRUCTIONS
    assert "Treat the provided context as the source of truth" in SYSTEM_INSTRUCTIONS
    assert "Every concrete claim in the email must be supported by the provided context." in SYSTEM_INSTRUCTIONS
    assert "Do not reverse roles" in SYSTEM_INSTRUCTIONS
    assert "Match the requested tone closely." in SYSTEM_INSTRUCTIONS
    assert "Avoid generic openings" in SYSTEM_INSTRUCTIONS
    assert "Prefer specific, useful next-step language" in SYSTEM_INSTRUCTIONS
    assert "When the context names topics the sender should cover" in SYSTEM_INSTRUCTIONS
    assert "Do not introduce meeting references" in SYSTEM_INSTRUCTIONS
    assert "Do not add placeholder sections" in SYSTEM_INSTRUCTIONS
    assert "Make the draft sound like a realistic sendable email" in SYSTEM_INSTRUCTIONS
    assert "Do not use markdown formatting" in SYSTEM_INSTRUCTIONS
    assert "Do not say something is attached" in SYSTEM_INSTRUCTIONS
    assert "If the context asks for next steps but does not specify them" in SYSTEM_INSTRUCTIONS


def test_extract_json_reads_direct_json() -> None:
    parsed = _extract_json('{"subject": "Hi", "body": "Hello"}')

    assert parsed == {"subject": "Hi", "body": "Hello"}


def test_extract_json_reads_embedded_json() -> None:
    parsed = _extract_json('Here is your result:\n{"subject": "Hi", "body": "Hello"}')

    assert parsed == {"subject": "Hi", "body": "Hello"}


def test_extract_json_rejects_empty_text() -> None:
    with pytest.raises(ValueError, match="empty response"):
        _extract_json("   ")


def test_extract_json_rejects_missing_json() -> None:
    with pytest.raises(ValueError, match="did not contain valid JSON"):
        _extract_json("No JSON here")


def test_normalize_text_replaces_unicode_punctuation_and_spacing() -> None:
    normalized = _normalize_text("Hello\u2014world\u2026  \n\n\nLet's\u00a0go\u2011now")

    assert normalized == "Hello-world...  \n\nLet's go-now"


def test_chat_message_to_text_handles_string_and_list_shapes() -> None:
    assert _chat_message_to_text(SimpleNamespace(content="hello")) == "hello"
    assert _chat_message_to_text(
        SimpleNamespace(content=[{"text": "hello"}, {"content": "world"}])
    ) == "hello\nworld"


def test_generate_email_uses_openai_without_reasoning_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class FakeResponses:
        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(output_text='{"subject": "Hello", "body": "World"}')

    class FakeOpenAI:
        def __init__(self, api_key: str) -> None:
            captured["api_key"] = api_key
            self.responses = FakeResponses()

    monkeypatch.setattr(
        "email_generator.core.get_settings",
        lambda: SimpleNamespace(
            provider="openai",
            api_key="key-123",
            model="gpt-5-mini",
            reasoning_effort="none",
            max_output_tokens=800,
            base_url=None,
        ),
    )
    monkeypatch.setattr("email_generator.core.OpenAI", FakeOpenAI)

    result = generate_email(
        EmailRequest(purpose="Follow up", tone="Warm", context="Share next steps")
    )

    assert result.subject == "Hello"
    assert result.body == "World"
    assert result.model == "gpt-5-mini"
    assert captured["api_key"] == "key-123"
    assert captured["model"] == "gpt-5-mini"
    assert captured["max_output_tokens"] == 800
    assert "reasoning" not in captured


def test_generate_email_includes_reasoning_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class FakeResponses:
        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(output_text='{"subject": "Hello", "body": "World"}')

    class FakeOpenAI:
        def __init__(self, api_key: str) -> None:
            self.responses = FakeResponses()

    monkeypatch.setattr(
        "email_generator.core.get_settings",
        lambda: SimpleNamespace(
            provider="openai",
            api_key="key-123",
            model="gpt-5",
            reasoning_effort="medium",
            max_output_tokens=500,
            base_url=None,
        ),
    )
    monkeypatch.setattr("email_generator.core.OpenAI", FakeOpenAI)

    generate_email(EmailRequest(purpose="Intro", tone="Formal", context="New client outreach"))

    assert captured["max_output_tokens"] == 500
    assert captured["reasoning"] == {"effort": "medium"}


def test_generate_email_passes_base_url_for_openrouter(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class FakeChatCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            message = SimpleNamespace(content='{"subject": "Hello", "body": "World"}')
            choice = SimpleNamespace(message=message)
            return SimpleNamespace(choices=[choice])

    class FakeOpenAI:
        def __init__(self, **kwargs) -> None:
            captured.update(kwargs)
            self.chat = SimpleNamespace(completions=FakeChatCompletions())

    monkeypatch.setattr(
        "email_generator.core.get_settings",
        lambda: SimpleNamespace(
            provider="openrouter",
            api_key="router-key",
            model="openrouter/free",
            reasoning_effort="none",
            max_output_tokens=250,
            base_url="https://openrouter.ai/api/v1",
        ),
    )
    monkeypatch.setattr("email_generator.core.OpenAI", FakeOpenAI)

    generate_email(EmailRequest(purpose="Intro", tone="Formal", context="New client outreach"))

    assert captured["api_key"] == "router-key"
    assert captured["base_url"] == "https://openrouter.ai/api/v1"
    assert captured["max_tokens"] == 250


def test_generate_email_normalizes_output(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponses:
        def create(self, **kwargs):
            return SimpleNamespace(output_text='{"subject": "Hello\\u2014World", "body": "Use e\\u2011sign\\u2026"}')

    class FakeOpenAI:
        def __init__(self, api_key: str) -> None:
            self.responses = FakeResponses()

    monkeypatch.setattr(
        "email_generator.core.get_settings",
        lambda: SimpleNamespace(
            provider="openai",
            api_key="key-123",
            model="gpt-5-mini",
            reasoning_effort="none",
            max_output_tokens=800,
            base_url=None,
        ),
    )
    monkeypatch.setattr("email_generator.core.OpenAI", FakeOpenAI)

    result = generate_email(EmailRequest(purpose="Follow up", tone="Warm", context="Share next steps"))

    assert result.subject == "Hello-World"
    assert result.body == "Use e-sign..."


def test_generate_email_rejects_missing_subject_or_body(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponses:
        def create(self, **kwargs):
            return SimpleNamespace(output_text='{"subject": "", "body": "World"}')

    class FakeOpenAI:
        def __init__(self, api_key: str) -> None:
            self.responses = FakeResponses()

    monkeypatch.setattr(
        "email_generator.core.get_settings",
        lambda: SimpleNamespace(
            provider="openai",
            api_key="key-123",
            model="gpt-5-mini",
            reasoning_effort="none",
            max_output_tokens=800,
            base_url=None,
        ),
    )
    monkeypatch.setattr("email_generator.core.OpenAI", FakeOpenAI)

    with pytest.raises(ValueError, match="missing a subject or body"):
        generate_email(EmailRequest(purpose="Follow up", tone="Warm", context="Share next steps"))


def test_generate_with_openrouter_parses_chat_completion() -> None:
    class FakeChatCompletions:
        def create(self, **kwargs):
            message = SimpleNamespace(content='{"subject": "Hello", "body": "World"}')
            choice = SimpleNamespace(message=message)
            return SimpleNamespace(choices=[choice])

    client = SimpleNamespace(chat=SimpleNamespace(completions=FakeChatCompletions()))

    parsed = _generate_with_openrouter(
        client=client,
        request=EmailRequest(purpose="Intro", tone="Warm", context="Context"),
        model="openrouter/free",
        max_output_tokens=120,
    )

    assert parsed == {"subject": "Hello", "body": "World"}


def test_generate_with_openrouter_retries_after_empty_response() -> None:
    call_count = {"value": 0}

    class FakeChatCompletions:
        def create(self, **kwargs):
            call_count["value"] += 1
            if call_count["value"] == 1:
                message = SimpleNamespace(content="")
            else:
                message = SimpleNamespace(content='{"subject": "Hello", "body": "World"}')
            choice = SimpleNamespace(message=message)
            return SimpleNamespace(choices=[choice])

    client = SimpleNamespace(chat=SimpleNamespace(completions=FakeChatCompletions()))

    parsed = _generate_with_openrouter(
        client=client,
        request=EmailRequest(purpose="Intro", tone="Warm", context="Context"),
        model="openrouter/free",
        max_output_tokens=120,
    )

    assert call_count["value"] == 2
    assert parsed == {"subject": "Hello", "body": "World"}


def test_generate_with_openai_parses_response_output_text() -> None:
    class FakeResponses:
        def create(self, **kwargs):
            return SimpleNamespace(output_text='{"subject": "Hello", "body": "World"}')

    client = SimpleNamespace(responses=FakeResponses())

    parsed = _generate_with_openai(
        client=client,
        request=EmailRequest(purpose="Intro", tone="Warm", context="Context"),
        model="gpt-5-mini",
        reasoning_effort="none",
        max_output_tokens=120,
    )

    assert parsed == {"subject": "Hello", "body": "World"}
