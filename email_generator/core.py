from __future__ import annotations

import re
import unicodedata

from openai import OpenAI
from pydantic import ValidationError

from email_generator.config import get_settings
from email_generator.errors import OutputContractError
from email_generator.providers import _generate_with_openai, _generate_with_openrouter
from email_generator.schemas import EmailRequest, EmailResponse, LLMRawOutput


def _normalize_text(text: str) -> str:
    replacements = {
        "‘": "'",
        "’": "'",
        "“": '"',
        "”": '"',
        "–": "-",
        "—": "-",
        "―": "-",
        "…": "...",
        " ": " ",
        "​": "",
        "‑": "-",
        "•": "-",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)

    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def generate_email(request: EmailRequest) -> EmailResponse:
    settings = get_settings()
    client_kwargs = {"api_key": settings.api_key}
    if settings.base_url:
        client_kwargs["base_url"] = settings.base_url
    client = OpenAI(**client_kwargs)

    if settings.provider == "openrouter":
        parsed = _generate_with_openrouter(
            client=client,
            request=request,
            model=settings.model,
            max_output_tokens=settings.max_output_tokens,
        )
    else:
        parsed = _generate_with_openai(
            client=client,
            request=request,
            model=settings.model,
            reasoning_effort=settings.reasoning_effort,
            max_output_tokens=settings.max_output_tokens,
        )

    try:
        raw = LLMRawOutput.model_validate(parsed)
    except ValidationError as exc:
        raise OutputContractError(f"Model output did not match the required contract: {exc}") from exc

    subject = _normalize_text(raw.subject)
    body = _normalize_text(raw.body)

    try:
        return EmailResponse(subject=subject, body=body, model=settings.model)
    except ValidationError as exc:
        raise OutputContractError(f"Model output failed post-normalization validation: {exc}") from exc
