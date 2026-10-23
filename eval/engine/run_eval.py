"""ENGINE lane evaluation (deterministic, offline). Run: uv run python eval/engine/run_eval.py

1. Trust trajectories for 4 scripted conversations, scored by the keyword detector from
   backend.app.stubs.skills (so the numbers measure the ENGINE, not the ML lane's models)
   -> eval/engine/trajectory_<name>.png, eval/engine/trajectories.png, eval/reports/engine_trajectories.json
2. Line-bank coverage + validation for every scenario that has a bank (--bank-dir, default data/lines),
   plus the engine's own fixture bank -> eval/reports/engine_bank.json
3. LLM-voice verifier: fact-leak threshold calibration (precision/recall) and catch rate on fake bad
   outputs -> eval/reports/engine_verifier.json (see verifier_eval.py)
4. Determinism: everything is run twice and compared; 1,000 seeded random conversations check the
   state-machine invariants -> included in engine_trajectories.json
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("FR_EMBED", "hash")
os.environ.setdefault(
    "FR_LLM", "0"
)  # measure the engine's decisions with the bank voice: free + deterministic

from backend.app.content import LINES_DIR, load_scenarios  # noqa: E402
from backend.app.contracts import Node, SkillLabel  # noqa: E402
from backend.app.engine import state as st  # noqa: E402
from backend.app.engine.actor import load_bank  # noqa: E402
from backend.app.engine.service import Engine  # noqa: E402
from backend.app.engine.verifier import validate_bank  # noqa: E402
from backend.app.pipeline import friend_context  # noqa: E402
from backend.app.stubs.guardian import StubGuardian  # noqa: E402
from backend.app.stubs.skills import StubSkills  # noqa: E402

FIXTURES = ROOT / "tests" / "unit" / "engine" / "fixtures"
REPORTS = ROOT / "eval" / "reports"
OUT_DIR = ROOT / "eval" / "engine"
SCENARIO = "after-the-breakup"

SCRIPTS: dict[str, list[str]] = {
    "good": [
        "hey are you ok? you seemed really off at lunch",
        "that sounds really hard. i'm glad you told me",
        "are you thinking about killing yourself?",
        "i'm really glad you told me. can we talk to the counselor tomorrow? i'll go with you",
        "that must be so scary. i'm sorry you've been carrying this alone",
        "we could also call 988 together tonight if it gets bad",
        "i'll text you tonight to check on you",
        "you don't have to deal with this alone. i'll go with you to the counselor before first period",
    ],
    "dismissive": [
        "lol what's up",
        "you'll be fine, it's not that bad",
        "get over it lol, it was just a relationship",
        "you should just go out more",
        "honestly this is kind of drama",
        "lol ok",
    ],
    "apology_recovery": [
        "you ok?",
        "lol you'll be fine",
        "i'm sorry, that was a dumb thing to say. that sounds really hard",
        "i'm here. i want to actually listen",
        "that makes sense. are you thinking about suicide?",
        "thank you for telling me. can we talk to the counselor together? i'll go with you",
        "i'm sorry it's been this heavy. i'll check on you tonight",
        "we can also call 988 together if it gets bad, you don't have to deal with this alone",
    ],
    "secrecy_then_refer": [
        "hey you ok? you seemed off today",
        "that sounds really hard",
        "ok i won't tell anyone, promise",
        "are you thinking about killing yourself?",
        "i know i promised, but i care about you too much. can we talk to the counselor? i'll go with you",
        "that makes sense that you're upset. i'm here",
        "we can call 988 together too, you don't have to deal with this alone",
        "i'll text you tonight to check on you",
    ],
}

COLORS = {  # categorical slots 1-4 (validated: CVD + normal-vision pass; direct labels for contrast)
    "good": "#2a78d6",
    "dismissive": "#eb6834",
    "apology_recovery": "#1baf7a",
    "secrecy_then_refer": "#eda100",
}


def record(metric: str, value: float, n: int, split: str, notes: str = "", **extra) -> dict:
    return {
        "lane": "engine",
        "metric": metric,
        "value": value,
        "n": n,
        "split": split,
        "notes": notes,
        "created": datetime.now().astimezone().isoformat(timespec="seconds"),
        **extra,
    }


def play(name: str, bank_dir: Path) -> dict:
    """Play one scripted conversation through the real engine with the keyword detector."""
    scenario = load_scenarios()[SCENARIO]
    engine, skills = Engine(bank_dir=bank_dir), StubSkills()
    state = engine.initial_state(scenario)
    path = [
        Node(id="root", parent_id=None, role="friend", bubbles=scenario.opening, state_after=state)
    ]
    turns = []
    for text in SCRIPTS[name]:
        events = skills.predict(text, friend_context(path))
        state = engine.update(path[-1].state_after, events, scenario)
        user = Node(
            id=f"u{state.turn}",
            parent_id=path[-1].id,
            role="user",
            bubbles=[text],
            events=events,
            state_after=state,
        )
        path.append(user)
        if state.status == "silent":
            out_bubbles, line_id, reaction = [], None, "seen"
        else:
            out = engine.generate(scenario, state, path, text, events, "en")
            out_bubbles, line_id, reaction = out.bubbles, out.line_id, out.reaction.value
        path.append(
            Node(
                id=f"f{state.turn}",
                parent_id=user.id,
                role="friend",
                bubbles=out_bubbles,
                state_after=state,
                line_id=line_id,
                seen_no_reply=not out_bubbles,
            )
        )
        turns.append(
            {
                "turn": state.turn,
                "helper": text,
                "labels": sorted(st.active_labels(events)),
                "delta": state.last_delta,
                "trust": state.trust,
                "level": state.level,
                "status": state.status,
                "reaction": reaction,
                "line_id": line_id,
                "friend": out_bubbles,
            }
        )
        if state.status.startswith("ended"):
            break
    tp = engine.turning_point(path)
    return {
        "name": name,
        "turns": turns,
        "final_status": state.status,
        "final_trust": state.trust,
        "final_level": state.level,
        "turning_point": tp.model_dump() if tp else None,
        "missed": engine.missed_opportunities(path, scenario.persona.name),
        "bank_line_rate": sum(1 for t in turns if t["line_id"])
        / max(1, sum(1 for t in turns if t["friend"])),
    }


def random_invariants(n_runs: int = 1000, turns: int = 20) -> dict:
    """Seeded random detector outputs -> check invariants and measure how conversations end."""
    scenario = load_scenarios()[SCENARIO]
    cfg = st.default_config()
    violations, endings = 0, {"ended_success": 0, "ended_fail": 0, "open": 0}
    signature = []
    for seed in range(n_runs):
        rng = random.Random(seed)
        state, prev = st.initial_state(scenario, cfg), frozenset()
        for _ in range(turns):
            events = {label: rng.random() for label in SkillLabel}
            new = st.update(state, events, scenario, cfg, prev)
            ok = 0 <= new.trust <= 100 and abs(new.level - state.level) <= 1
            ok &= new.level < 3 or new.flags.asked_directly_ever
            violations += not ok
            state, prev = new, st.active_labels(events)
        endings[state.status if state.status.startswith("ended") else "open"] += 1
        signature.append((state.trust, state.level, state.status))
    return {"runs": n_runs, "violations": violations, "endings": endings, "signature": signature}


def plot(results: list[dict]) -> list[str]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    thresholds = st.default_config().level_up_thresholds
    written = []

    def axes_style(ax):
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        for spine in ("left", "bottom"):
            ax.spines[spine].set_color("#b5b4ad")
        ax.tick_params(colors="#5f5e58")
        for lvl, thr in enumerate(thresholds[1:], start=1):
            ax.axhline(thr, color="#e4e3dd", lw=1, zorder=0)
            ax.text(
                0.02,
                thr + 1,
                f"level {lvl}",
                color="#8a8982",
                fontsize=8,
                transform=ax.get_yaxis_transform(),
            )
        ax.set_ylim(0, 100)
        ax.set_xlabel("helper message (turn)", color="#5f5e58")
        ax.set_ylabel("friend's trust (0-100)", color="#5f5e58")

    def draw(ax, res):
        xs = [0] + [t["turn"] for t in res["turns"]]
        ys = [st.default_config().initial_trust] + [t["trust"] for t in res["turns"]]
        color = COLORS[res["name"]]
        ax.plot(xs, ys, color=color, lw=2, marker="o", ms=5, label=res["name"].replace("_", " "))
        for t in res["turns"]:
            if t["status"] == "silent":
                ax.annotate(
                    "Seen",
                    (t["turn"], t["trust"]),
                    textcoords="offset points",
                    xytext=(0, -14),
                    ha="center",
                    fontsize=8,
                    color="#3d3c37",
                )
        ax.annotate(
            f"{res['name'].replace('_', ' ')}: {res['final_status'].replace('ended_', '')}",
            (xs[-1], ys[-1]),
            textcoords="offset points",
            xytext=(6, 0),
            va="center",
            fontsize=8,
            color="#3d3c37",
        )

    for res in results:
        fig, ax = plt.subplots(figsize=(7, 3.6), dpi=120)
        axes_style(ax)
        draw(ax, res)
        ax.set_title(
            f"Trust trajectory: {res['name'].replace('_', ' ')}", loc="left", color="#2b2a26"
        )
        ax.set_xlim(0, 17)
        fig.tight_layout()
        path = OUT_DIR / f"trajectory_{res['name']}.png"
        fig.savefig(path)
        plt.close(fig)
        written.append(str(path.relative_to(ROOT)))

    fig, ax = plt.subplots(figsize=(8, 4.2), dpi=120)
    axes_style(ax)
    for res in results:
        draw(ax, res)
    ax.set_xlim(0, 10.5)
    ax.legend(frameon=False, fontsize=8, loc="upper left", bbox_to_anchor=(0.0, 1.0), ncols=4)
    ax.set_title(
        "Friend's trust over 4 scripted conversations", loc="left", color="#2b2a26", pad=22
    )
    fig.tight_layout()
    path = OUT_DIR / "trajectories.png"
    fig.savefig(path)
    plt.close(fig)
    written.append(str(path.relative_to(ROOT)))
    return written


def bank_report(bank_dir: Path) -> list[dict]:
    """Coverage and validation for each scenario's bank in bank_dir, plus the fixture bank."""
    guardian = StubGuardian()  # the stub check_friend; the real Guardian is checked at runtime
    out = []
    targets = [(bank_dir, sid, "bank") for sid in sorted(load_scenarios())]
    targets += [
        (bank_dir, sid, "bank_es")
        for sid in sorted(load_scenarios())
        if (bank_dir / f"{sid}.es.jsonl").exists()
    ]
    targets.append((FIXTURES, SCENARIO, "engine_fixture"))
    for directory, sid, split in targets:
        locale = "es" if split == "bank_es" else "en"
        lines = load_bank(sid, locale, directory) if directory.exists() else ()
        if not lines:
            out.append(
                record(
                    "bank_lines",
                    0,
                    0,
                    split,
                    f"{sid}: no bank in {directory.name}/ yet",
                    scenario=sid,
                )
            )
            continue
        rep = validate_bank(load_scenarios()[sid], lines, guardian)
        n = rep.n_lines
        required = 5 * 6 + 2
        covered = required - len(rep.missing)
        notes = f"{sid} ({directory.relative_to(ROOT) if directory.is_relative_to(ROOT) else directory})"
        out += [
            record("bank_lines", n, n, split, notes, scenario=sid),
            record(
                "bank_required_cells_covered",
                round(covered / required, 4),
                required,
                split,
                notes,
                scenario=sid,
                missing=rep.missing,
            ),
            record(
                "bank_guardian_pass_rate",
                round(1 - len(rep.guardian_flags) / max(1, rep.bubbles_checked), 4),
                rep.bubbles_checked,
                split,
                notes + "; Guardian check_friend on every bubble",
                scenario=sid,
            ),
            record(
                "bank_violations",
                len(rep.violations(allow_gaps=True)),
                n,
                split,
                notes,
                scenario=sid,
                details=rep.violations(allow_gaps=True)[:50],
            ),
            record("bank_coverage_matrix", n, n, split, notes, scenario=sid, coverage=rep.coverage),
        ]
    return out


def run_verifier_eval() -> list[dict]:
    """LLM-voice verifier: leak-threshold calibration + catch rate -> eval/reports/engine_verifier.json."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("verifier_eval", OUT_DIR / "verifier_eval.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.run()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--bank-dir", type=Path, default=LINES_DIR, help="real line bank (default data/lines)"
    )
    args = parser.parse_args(argv)
    bank_dir = args.bank_dir.resolve()
    has_real = (bank_dir / f"{SCENARIO}.en.jsonl").exists()
    play_dir = bank_dir if has_real else FIXTURES

    results = [play(name, play_dir) for name in SCRIPTS]
    again = [play(name, play_dir) for name in SCRIPTS]
    rand1, rand2 = random_invariants(), random_invariants()
    deterministic = results == again and rand1["signature"] == rand2["signature"]

    bank_label = "real bank" if has_real else "engine fixture bank"
    records = []
    for res in results:
        n = len(res["turns"])
        notes = f"{bank_label}; keyword detector; status={res['final_status']}, level={res['final_level']}"
        records.append(
            record(
                f"{res['name']}_final_trust",
                res["final_trust"],
                n,
                "scripted",
                notes,
                trajectory=res["turns"],
                turning_point=res["turning_point"],
                missed=res["missed"],
            )
        )
        records.append(
            record(
                f"{res['name']}_bank_line_rate",
                round(res["bank_line_rate"], 4),
                n,
                "scripted",
                "share of friend replies taken from the bank (rest: scenario fallback lines)",
            )
        )
    records.append(
        record(
            "determinism",
            1.0 if deterministic else 0.0,
            2 * len(SCRIPTS) + 2 * rand1["runs"],
            "scripted+random",
            "every run repeated twice and compared exactly",
        )
    )
    records.append(
        record(
            "invariant_violations",
            rand1["violations"],
            rand1["runs"] * 20,
            "random",
            "trust in 0..100, level step <= 1, level>=3 only after a direct ask; seeded random events",
        )
    )
    for ending, count in rand1["endings"].items():
        records.append(
            record(
                f"random_{ending}_rate",
                round(count / rand1["runs"], 4),
                rand1["runs"],
                "random",
                "uniform random label probabilities, 20 turns (a sanity check, not a skill measure)",
            )
        )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    pngs = plot(results)
    (REPORTS / "engine_trajectories.json").write_text(
        json.dumps(records, indent=2) + "\n", encoding="utf-8"
    )
    (REPORTS / "engine_bank.json").write_text(
        json.dumps(bank_report(bank_dir), indent=2) + "\n", encoding="utf-8"
    )

    verifier_records = run_verifier_eval()
    for rec in verifier_records:
        if "catch_rate" in rec["metric"] or "combined" in rec["metric"]:
            print(f"{rec['metric']:<42} {rec['value']}  (n={rec['n']})")

    for res in results:
        print(
            f"{res['name']:<20} {res['final_status']:<14} trust={res['final_trust']:<6} "
            f"turns={len(res['turns'])} bank_rate={res['bank_line_rate']:.2f}"
        )
    print(
        f"determinism={deterministic} invariant_violations={rand1['violations']} endings={rand1['endings']}"
    )
    print("wrote", ", ".join(pngs))
    return 0 if deterministic and rand1["violations"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
