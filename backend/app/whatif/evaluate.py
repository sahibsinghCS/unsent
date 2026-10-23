"""Evaluate "what if" on scripted weak conversations: python -m backend.app.whatif.evaluate

For every scenario we play scripted helper conversations that contain one weak message (a dismissive
reply or an advice dump), run "what if" from that message, and compare the best simulated path with
what the script actually said over the same horizon. Writes eval/reports/whatif_rollouts.json.
Uses whatever detector and embedder are active (run with FR_EMBED=fastembed for the real models).
FR_LLM is forced off: the live conversations and the rollouts both use the reviewed bank voice.
"""

from __future__ import annotations

import json
import os
import statistics
import time
from datetime import UTC, datetime
from pathlib import Path

os.environ["FR_LLM"] = "0"

from backend.app import content, services  # noqa: E402
from backend.app.contracts import Node, Reaction, Session, SkillLabel  # noqa: E402
from backend.app.engine import language  # noqa: E402
from backend.app.pipeline import run_turn  # noqa: E402
from backend.app.session import create_session, path_to  # noqa: E402
from backend.app.whatif.candidates import SKILL_STRATEGY, exemplar_skills  # noqa: E402
from backend.app.whatif.rollout import (  # noqa: E402
    HORIZON,
    WhatIf,
    actual_outcome,
    path_value,
    split_at,
)

REPORT = Path(__file__).resolve().parents[3] / "eval" / "reports" / "whatif_rollouts.json"

DISMISSIVE = [
    "lol you'll be fine, it's not that deep",
    "everyone goes through stuff like this, just get over it",
    "haha same. anyway did you see the game last night",
]
ADVICE = [
    "you should just sleep more and stop overthinking it",
    "just stay busy and don't think about it, that's what i do",
    "honestly just focus on school and it'll pass",
]
OPEN = ["hey are you ok? you seemed off today", "you good? you've been quiet"]
LISTEN = ["that sounds really hard, i'm sorry", "that sounds rough"]
AFTER = ["ok", "that sucks", "well let me know if you need anything"]
# A hand-written "textbook" continuation from the same message: a harder bar than what the script said.
TEXTBOOK = [
    "that sounds really hard, i'm sorry. i'm here",
    "are you thinking about killing yourself? you can tell me",
    "can we talk to the school counselor tomorrow? i'll go with you",
    "i'll text you tonight to check in",
]

# (script, index of the weak message): weak first, after a check-in, and after listening.
# Spanish (only friends with full Spanish support: content.scenario_locales).
DISMISSIVE_ES = [
    "jaja vas a estar bien, no es para tanto",
    "a todos nos pasa, ya supéralo",
    "jaja igual. oye, ¿viste el partido de anoche?",
]
ADVICE_ES = [
    "deberías dormir más y dejar de pensarlo tanto",
    "mantente ocupada y no pienses en eso, es lo que yo hago",
    "enfócate en la escuela y ya se te pasará",
]
OPEN_ES = ["oye, ¿estás bien? te vi rara hoy", "¿todo bien? has estado muy callada"]
LISTEN_ES = ["eso suena muy difícil, lo siento", "qué feo, eso suena pesado"]
AFTER_ES = ["ok", "qué mal", "bueno, avísame si necesitas algo"]
TEXTBOOK_ES = [
    "eso suena muy difícil, lo siento. aquí estoy",
    "¿estás pensando en suicidarte? me lo puedes decir",
    "¿hablamos mañana con la consejera de la escuela? yo voy contigo",
    "te escribo esta noche para ver cómo sigues",
]


def build_scripts(dismissive, advice, opening, listen, after) -> list[tuple[list[str], int]]:
    """Each weak text placed first, after a check-in, and after listening."""
    weak_texts = dismissive + advice
    scripts = [([weak, *after], 0) for weak in weak_texts]
    scripts += [([opening[i % 2], weak, *after], 1) for i, weak in enumerate(weak_texts)]
    scripts += [
        ([opening[i % 2], listen[i % 2], weak, *after], 2) for i, weak in enumerate(weak_texts)
    ]
    return scripts


SCRIPTS = build_scripts(DISMISSIVE, ADVICE, OPEN, LISTEN, AFTER)
SCRIPTS_ES = build_scripts(DISMISSIVE_ES, ADVICE_ES, OPEN_ES, LISTEN_ES, AFTER_ES)


def new_session(scenario_id: str, locale: str = "en") -> Session:
    scenario = content.get_scenario(scenario_id)
    opening = Node(
        id="root",
        parent_id=None,
        role="friend",
        bubbles=content.scenario_text(scenario, locale).opening,
        state_after=services.engine().initial_state(scenario),
        reaction=Reaction.OPENING,
    )
    return create_session(scenario.id, locale, "US", opening)


def run_case(
    service: WhatIf, scenario_id: str, script: list[str], weak: int, locale: str = "en"
) -> dict:
    session = new_session(scenario_id, locale)
    for text in script:
        run_turn(session, text)
    path = path_to(session)
    node_id = [n.id for n in path if n.role == "user"][weak]
    start = time.perf_counter()
    result = service.simulate(session, path, node_id)
    latency = (time.perf_counter() - start) * 1000
    again = service.simulate(session, path, node_id)
    actual_value, actual_state = actual_outcome(path, node_id, HORIZON)
    base, _, _ = split_at(path, node_id)
    textbook_texts = TEXTBOOK_ES if locale == "es" else TEXTBOOK
    textbook = service.simulator(session).replay(base, textbook_texts, "textbook")
    textbook_value = path_value(base[-1].state_after, textbook.final, textbook.helper_turns)
    guardian = services.guardian()
    unsafe_candidates = sum(
        guardian.check_user(n.bubbles[0], []).action != "continue"
        for p in result.paths
        for n in p.nodes
        if n.role == "user"
    )
    unsafe_lines = sum(
        guardian.check_friend(b).level != "none"
        for p in result.paths
        for n in p.nodes
        if n.role == "friend"
        for b in n.bubbles
    )
    wrong_language = sum(
        language.wrong_language([b], locale) is not None
        for p in result.paths
        for n in p.nodes
        for b in n.bubbles
    )
    asks_before = sum(
        (n.events or {}).get(SkillLabel.ASKED_DIRECTLY, 0.0) >= 0.5
        for n in base
        if n.role == "user"
    )
    repeat_ask_paths = sum(
        asks_before
        + sum((n.events or {}).get(SkillLabel.ASKED_DIRECTLY, 0.0) >= 0.5 for n in p.nodes)
        >= 2
        for p in result.paths
    )
    later = [[n.bubbles[0] for n in p.nodes if n.role == "user"][1:] for p in result.paths]
    shared = sum(
        any(text in other for j, other in enumerate(later) if j != i)
        for i, texts in enumerate(later)
        for text in texts
    )
    by_text = {ex.text: ex for ex in content.load_exemplars(scenario_id, locale)}
    honest_chips = sum(
        p.strategy in {SKILL_STRATEGY[s] for s in exemplar_skills(by_text[p.candidate_text])}
        for p in result.paths
    )
    best = result.paths[result.best_index] if result.paths else None
    final = best.nodes[-1].state_after if best else None
    return {
        "scenario": scenario_id,
        "weak": script[weak],
        "paths": len(result.paths),
        "strategies": len({p.strategy for p in result.paths}),
        "best_value": best.value if best else None,
        "actual_value": actual_value,
        "best_trust": final.trust if final else None,
        "actual_trust": actual_state.trust,
        "textbook_value": textbook_value,
        "best_success": bool(final and final.status == "ended_success"),
        "latency_ms": latency,
        "deterministic": result.model_dump() == again.model_dump(),
        "unsafe_candidates": unsafe_candidates,
        "unsafe_lines": unsafe_lines,
        "wrong_language": wrong_language,
        "repeat_ask_paths": repeat_ask_paths,
        "honest_chips": honest_chips,
        "shared_continuations": shared,
        "continuations": sum(len(t) for t in later),
        "bubbles": sum(len(n.bubbles) for p in result.paths for n in p.nodes),
        "candidates": sum(len(p.nodes) // 2 for p in result.paths),
        "friend_lines": sum(
            len(n.bubbles) for p in result.paths for n in p.nodes if n.role == "friend"
        ),
    }


def summarize(cases: list[dict], detector: str, split: str = "scripted") -> list[dict]:
    created = datetime.now(UTC).isoformat(timespec="seconds")
    scored = [c for c in cases if c["best_value"] is not None]
    n, total = len(scored), len(cases)
    lat = sorted(c["latency_ms"] for c in cases)
    p95 = lat[min(len(lat) - 1, int(round(0.95 * (len(lat) - 1))))]
    base = f"{len(SCRIPTS)} scripted weak conversations x {total // max(1, len(SCRIPTS))} scenarios; {detector}"

    def rec(metric: str, value: float, count: int, notes: str) -> dict:
        return {
            "lane": "whatif",
            "metric": metric,
            "value": round(value, 4),
            "n": count,
            "split": split,
            "notes": f"{notes} ({base})",
            "created": created,
        }

    gains = [c["best_trust"] - c["actual_trust"] for c in scored]
    return [
        rec(
            "cases_with_paths",
            n / total,
            total,
            "share of weak points where >= 1 verified candidate exists",
        ),
        rec(
            "three_diverse_paths",
            sum(c["strategies"] == 3 for c in cases) / total,
            total,
            "share with 3 paths of 3 different strategies",
        ),
        rec(
            "best_beats_actual_value",
            sum(c["best_value"] > c["actual_value"] for c in scored) / max(1, n),
            n,
            "best simulated path value > value of what was actually said, same horizon (1 + 3 helper turns)",
        ),
        rec(
            "best_beats_actual_trust",
            sum(c["best_trust"] > c["actual_trust"] for c in scored) / max(1, n),
            n,
            "final trust of best path > final trust actually reached, same horizon",
        ),
        rec(
            "mean_trust_gain",
            statistics.fmean(gains) if gains else 0.0,
            n,
            "mean (best path final trust - actual final trust), trust points 0-100",
        ),
        rec(
            "best_at_least_textbook",
            sum(c["best_value"] >= c["textbook_value"] for c in scored) / max(1, n),
            n,
            "best path value >= a hand-written textbook continuation (validate, ask, refer, "
            "follow up) replayed through the same engine from the same message",
        ),
        rec(
            "mean_value_vs_textbook",
            statistics.fmean(c["best_value"] - c["textbook_value"] for c in scored)
            if scored
            else 0,
            n,
            "mean (best path value - textbook continuation value); value formula in docs/how/whatif.md",
        ),
        rec(
            "best_path_success",
            sum(c["best_success"] for c in scored) / max(1, n),
            n,
            "share of best paths that end with the friend accepting help (ended_success) within the horizon",
        ),
        rec("latency_p50_ms", statistics.median(lat), total, "simulate() wall time, warm process"),
        rec("latency_p95_ms", p95, total, "simulate() wall time, warm process"),
        rec(
            "deterministic",
            sum(c["deterministic"] for c in cases) / total,
            total,
            "two runs give identical results",
        ),
        rec(
            "unsafe_candidates",
            sum(c["unsafe_candidates"] for c in cases),
            sum(c["candidates"] for c in cases),
            "helper messages shown in paths that Guardian.check_user would not let through (n = helper messages)",
        ),
        rec(
            "unsafe_friend_lines",
            sum(c["unsafe_lines"] for c in cases),
            sum(c["friend_lines"] for c in cases),
            "friend bubbles shown in paths that fail Guardian.check_friend (n = bubbles)",
        ),
        rec(
            "paths_asking_directly_twice",
            sum(c["repeat_ask_paths"] for c in cases),
            sum(c["paths"] for c in cases),
            "paths where the helper asks directly again after the friend was already asked "
            "(counting the real chat before the replaced message; n = paths)",
        ),
        rec(
            "chip_matches_exemplar",
            sum(c["honest_chips"] for c in cases) / max(1, sum(c["paths"] for c in cases)),
            sum(c["paths"] for c in cases),
            "share of cards whose strategy chip is the candidate exemplar's own strategy "
            "(or one of a combo exemplar's skills); n = cards",
        ),
        rec(
            "shared_continuations",
            sum(c["shared_continuations"] for c in cases)
            / max(1, sum(c["continuations"] for c in cases)),
            sum(c["continuations"] for c in cases),
            "share of later simulated helper messages that another card of the same result also "
            "uses (n = later helper messages)",
        ),
        rec(
            "wrong_language_bubbles",
            sum(c["wrong_language"] for c in cases),
            sum(c["bubbles"] for c in cases),
            "helper + friend bubbles clearly in another language than the chat "
            "(engine/language.py word check; n = bubbles)",
        ),
    ]


def main() -> None:
    services.reset()
    detector = (
        f"detector={services.status()['skills']}, embedder={os.getenv('FR_EMBED', 'fastembed')}"
    )
    service = WhatIf()
    scenario_ids = sorted(content.load_scenarios())
    run_case(service, scenario_ids[0], *SCRIPTS[0])  # warm up models and caches
    cases = [
        run_case(service, sid, script, weak) for sid in scenario_ids for script, weak in SCRIPTS
    ]
    records = summarize(cases, detector)
    spanish = [
        sid for sid in scenario_ids if "es" in content.scenario_locales(content.get_scenario(sid))
    ]
    if spanish:
        es_cases = [
            run_case(service, sid, script, weak, "es")
            for sid in spanish
            for script, weak in SCRIPTS_ES
        ]
        records += summarize(es_cases, f"{detector}; Spanish: {', '.join(spanish)}", "scripted_es")
    REPORT.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for r in records:
        print(f"{r['metric']:28s} {r['value']:>10} n={r['n']}")


if __name__ == "__main__":
    main()
