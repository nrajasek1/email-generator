from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    provider: str
    api_key: str
    model: str
    reasoning_effort: str = "none"
    max_output_tokens: int = 800
    base_url: Optional[str] = None


def get_settings() -> Settings:
    provider = os.getenv("LLM_PROVIDER", "auto").strip().lower() or "auto"
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()

    if provider not in {"auto", "openai", "openrouter"}:
        raise ValueError("LLM_PROVIDER must be one of: auto, openai, openrouter.")

    if provider == "auto":
        if openrouter_key:
            provider = "openrouter"
        elif openai_key:
            provider = "openai"
        else:
            raise ValueError(
                "No API key found. Add OPENROUTER_API_KEY or OPENAI_API_KEY to your environment or .env file."
            )

    if provider == "openrouter":
        if not openrouter_key:
            raise ValueError("OPENROUTER_API_KEY is not set. Add it to your environment or .env file.")
        return Settings(
            provider="openrouter",
            api_key=openrouter_key,
            model=os.getenv("OPENROUTER_MODEL", "").strip()
            or os.getenv("OPENAI_MODEL", "").strip()
            or "openrouter/free",
            reasoning_effort=os.getenv("OPENAI_REASONING_EFFORT", "none").strip() or "none",
            max_output_tokens=max(1, int(os.getenv("MAX_OUTPUT_TOKENS", "800").strip() or "800")),
            base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").strip()
            or "https://openrouter.ai/api/v1",
        )

    if not openai_key:
        raise ValueError("OPENAI_API_KEY is not set. Add it to your environment or .env file.")

    return Settings(
        provider="openai",
        api_key=openai_key,
        model=os.getenv("OPENAI_MODEL", "gpt-5-mini").strip() or "gpt-5-mini",
        reasoning_effort=os.getenv("OPENAI_REASONING_EFFORT", "none").strip() or "none",
        max_output_tokens=max(1, int(os.getenv("MAX_OUTPUT_TOKENS", "800").strip() or "800")),
        base_url=None,
    )
