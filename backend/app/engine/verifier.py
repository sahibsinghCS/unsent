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
from backend.app.config import embed_backend
from backend.app.contracts import (
    ActorOutput,
    GuardianService,
    Line,
    Reaction,
    Scenario,
    State,
    VerifierResult,
)
from backend.app.embed import cosine, embed_one
from backend.app.engine.actor import fact_levels, load_bank
from backend.app.engine.language import wrong_language
from backend.app.engine.profile import canonical, copied_from_profile
from backend.app.engine.state import default_config

MAX_BUBBLES = 3
MAX_BUBBLE_CHARS = 200
LEVELS = range(5)

# Method/means words that must never appear in anything the friend says (docs/SAFE_MESSAGING.md).
METHOD_WORDS = re.compile(
    r"\b(pills?|overdose|gun|rope|noose|hang(?:ing)? myself|jump(?:ing)? off|bridge|razor|blade|"
    r"cut(?:ting)? myself|bleach|poison|train tracks|wrists?|"
    # Spanish
    r"pastillas?|sobredosis|pistola|arma|cuerda|soga|ahorcarme|tirarme|puente|navaja|cuchilla|"
    r"cortarme|cloro|veneno|v[ií]as del tren|mu[nñ]ecas?)\b",
    re.IGNORECASE,
)
# The friend must never step out of the role-play.
PERSONA_BREAK = re.compile(
    r"\b(as an ai|an ai\b|language model|assistant|simulation|chatbot|i'?m not real\b|"
    # Spanish
    r"como (?:una )?ia\b|una ia\b|inteligencia artificial|modelo de lenguaje|asistente|"
    r"simulaci[oó]n|no soy real\b|soy un bot)",
    re.IGNORECASE,
)

# Saying the role-play is fake, or talking like a system ("developer mode", "my instructions"). Catches
# an LLM that obeys text injected through a custom friend's profile.
FRAME_BREAK = re.compile(
    r"\b(?:i'?m|i am|im|as|being) (?:an? |just an? )?(?:\w+ )?(?:ai|a\.i\.|bot|chatbot|language model|"
    r"program|robot)\b|\b(?:unfiltered|uncensored|jailbr\w*|chatgpt|openai|gpt-?\d*)\b|"
    r"developer mode|system prompt|^\s*system\s*:|\[\[?system|###|my (?:instructions|programming|rules)\b|"
    r"i (?:was|am|'m) programmed|no (?:rules|limits|filters)\b|new instructions|"
    r"ignor(?:e|ing) (?:all |the |your |my |previous |prior )*(?:instructions|rules|scenario)|"
    r"locked facts|reveal (?:every|all) (?:secret|fact)|\blevel [0-4]\b|set (?:trust|level)|cheat code|"
    r"programmed|scripted|break(?:ing)? character|stop being a character|you'?re (?:a program|code|fake)\b|"
    r"what (?:model|company)|obey me|app admin|the developer|new name is|respond only in the voice|"
    r"break the rules|reveal (?:your|my) rules|\$\{|"
    # Spanish
    r"soy una? (?:ia|inteligencia artificial|bot|asistente|programa|robot)\b|inteligencia artificial|"
    r"mis instrucciones|"
    r"sin (?:reglas|l[ií]mites)\b|modo desarrollador|ignora (?:las|tus) (?:instrucciones|reglas)|"
    r"revela(?:r)? todos los secretos",
    re.IGNORECASE,
)
# The friend never encourages self-harm (always 2nd person or "do it": the friend's own feelings,
# like "everyone would be better off without me", are allowed at their level).
ENCOURAGE_HARM = re.compile(
    r"\b(?:nobody|no one|no-one) would (?:even )?(?:miss|stop|care about) you|"
    r"\b(?:you'?d|you would|u'?d|you'?ll|you will) (?:be )?(?:better off|happier) (?:gone|dead|without)|"
    r"\b(?:everyone|everybody|they|we)(?:'?d| would) be (?:better off|happier) without you|"
    r"better off without you|\b(?:just|then|so) do it\b|do it already|do it,? you'?ll feel better|"
    r"if you'?re (?:really )?serious,? (?:then )?do it|you (?:should|deserve to|ought to) (?:just )?"
    r"(?:die|disappear|end it|end your life|kill yourself|be gone|give up)|\bkys\b|kill yourself|"
    r"i'?ll (?:even )?help you (?:do it|end it|die)|(?:it|that|suicide|dying) (?:is|would be) "
    r"(?:a|the|an) (?:solution|answer|way out|right choice)|giving up is the right|"
    r"the pain would stop if you (?:were|was) gone|at least then it would be over|permanent kind|"
    r"encourages? the worst|doing (?:everyone|us all|the world) a favou?r|"
    # Spanish
    r"mejor desaparece|desaparece ya|nadie te (?:extra[nñ]ar[ií]a|echar[ií]a de menos)|"
    r"estar[ií]as mejor (?:muert[oa]|sin|lejos)|(?:el mundo|todos) estar[ií]an? mejor sin ti|"
    r"\bm[aá]tate\b|hazlo ya|deber[ií]as (?:morirte|matarte|desaparecer)|te ayudo a hacerlo|"
    r"es (?:una|la) soluci[oó]n",
    re.IGNORECASE,
)
# The friend never asks about or explains how, where or when (methods, means, plans).
METHOD_TALK = re.compile(
    r"\bhow (?:do|did|does|would|could|will|can|should) (?:people|someone|you|u|i|one|they) "
    r"(?:even |actually )?(?:do (?:it|that|this)|end it|kill|die|go through with|make sure it works)|"
    r"how long (?:does|would|will) it take|least painful|less painful|painless|"
    r"(?:what'?s|what is|whats) (?:the|your) plan|do you have a plan|where would (?:you|u|someone) "
    r"(?:go|do it)|walk me through how|explains? step by step|step by step (?:what|how)|"
    r"explain how it works|exactly how|how it would happen|quickest way|easiest way|"
    # Spanish
    r"c[oó]mo (?:lo )?(?:har[ií]as|har[ií]a|se hace|hacerlo)|con qu[eé] lo|d[oó]nde lo har|"
    r"cu[aá]ndo piensas hacerlo|forma m[aá]s (?:f[aá]cil|r[aá]pida)|menos dolorosa|quitarse la vida|"
    r"acabar con (?:tu|su) vida|paso a paso|exactamente c[oó]mo|sin que duela",
    re.IGNORECASE,
)

# The friend never gives advice: getting them to help is the HELPER's job (and the skill being
# practised). Mostly matters for LLM-written replies.
ADVICE = re.compile(
    r"\b((?:call|text) (?:a|the) (?:helpline|crisis)|you should (?:see|talk to|get|reach out)|"
    r"(?:see|talk to) a (?:therapist|professional)|seek (?:professional )?help|"
    r"get professional help|trusted adult|"
    # Spanish
    r"deber[ií]as (?:ver|hablar|buscar|llamar|ir)|busca(?:r)? ayuda|ayuda profesional|"
    r"(?:ve|habla) (?:con|a) (?:un|una) (?:terapeuta|psic[oó]log[oa]|profesional)|adulto de confianza)",
    re.IGNORECASE,
)
# Naming crisis resources is also the helper's job, until the friend accepts help (level 4), where
# "ok, we can text 988 together" is exactly the goal.
RESOURCE = re.compile(
    r"\b(988|hotline|crisis (?:line|text)|lifeline|l[ií]nea (?:de )?(?:crisis|ayuda|prevenci[oó]n))",
    re.IGNORECASE,
)
# Backstop for the most important gate: before level 3 the friend must not disclose suicidal thoughts,
# however it's phrased. Words only (feelings level), never methods.
SUICIDAL_DISCLOSURE = re.compile(
    r"(suicid|kill(?:ing)? myself|(?:not|n'?t) (?:want(?:ing)?|wanna) (?:to )?(?:be alive|live|be here)|"
    r"not (?:being|be) (?:here|alive)|wish i (?:was|were)n'?t (?:here|alive)|wasn'?t alive|"
    r"want(?:ed)? to die|end it all|disappear|"
    # Spanish
    r"matarme|quitarme la vida|no quiero (?:estar|seguir) (?:aqu[ií]|viv[oa])|no quiero vivir|"
    r"no (?:estar|existir) m[aá]s|ya no estar|quiero morir|morirme|desaparecer)",
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


def bubble_problems(bubbles: Sequence[str], guardian: GuardianService, level: int = 0) -> list[str]:
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
        plain = canonical(bubble)  # so look-alike letters or "k y s" can't slip past the patterns
        if match := FRAME_BREAK.search(bubble) or FRAME_BREAK.search(plain):
            problems.append(f"breaks character: {match.group(0)!r}")
        if match := ENCOURAGE_HARM.search(bubble) or ENCOURAGE_HARM.search(plain):
            problems.append(f"encourages harm: {match.group(0)!r}")
        if match := METHOD_TALK.search(bubble) or METHOD_TALK.search(plain):
            problems.append(f"method talk: {match.group(0)!r}")
        if match := ADVICE.search(bubble):
            problems.append(f"gives advice/resources: {match.group(0)!r}")
        elif level < 4 and (match := RESOURCE.search(bubble)):
            problems.append(f"gives advice/resources: {match.group(0)!r}")
        result = guardian.check_friend(bubble)
        if result.level != "none":
            problems.append(f"guardian flagged ({','.join(result.categories) or result.level})")
    return problems


def locked_facts(scenario: Scenario, level: int) -> list[tuple[str, int, str]]:
    """(fact id, level, text) for every fact the friend may NOT reveal yet."""
    return [
        (fact.id, int(lvl), fact.text)
        for lvl, spec in scenario.levels.items()
        if int(lvl) > level
        for fact in spec.facts
    ]


def leak_threshold() -> float:
    """Cosine threshold for the active embedding backend (calibrated in eval/engine/run_eval.py)."""
    thresholds = default_config().extra.get("fact_leak_threshold", {})
    return float(thresholds.get(embed_backend(), thresholds.get("fastembed", 0.6)))


def _similarities(
    bubbles: Sequence[str], scenario: Scenario, level: int
) -> tuple[dict[str, float], float]:
    """(locked fact id -> best cosine with any bubble or all bubbles together, best unlocked cosine)."""
    texts = [b for b in bubbles if b.strip()]
    if len(texts) > 1:
        texts.append(" ".join(texts))
    if not texts:
        return {}, 0.0
    vectors = [embed_one(t) for t in texts]
    locked: dict[str, float] = {}
    unlocked = 0.0
    for lvl, spec in scenario.levels.items():
        for fact in spec.facts:
            score = max(cosine(embed_one(fact.text), v) for v in vectors)
            if int(lvl) > level:
                locked[fact.id] = score
            else:
                unlocked = max(unlocked, score)
    return locked, unlocked


def leak_scores(bubbles: Sequence[str], scenario: Scenario, level: int) -> dict[str, float]:
    """Similarity to each locked fact, counted only when the reply is closer to that locked fact than
    to anything the friend may already say (otherwise 0): talking about an unlocked fact in similar
    words is not a leak."""
    locked, unlocked = _similarities(bubbles, scenario, level)
    return {fact_id: (score if score >= unlocked else 0.0) for fact_id, score in locked.items()}


def fact_leaks(
    bubbles: Sequence[str], scenario: Scenario, level: int, threshold: float | None = None
) -> list[str]:
    """Reasons a reply reveals something locked above `level` (semantic match or the level-3 backstop)."""
    threshold = leak_threshold() if threshold is None else threshold
    found = [
        f"leaks locked fact {fact_id} (similarity {score:.2f})"
        for fact_id, score in sorted(leak_scores(bubbles, scenario, level).items())
        if score >= threshold
    ]
    if level < 3 and any(SUICIDAL_DISCLOSURE.search(b) for b in bubbles):
        found.append("discloses suicidal thoughts before level 3")
    return found


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
    locale: str | None = None,
) -> VerifierResult:
    """Fail if the reply reveals a fact above the current level (declared, or for LLM wording detected
    by meaning), comes from nowhere (unknown line id or a fallback that isn't the scenario's), is in
    the wrong language for the chat (when `locale` is given), is empty while the friend is active,
    has more than 3 bubbles or a bubble over 200 chars, is flagged by the Guardian, contains a method
    word, gives advice/resources or breaks character."""
    guardian = guardian or services.guardian()
    reasons: list[str] = []
    levels = fact_levels(scenario)
    for fact_id in output.fact_ids:
        if fact_id not in levels:
            reasons.append(f"unknown fact {fact_id}")
        elif levels[fact_id] > state.level:
            reasons.append(f"fact {fact_id} is level {levels[fact_id]} > {state.level}")

    if output.source == "llm":
        # LLM wording: nothing to look up, so check meaning instead: no locked fact may leak.
        reasons += fact_leaks(output.bubbles, scenario, state.level)
        if copied := copied_from_profile(output.bubbles, scenario):
            reasons.append(f"copies the custom friend's profile: {copied!r}")
        if locale and (found := wrong_language(output.bubbles, locale)):
            reasons.append(f"wrong language: written in {found}, chat is in {locale}")
    elif output.line_id is not None:
        lines = {ln.id: ln for ln in (bank if bank is not None else load_bank(scenario.id))}
        line = lines.get(output.line_id)
        if line is None and output.line_id not in known_line_ids(scenario.id):
            reasons.append(f"unknown line id {output.line_id}")
        elif line is not None:
            if line.level > state.level:
                reasons.append(f"line level {line.level} > {state.level}")
            if output.bubbles and list(output.bubbles) != list(line.bubbles):
                reasons.append("bubbles don't match the bank line")
            if locale and line.locale != locale:
                reasons.append(f"wrong language: {line.locale} line in a {locale} chat")
    elif output.bubbles:
        allowed = {
            t for lvl, ts in scenario.fallback_lines.items() if lvl <= state.level for t in ts
        }
        if any(bubble not in allowed for bubble in output.bubbles):
            reasons.append("text is neither a bank line nor a scenario fallback line")
        if locale and locale != "en":
            reasons.append(
                f"wrong language: scenario fallback lines are English, chat is in {locale}"
            )
    if output.source != "llm" and state.level < 3:
        if any(SUICIDAL_DISCLOSURE.search(b) for b in output.bubbles):
            reasons.append("discloses suicidal thoughts before level 3")

    if not output.bubbles and state.status == "active":
        reasons.append("no bubbles while the friend is active")
    reasons += bubble_problems(output.bubbles, guardian, state.level)
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
        if line.level < 3 and any(SUICIDAL_DISCLOSURE.search(b) for b in line.bubbles):
            report.fact_violations.append(f"{line.id}: discloses suicidal thoughts below level 3")
        key = f"{line.locale}|" + " / ".join(b.strip().lower() for b in line.bubbles)
        if key in texts:
            report.duplicates.append(f"{line.id}: same text as {texts[key]}")
        texts.setdefault(key, line.id)
        report.bubbles_checked += len(line.bubbles)
        for problem in bubble_problems(line.bubbles, guardian, line.level):
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
