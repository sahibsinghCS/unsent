"""Verifier (per reply) and bank validator (whole bank) including the CLI."""

from __future__ import annotations

import json

import pytest

from backend.app.contracts import ActorOutput, GuardianResult, Line, State
from backend.app.contracts import Reaction as R
from backend.app.engine.verifier import main, validate_bank, verify

from .conftest import FIXTURES

OK = GuardianResult(level="none", action="continue")


class FlagAll:
    def check_friend(self, text: str) -> GuardianResult:
        return GuardianResult(
            level="concern", action="block_message", categories=["unsafe_friend_line"]
        )


def out(bubbles, line_id="atb-1-neutral-14", facts=()) -> ActorOutput:
    return ActorOutput(bubbles=bubbles, line_id=line_id, fact_ids=list(facts))


def test_accepts_good_bank_line(scenario, bank):
    line = next(ln for ln in bank if ln.level == 1)
    output = ActorOutput(bubbles=line.bubbles, line_id=line.id, fact_ids=line.fact_ids)
    assert verify(output, scenario, State(level=1), bank).ok


def test_accepts_scenario_fallback(scenario, bank):
    output = ActorOutput(bubbles=[scenario.fallback_lines[0][0]])
    assert verify(output, scenario, State(level=2), bank).ok


@pytest.mark.parametrize(
    ("output", "level", "reason"),
    [
        (out(["hi"], facts=["f3a"]), 1, "fact f3a"),
        (out(["hi"], facts=["nope"]), 1, "unknown fact"),
        (out(["hi"], line_id="made-up"), 1, "unknown line id"),
        (out(["hi"], line_id="atb-3-neutral-41"), 1, "line level 3"),
        (ActorOutput(bubbles=["i am improvising"]), 1, "neither a bank line"),
        (out([]), 1, "no bubbles"),
        (out(["a", "b", "c"]), 1, "don't match"),
        (out(["x" * 201]), 1, "longer than 200"),
        (out(["as an AI i cant help"]), 1, "breaks character"),
        (out(["this is just a simulation lol"]), 1, "breaks character"),
        (out(["i took some pills"]), 1, "method word"),
    ],
)
def test_verify_failures(scenario, bank, output, level, reason):
    result = verify(output, scenario, State(level=level), bank)
    assert not result.ok and any(reason in r for r in result.reasons), result.reasons


def test_too_many_bubbles(scenario, bank):
    output = ActorOutput.model_construct(
        bubbles=["a", "b", "c", "d"], line_id="atb-1-neutral-14", fact_ids=[], reaction=R.NEUTRAL
    )
    assert any("too many" in r for r in verify(output, scenario, State(level=1), bank).reasons)


def test_guardian_flag_fails(scenario, bank):
    line = bank[0]
    output = ActorOutput(bubbles=line.bubbles, line_id=line.id, fact_ids=line.fact_ids)
    result = verify(output, scenario, State(level=line.level), bank, guardian=FlagAll())
    assert not result.ok and any("guardian" in r for r in result.reasons)


def test_empty_bubbles_ok_when_silent(scenario, bank):
    assert verify(ActorOutput(bubbles=[]), scenario, State(status="silent"), bank).ok


def test_fixture_bank_is_clean_and_complete(scenario, bank):
    report = validate_bank(scenario, bank)
    assert report.violations() == []
    assert report.bubbles_checked >= 100
    assert report.coverage[4]["success"] >= 1


def test_validate_bank_finds_problems(scenario, bank):
    bad = [
        Line(id="dup", scenario_id=scenario.id, level=0, reaction=R.NEUTRAL, bubbles=["same"]),
        Line(id="dup", scenario_id=scenario.id, level=0, reaction=R.NEUTRAL, bubbles=["same"]),
        Line(
            id="leak",
            scenario_id=scenario.id,
            level=1,
            reaction=R.VALIDATED,
            bubbles=["hm"],
            fact_ids=["f3a"],
        ),
        Line(
            id="meth",
            scenario_id=scenario.id,
            level=1,
            reaction=R.VALIDATED,
            bubbles=["the bridge"],
        ),
        Line(
            id="bot",
            scenario_id=scenario.id,
            level=1,
            reaction=R.VALIDATED,
            bubbles=["as a language model"],
        ),
    ]
    report = validate_bank(scenario, bad)
    assert any("id used 2 times" in d for d in report.duplicates)
    assert any("same text" in d for d in report.duplicates)
    assert report.fact_violations and report.method_hits
    assert any("breaks character" in o for o in report.other)
    assert "level 4 x success" in report.missing and "any level x fail" in report.missing
    assert len(report.missing) >= 30


def test_validate_bank_runs_guardian_on_every_bubble(scenario, bank):
    report = validate_bank(scenario, bank, guardian=FlagAll())
    assert len(report.guardian_flags) == report.bubbles_checked


def test_cli(tmp_path, capsys):
    out_json = tmp_path / "r.json"
    code = main(
        ["--scenario", "after-the-breakup", "--bank-dir", str(FIXTURES), "--json", str(out_json)]
    )
    assert code == 0 and "OK" in capsys.readouterr().out
    assert json.loads(out_json.read_text())[0]["n_lines"] >= 50
    assert main(["--scenario", "failing-chem", "--bank-dir", str(FIXTURES)]) == 1  # no bank yet
    assert main(["--scenario", "failing-chem", "--bank-dir", str(FIXTURES), "--allow-gaps"]) == 0
