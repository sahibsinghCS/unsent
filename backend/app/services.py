"""Component registry.

Each component has a real module (owned by a lane) and a stub (owned by the integrator).
The real module is used only when it sets IMPLEMENTED = True, so a lane "turns itself on" by editing
nothing but its own files. FR_STUB=1 forces all stubs; FR_STUB_ONLY=engine,critic forces some.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from backend.app.config import stub_mode, stub_only
from backend.app.contracts import (
    CriticService,
    EngineService,
    GuardianService,
    SkillService,
    WhatIfService,
)

COMPONENTS: dict[str, tuple[str, str]] = {
    "guardian": ("backend.app.safety.guardian", "backend.app.stubs.guardian"),
    "skills": ("backend.app.ml.skill_detector", "backend.app.stubs.skills"),
    "engine": ("backend.app.engine.service", "backend.app.stubs.engine"),
    "critic": ("backend.app.ml.critic", "backend.app.stubs.critic"),
    "whatif": ("backend.app.whatif.rollout", "backend.app.stubs.whatif"),
}

_cache: dict[str, tuple[Any, str]] = {}


def _load(name: str) -> tuple[Any, str]:
    real_path, stub_path = COMPONENTS[name]
    if not stub_mode() and name not in stub_only():
        module = import_module(real_path)
        if getattr(module, "IMPLEMENTED", False):
            return module.get_service(), "real"
    return import_module(stub_path).get_service(), "stub"


def get(name: str) -> Any:
    if name not in _cache:
        _cache[name] = _load(name)
    return _cache[name][0]


def status() -> dict[str, str]:
    """{'guardian': 'real' | 'stub', ...} for /api/health and the Transparency page."""
    for name in COMPONENTS:
        get(name)
    return {name: _cache[name][1] for name in COMPONENTS}


def reset() -> None:
    """Forget loaded components (tests and hot-reload)."""
    _cache.clear()


def guardian() -> GuardianService:
    return get("guardian")


def skills() -> SkillService:
    return get("skills")


def engine() -> EngineService:
    return get("engine")


def critic() -> CriticService:
    return get("critic")


def whatif() -> WhatIfService:
    return get("whatif")
