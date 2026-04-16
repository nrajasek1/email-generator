from __future__ import annotations

import runpy


def test_module_entrypoint_calls_cli_main(monkeypatch) -> None:
    called = {"value": False}

    monkeypatch.setattr(
        "email_generator.cli.main",
        lambda: called.__setitem__("value", True),
    )

    runpy.run_module("email_generator.__main__", run_name="__main__")

    assert called["value"] is True
