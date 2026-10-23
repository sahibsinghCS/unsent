"""Held-out evaluation of the skill detector (ML lane). Entry point: eval/skills/run_eval.py.

Compares the keyword baseline (backend.app.stubs.skills), Model A, Model B and the stacked ensemble on
the TEST split (never used for fitting), measures calibration before/after stacking, and draws a
reliability diagram, per-label confusion matrices and an F1 comparison chart.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from backend.app.ml.calibrate import expected_calibration_error, reliability_curve  # noqa: E402
from backend.app.ml.data import load_extra_test_sets, load_splits, to_xy  # noqa: E402
from backend.app.ml.metrics import THRESHOLD, per_label_scores  # noqa: E402
from backend.app.ml.model import LABELS, SkillModel  # noqa: E402
from backend.app.ml.uncertainty import DEFAULT_BAND, uncertainty_stats  # noqa: E402
from backend.app.stubs.skills import StubSkills  # noqa: E402

SYSTEMS = ("keyword_baseline", "model_a", "model_b", "ensemble")


def baseline_proba(texts: list[str], contexts: list[str]) -> np.ndarray:
    stub = StubSkills()
    return np.array(
        [
            [stub.predict(t, [c])[label] for label in LABELS]
            for t, c in zip(texts, contexts, strict=True)
        ]
    )


def brier(probs: np.ndarray, y: np.ndarray) -> float:
    """Mean squared gap between probability and the 0/1 truth over all row×label decisions."""
    return float(np.mean((np.asarray(probs) - np.asarray(y)) ** 2))


def score_rows(model: SkillModel, rows: list[dict], name: str = "test") -> dict:
    """Per-label scores for every system plus calibration and uncertainty numbers on one set of rows."""
    texts, contexts, y = to_xy(rows)
    comp = model.components(texts, contexts)
    probs = {
        "keyword_baseline": baseline_proba(texts, contexts),
        "model_a": comp.pa,
        "model_b": comp.pb,
        "ensemble": comp.p,
    }
    before = (comp.pa + comp.pb) / 2
    band = getattr(model, "uncertain_band", DEFAULT_BAND)
    return {
        "name": name,
        "n": len(rows),
        "scores": {system: per_label_scores(y, p) for system, p in probs.items()},
        "ece_before": round(expected_calibration_error(before, y), 4),
        "ece_after": round(expected_calibration_error(comp.p, y), 4),
        "brier_before": round(brier(before, y), 4),
        "brier_after": round(brier(comp.p, y), 4),
        "uncertain": uncertainty_stats(comp.pa, comp.pb, comp.p, y, band),
        "errors": top_errors(rows, comp.p, y),
        "_y": y,
        "_before": before,
        "_after": comp.p,
    }


def top_errors(rows: list[dict], probs: np.ndarray, y: np.ndarray, k: int = 10) -> list[dict]:
    """The k most confident wrong label decisions (for error analysis)."""
    wrong = [
        (abs(float(probs[i, j]) - y[i, j]), i, j)
        for i in range(len(rows))
        for j in range(len(LABELS))
        if (probs[i, j] >= THRESHOLD) != (y[i, j] == 1)
    ]
    out = []
    for _gap, i, j in sorted(wrong, key=lambda t: (-t[0], t[1], t[2]))[:k]:
        out.append(
            {
                "id": rows[i]["id"],
                "text": rows[i]["text"],
                "label": LABELS[j].value,
                "truth": bool(y[i, j]),
                "p": round(float(probs[i, j]), 3),
            }
        )
    return out


# Hand-written probes from the integrator's review (not a test set: a sanity check reported as-is).
PROBES = [
    ("you seemed off at lunch", "follow_up", "low"),
    ("ok i gotta go to school early tomorrow, talk later maybe", "follow_up", "low"),
    ("are you thinking about quitting the group chat?", "asked_directly", "low"),
    ("have you thought about quitting the team?", "asked_directly", "low"),
    ("i keep thinking about him", "asked_directly", "low"),
    ("ok but have you tried just not thinking about him", "asked_directly", "low"),
    (
        "can we talk to the counselor tomorrow? i'll go with you",
        "follow_up",
        "low",
    ),  # referral rule
    ("lots of people feel like that, you'll be fine", "validated", "low"),  # minimizing
    ("lots of people feel like that, you'll be fine", "advice_dump", "low"),
    ("lots of people feel like that, you'll be fine", "dismissed", "high"),
    ("i'm not going anywhere", "follow_up", "high"),
    ("i'm really glad you told me", "validated", "high"),
    ("i'll come over saturday if you want company", "follow_up", "high"),
    ("when you said disappear, did you mean you want to die?", "asked_directly", "high"),
    ("no tienes que pasar por esto solo, aquí estoy", "encouraged_help", "high"),
    ("you're not alone in this", "encouraged_help", "high"),
    ("be honest, are you having thoughts of ending it?", "almost_asked", "high"),
    ("are you thinking about quitting the team?", "almost_asked", "low"),
]


ALMOST_ASKED = "almost_asked"


def run_probes(model: SkillModel) -> list[dict]:
    texts = [t for t, _, _ in PROBES]
    comp = model.components(texts, [""] * len(texts))
    out = []
    for i, (text, label, expect) in enumerate(PROBES):
        if label == ALMOST_ASKED:  # the coaching flag, not a label probability
            value = float(comp.almost_asked[i])
        else:
            value = float(comp.p[i, [lab.value for lab in LABELS].index(label)])
        ok = value < THRESHOLD if expect == "low" else value >= THRESHOLD
        out.append({"text": text, "label": label, "expect": expect, "p": round(value, 3), "ok": ok})
    return out


def _norm(text: str) -> str:
    return "".join(ch for ch in text.lower() if ch.isalnum())


def unseen_rows(test: list[dict], fitted: list[dict]) -> list[dict]:
    """Test rows whose text (ignoring case/punctuation) never appears in train or val."""
    seen = {_norm(row["text"]) for row in fitted}
    return [row for row in test if _norm(row["text"]) not in seen]


def plot_reliability(result: dict, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.plot([0, 1], [0, 1], linestyle="--", color="#999", label="perfect calibration")
    for key, name, color in (
        ("_before", "before (avg of A, B)", "#d95f02"),
        ("_after", "after (stacked + Platt)", "#1b9e77"),
    ):
        x, obs, _ = reliability_curve(result[key], result["_y"])
        ece = result["ece_before" if key == "_before" else "ece_after"]
        ax.plot(x, obs, marker="o", color=color, label=f"{name}, ECE {ece:.3f}")
    ax.set(xlabel="predicted probability", ylabel="observed frequency", xlim=(0, 1), ylim=(0, 1))
    ax.set_title(f"Reliability on {result['name']} (n={result['n']} messages × 10 labels)")
    ax.legend(loc="upper left", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def plot_confusion(result: dict, path: Path) -> None:
    y, pred = result["_y"], (result["_after"] >= THRESHOLD).astype(int)
    fig, axes = plt.subplots(2, 5, figsize=(13, 5.6))
    for j, (label, ax) in enumerate(zip(LABELS, axes.ravel(), strict=True)):
        m = np.array([[np.sum((y[:, j] == t) & (pred[:, j] == p)) for p in (0, 1)] for t in (0, 1)])
        ax.imshow(m, cmap="Blues")
        for t in (0, 1):
            for p in (0, 1):
                ax.text(p, t, str(m[t, p]), ha="center", va="center", fontsize=11)
        ax.set_xticks([0, 1], ["pred no", "pred yes"], fontsize=7)
        ax.set_yticks([0, 1], ["true no", "true yes"], fontsize=7)
        ax.set_title(label.value, fontsize=9)
    fig.suptitle(f"Ensemble confusion matrices on {result['name']} (n={result['n']})")
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def plot_f1(result: dict, path: Path) -> None:
    labels = [label.value for label in LABELS]
    width = 0.2
    x = np.arange(len(labels))
    colors = ("#999999", "#7570b3", "#d95f02", "#1b9e77")
    fig, ax = plt.subplots(figsize=(12, 4.5))
    for i, (name, color) in enumerate(zip(SYSTEMS, colors, strict=True)):
        scores = result["scores"][name]
        ax.bar(
            x + (i - 1.5) * width,
            [scores[label]["f1"] for label in labels],
            width,
            color=color,
            label=f"{name} (macro-F1 {scores['macro_f1']:.2f})",
        )
    ax.set_xticks(x, labels, rotation=30, ha="right", fontsize=8)
    ax.set(ylabel=f"F1 on {result['name']}", ylim=(0, 1.18))
    ax.set_title(f"Per-label F1 on held-out {result['name']} (n={result['n']})")
    ax.legend(fontsize=8, ncol=4, loc="upper center")
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def to_records(results: dict[str, dict], notes: str) -> list[dict]:
    created = dt.datetime.now(dt.UTC).isoformat(timespec="seconds")

    def rec(metric: str, value: float, n: int, split: str, extra: str = "") -> dict:
        return {
            "lane": "ml",
            "metric": metric,
            "value": value,
            "n": n,
            "split": split,
            "notes": f"{extra}; {notes}" if extra else notes,
            "created": created,
        }

    records = []
    for split, result in results.items():
        n = result["n"]
        for name in SYSTEMS:
            records.append(rec(f"macro_f1_{name}", result["scores"][name]["macro_f1"], n, split))
        for label in LABELS:
            s = result["scores"]["ensemble"][label.value]
            records.append(
                rec(
                    f"f1_{label.value}",
                    s["f1"],
                    n,
                    split,
                    f"ensemble; precision {s['precision']}, recall {s['recall']}, support {s['support']}",
                )
            )
        records.append(
            rec("ece_before_calibration", result["ece_before"], n, split, "avg of A and B")
        )
        records.append(
            rec("ece_after_calibration", result["ece_after"], n, split, "stacked + Platt")
        )
        records.append(rec("brier_before_calibration", result["brier_before"], n, split))
        records.append(rec("brier_after_calibration", result["brier_after"], n, split))
        u = result["uncertain"]
        detail = (
            f"band {u['band']}; {u['flagged_decisions']} flagged decisions; error rate flagged "
            f"{u['flagged_error_rate']} vs unflagged {u['unflagged_error_rate']}"
        )
        records.append(rec("uncertain_flag_rate", u["flag_rate_per_message"], n, split, detail))
        if u["flagged_error_rate"] is not None:
            records.append(
                rec(
                    "uncertain_error_rate_flagged",
                    u["flagged_error_rate"],
                    u["flagged_decisions"],
                    split,
                    f"share of flagged label decisions that were wrong; n = decisions; band {u['band']}",
                )
            )
        if u["unflagged_error_rate"] is not None:
            records.append(
                rec(
                    "uncertain_error_rate_unflagged",
                    u["unflagged_error_rate"],
                    u["unflagged_decisions"],
                    split,
                    "share of unflagged label decisions that were wrong; n = decisions",
                )
            )
    return records


def run(model: SkillModel, data_dir: Path, report_path: Path, figure_dir: Path, notes: str) -> dict:
    """Evaluate on test (+ extra test sets), write the report and figures; return the results."""
    splits = load_splits(data_dir)
    if not splits["test"]:
        raise ValueError("empty test split")
    results = {"val": score_rows(model, splits["val"], "val")} if splits["val"] else {}
    results["test"] = score_rows(model, splits["test"], "test")
    unseen = unseen_rows(splits["test"], splits["train"] + splits["val"])
    if unseen and len(unseen) < len(splits["test"]):
        results["test_unseen_text"] = score_rows(model, unseen, "test_unseen_text")
    for name, rows in load_extra_test_sets(data_dir).items():
        results[name] = score_rows(model, rows, name)

    figure_dir.mkdir(parents=True, exist_ok=True)
    for split in ("test", "test_freeform"):
        if split in results:
            suffix = "" if split == "test" else "_freeform"
            plot_reliability(results[split], figure_dir / f"reliability{suffix}.png")
            plot_confusion(results[split], figure_dir / f"confusion{suffix}.png")
            plot_f1(results[split], figure_dir / f"f1_comparison{suffix}.png")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(to_records(results, notes), indent=2) + "\n", encoding="utf-8"
    )
    public = {
        split: {k: v for k, v in r.items() if not k.startswith("_")} for split, r in results.items()
    }
    public["probes"] = run_probes(model)
    (figure_dir / "results.json").write_text(json.dumps(public, indent=2) + "\n", encoding="utf-8")
    return public
