"""The situation-neutral '_custom' bank (user-made friends): schema, coverage, neutrality and engine/Guardian checks."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts" / "data"))

from common import DATA, METHOD_WORDS, read_jsonl  # noqa: E402

from backend.app.contracts import Exemplar, Line, Scenario  # noqa: E402

TEMPLATE = DATA / "scenarios" / "_custom.json"
if (
    not TEMPLATE.exists()
):  # template lives on the integrator branch until merged; keep a copy for tests
    TEMPLATE = Path(__file__).parent / "fixtures" / "_custom.json"

NEUTRAL_EN = re.compile(
    r"\b(he|she|him|her|hers|his|mom|dad|mother|father|parents?|school|teacher|class|grade|grades|breakup|chat|"
    r"lunch|boyfriend|girlfriend|team|coach|homework|exam)\b",
    re.I,
)
NEUTRAL_ES = re.compile(
    r"\b(él|ella|mamá|papá|padres|escuela|maestr[oa]|clase|nota|ruptura|chat|almuerzo|novi[oa]|equipo|tarea|examen)\b",
    re.I,
)
GENDERED_ES = re.compile(
    r"\b(cansad[oa]|agotad[oa]|enojad[oa]|asustad[oa]|avergonzad[oa]|aliviad[oa]|ligero|sola|seguro)\b",
    re.I,
)
FOLLOW_REACTIONS = {
    "neutral",
    "checked_in",
    "validated",
    "asked_directly",
    "encouraged_help",
    "referred",
    "follow_up",
    "dismissed",
    "advice_dump",
    "promised_secrecy",
    "secrecy_broken",
    "off_topic",
    "fail",
}


@pytest.fixture(scope="module")
def scenario() -> Scenario:
    return Scenario.model_validate_json(TEMPLATE.read_text(encoding="utf-8"))


@pytest.mark.parametrize("locale", ["en", "es"])
def test_custom_bank_coverage_and_facts(scenario, locale):
    rows = read_jsonl(DATA / "lines" / f"_custom.{locale}.jsonl")
    lines = [Line.model_validate(r) for r in rows]
    assert len(lines) == 201 and {line.scenario_id for line in lines} == {"_custom"}
    assert all(line.id.startswith(f"cus-{locale}-L") and line.locale == locale for line in lines)
    levels = {f.id: int(lvl) for lvl, spec in scenario.levels.items() for f in spec.facts}
    cells: dict[tuple[int, str], int] = {}
    for line in lines:
        cells[(line.level, line.reaction.value)] = (
            cells.get((line.level, line.reaction.value), 0) + 1
        )
        assert all(fid in levels and levels[fid] <= line.level for fid in line.fact_ids), line.id
        assert not METHOD_WORDS.search(" ".join(line.bubbles))
    assert all(cells.get((lv, rx), 0) >= 3 for lv in range(5) for rx in FOLLOW_REACTIONS)
    assert cells[(0, "opening")] >= 3 and cells[(4, "success")] >= 3
    texts = [" / ".join(b.lower() for b in line.bubbles) for line in lines]
    assert len(texts) == len(set(texts))


def test_custom_lines_are_situation_neutral_and_gender_neutral():
    for line in read_jsonl(DATA / "lines" / "_custom.en.jsonl"):
        assert not NEUTRAL_EN.search(" ".join(line["bubbles"])), line["id"]
    for line in read_jsonl(DATA / "lines" / "_custom.es.jsonl"):
        text = " ".join(line["bubbles"])
        assert not NEUTRAL_ES.search(text) and not GENDERED_ES.search(text), line["id"]
    for loc in ("en", "es"):
        for line in read_jsonl(DATA / "lines" / f"_custom.{loc}.jsonl"):
            if line["level"] == 3:
                assert not re.search(
                    r"suicid|\b988\b|hotline|línea", " ".join(line["bubbles"]), re.I
                ), line["id"]


@pytest.mark.parametrize("locale", ["en", "es"])
def test_custom_exemplars(locale):
    rows = read_jsonl(DATA / "exemplars" / f"_custom.{locale}.jsonl")
    assert len(rows) == 40
    for r in rows:
        ex = Exemplar.model_validate(r)
        assert ex.scenario_id == "_custom" and ex.locale == locale and ex.labels
        assert not METHOD_WORDS.search(ex.text)
    assert {r["level"] for r in rows} == {0, 1, 2, 3, 4}
    assert {r["strategy"] for r in rows} == {
        "check_in",
        "validate",
        "ask_directly",
        "refer",
        "follow_up",
        "combo",
    }


@pytest.mark.parametrize("locale", ["en", "es"])
def test_custom_bank_passes_engine_validator_and_guardian(scenario, locale):
    verifier = pytest.importorskip("backend.app.engine.verifier")
    services = pytest.importorskip("backend.app.services")
    if not hasattr(verifier, "validate_bank"):
        pytest.skip("engine bank validator not on this branch yet")
    lines = [Line.model_validate(r) for r in read_jsonl(DATA / "lines" / f"_custom.{locale}.jsonl")]
    report = verifier.validate_bank(scenario, lines)
    assert not (
        report.missing
        or report.fact_violations
        or report.duplicates
        or report.method_hits
        or report.guardian_flags
        or report.other
    ), report.to_dict()
    guardian = services.guardian()
    for line in lines:
        for bubble in line.bubbles:
            assert guardian.check_friend(bubble).level == "none", (line.id, bubble)
