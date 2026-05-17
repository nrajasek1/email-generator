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
- [ ] Rename `generator.py` → `core.py`
- [ ] Extract `prompt.py`, `providers.py`, `errors.py`
- [ ] Split `web.py` into `api.py` (JSON) and `web.py` (HTML form)

### Trusted (§1)
- [ ] Validate raw LLM output via `LLMRawOutput` (extra="forbid")
- [ ] Enforce `min_length` on `EmailResponse` fields
- [ ] Tests: malformed, partial, extra-field LLM output rejected

### System-Ready (§3)
- [ ] Typed errors: `ValidationError`, `ProviderError`, `OutputContractError`
- [ ] Nested error envelope `{error: {code, message}}` on API and Web
- [ ] Structured logging per request (model, outcome)
- [ ] Unify retry policy across providers

### Verification
- [ ] Bump enforced coverage to 95% in `pyproject.toml` and `README.md`
- [ ] Add entry-point equivalence test
- [ ] Replace brittle implementation-asserting tests with behavior tests
- [ ] Consolidate test mocks into fixtures

### Done
- [x] Author `AGENT.md`

## Out of Scope
- Docker, deployment
- UI features (presets, copy buttons)
- Auth, rate limiting
- Additional providers
