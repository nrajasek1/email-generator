from __future__ import annotations

from fastapi.testclient import TestClient

from email_generator.errors import OutputContractError
from email_generator.web import app


client = TestClient(app)


def test_index_page_loads() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "Email Generator" in response.text


def test_form_submission_renders_result(monkeypatch) -> None:
    monkeypatch.setattr(
        "email_generator.web.generate_email",
        lambda request: type(
            "Result",
            (),
            {"subject": "Thanks for your time", "body": "Here are the next steps.", "model": "gpt-5-mini"},
        )(),
    )

    response = client.post(
        "/",
        data={
            "purpose": "Follow up",
            "tone": "Warm",
            "context": "Share next steps",
        },
    )

    assert response.status_code == 200
    assert "Thanks for your time" in response.text
    assert "Here are the next steps." in response.text


def test_form_submission_renders_typed_error_with_status_code(monkeypatch) -> None:
    monkeypatch.setattr(
        "email_generator.web.generate_email",
        lambda request: (_ for _ in ()).throw(OutputContractError("model misbehaved")),
    )

    response = client.post(
        "/",
        data={"purpose": "Follow up", "tone": "Warm", "context": "Share next steps"},
    )

    assert response.status_code == 502
    assert "model misbehaved" in response.text


def test_form_submission_renders_error(monkeypatch) -> None:
    monkeypatch.setattr("email_generator.web.generate_email", lambda request: (_ for _ in ()).throw(ValueError("boom")))

    response = client.post(
        "/",
        data={
            "purpose": "Follow up",
            "tone": "Warm",
            "context": "Share next steps",
        },
    )

    assert response.status_code == 400
    assert "boom" in response.text


def test_api_generate_returns_json(monkeypatch) -> None:
    monkeypatch.setattr(
        "email_generator.api.generate_email",
        lambda request: {"subject": "Hello", "body": "Body text", "model": "gpt-5-mini"},
    )

    response = client.post(
        "/api/generate",
        json={
            "purpose": "Follow up",
            "tone": "Warm",
            "context": "Share next steps",
        },
    )

    assert response.status_code == 200
    assert response.json()["subject"] == "Hello"


def test_api_generate_returns_typed_error_envelope(monkeypatch) -> None:
    monkeypatch.setattr(
        "email_generator.api.generate_email",
        lambda request: (_ for _ in ()).throw(OutputContractError("model misbehaved")),
    )

    response = client.post(
        "/api/generate",
        json={
            "purpose": "Follow up",
            "tone": "Warm",
            "context": "Share next steps",
        },
    )

    assert response.status_code == 502
    assert response.json() == {
        "error": {"code": "output_contract", "message": "model misbehaved"}
    }


def test_api_generate_returns_input_invalid_envelope_for_missing_field() -> None:
    response = client.post("/api/generate", json={"purpose": "x", "tone": "y"})

    assert response.status_code == 400
    body = response.json()
    assert body["error"]["code"] == "input_invalid"
