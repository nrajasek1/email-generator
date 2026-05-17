from __future__ import annotations

import json
import re
from typing import Any, Dict

from openai import OpenAI

from email_generator.prompt import SYSTEM_INSTRUCTIONS, build_user_prompt
from email_generator.schemas import EmailRequest


def _extract_json(raw_text: str) -> Dict[str, Any]:
    raw_text = raw_text.strip()
    if not raw_text:
        raise ValueError("The model returned an empty response.")

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if not match:
            raise ValueError("The model response did not contain valid JSON.")
        return json.loads(match.group(0))


def _chat_message_to_text(message: Any) -> str:
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
                continue
            if isinstance(item, dict):
                text_value = item.get("text") or item.get("content") or ""
                if text_value:
                    parts.append(str(text_value))
                continue
            text_value = getattr(item, "text", "") or getattr(item, "content", "")
            if text_value:
                parts.append(str(text_value))
        return "\n".join(part for part in parts if part).strip()
    return str(content or "").strip()


def _generate_with_openrouter(client: OpenAI, request: EmailRequest, model: str, max_output_tokens: int) -> Dict[str, Any]:
    last_error: Exception | None = None
    for _ in range(3):
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTIONS},
                {"role": "user", "content": build_user_prompt(request)},
            ],
            max_tokens=max_output_tokens,
        )
        content = _chat_message_to_text(response.choices[0].message)
        try:
            return _extract_json(content)
        except ValueError as exc:
            last_error = exc

    raise ValueError("OpenRouter returned an unusable response after 3 attempts.") from last_error


def _generate_with_openai(client: OpenAI, request: EmailRequest, model: str, reasoning_effort: str, max_output_tokens: int) -> Dict[str, Any]:
    request_kwargs = {
        "model": model,
        "instructions": SYSTEM_INSTRUCTIONS,
        "input": build_user_prompt(request),
        "max_output_tokens": max_output_tokens,
    }
    if reasoning_effort.lower() != "none":
        request_kwargs["reasoning"] = {"effort": reasoning_effort}

    response = client.responses.create(**request_kwargs)
    return _extract_json(response.output_text)
