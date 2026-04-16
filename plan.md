# Email Generator Plan

## Goal

Build a Python email generator that uses the OpenAI API to turn three inputs:

- `purpose`
- `tone`
- `context`

into two plain-text outputs:

- `subject`
- `body`

The project should support three ways to use the same underlying generator:

- CLI
- browser-based web app
- JSON API

## Current Status

The base application is already scaffolded and includes:

- shared email generation service
- FastAPI web app
- server-rendered HTML form
- CLI entrypoint
- environment-based configuration
- OpenAI and OpenRouter provider support
- automated tests with coverage enforcement

## Architecture

### Core module

`email_generator/generator.py`

- Builds the prompt from user input
- Calls the OpenAI Responses API
- Extracts JSON from the model output
- Validates that both `subject` and `body` exist

### Configuration

`email_generator/config.py`

- Loads environment variables from `.env`
- Supports provider selection:
  - `LLM_PROVIDER=auto`
  - `LLM_PROVIDER=openai`
  - `LLM_PROVIDER=openrouter`
- Supports both `OPENAI_API_KEY` and `OPENROUTER_API_KEY`
- Supports optional model configuration:
  - `OPENAI_MODEL`
  - `OPENROUTER_MODEL`
  - `OPENAI_REASONING_EFFORT`
  - `MAX_OUTPUT_TOKENS`

### Data models

`email_generator/schemas.py`

- Validates request fields
- Defines a consistent API response shape

### Interfaces

`email_generator/cli.py`

- Accepts `purpose`, `tone`, and `context` from the command line
- Prints the generated subject and body

`email_generator/web.py`

- `GET /` renders the HTML form
- `POST /` submits form data and renders results
- `POST /api/generate` accepts JSON and returns structured JSON

`templates/index.html`

- Simple browser UI for manual testing and demos

## Delivery Plan

### Phase 1: Foundation

- Define project structure
- Implement environment loading
- Add OpenAI integration
- Add OpenRouter integration
- Build shared generator logic

Status: completed

### Phase 2: User Interfaces

- Add CLI entrypoint
- Add FastAPI API route
- Add HTML form interface

Status: completed

### Phase 3: Testing And Quality

- Add tests for prompt construction
- Add tests for config validation and defaults
- Add tests for JSON extraction behavior
- Add tests for API and form routes
- Add tests for CLI output
- Enforce at least 80% coverage

Status: completed

### Phase 4: Local Run And Validation

- Install dependencies
- Configure `.env`
- Run test suite with coverage
- Start local server
- Validate CLI, form, and API manually

Status: in progress

### Phase 5: Nice-To-Have Enhancements

- Add copy-to-clipboard button in the UI
- Add sample presets for common email purposes
- Add retry/fallback behavior for malformed model output
- Add logging for request failures
- Add Docker support
- Add deployment instructions

Status: pending

## Testing Strategy

The test suite should verify:

- prompt generation contains all required inputs
- config fails clearly when API key is missing
- config defaults are stable
- JSON parsing works for direct JSON and embedded JSON
- generator raises helpful errors for incomplete model responses
- web routes return expected HTTP responses
- CLI output format is stable

Coverage target:

- minimum 80% for the `email_generator` package

## Environment Variables

Required:

```env
OPENROUTER_API_KEY=... or OPENAI_API_KEY=...
```

Optional:

```env
LLM_PROVIDER=auto
OPENROUTER_MODEL=openrouter/free
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=gpt-5-mini
OPENAI_REASONING_EFFORT=none
MAX_OUTPUT_TOKENS=800
```

## Local Run Checklist

1. Create a virtual environment.
2. Install the project and dev dependencies.
3. Add `OPENROUTER_API_KEY` or `OPENAI_API_KEY` to `.env`.
4. Run `pytest`.
5. Run `uvicorn email_generator.web:app --reload`.
6. Test:
   - browser form
   - `POST /api/generate`
   - CLI invocation

## Risks And Mitigations

### Risk: model returns non-JSON output

Mitigation:

- instruct the model to return strict JSON
- attempt JSON extraction from surrounding text
- raise a clear validation error if parsing fails

### Risk: missing API key

Mitigation:

- fail early in config loading with a specific message

### Risk: interface drift between CLI, API, and web form

Mitigation:

- keep all interfaces routed through the same shared generator module

### Risk: low test confidence

Mitigation:

- enforce coverage threshold
- cover both happy paths and error paths

## Next Execution Steps

1. Add `OPENROUTER_API_KEY` or `OPENAI_API_KEY` to `.env`.
2. Launch the FastAPI app and verify browser and API flows against the live provider.
3. Run the CLI against a real prompt and confirm the output quality.
4. Refine UX and error handling based on live validation.
