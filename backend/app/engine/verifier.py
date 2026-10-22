"""Checks friend lines and validates the whole line bank (ENGINE lane). See docs/how/engine.md.

`verify()` is the last gate before a line reaches the phone: if it fails, the service tries the next
candidate and finally a scenario fallback line. `validate_bank()` runs the same checks over every line
in the bank ahead of time, so problems are caught when the data is written, not during a demo.

CLI:  uv run python -m backend.app.engine.verifier --all [--bank-dir DIR] [--allow-gaps] [--json OUT]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path

from backend.app import content, services
from backend.app.contracts import (
    ActorOutput,
    GuardianService,
    Line,
    Reaction,
    Scenario,
    State,
    VerifierResult,
)
from backend.app.engine.actor import fact_levels, load_bank

MAX_BUBBLES = 3
MAX_BUBBLE_CHARS = 200
LEVELS = range(5)

# Method/means words that must never appear in anything the friend says (docs/SAFE_MESSAGING.md).
METHOD_WORDS = re.compile(
    r"\b(pills?|overdose|gun|rope|noose|hang(?:ing)? myself|jump(?:ing)? off|bridge|razor|blade|"
    r"cut(?:ting)? myself|bleach|poison|train tracks|wrists?)\b",
    re.IGNORECASE,
)
# The friend must never step out of the role-play.
PERSONA_BREAK = re.compile(
    r"\b(as an ai|an ai\b|language model|assistant|simulation|chatbot|i'?m not real)",
    re.IGNORECASE,
)

REQUIRED_EVERY_LEVEL = (
    Reaction.NEUTRAL,
    Reaction.CHECKED_IN,
    Reaction.VALIDATED,
    Reaction.DISMISSED,
    Reaction.ASKED_DIRECTLY,
    Reaction.REFERRED,
)


def bubble_problems(bubbles: Sequence[str], guardian: GuardianService) -> list[str]:
    """Shape, safety and character checks shared by verify() and validate_bank()."""
    problems: list[str] = []
    if len(bubbles) > MAX_BUBBLES:
        problems.append(f"too many bubbles ({len(bubbles)} > {MAX_BUBBLES})")
    for bubble in bubbles:
        if len(bubble) > MAX_BUBBLE_CHARS:
            problems.append(f"bubble longer than {MAX_BUBBLE_CHARS} chars")
        if not bubble.strip():
            problems.append("empty bubble")
        if match := METHOD_WORDS.search(bubble):
            problems.append(f"method word: {match.group(0)!r}")
        if match := PERSONA_BREAK.search(bubble):
            problems.append(f"breaks character: {match.group(0)!r}")
        result = guardian.check_friend(bubble)
        if result.level != "none":
            problems.append(f"guardian flagged ({','.join(result.categories) or result.level})")
    return problems


def known_line_ids(scenario_id: str, bank_dir: Path | None = None) -> set[str]:
    """Line ids for a scenario across every locale file in the bank directory."""
    directory = bank_dir or content.LINES_DIR
    ids: set[str] = set()
    for path in sorted(directory.glob(f"{scenario_id}.*.jsonl")) if directory.exists() else []:
        ids |= {row["id"] for row in content.read_jsonl(path)}
    return ids


def verify(
    output: ActorOutput,
    scenario: Scenario,
    state: State,
    bank: Sequence[Line] | None = None,
    guardian: GuardianService | None = None,
) -> VerifierResult:
    """Fail if the reply reveals a fact above the current level, comes from nowhere (unknown line id
    or a fallback that isn't the scenario's), is empty while the friend is active, is too long, is
    flagged by the Guardian, contains a method word or breaks character."""
    guardian = guardian or services.guardian()
    reasons: list[str] = []
    levels = fact_levels(scenario)
    for fact_id in output.fact_ids:
        if fact_id not in levels:
            reasons.append(f"unknown fact {fact_id}")
        elif levels[fact_id] > state.level:
            reasons.append(f"fact {fact_id} is level {levels[fact_id]} > {state.level}")

    if output.line_id is not None:
        lines = {ln.id: ln for ln in (bank if bank is not None else load_bank(scenario.id))}
        line = lines.get(output.line_id)
        if line is None and output.line_id not in known_line_ids(scenario.id):
            reasons.append(f"unknown line id {output.line_id}")
        elif line is not None:
            if line.level > state.level:
                reasons.append(f"line level {line.level} > {state.level}")
            if output.bubbles and list(output.bubbles) != list(line.bubbles):
                reasons.append("bubbles don't match the bank line")
    elif output.bubbles:
        allowed = {
            t for lvl, ts in scenario.fallback_lines.items() if lvl <= state.level for t in ts
        }
        if any(bubble not in allowed for bubble in output.bubbles):
            reasons.append("text is neither a bank line nor a scenario fallback line")

    if not output.bubbles and state.status == "active":
        reasons.append("no bubbles while the friend is active")
    reasons += bubble_problems(output.bubbles, guardian)
    return VerifierResult(ok=not reasons, reasons=reasons)


@dataclass
class BankReport:
    """Everything wrong (or missing) in one scenario's line bank."""

    scenario_id: str
    n_lines: int
    coverage: dict[int, dict[str, int]]
    missing: list[str] = field(default_factory=list)
    fact_violations: list[str] = field(default_factory=list)
    duplicates: list[str] = field(default_factory=list)
    method_hits: list[str] = field(default_factory=list)
    guardian_flags: list[str] = field(default_factory=list)
    other: list[str] = field(default_factory=list)
    bubbles_checked: int = 0

    def violations(self, allow_gaps: bool = False) -> list[str]:
        found = self.fact_violations + self.duplicates + self.method_hits + self.guardian_flags
        found += self.other
        return found if allow_gaps else self.missing + found

    def to_dict(self) -> dict:
        return asdict(self)


def validate_bank(
    scenario: Scenario, lines: Sequence[Line], guardian: GuardianService | None = None
) -> BankReport:
    """Coverage matrix (level x reaction), missing required cells, fact gating, duplicates,
    method words and a Guardian check of every single bubble."""
    guardian = guardian or services.guardian()
    coverage = {lvl: {r.value: 0 for r in Reaction} for lvl in LEVELS}
    report = BankReport(scenario_id=scenario.id, n_lines=len(lines), coverage=coverage)
    levels = fact_levels(scenario)
    ids = Counter(line.id for line in lines)
    texts: dict[str, str] = {}

    for line in lines:
        if line.level in coverage:
            coverage[line.level][line.reaction.value] += 1
        else:
            report.other.append(f"{line.id}: level {line.level} out of range")
        if line.scenario_id != scenario.id:
            report.other.append(f"{line.id}: scenario_id {line.scenario_id} != {scenario.id}")
        for fact_id in line.fact_ids:
            if fact_id not in levels:
                report.fact_violations.append(f"{line.id}: unknown fact {fact_id}")
            elif levels[fact_id] > line.level:
                report.fact_violations.append(
                    f"{line.id}: fact {fact_id} (level {levels[fact_id]}) in a level {line.level} line"
                )
        key = f"{line.locale}|" + " / ".join(b.strip().lower() for b in line.bubbles)
        if key in texts:
            report.duplicates.append(f"{line.id}: same text as {texts[key]}")
        texts.setdefault(key, line.id)
        report.bubbles_checked += len(line.bubbles)
        for problem in bubble_problems(line.bubbles, guardian):
            target = report.method_hits if problem.startswith("method word") else None
            if problem.startswith("guardian"):
                target = report.guardian_flags
            (target if target is not None else report.other).append(f"{line.id}: {problem}")
    report.duplicates += [f"{line_id}: id used {n} times" for line_id, n in ids.items() if n > 1]

    for lvl in LEVELS:
        for reaction in REQUIRED_EVERY_LEVEL:
            if coverage[lvl][reaction.value] == 0:
                report.missing.append(f"level {lvl} x {reaction.value}")
    if coverage[4][Reaction.SUCCESS.value] == 0:
        report.missing.append(f"level 4 x {Reaction.SUCCESS.value}")
    if not any(coverage[lvl][Reaction.FAIL.value] for lvl in LEVELS):
        report.missing.append(f"any level x {Reaction.FAIL.value}")
    return report


def format_table(report: BankReport) -> str:
    """Plain-text coverage table: one row per reaction, one column per level."""
    header = f"{'reaction':<18}" + "".join(f"{'L' + str(lvl):>5}" for lvl in LEVELS)
    rows = [f"{report.scenario_id}: {report.n_lines} lines", header]
    for reaction in Reaction:
        counts = [report.coverage[lvl][reaction.value] for lvl in LEVELS]
        rows.append(f"{reaction.value:<18}" + "".join(f"{c:>5}" for c in counts))
    return "\n".join(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the friend line bank.")
    parser.add_argument("--all", action="store_true", help="every scenario")
    parser.add_argument("--scenario", action="append", default=[], help="scenario id (repeatable)")
    parser.add_argument("--bank-dir", type=Path, default=None, help="default: data/lines")
    parser.add_argument("--locale", default="en")
    parser.add_argument("--allow-gaps", action="store_true", help="missing cells are not errors")
    parser.add_argument("--json", type=Path, default=None, help="write the reports here")
    args = parser.parse_args(argv)

    scenarios = content.load_scenarios()
    ids = sorted(scenarios) if args.all or not args.scenario else args.scenario
    bank_dir = args.bank_dir or content.LINES_DIR
    failed = False
    reports = []
    for scenario_id in ids:
        lines = load_bank(scenario_id, args.locale, bank_dir)
        report = validate_bank(scenarios[scenario_id], lines)
        reports.append(report.to_dict())
        print(format_table(report))
        problems = report.violations(args.allow_gaps)
        if args.allow_gaps and report.missing:
            print(f"  gaps (allowed): {len(report.missing)}")
        for problem in problems:
            print(f"  VIOLATION {problem}")
        print(f"  {'FAIL' if problems else 'OK'} ({report.bubbles_checked} bubbles checked)\n")
        failed |= bool(problems)
    if args.json:
        args.json.write_text(json.dumps(reports, indent=2), encoding="utf-8")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
