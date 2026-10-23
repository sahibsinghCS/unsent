"""Loaders for the content files that live in the repo: scenarios, friend line bank, exemplar replies,
real-mode steps, crisis lines and evaluation reports. Nothing here calls the network.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from backend.app.config import CONTENT_DIR, DATA_DIR, EVAL_REPORTS_DIR
from backend.app.contracts import Exemplar, Line, Scenario, ScenarioText

SCENARIO_DIR = DATA_DIR / "scenarios"
LINES_DIR = DATA_DIR / "lines"
EXEMPLARS_DIR = DATA_DIR / "exemplars"


def read_jsonl(path: Path) -> list[dict]:
    """Read a JSON-lines file (blank lines ignored)."""
    rows: list[dict] = []
    with path.open(encoding="utf-8") as handle:
        for raw in handle:
            raw = raw.strip()
            if raw:
                rows.append(json.loads(raw))
    return rows


@lru_cache(maxsize=1)
def load_scenarios() -> dict[str, Scenario]:
    """All scenarios in data/scenarios/*.json (files starting with '_' are skipped)."""
    scenarios: dict[str, Scenario] = {}
    for path in sorted(SCENARIO_DIR.glob("*.json")):
        if path.name.startswith("_"):
            continue
        scenario = Scenario.model_validate_json(path.read_text(encoding="utf-8"))
        scenarios[scenario.id] = scenario
    return scenarios


def get_scenario(scenario_id: str) -> Scenario:
    """Scenario by id; raises KeyError if unknown."""
    return load_scenarios()[scenario_id]


def scenario_locales(scenario: Scenario) -> list[str]:
    """Languages a scenario fully supports: English, plus every language that has both the scenario's
    translated text (Scenario.i18n) and a friend line bank. A chat never mixes languages."""
    extra = [loc for loc in sorted(scenario.i18n) if loc != "en" and load_lines(scenario.id, loc)]
    return ["en", *extra]


def scenario_text(scenario: Scenario, locale: str) -> ScenarioText:
    """The scenario's user-facing text in `locale` (English when it isn't supported)."""
    if locale != "en" and locale in scenario_locales(scenario):
        return scenario.i18n[locale]
    return ScenarioText(
        title=scenario.title,
        situation=scenario.situation,
        opening=scenario.opening,
        content_warning=scenario.content_warning,
    )


@lru_cache(maxsize=64)
def load_lines(scenario_id: str, locale: str = "en") -> tuple[Line, ...]:
    """Friend line bank for a scenario (empty until the DATA lane writes data/lines/<id>.<locale>.jsonl)."""
    path = LINES_DIR / f"{scenario_id}.{locale}.jsonl"
    if not path.exists():
        return ()
    return tuple(Line.model_validate(row) for row in read_jsonl(path))


@lru_cache(maxsize=64)
def load_exemplars(scenario_id: str, locale: str = "en") -> tuple[Exemplar, ...]:
    """Exemplar helper replies for a scenario (empty until the DATA lane writes them)."""
    path = EXEMPLARS_DIR / f"{scenario_id}.{locale}.jsonl"
    if not path.exists():
        return ()
    return tuple(Exemplar.model_validate(row) for row in read_jsonl(path))


def load_realmode(lang: str = "en") -> dict:
    """Fixed 'it's real right now' steps (no AI). Falls back to English."""
    path = CONTENT_DIR / f"realmode.{lang}.json"
    if not path.exists():
        path = CONTENT_DIR / "realmode.en.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_crisis_lines() -> dict:
    return json.loads((CONTENT_DIR / "crisis_lines.json").read_text(encoding="utf-8"))


def crisis_lines_for(country: str) -> dict:
    """Crisis line entries for a country plus the international fallback."""
    data = load_crisis_lines()
    lines = [entry for entry in data["lines"] if entry["country"] in (country, "*")]
    emergency = data.get("emergency", {})
    return {
        "country": country,
        "lines": lines,
        "emergency": emergency.get(country, emergency.get("*", "")),
        "verified_on": data.get("verified_on"),
    }


def load_metrics() -> list[dict]:
    """Every record in eval/reports/*.json (each file holds a list of records or one record)."""
    records: list[dict] = []
    if not EVAL_REPORTS_DIR.exists():
        return records
    for path in sorted(EVAL_REPORTS_DIR.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        items = payload if isinstance(payload, list) else [payload]
        for item in items:
            if isinstance(item, dict):
                records.append({**item, "source": path.name})
    return records


def load_headline() -> list[dict]:
    """The few numbers judges should see first (content/headline_metrics.json), in EN and ES.
    The How page and `make report` both read this file, so the headline is defined once."""
    path = CONTENT_DIR / "headline_metrics.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _find_record(records: list[dict], lane: str, metric: str, split: str) -> dict | None:
    """The newest report record for (lane, metric, split), or None."""
    matches = [
        r
        for r in records
        if r.get("lane") == lane and r.get("metric") == metric and r.get("split") == split
    ]
    return max(matches, key=lambda r: str(r.get("created", ""))) if matches else None


def resolve_headline(records: list[dict]) -> list[dict]:
    """Each headline definition with its measured value, n and notes filled in from the reports.
    `found` is False until the lane has written that number (the UI hides those)."""
    resolved = []
    for item in load_headline():
        record = _find_record(records, item["lane"], item["metric"], item["split"])
        entry = {**item, "found": record is not None and record.get("value") is not None}
        if record is not None:
            entry.update(
                value=record.get("value"),
                n=record.get("n"),
                notes=record.get("notes", ""),
                created=record.get("created"),
                source=record.get("source"),
            )
        base = item.get("baseline")
        if base:
            base_record = _find_record(records, base["lane"], base["metric"], base["split"])
            entry["baseline"] = {
                **base,
                "value": None if base_record is None else base_record.get("value"),
                "n": None if base_record is None else base_record.get("n"),
            }
        resolved.append(entry)
    return resolved


def clear_caches() -> None:
    load_scenarios.cache_clear()
    load_lines.cache_clear()
    load_exemplars.cache_clear()
