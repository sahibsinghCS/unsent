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


def score_rows(model: SkillModel, rows: list[dict]) -> dict:
    """Per-label scores for every system plus calibration numbers on one set of rows."""
    texts, contexts, y = to_xy(rows)
    comp = model.components(texts, contexts)
    probs = {
        "keyword_baseline": baseline_proba(texts, contexts),
        "model_a": comp.pa,
        "model_b": comp.pb,
        "ensemble": comp.p,
    }
    before = (comp.pa + comp.pb) / 2
    return {
        "n": len(rows),
        "scores": {name: per_label_scores(y, p) for name, p in probs.items()},
        "ece_before": round(expected_calibration_error(before, y), 4),
        "ece_after": round(expected_calibration_error(comp.p, y), 4),
        "_y": y,
        "_before": before,
        "_after": comp.p,
    }


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
    ax.set_title(f"Reliability on test (n={result['n']} messages × 10 labels)")
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
    fig.suptitle(f"Ensemble confusion matrices on test (n={result['n']})")
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
    ax.set(ylabel="F1 on test", ylim=(0, 1))
    ax.set_title(f"Per-label F1 on the held-out test split (n={result['n']})")
    ax.legend(fontsize=8)
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
    return records


def run(model: SkillModel, data_dir: Path, report_path: Path, figure_dir: Path, notes: str) -> dict:
    """Evaluate on test (+ extra test sets), write the report and figures; return the results."""
    splits = load_splits(data_dir)
    if not splits["test"]:
        raise ValueError("empty test split")
    results = {"test": score_rows(model, splits["test"])}
    for name, rows in load_extra_test_sets(data_dir).items():
        results[name] = score_rows(model, rows)

    figure_dir.mkdir(parents=True, exist_ok=True)
    plot_reliability(results["test"], figure_dir / "reliability.png")
    plot_confusion(results["test"], figure_dir / "confusion.png")
    plot_f1(results["test"], figure_dir / "f1_comparison.png")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(to_records(results, notes), indent=2) + "\n", encoding="utf-8"
    )
    public = {
        split: {k: v for k, v in r.items() if not k.startswith("_")} for split, r in results.items()
    }
    (figure_dir / "results.json").write_text(json.dumps(public, indent=2) + "\n", encoding="utf-8")
    return public
