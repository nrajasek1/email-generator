from __future__ import annotations

from fastapi import APIRouter, HTTPException

from email_generator.core import generate_email
from email_generator.schemas import EmailRequest, EmailResponse

router = APIRouter()


@router.post("/api/generate", response_model=EmailResponse)
def generate_from_api(payload: EmailRequest) -> EmailResponse:
    try:
        return generate_email(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
