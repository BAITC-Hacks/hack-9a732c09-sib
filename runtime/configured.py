"""Explicit opt-in runtime factory; .env is read only for enabled LLM mode."""

import os
from pathlib import Path

from false_positive.strategy.engine import StrategyEngine

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {"OPENAI_API_KEY", "OPEN_AI_API_KEY", "OPENAI_MODEL"}


def settings_from_env_file():
    values = {}
    path = ROOT / ".env"
    if path.is_file():
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            name, separator, value = line.partition("=")
            name = name.strip().removeprefix("export ").strip()
            if separator and name in ALLOWED:
                values[name] = value.strip().strip("\"'")
    values.update({name: value for name, value in os.environ.items() if name in ALLOWED})
    return values


def build_engine(provider=None):
    chosen = provider if provider is not None else os.environ.get("FP_LLM_PROVIDER", "off")
    if chosen == "off":
        return StrategyEngine()
    if chosen != "openai":
        raise ValueError("FP_LLM_PROVIDER must be off or openai")
    from .llm import LLMHypothesisAdvisor
    try:
        settings = settings_from_env_file()
    except (OSError, UnicodeError):
        # Missing credentials trigger the engine's observable advisor fallback.
        # Do not expose a filesystem exception or its contents in API responses.
        settings = {}
    key = settings.get("OPENAI_API_KEY") or settings.get("OPEN_AI_API_KEY", "")
    model = settings.get("OPENAI_MODEL", "")
    return StrategyEngine(hypothesis_advisor=LLMHypothesisAdvisor(chosen, key, model))
