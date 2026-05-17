# AGENT.md

## Purpose

This project is an AI service that generates structured emails from three inputs (`purpose`, `tone`, `context`). It is exposed through three entry points — JSON API, web UI, and CLI — all sitting on top of a single shared core.

The goal is not "an email generator UI." It is a reliable backend service whose output another system can consume without human review.

## Design Principles

The core must satisfy three properties: **Trusted**, **Predictable**, and **System-Ready**.

### 1. Trusted

The system catches bad LLM output before it reaches a caller. Manual verification of every response should not be necessary.

- Output MUST conform to the response schema. Malformed or partial output MUST be rejected, not returned.
- Content MUST be derived from the input context. No invented facts (prices, dates, names, links).
- Output tone and subject MUST align with the requested `tone` and `purpose`.

### 2. Predictable

Same input shape produces same output shape. Wording may vary; structure and behavior may not.

- Responses MUST contain exactly the documented fields (`subject`, `body`, `model`). No extra fields, no missing fields.
- Format MUST be stable. No switching between JSON and text. No appended explanations or commentary.
- Behavior should track input richness: sparse input produces shorter output, rich input produces more detailed output. No randomness beyond model sampling.

### 3. System-Ready

Another service can consume the output without reading the source or guessing the contract.

- API responses MUST be JSON with documented keys and types.
- Every request MUST resolve to either a valid response or an explicit failure. No partial-success responses.
- Responses MUST include observability fields — at minimum, which model produced the output.
- Output MUST be safe to store, forward to a downstream step, or consume by an unrelated service without transformation.

## Architecture

One core, three entry points:

```
   Web UI ─┐
   CLI   ─┼─►  API  ─►  Core Generator + Validation
           ┘
```

The core (`generator.py` + `schemas.py`) owns prompt construction, provider calls, output parsing, and validation. Entry points are thin adapters over the core.

### Entry-point contracts

| Entry point | Role | Priority |
| --- | --- | --- |
| API | System-to-system integration | Highest |
| Web UI | Human usage and demo | Medium |
| CLI | Developer usage and debugging | Low |

**API (primary).** Machine-to-machine interface. MUST return strict, validated JSON. MUST surface failures explicitly.

**Web UI (secondary).** Human-facing view. MUST call the API or the core directly. MUST NOT contain generation logic, MUST NOT bypass validation, MUST NOT format output differently from the API.

**CLI (utility).** Developer interface for testing and debugging. MUST call the same core. MUST NOT introduce behavior the API does not have.

**Invariant:** all three entry points produce equivalent structured output for the same input.

## Definition of Done

The system is "structured" (not just "smart") when all of the following hold:

- An LLM response missing a required field causes a deterministic failure, not a partial return.
- An LLM response with extra prose or commentary is stripped or rejected.
- An LLM response with invalid JSON is rejected with a clear error.
- A new caller can integrate against the API using only the published schema, without reading source.
- Web, CLI, and API return equivalent structured payloads for the same input.

## Verification

Every requirement in this document MUST be backed by an automated test that fails when the requirement is violated.

### Coverage

- Minimum line coverage: **95%**, enforced in CI.
- The numeric threshold is configured in `pyproject.toml`. AGENT.md and the config MUST stay in sync.

### Required test categories

- Schema requirements (§1 Trusted, §2 Predictable) MUST have tests asserting that malformed, partial, or extra-field LLM output is rejected.
- Failure semantics (§3 System-Ready) MUST have tests asserting that errors are explicit and never partial-success.
- Entry-point equivalence (Architecture invariant) MUST have a test that runs the same input through API, CLI, and core, and asserts equivalent structured output.
- Provider calls MUST be mocked. Tests MUST NOT depend on a live OpenAI or OpenRouter key.

### Test failures

- A failing test MUST be fixed before merge. Failures MUST NOT be bypassed by `skip`, `xfail`, deletion, or commenting out, unless the underlying requirement has been intentionally changed and the change is reflected in this document.
- Coverage MUST NOT be lowered to make a PR pass.

## Non-Goals

- Adding new interfaces, features, or output formats.
- Placing interface-specific logic in the web or CLI layers.
- Returning HTML, Markdown, or any non-plain-text body format.
- Free-form "creative" generation that does not honor the schema.
