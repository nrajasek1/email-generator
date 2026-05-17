# AI Email Generator

## 🚀 Overview
This project is an AI-powered email generation system that creates structured emails (subject + body) based on user intent.

It is designed as a multi-interface application supporting:
- CLI (Command Line)
- Web UI
- REST API

The system demonstrates how to build production-ready AI applications using modular architecture, configurable LLM providers, and test-driven development.


Generate a plain-text email subject and body from three inputs:

- `purpose`
- `tone`
- `context`

The project exposes the same shared generator through three interfaces:

- CLI
- Web app
- JSON API

## Features

- Multi-interface support: CLI, Web UI, REST API
- Pluggable LLM provider support (OpenAI, OpenRouter)
- Centralized prompt generation logic
- Structured output (subject + body)
- Automated test coverage (80%+)
- Clean modular architecture

## 🏗 Architecture

User Input (CLI / API / Web)
        ↓
Prompt Builder (`generator.py`)
        ↓
LLM Provider (OpenAI / OpenRouter)
        ↓
Response Parsing + Validation
        ↓
Formatted Output (Subject + Body)

Key Design Decisions:
- Shared generation logic across all interfaces
- Provider abstraction via configuration
- Strict response validation using schemas
- Separation of concerns (CLI, Web, Core logic)

## Requirements

- Python `3.9+`
- One provider API key:
  - `OPENAI_API_KEY`, or
  - `OPENROUTER_API_KEY`

## Quick Start

1. Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install the project and development dependencies:

```bash
pip install -e .[dev]
```

3. Copy the example environment file:

```bash
cp .env.example .env
```

4. Add your API key to `.env`.

## Environment Variables

Required:

```env
OPENAI_API_KEY=your_key_here
```

or

```env
OPENROUTER_API_KEY=your_key_here
```

Optional:

```env
LLM_PROVIDER=auto
OPENAI_MODEL=gpt-5-mini
OPENAI_REASONING_EFFORT=none
OPENROUTER_MODEL=openrouter/free
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
MAX_OUTPUT_TOKENS=800
```

Provider selection:

- `LLM_PROVIDER=auto` prefers OpenRouter when `OPENROUTER_API_KEY` is set
- `LLM_PROVIDER=openai` forces OpenAI
- `LLM_PROVIDER=openrouter` forces OpenRouter

## Running The Project

Run the web app:

```bash
.venv/bin/uvicorn email_generator.web:app --reload
```

Then open `http://127.0.0.1:8000`.

Run the CLI with the installed script:

```bash
email-generator \
  --purpose "Follow up after a product demo" \
  --tone "Professional and warm" \
  --context "The prospect asked for pricing details and onboarding next steps."
```

Or run it as a Python module:

```bash
python3 -m email_generator.cli \
  --purpose "Follow up after a product demo" \
  --tone "Professional and warm" \
  --context "The prospect asked for pricing details and onboarding next steps."
```

Call the JSON API:

```bash
curl -X POST http://127.0.0.1:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "purpose": "Follow up after a product demo",
    "tone": "Professional and warm",
    "context": "The prospect asked for pricing details and onboarding next steps."
  }'
```

## Running Tests

Run the full suite:

```bash
.venv/bin/pytest -q
```

The project enforces a minimum coverage threshold of `95%`. See `AGENT.md` for the rationale and the required test categories.

## Project Structure

```text
email-generator/
  email_generator/
    __init__.py
    __main__.py
    api.py
    cli.py
    config.py
    core.py
    errors.py
    prompt.py
    providers.py
    schemas.py
    web.py
    templates/
      index.html
  tests/
    conftest.py
    test_cli.py
    test_config.py
    test_core.py
    test_equivalence.py
    test_main_module.py
    test_web.py
  .env.example
  .gitignore
  AGENT.md
  README.md
  plan.md
  pyproject.toml
```

## How It Works

- `email_generator/core.py` orchestrates a request: call the provider, validate raw output, normalize, retry on contract failure, log the outcome
- `email_generator/prompt.py` holds the system instructions and user-prompt template
- `email_generator/providers.py` wraps the OpenAI and OpenRouter calls (single-attempt; retry lives in core)
- `email_generator/schemas.py` defines `EmailRequest`, `LLMRawOutput` (strict, `extra="forbid"`), and `EmailResponse`
- `email_generator/errors.py` defines typed errors that map to the nested error envelope (`InputValidationError`, `OutputContractError`, `ProviderError`)
- `email_generator/config.py` loads provider settings from environment variables
- `email_generator/cli.py` exposes the command-line interface
- `email_generator/api.py` exposes the `/api/generate` JSON route as a FastAPI router
- `email_generator/web.py` serves the HTML form and mounts the API router; registers the error-envelope exception handlers

See `AGENT.md` for the contract this implementation must satisfy.

## Contributor Checklist

For someone cloning the repo and testing it locally:

1. `python3 -m venv .venv`
2. `source .venv/bin/activate`
3. `pip install -e .[dev]`
4. `cp .env.example .env`
5. Add an API key to `.env`
6. `.venv/bin/pytest -q`
7. `.venv/bin/uvicorn email_generator.web:app --reload`

## Notes

- OpenAI recommends the Responses API for new projects:
  https://platform.openai.com/docs/guides/responses-vs-chat-completions
- The Python quickstart documents the `response.output_text` pattern:
  https://platform.openai.com/docs/quickstart?api-mode=responses&lang=python
- OpenRouter documents an OpenAI-compatible Responses API at:
  https://openrouter.ai/docs/api-reference/responses-api/overview

## 🧠 What I Learned

- Built a modular AI application with shared core logic
- Implemented multi-interface access (CLI, API, Web)
- Integrated multiple LLM providers (OpenAI, OpenRouter)
- Applied environment-based configuration management
- Practiced test-driven development with coverage enforcement
