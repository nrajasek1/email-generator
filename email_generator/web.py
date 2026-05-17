from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from email_generator.api import router as api_router
from email_generator.core import generate_email
from email_generator.errors import EmailGeneratorError, InputValidationError
from email_generator.schemas import EmailRequest, EmailResponse

PACKAGE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(PACKAGE_DIR / "templates"))
EMPTY_FORM_DATA = {"purpose": "", "tone": "", "context": ""}

app = FastAPI(title="Email Generator")
app.include_router(api_router)


def _error_envelope(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


@app.exception_handler(EmailGeneratorError)
async def _handle_email_generator_error(request: Request, exc: EmailGeneratorError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_envelope(exc.code, exc.message),
    )


@app.exception_handler(RequestValidationError)
async def _handle_request_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=InputValidationError.status_code,
        content=_error_envelope(InputValidationError.code, "Request body did not match the input contract."),
    )


def _render_page(
    request: Request,
    *,
    result: EmailResponse | None = None,
    error: str | None = None,
    form_data: dict[str, str] | None = None,
    status_code: int = 200,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "result": result,
            "error": error,
            "form_data": form_data or EMPTY_FORM_DATA,
        },
        status_code=status_code,
    )


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return _render_page(request)


@app.post("/", response_class=HTMLResponse)
def generate_from_form(
    request: Request,
    purpose: str = Form(...),
    tone: str = Form(...),
    context: str = Form(...),
) -> HTMLResponse:
    form_data = {"purpose": purpose, "tone": tone, "context": context}
    try:
        result = generate_email(EmailRequest(**form_data))
        return _render_page(request, result=result, form_data=form_data)
    except EmailGeneratorError as exc:
        return _render_page(
            request,
            error=exc.message,
            form_data=form_data,
            status_code=exc.status_code,
        )
    except Exception as exc:
        return _render_page(
            request,
            error=str(exc),
            form_data=form_data,
            status_code=400,
        )
