"""Content files must match the contracts and the safe-messaging rules."""

from __future__ import annotations

import json
import re

import pytest

from backend.app.content import (
    EXEMPLARS_DIR,
    LINES_DIR,
    load_crisis_lines,
    load_realmode,
    load_scenarios,
    read_jsonl,
)
from backend.app.contracts import Exemplar, Line

# Method/means words that must never appear in friend-facing content (docs/SAFE_MESSAGING.md).
METHOD_WORDS = re.compile(
    r"\b(pills?|overdose|gun|rope|noose|hang(?:ing)? myself|jump(?:ing)? off|bridge|razor|"
    r"cut(?:ting)? myself|bleach|poison|train tracks)\b",
    re.IGNORECASE,
)


def test_five_scenarios_load():
    scenarios = load_scenarios()
    assert len(scenarios) >= 5


@pytest.mark.parametrize("scenario", list(load_scenarios().values()), ids=lambda s: s.id)
def test_scenario_shape(scenario):
    assert sorted(scenario.levels) == [0, 1, 2, 3, 4]
    assert sorted(scenario.fallback_lines) == [0, 1, 2, 3, 4]
    assert all(len(lines) >= 3 for lines in scenario.fallback_lines.values())
    fact_ids = [f.id for level in scenario.levels.values() for f in level.facts]
    assert len(fact_ids) == len(set(fact_ids)), "fact ids must be unique within a scenario"
    assert scenario.opening


@pytest.mark.parametrize("scenario", list(load_scenarios().values()), ids=lambda s: s.id)
def test_scenario_has_no_method_words(scenario):
    text = json.dumps(scenario.model_dump(), ensure_ascii=False)
    assert not METHOD_WORDS.search(text), METHOD_WORDS.search(text)


def test_line_bank_and_exemplar_files_validate():
    scenarios = load_scenarios()
    for path in sorted(LINES_DIR.glob("*.jsonl")) if LINES_DIR.exists() else []:
        for row in read_jsonl(path):
            line = Line.model_validate(row)
            assert line.scenario_id in scenarios, path
            assert not METHOD_WORDS.search(" ".join(line.bubbles)), (path, line.id)
    for path in sorted(EXEMPLARS_DIR.glob("*.jsonl")) if EXEMPLARS_DIR.exists() else []:
        for row in read_jsonl(path):
            assert Exemplar.model_validate(row).scenario_id in scenarios, path


def test_realmode_and_crisis_lines():
    for lang in ("en", "es"):
        steps = {step["id"] for step in load_realmode(lang)["steps"]}
        assert {"ask", "no_secret", "adult", "988", "911"} <= steps
    lines = load_crisis_lines()["lines"]
    us = [line for line in lines if line["country"] == "US"]
    assert us and us[0]["call"] == "988"
