from __future__ import annotations

from types import SimpleNamespace

import pytest

from email_generator import cli


def test_build_parser_requires_all_arguments() -> None:
    parser = cli.build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_main_prints_generated_email(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(
        "email_generator.cli.generate_email",
        lambda request: SimpleNamespace(subject="Test Subject", body="Test Body"),
    )
    monkeypatch.setattr(
        "argparse.ArgumentParser.parse_args",
        lambda self: SimpleNamespace(
            purpose="Follow up",
            tone="Warm",
            context="Share next steps",
        ),
    )

    cli.main()

    output = capsys.readouterr().out
    assert "Subject:" in output
    assert "Test Subject" in output
    assert "Body:" in output
    assert "Test Body" in output
