from __future__ import annotations

import logging
from types import SimpleNamespace

import pytest

from email_generator.core import _normalize_text, generate_email
from email_generator.errors import OutputContractError
from email_generator.prompt import build_user_prompt
from email_generator.providers import (
    _chat_message_to_text,
    _extract_json,
    _generate_with_openai,
    _generate_with_openrouter,
)
from email_generator.schemas import EmailRequest


def test_build_user_prompt_includes_user_inputs() -> None:
    prompt = build_user_prompt(
        EmailRequest(purpose="Follow up after meeting", tone="Friendly", context="Mention timeline.")
    )

    assert "Purpose: Follow up after meeting" in prompt
    assert "Tone: Friendly" in prompt
    assert "Context: Mention timeline." in prompt


def test_build_user_prompt_specifies_json_output_shape() -> None:
    prompt = build_user_prompt(
        EmailRequest(purpose="P", tone="T", context="C")
    )

    assert "subject" in prompt
    assert "body" in prompt


def test_system_instructions_forbid_hallucination_and_markdown() -> None:
    from email_generator.prompt import SYSTEM_INSTRUCTIONS

    assert "Do not invent" in SYSTEM_INSTRUCTIONS
    assert "Do not return markdown" in SYSTEM_INSTRUCTIONS


def test_extract_json_reads_direct_json() -> None:
    parsed = _extract_json('{"subject": "Hi", "body": "Hello"}')

    assert parsed == {"subject": "Hi", "body": "Hello"}


def test_extract_json_reads_embedded_json() -> None:
    parsed = _extract_json('Here is your result:\n{"subject": "Hi", "body": "Hello"}')

    assert parsed == {"subject": "Hi", "body": "Hello"}


def test_extract_json_rejects_empty_text() -> None:
    with pytest.raises(OutputContractError, match="empty response"):
        _extract_json("   ")


def test_extract_json_rejects_missing_json() -> None:
    with pytest.raises(OutputContractError, match="did not contain valid JSON"):
        _extract_json("No JSON here")


def test_extract_json_rejects_malformed_embedded_json() -> None:
    with pytest.raises(OutputContractError, match="malformed JSON"):
        _extract_json('prefix {"key":} suffix')


def test_normalize_text_replaces_unicode_punctuation_and_spacing() -> None:
    normalized = _normalize_text("Hello—world…  \n\n\nLet's go‑now")

    assert normalized == "Hello-world...  \n\nLet's go-now"


def test_chat_message_to_text_handles_string_and_list_shapes() -> None:
    assert _chat_message_to_text(SimpleNamespace(content="hello")) == "hello"
    assert _chat_message_to_text(
        SimpleNamespace(content=[{"text": "hello"}, {"content": "world"}])
    ) == "hello\nworld"


def test_generate_email_uses_openai_without_reasoning_when_disabled(openai_settings, patch_openai) -> None:
    captured = patch_openai(openai_settings, '{"subject": "Hello", "body": "World"}')

    result = generate_email(EmailRequest(purpose="Follow up", tone="Warm", context="Share next steps"))

    assert result.subject == "Hello"
    assert result.body == "World"
    assert result.model == "gpt-5-mini"
    assert captured["api_key"] == "key-123"
    assert captured["model"] == "gpt-5-mini"
    assert captured["max_output_tokens"] == 800
    assert "reasoning" not in captured


def test_generate_email_includes_reasoning_when_enabled(openai_settings, patch_openai) -> None:
    openai_settings.model = "gpt-5"
    openai_settings.reasoning_effort = "medium"
    openai_settings.max_output_tokens = 500
    captured = patch_openai(openai_settings, '{"subject": "Hello", "body": "World"}')

    generate_email(EmailRequest(purpose="Intro", tone="Formal", context="New client outreach"))

    assert captured["max_output_tokens"] == 500
    assert captured["reasoning"] == {"effort": "medium"}


def test_generate_email_passes_base_url_for_openrouter(openrouter_settings, patch_openrouter) -> None:
    captured = patch_openrouter(openrouter_settings, '{"subject": "Hello", "body": "World"}')

    generate_email(EmailRequest(purpose="Intro", tone="Formal", context="New client outreach"))

    assert captured["api_key"] == "router-key"
    assert captured["base_url"] == "https://openrouter.ai/api/v1"
    assert captured["max_tokens"] == 250


def test_generate_email_normalizes_output(openai_settings, patch_openai) -> None:
    patch_openai(openai_settings, '{"subject": "Hello\\u2014World", "body": "Use e\\u2011sign\\u2026"}')

    result = generate_email(EmailRequest(purpose="Follow up", tone="Warm", context="Share next steps"))

    assert result.subject == "Hello-World"
    assert result.body == "Use e-sign..."


def test_generate_email_rejects_empty_subject_in_raw_output(openai_settings, patch_openai) -> None:
    patch_openai(openai_settings, '{"subject": "", "body": "World"}')

    with pytest.raises(OutputContractError, match="did not match the required contract"):
        generate_email(EmailRequest(purpose="P", tone="T", context="C"))


def test_generate_email_rejects_extra_fields_in_raw_output(openai_settings, patch_openai) -> None:
    patch_openai(openai_settings, '{"subject": "Hello", "body": "World", "rogue": "value"}')

    with pytest.raises(OutputContractError, match="did not match the required contract"):
        generate_email(EmailRequest(purpose="P", tone="T", context="C"))


def test_generate_email_rejects_post_normalization_empty(openai_settings, patch_openai) -> None:
    patch_openai(openai_settings, '{"subject": "Hello", "body": "\\u4e2d\\u6587"}')

    with pytest.raises(OutputContractError, match="failed post-normalization validation"):
        generate_email(EmailRequest(purpose="P", tone="T", context="C"))


def test_generate_email_retries_on_output_contract_error(monkeypatch: pytest.MonkeyPatch) -> None:
    call_count = {"value": 0}

    class FakeResponses:
        def create(self, **kwargs):
            call_count["value"] += 1
            text = "" if call_count["value"] == 1 else '{"subject": "Hello", "body": "World"}'
            return SimpleNamespace(output_text=text)

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

    result = generate_email(EmailRequest(purpose="P", tone="T", context="C"))

    assert result.subject == "Hello"
    assert call_count["value"] == 2


def test_generate_email_fails_after_max_attempts(monkeypatch: pytest.MonkeyPatch) -> None:
    call_count = {"value": 0}

    class FakeResponses:
        def create(self, **kwargs):
            call_count["value"] += 1
            return SimpleNamespace(output_text="")

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

    with pytest.raises(OutputContractError, match="after 3 attempts"):
        generate_email(EmailRequest(purpose="P", tone="T", context="C"))

    assert call_count["value"] == 3


def test_generate_email_emits_info_log_on_success(openai_settings, patch_openai, caplog: pytest.LogCaptureFixture) -> None:
    patch_openai(openai_settings, '{"subject": "Hi", "body": "There"}')
    caplog.set_level(logging.INFO, logger="email_generator.core")

    generate_email(EmailRequest(purpose="P", tone="T", context="C"))

    info_messages = [r.getMessage() for r in caplog.records if r.levelname == "INFO"]
    assert any("generated email" in msg and "model=gpt-5-mini" in msg for msg in info_messages)


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


def test_generate_with_openai_raises_provider_error_on_client_failure() -> None:
    from email_generator.errors import ProviderError

    class FailingResponses:
        def create(self, **kwargs):
            raise RuntimeError("Network timeout")

    client = SimpleNamespace(responses=FailingResponses())

    with pytest.raises(ProviderError, match="OpenAI client error"):
        _generate_with_openai(
            client=client,
            request=EmailRequest(purpose="Intro", tone="Warm", context="Context"),
            model="gpt-5-mini",
            reasoning_effort="none",
            max_output_tokens=120,
        )


def test_generate_with_openrouter_raises_provider_error_on_client_failure() -> None:
    from email_generator.errors import ProviderError

    class FailingChatCompletions:
        def create(self, **kwargs):
            raise RuntimeError("API rate limit exceeded")

    client = SimpleNamespace(chat=SimpleNamespace(completions=FailingChatCompletions()))

    with pytest.raises(ProviderError, match="OpenRouter client error"):
        _generate_with_openrouter(
            client=client,
            request=EmailRequest(purpose="Intro", tone="Warm", context="Context"),
            model="openrouter/free",
            max_output_tokens=120,
        )


def test_extract_json_uses_non_greedy_regex_for_embedded_json() -> None:
    # Ensure non-greedy matching stops at first closing brace
    text = 'prefix {"subject": "Hello", "body": "World"} suffix {"extra": "ignored"}'
    parsed = _extract_json(text)
    
    # Should extract first JSON object only
    assert parsed == {"subject": "Hello", "body": "World"}
    assert "ignored" not in str(parsed)


def test_generate_email_never_logs_api_key(openai_settings, patch_openai, caplog: pytest.LogCaptureFixture) -> None:
    """Verify that API keys are never exposed in log output."""
    patch_openai(openai_settings, '{"subject": "Hi", "body": "There"}')
    caplog.set_level(logging.DEBUG)  # Capture all log levels

    generate_email(EmailRequest(purpose="P", tone="T", context="C"))

    # Reconstruct full log output
    full_log = "\n".join(r.getMessage() for r in caplog.records)
    
    # Ensure no API key is logged
    assert "key-123" not in full_log
    assert "api_key" not in full_log.lower()
    # But provider and model should be logged
    assert "openai" in full_log
    assert "gpt-5-mini" in full_log
