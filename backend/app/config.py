"""Runtime configuration, read from environment variables (and an optional .env file).

FirstReply needs no API keys: everything runs locally and free.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env", override=False)

DATA_DIR = ROOT / "data"
CONTENT_DIR = ROOT / "content"
EVAL_REPORTS_DIR = ROOT / "eval" / "reports"
MODELS_DIR = ROOT / "models"
FRONTEND_DIST = ROOT / "frontend" / "dist"

DEFAULT_EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def env_flag(name: str, default: bool = False) -> bool:
    """True if the environment variable is set to a truthy value (1/true/yes/on)."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_int(name: str, default: int) -> int:
    """Integer environment variable with a fallback."""
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def stub_mode() -> bool:
    """FR_STUB=1 forces every component to its stub implementation (frontend development)."""
    return env_flag("FR_STUB")


def stub_only() -> set[str]:
    """FR_STUB_ONLY=engine,critic forces just those components to stubs."""
    return {name.strip() for name in os.getenv("FR_STUB_ONLY", "").split(",") if name.strip()}


def embed_backend() -> str:
    """'fastembed' (real local model, downloaded once) or 'hash' (deterministic fake for tests/CI)."""
    return os.getenv("FR_EMBED", "fastembed").strip().lower()


def embed_model_name() -> str:
    return os.getenv("FR_EMBED_MODEL", DEFAULT_EMBED_MODEL)


def max_message_chars() -> int:
    return env_int("FR_MAX_MESSAGE_CHARS", 500)


def max_turns() -> int:
    return env_int("FR_MAX_TURNS", 16)


def session_ttl_seconds() -> int:
    return env_int("FR_SESSION_TTL_MIN", 60) * 60


def is_prod() -> bool:
    return os.getenv("FR_ENV", "dev").strip().lower() == "prod"
