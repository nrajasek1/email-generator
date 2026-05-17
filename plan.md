# Project Plan

Living checklist for in-flight work. The contract this project must satisfy
lives in `AGENT.md`. Setup and run instructions live in `README.md`. This
file tracks what is being done now, in what order.

## Current Phase: Smart → Structured Migration

Bring the implementation in line with `AGENT.md`: trusted, predictable, and
system-ready output across all three entry points.

### Cleanup
- [x] Remove stale `/templates/` and `/main.py`
- [ ] Deduplicate prompt rules between `SYSTEM_INSTRUCTIONS` and user prompt
- [ ] Factor repeated env-var helpers in `config.py`

### Restructure (flat layout)
- [x] Rename `generator.py` → `core.py`
- [x] Extract `prompt.py`, `providers.py`, `errors.py`
- [x] Split `web.py` into `api.py` (JSON) and `web.py` (HTML form)

### Trusted (§1)
- [x] Validate raw LLM output via `LLMRawOutput` (extra="forbid")
- [x] Enforce `min_length` on `EmailResponse` fields
- [x] Tests: malformed, partial, extra-field LLM output rejected

### System-Ready (§3)
- [x] Typed errors: `EmailGeneratorError`, `InputValidationError`, `OutputContractError`, `ProviderError`
- [x] Nested error envelope `{error: {code, message}}` on API and Web
- [x] Structured logging per request (provider, model, attempts, outcome)
- [x] Unify retry policy across providers (single MAX_ATTEMPTS in core)

### Verification
- [x] Bump enforced coverage to 95% in `pyproject.toml` and `README.md`
- [x] Add entry-point equivalence test (`tests/test_equivalence.py`)
- [x] Consolidate test mocks into conftest fixtures
- [x] Loosen brittle prompt-phrase and UI-string asserts to behavior checks

### Done
- [x] Author `AGENT.md`

## Out of Scope
- Docker, deployment
- UI features (presets, copy buttons)
- Auth, rate limiting
- Additional providers

## Remaining (deferred)
- Prompt rule deduplication between `SYSTEM_INSTRUCTIONS` and `build_user_prompt`. Skipped this round because rewording the prompt is a behavior change for the live LLM that should be validated separately.
- Env-var helper factoring in `config.py`. Cosmetic; left for a follow-up.
- Provider-specific resilience around real upstream failures (`ProviderError` is defined but not yet raised). Add when wiring real network-failure paths.
