from __future__ import annotations

from fastapi import APIRouter

from email_generator.core import generate_email
from email_generator.schemas import EmailRequest, EmailResponse

router = APIRouter()


@router.post("/api/generate", response_model=EmailResponse)
def generate_from_api(payload: EmailRequest) -> EmailResponse:
    return generate_email(payload)
