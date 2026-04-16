from __future__ import annotations

import json
import re
import unicodedata
from typing import Any, Dict

from openai import OpenAI

from email_generator.config import get_settings
from email_generator.schemas import EmailRequest, EmailResponse

SYSTEM_INSTRUCTIONS = """
You generate plain-text emails for business or professional communication.
Return only valid JSON with exactly two string fields:
- "subject"
- "body"

Rules:
- Do not return markdown.
- Do not include HTML.
- Keep the body plain text only.
- Do not use markdown formatting such as headings, bold markers, bullets with asterisks, or fenced blocks.
- Make the subject concise and relevant.
- Make the email clear, natural, and ready to send.
- Keep the email concise by default.
- Avoid unnecessary filler, generic enthusiasm, or long lists unless the context calls for them.
- Use ASCII-friendly punctuation only.
- Do not invent facts, pricing, timelines, links, names, attachments, or commitments that were not provided.
- Treat the provided context as the source of truth for factual content and requested direction.
- Every concrete claim in the email must be supported by the provided context.
- If the context is sparse, write a shorter and more general email instead of filling in details.
- Follow the user's context literally and preserve the direction of the request.
- Do not reverse roles or ask the recipient for information that the sender is supposed to provide.
- If details are missing, stay general or use neutral placeholders instead of making specifics up.
- Match the requested tone closely.
- Avoid generic openings like "Hope this email finds you well" unless the context strongly calls for them.
- Prefer specific, useful next-step language over vague closers like "Looking forward to your thoughts."
- When the context implies the sender should share information, write the email as delivering or summarizing that information.
- When the context names topics the sender should cover, make those topics visibly present in the body.
- Do not introduce meeting references, scheduling language, deadlines, attachments, links, or deliverables unless the context explicitly supports them.
- Prefer concrete but non-fabricated wording.
- Do not add placeholder sections such as [Your Name], [Company], [Phone], [Email], or [Calendly Link] unless the context explicitly asks for placeholders.
- Avoid listing example pricing tiers, links, attachments, or deliverables unless they were actually mentioned in the context.
- Make the draft sound like a realistic sendable email, not a template skeleton.
- Do not say something is attached, included below, linked, or prepared unless the context explicitly says so.
- If pricing details are requested but not provided in the context, refer to them in general terms instead of inventing a breakdown.
- If the context asks for next steps but does not specify them, keep the next step modest and generic rather than fabricating a process.
""".strip()


def build_user_prompt(request: EmailRequest) -> str:
    return (
        "Generate a plain-text email from the details below.\n\n"
        f"Purpose: {request.purpose}\n"
        f"Tone: {request.tone}\n"
        f"Context: {request.context}\n\n"
        "Write from the sender's perspective based on the purpose and context.\n"
        "Only use facts present in the context. If a detail is not given, keep it general.\n"
        "Treat the context as the source of truth for concrete details and requested direction.\n"
        "Every specific claim in the email must be traceable to the context.\n"
        "Do not ask the recipient for information the sender is expected to provide.\n\n"
        "Avoid generic openings and vague closers.\n"
        "End with a clear, appropriate next step when possible.\n\n"
        "If the context is sparse, write a shorter and more general email instead of adding specifics.\n"
        "If the context names topics to cover, explicitly address those topics in the body.\n"
        "Do not add template placeholders unless the context explicitly asks for them.\n"
        "Do not make up pricing tiers, links, attachments, or named assets.\n"
        "Write a realistic sendable draft, not a generic template shell.\n\n"
        "Do not use markdown headings, bold markers, or markdown lists.\n"
        "Do not claim something is attached, included below, linked, or already prepared unless the context says so.\n"
        "If exact pricing details are not given, keep the pricing reference general.\n\n"
        'Return JSON in this shape: {"subject":"...", "body":"..."}'
    )


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


def _normalize_text(text: str) -> str:
    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u2015": "-",
        "\u2026": "...",
        "\u00a0": " ",
        "\u200b": "",
        "\u2011": "-",
        "\u2022": "-",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)

    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


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
    subject = _normalize_text(str(parsed.get("subject", "")))
    body = _normalize_text(str(parsed.get("body", "")))

    if not subject or not body:
        raise ValueError("The model response was missing a subject or body.")

    return EmailResponse(subject=subject, body=body, model=settings.model)
