from __future__ import annotations

import logging
import re
import unicodedata
from typing import Any, Dict

from openai import OpenAI
from pydantic import ValidationError

from email_generator.config import Settings, get_settings
from email_generator.errors import OutputContractError
from email_generator.providers import _generate_with_openai, _generate_with_openrouter
from email_generator.schemas import EmailRequest, EmailResponse, LLMRawOutput

MAX_ATTEMPTS = 3
logger = logging.getLogger(__name__)


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


def _call_provider(client: OpenAI, settings: Settings, request: EmailRequest) -> Dict[str, Any]:
    if settings.provider == "openrouter":
        return _generate_with_openrouter(
            client=client,
            request=request,
            model=settings.model,
            max_output_tokens=settings.max_output_tokens,
        )
    return _generate_with_openai(
        client=client,
        request=request,
        model=settings.model,
        reasoning_effort=settings.reasoning_effort,
        max_output_tokens=settings.max_output_tokens,
    )


def _build_response(parsed: Dict[str, Any], model: str) -> EmailResponse:
    try:
        raw = LLMRawOutput.model_validate(parsed)
    except ValidationError as exc:
        raise OutputContractError(
            f"Model output did not match the required contract: {exc}"
        ) from exc

    subject = _normalize_text(raw.subject)
    body = _normalize_text(raw.body)

    try:
        return EmailResponse(subject=subject, body=body, model=model)
    except ValidationError as exc:
        raise OutputContractError(
            f"Model output failed post-normalization validation: {exc}"
        ) from exc


def generate_email(request: EmailRequest) -> EmailResponse:
    settings = get_settings()
    client_kwargs = {"api_key": settings.api_key}
    if settings.base_url:
        client_kwargs["base_url"] = settings.base_url
    client = OpenAI(**client_kwargs)

    last_error: OutputContractError | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            parsed = _call_provider(client, settings, request)
            response = _build_response(parsed, settings.model)
        except OutputContractError as exc:
            last_error = exc
            if attempt < MAX_ATTEMPTS:
                logger.warning(
                    "retrying after output contract error (attempt=%d/%d provider=%s model=%s): %s",
                    attempt,
                    MAX_ATTEMPTS,
                    settings.provider,
                    settings.model,
                    exc.message,
                )
            continue

        logger.info(
            "generated email (provider=%s model=%s attempts=%d)",
            settings.provider,
            settings.model,
            attempt,
        )
        return response

    assert last_error is not None
    logger.error(
        "output contract failed after %d attempts (provider=%s model=%s): %s",
        MAX_ATTEMPTS,
        settings.provider,
        settings.model,
        last_error.message,
    )
    raise OutputContractError(
        f"Model output did not satisfy the contract after {MAX_ATTEMPTS} attempts: {last_error.message}"
    ) from last_error
