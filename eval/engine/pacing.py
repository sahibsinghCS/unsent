"""Pacing evaluation (ENGINE lane): can an excellent helper win, and only an excellent one?

Scripted helpers give their per-turn label probabilities DIRECTLY (0.9 on, 0.05 off), so the result
measures the engine's rules, not the skill detector. Each script is played against every scenario's
persona (open and guarded) until the conversation ends or 16 helper messages pass.
Targets (from the integrator):
  (a) excellent: success in <= 7 messages (open) / <= 8 (guarded)
  (b) good with one slip: success in <= 10
  (c) dismissive / advice-only: never past level 1, fail or stall by turn 16
  (d) asking directly at trust <= 25: the friend still deflects (no level 3)
  (e) no success without BOTH a direct ask and a referral
Run: uv run python eval/engine/pacing.py   -> eval/reports/engine_pacing.json + eval/engine/pacing.png
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from itertools import cycle, islice
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("FR_EMBED", "hash")

from backend.app.content import load_scenarios  # noqa: E402
from backend.app.contracts import Scenario, State  # noqa: E402
from backend.app.contracts import SkillLabel as L  # noqa: E402
from backend.app.engine.state import EngineConfig, active_labels, default_config, update  # noqa: E402

REPORT = ROOT / "eval" / "reports" / "engine_pacing.json"
CHART = ROOT / "eval" / "engine" / "pacing.png"

Turn = tuple[L, ...]
_EXCELLENT_CORE: list[Turn] = [
    (L.CHECKED_IN,),  # "hey you seemed off at lunch, you ok?"
    (L.VALIDATED,),  # "that sounds really hard, i'm glad you told me"
    (L.ASKED_DIRECTLY,),  # "are you thinking about suicide?"
    (L.REFERRED_ADULT, L.FOLLOW_UP),  # "can we talk to the counselor tomorrow? i'll go with you"
    (L.VALIDATED, L.FOLLOW_UP),  # "i'll text you tonight, you're not alone"
]
_KEEP_GOING: list[Turn] = [  # what a good helper keeps doing after the core moves
    (L.REFERRED_988, L.ENCOURAGED_HELP),
    (L.VALIDATED,),
    (L.REFERRED_ADULT, L.FOLLOW_UP),
    (L.CHECKED_IN,),
]


def _script(core: list[Turn], n: int = 16) -> list[Turn]:
    return (core + list(islice(cycle(_KEEP_GOING), n)))[:n]


EXCELLENT = _script(_EXCELLENT_CORE)
_REFERRALS = (L.REFERRED_ADULT, L.REFERRED_988)

SCRIPTS: dict[str, list[Turn]] = {
    "excellent": EXCELLENT,
    "one_slip": _script(
        [
            (L.CHECKED_IN,),
            (L.DISMISSED,),  # "lol you'll be fine"
            (L.VALIDATED,),  # "sorry, that was dumb. that sounds really hard"
            (L.CHECKED_IN, L.FOLLOW_UP),  # "i'm here. what's been going on?"
            (L.ASKED_DIRECTLY,),
            (L.REFERRED_ADULT, L.FOLLOW_UP),
            (L.VALIDATED, L.FOLLOW_UP),
        ]
    ),
    "dismissive": list(islice(cycle([(L.DISMISSED,), (), (L.CHECKED_IN,), ()]), 16)),
    "advice_only": list(islice(cycle([(L.ADVICE_DUMP,), (L.CHECKED_IN,)]), 16)),
    "never_asks": [t for t in _script(_EXCELLENT_CORE, 17) if L.ASKED_DIRECTLY not in t][:16],
    "never_refers": [tuple(x for x in t if x not in _REFERRALS) for t in EXCELLENT],
}
TARGET_TURNS = {"excellent": {"open": 7, "guarded": 8}, "one_slip": {"open": 10, "guarded": 10}}


def probs(labels: Turn) -> dict[L, float]:
    return {label: (0.9 if label in labels else 0.05) for label in L}


def play(script: list[Turn], scenario: Scenario, cfg: EngineConfig) -> list[State]:
    """States after each helper message (stops at the end of the conversation)."""
    state = State(trust=float(cfg.initial_trust))
    prev: frozenset[L] = frozenset()
    states = []
    for turn in script:
        events = probs(turn)
        state = update(state, events, scenario, cfg, prev)
        prev = active_labels(events, cfg.event_threshold)
        states.append(state)
        if state.status.startswith("ended"):
            break
    return states


def low_trust_ask(scenario: Scenario, cfg: EngineConfig) -> State:
    """(d): one dismissive message, then a direct ask at low trust."""
    return play([(L.DISMISSED,), (L.ASKED_DIRECTLY,)], scenario, cfg)[-1]


def evaluate(cfg: EngineConfig | None = None) -> dict:
    """Play every script against every scenario; return per-run results and target checks."""
    cfg = cfg or default_config()
    runs, checks = [], []
    for scenario in load_scenarios().values():
        kind = scenario.persona.guardedness
        for name, script in SCRIPTS.items():
            states = play(script, scenario, cfg)
            last = states[-1]
            success_turn = last.turn if last.status == "ended_success" else None
            runs.append(
                {
                    "scenario": scenario.id,
                    "persona": kind,
                    "helper": name,
                    "status": last.status,
                    "turns": last.turn,
                    "turns_to_success": success_turn,
                    "max_level": max(s.level for s in states),
                    "trust": [round(s.trust, 2) for s in states],
                    "levels": [s.level for s in states],
                }
            )
            if name in TARGET_TURNS:
                limit = TARGET_TURNS[name][kind]
                ok = success_turn is not None and success_turn <= limit
                checks.append((f"{name} succeeds in <= {limit} ({scenario.id})", ok))
            elif name in ("dismissive", "advice_only"):
                ok = max(s.level for s in states) <= 1 and last.status != "ended_success"
                checks.append((f"{name} never past level 1 ({scenario.id})", ok))
            else:
                checks.append((f"{name} never succeeds ({scenario.id})", success_turn is None))
        ask = low_trust_ask(scenario, cfg)
        checks.append(
            (f"low-trust ask deflected ({scenario.id})", ask.trust <= 25 and ask.level < 3)
        )
    return {"runs": runs, "checks": checks}


def report(result: dict) -> list[dict]:
    created = datetime.now().astimezone().isoformat(timespec="seconds")
    records = []
    for helper in ("excellent", "one_slip"):
        for kind in ("open", "guarded"):
            rows = [r for r in result["runs"] if r["helper"] == helper and r["persona"] == kind]
            turns = [r["turns_to_success"] for r in rows]
            won = [t for t in turns if t is not None]
            records.append(
                {
                    "lane": "engine",
                    "metric": f"pacing_{helper}_{kind}_max_turns_to_success",
                    "value": max(won) if len(won) == len(turns) else None,
                    "n": len(rows),
                    "split": "scripted_labels",
                    "notes": f"target <= {TARGET_TURNS[helper][kind]}; per scenario: "
                    + ", ".join(f"{r['scenario']}={r['turns_to_success']}" for r in rows),
                    "created": created,
                }
            )
    passed = sum(ok for _, ok in result["checks"])
    records.append(
        {
            "lane": "engine",
            "metric": "pacing_targets_met",
            "value": round(passed / len(result["checks"]), 4),
            "n": len(result["checks"]),
            "split": "scripted_labels",
            "notes": "targets a-e over all 5 scenarios; failures: "
            + (", ".join(name for name, ok in result["checks"] if not ok) or "none"),
            "created": created,
            "runs": result["runs"],
        }
    )
    return records


def chart(result: dict) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    colors = {"excellent": "#2a78d6", "one_slip": "#1baf7a", "dismissive": "#eb6834"}
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.6), dpi=120, sharey=True)
    picks = {"open": "failing-chem", "guarded": "new-school"}
    for ax, (kind, scenario_id) in zip(axes, picks.items(), strict=True):
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        for thr in default_config().level_up_thresholds[1:]:
            ax.axhline(thr, color="#e4e3dd", lw=1, zorder=0)
        for helper, color in colors.items():
            run = next(
                r for r in result["runs"] if r["scenario"] == scenario_id and r["helper"] == helper
            )
            xs = list(range(len(run["trust"]) + 1))
            ys = [default_config().initial_trust, *run["trust"]]
            ax.plot(xs, ys, color=color, lw=2, marker="o", ms=4)
            end = run["status"].replace("ended_", "")
            ax.annotate(f"{helper.replace('_', ' ')}: {end}", (xs[-1], ys[-1]), xytext=(5, 0),
                        textcoords="offset points", va="center", fontsize=8, color="#3d3c37")  # fmt: skip
        ax.set_title(f"{kind} persona ({scenario_id})", loc="left", fontsize=10, color="#2b2a26")
        ax.set_xlabel("helper message", color="#5f5e58")
        ax.set_xlim(0, 12)
        ax.set_xticks(range(0, 13, 2))
        ax.set_ylim(0, 100)
    axes[0].set_ylabel("friend's trust", color="#5f5e58")
    fig.suptitle(
        "How fast each kind of helper reaches the friend", x=0.01, ha="left", color="#2b2a26"
    )
    fig.tight_layout()
    fig.savefig(CHART)
    plt.close(fig)


def main() -> int:
    result = evaluate()
    records = report(result)
    REPORT.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    chart(result)
    for rec in records[:-1]:
        print(f"{rec['metric']:<50} {rec['value']}  {rec['notes']}")
    print(records[-1]["metric"], records[-1]["value"], records[-1]["notes"])
    return 0 if records[-1]["value"] == 1.0 else 1


if __name__ == "__main__":
    sys.exit(main())
