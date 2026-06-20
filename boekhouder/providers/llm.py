"""LLM seam.

Agents that benefit from natural-language reasoning (intake parsing, fiscal/CFO
narrative) call through this interface. The default ``RuleBasedLLM`` is fully
deterministic and offline so everything runs and unit-tests without an API key. When
``BOEKHOUDER_ANTHROPIC_API_KEY`` is set, ``get_llm`` returns ``ClaudeLLM`` which calls
Claude (claude-opus-4-8) for free-form text — never for the numbers, which always come
from the deterministic engine.
"""
from __future__ import annotations

import logging
from functools import lru_cache

from boekhouder.config import get_settings

log = logging.getLogger("boekhouder.llm")


class LLM:
    name = "base"

    def complete(self, system: str, prompt: str) -> str:  # pragma: no cover - interface
        raise NotImplementedError


class RuleBasedLLM(LLM):
    """Deterministic no-op: returns an empty string so callers use their own logic."""

    name = "rule_based"

    def complete(self, system: str, prompt: str) -> str:
        return ""


class ClaudeLLM(LLM):
    """Thin Anthropic wrapper. Only used when an API key is configured."""

    name = "claude"

    def __init__(self) -> None:
        self.settings = get_settings()

    def complete(self, system: str, prompt: str) -> str:
        try:
            import anthropic  # imported lazily; optional dependency
        except ImportError:
            log.warning("anthropic SDK not installed; falling back to rule-based logic")
            return ""
        try:
            client = anthropic.Anthropic(api_key=self.settings.anthropic_api_key)
            msg = client.messages.create(
                model=self.settings.anthropic_model,
                max_tokens=1024,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
            return "".join(getattr(b, "text", "") for b in msg.content)
        except Exception as exc:  # noqa: BLE001 - degrade gracefully, never crash a booking
            log.warning("LLM call failed (%s); using rule-based logic", exc)
            return ""


@lru_cache
def get_llm() -> LLM:
    settings = get_settings()
    return ClaudeLLM() if settings.has_llm else RuleBasedLLM()
