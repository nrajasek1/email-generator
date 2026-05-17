from __future__ import annotations

import contextlib
import io
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from email_generator import cli
from email_generator.schemas import EmailRequest, EmailResponse
from email_generator.web import app


def test_entry_points_funnel_to_same_core(monkeypatch: pytest.MonkeyPatch) -> None:
    """API, Web form, and CLI must each invoke generate_email with an
    equivalent EmailRequest and surface the same EmailResponse content.

    This is the architecture invariant from AGENT.md: one core, three
    entry points, same structured output for the same input.
    """

    captured_requests: list[EmailRequest] = []
    fixed = EmailResponse(subject="The Subject", body="The Body", model="m")

    def fake_generate(request: EmailRequest) -> EmailResponse:
        captured_requests.append(request)
        return fixed

    monkeypatch.setattr("email_generator.api.generate_email", fake_generate)
    monkeypatch.setattr("email_generator.cli.generate_email", fake_generate)
    monkeypatch.setattr("email_generator.web.generate_email", fake_generate)

    payload = {"purpose": "P", "tone": "T", "context": "C"}

    client = TestClient(app)
    api_response = client.post("/api/generate", json=payload)
    form_response = client.post("/", data=payload)

    monkeypatch.setattr(
        "argparse.ArgumentParser.parse_args",
        lambda self: SimpleNamespace(**payload),
    )
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        cli.main()
    cli_output = buf.getvalue()

    # All three entry points constructed an equivalent EmailRequest.
    assert len(captured_requests) == 3
    for r in captured_requests:
        assert r.purpose == "P"
        assert r.tone == "T"
        assert r.context == "C"

    # All three surfaced equivalent response content.
    assert api_response.status_code == 200
    assert api_response.json() == {
        "subject": "The Subject",
        "body": "The Body",
        "model": "m",
    }

    assert form_response.status_code == 200
    assert "The Subject" in form_response.text
    assert "The Body" in form_response.text

    assert "The Subject" in cli_output
    assert "The Body" in cli_output
