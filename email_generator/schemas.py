from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class EmailRequest(BaseModel):
    purpose: str = Field(..., min_length=1, description="Why the email is being written.")
    tone: str = Field(..., min_length=1, description="Desired writing tone.")
    context: str = Field(..., min_length=1, description="Supporting details for the email.")


class LLMRawOutput(BaseModel):
    """Strict schema for the parsed JSON returned by the LLM.

    Rejects extra fields so undocumented keys never reach a caller.
    """

    model_config = ConfigDict(extra="forbid")

    subject: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)


class EmailResponse(BaseModel):
    subject: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)
    model: str = Field(..., min_length=1)
