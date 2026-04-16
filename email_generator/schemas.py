from __future__ import annotations

from pydantic import BaseModel, Field


class EmailRequest(BaseModel):
    purpose: str = Field(..., min_length=1, description="Why the email is being written.")
    tone: str = Field(..., min_length=1, description="Desired writing tone.")
    context: str = Field(..., min_length=1, description="Supporting details for the email.")


class EmailResponse(BaseModel):
    subject: str
    body: str
    model: str
