from __future__ import annotations


class EmailGeneratorError(Exception):
    """Base class for typed errors raised by the email generator."""

    code: str = "internal_error"
    status_code: int = 500

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class InputValidationError(EmailGeneratorError):
    """The caller-supplied request did not satisfy the input contract."""

    code = "input_invalid"
    status_code = 400


class OutputContractError(EmailGeneratorError):
    """The LLM response did not satisfy the output contract."""

    code = "output_contract"
    status_code = 502


class ProviderError(EmailGeneratorError):
    """A call to the upstream LLM provider failed."""

    code = "provider_error"
    status_code = 502
