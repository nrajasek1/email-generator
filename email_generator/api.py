from __future__ import annotations

from fastapi import APIRouter

from email_generator.core import generate_email
from email_generator.schemas import EmailRequest, EmailResponse, ErrorEnvelope

router = APIRouter()


@router.post(
    "/api/generate",
    response_model=EmailResponse,
    summary="Generate a structured email",
    description=(
        "Generate a validated email subject and body from a purpose, tone, "
        "and context. The response is schema-validated end-to-end; extra "
        "fields are rejected and partial output never reaches the caller. "
        "See `AGENT.md` for the full contract."
    ),
    responses={
        400: {
            "model": ErrorEnvelope,
            "description": (
                "Request body failed input validation "
                "(envelope code: `input_invalid`)."
            ),
        },
        500: {
            "model": ErrorEnvelope,
            "description": (
                "Unexpected server-side failure "
                "(envelope code: `internal_error`)."
            ),
        },
        502: {
            "model": ErrorEnvelope,
            "description": (
                "Upstream LLM output failed the contract after retries "
                "(envelope code: `output_contract`)."
            ),
        },
    },
    tags=["generation"],
)
def generate_from_api(payload: EmailRequest) -> EmailResponse:
    return generate_email(payload)
