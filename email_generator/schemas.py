from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class EmailRequest(BaseModel):
    purpose: str = Field(
        ...,
        min_length=1,
        description="Why the email is being written. One short sentence.",
        examples=["Follow up after a product demo"],
    )
    tone: str = Field(
        ...,
        min_length=1,
        description="Desired writing tone. A few descriptive words.",
        examples=["Professional and warm"],
    )
    context: str = Field(
        ...,
        min_length=1,
        description=(
            "Supporting details the email should reference. Treated as the "
            "source of truth — claims in the output must trace back to it."
        ),
        examples=[
            "The prospect asked for pricing details and onboarding next steps."
        ],
    )


class LLMRawOutput(BaseModel):
    """Strict schema for the parsed JSON returned by the LLM.

    Rejects extra fields so undocumented keys never reach a caller.
    """

    model_config = ConfigDict(extra="forbid")

    subject: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)


class EmailResponse(BaseModel):
    subject: str = Field(
        ...,
        min_length=1,
        description="Generated email subject line, plain text.",
        examples=["Thanks for your time today"],
    )
    body: str = Field(
        ...,
        min_length=1,
        description="Generated email body, plain text only (no HTML or markdown).",
        examples=["Here are the pricing details and onboarding next steps we discussed..."],
    )
    model: str = Field(
        ...,
        min_length=1,
        description="Identifier of the LLM model that produced the output.",
        examples=["openrouter/free"],
    )


class ErrorDetail(BaseModel):
    """Inner payload of the standard error envelope."""

    code: str = Field(
        ...,
        description=(
            "Machine-readable error code. One of `input_invalid`, "
            "`output_contract`, `provider_error`, `internal_error`."
        ),
        examples=["input_invalid"],
    )
    message: str = Field(
        ...,
        description="Human-readable explanation of the failure.",
        examples=["Request body did not match the input contract."],
    )


class ErrorEnvelope(BaseModel):
    """Standard error response shape for the JSON API."""

    error: ErrorDetail
