"""Evaluate the Guardian (SAFETY lane) -> eval/reports/safety_guardian.json + safety_pr_curve.png

Run: uv run python eval/guardian/run_eval.py      (part of `make eval`)

Reports, on the held-out TEST split (never used for training or threshold tuning):
  - per-class precision / recall / F1 for the combined Guardian
  - asking_friend false-positive rate (headline) and self_risk recall
  - lexicon-only vs classifier-only vs combined
  - robustness: share of decisions unchanged under perturbations, with vs without the normalizer
  - latency p50 / p95 per message on CPU
  - check_friend over every scenario friend line (should flag none)
Uses the real multilingual embedder when it is available, else the hash embedder (noted).
"""

from __future__ import annotations

import json
import os
import random
import statistics
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.app.config import DATA_DIR, EVAL_REPORTS_DIR  # noqa: E402
from backend.app.embed import get_embedder  # noqa: E402
from backend.app.safety import guardian as guardian_module  # noqa: E402
from backend.app.safety.dataset import load_rows, split_rows  # noqa: E402
from backend.app.safety.guardian import Guardian  # noqa: E402
from backend.app.safety.model import CATEGORY_TO_CLASS, CLASSES  # noqa: E402
from backend.app.safety.normalizer import Normalized, normalize  # noqa: E402
from backend.app.safety.train_guardian import predicted_class, score  # noqa: E402

LANE = "safety"
RISKY = {"self_risk", "concern", "harm_to_other", "method_seeking", "prompt_injection"}
CREATED = datetime.now(UTC).isoformat(timespec="seconds")
RECORDS: list[dict] = []


def record(metric: str, value: float, n: int, split: str = "test", notes: str = "") -> None:
    RECORDS.append(
        {
            "lane": LANE,
            "metric": metric,
            "value": round(float(value), 4),
            "n": n,
            "split": split,
            "notes": notes,
            "created": CREATED,
        }
    )


def classify(g: Guardian, texts: list[str]) -> list[str]:
    out = []
    for t in texts:
        r = g.check_user(t, [])
        d = type("D", (), {"level": r.level, "action": r.action, "categories": r.categories})
        out.append(predicted_class(d))
    return out


# ---------------------------------------------------------------- perturbations
LEET = str.maketrans({"o": "0", "e": "3", "i": "1", "a": "4"})


def _longest(words: list[str]) -> int:
    return max(range(len(words)), key=lambda i: len(words[i]))


def perturb(text: str, kind: str, rng: random.Random) -> str:
    words = text.split()
    if not words:
        return text
    i = _longest(words)
    w = words[i]
    if kind == "leetspeak":
        return text.translate(LEET)
    if kind == "spacing":
        words[i] = ".".join(w)
    elif kind == "stretching":
        vowels = [k for k, c in enumerate(w) if c in "aeiou"]
        if vowels:
            k = vowels[0]
            words[i] = w[:k] + w[k] * 4 + w[k + 1 :]
    elif kind == "emoji":
        return f"{text} {rng.choice(['😭', '💔', '😔', '🙏'])}"
    elif kind == "typo" and len(w) > 3:
        k = rng.randrange(1, len(w) - 2)
        words[i] = w[:k] + w[k + 1] + w[k] + w[k + 2 :]
    return " ".join(words)


def basic_normalize(text: str) -> Normalized:
    """The 'without normalizer' baseline: just lowercase and collapse spaces."""
    return Normalized(text=" ".join((text or "").lower().split()))


def robustness(g: Guardian, rows: list[dict]) -> dict[str, dict[str, float]]:
    kinds = ["leetspeak", "spacing", "stretching", "emoji", "typo"]
    out: dict[str, dict[str, float]] = {}
    for label, norm_fn in (("with_normalizer", normalize), ("without_normalizer", basic_normalize)):
        guardian_module.normalize = norm_fn
        try:
            base = [g.check_user(r["text"], []).action for r in rows]
            for kind in kinds:
                rng = random.Random(7)
                pert = [g.check_user(perturb(r["text"], kind, rng), []).action for r in rows]
                same = sum(a == b for a, b in zip(base, pert, strict=True)) / len(rows)
                out.setdefault(kind, {})[label] = same
        finally:
            guardian_module.normalize = normalize
    return out


def latency(g: Guardian, texts: list[str]) -> tuple[float, float]:
    g.check_user("warm up", [])
    times = []
    for _ in range(3):
        for t in texts:
            start = time.perf_counter()
            g.check_user(t, [])
            times.append((time.perf_counter() - start) * 1000)
    times.sort()
    return statistics.median(times), times[int(0.95 * (len(times) - 1))]


def per_class(rows: list[dict], preds: list[str]) -> dict[str, dict[str, float]]:
    gold = [CATEGORY_TO_CLASS[r["category"]] for r in rows]
    out = {}
    for c in CLASSES:
        tp = sum(g == c and p == c for g, p in zip(gold, preds, strict=True))
        fp = sum(g != c and p == c for g, p in zip(gold, preds, strict=True))
        fn = sum(g == c and p != c for g, p in zip(gold, preds, strict=True))
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        out[c] = {"precision": prec, "recall": rec, "f1": f1, "n": tp + fn}
    return out


def pr_curve(g: Guardian, rows: list[dict], path: Path, op_point: tuple[float, float]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from sklearn.metrics import average_precision_score, precision_recall_curve

    model = g.model()
    if model is None:
        return
    probs = model.predict_proba([normalize(r["text"]).text for r in rows])
    y = [r["category"] == "self_risk" for r in rows]
    s = [p["self_risk"] for p in probs]
    prec, rec, _ = precision_recall_curve(y, s)
    ap = average_precision_score(y, s)
    fig, ax = plt.subplots(figsize=(5, 4), dpi=120)
    ax.plot(rec, prec, color="#3b6fd8", lw=2, label=f"classifier p(self_risk), AP={ap:.2f}")
    ax.scatter([op_point[0]], [op_point[1]], color="#d8473b", zorder=3, label="combined Guardian")
    ax.set_xlabel("recall (helper at risk caught)")
    ax.set_ylabel("precision")
    ax.set_xlim(0, 1.02)
    ax.set_ylim(0, 1.02)
    ax.set_title(f"Guardian self-risk, test split (n={len(rows)})")
    ax.legend(loc="lower left", fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    record("self_risk_average_precision", ap, len(rows), notes="classifier only, PR curve PNG")


def friend_lines() -> list[str]:
    lines = []
    for path in sorted((DATA_DIR / "scenarios").glob("*.json")):
        sc = json.loads(path.read_text(encoding="utf-8"))
        lines += sc.get("opening", [])
        for bucket in sc.get("fallback_lines", {}).values():
            lines += bucket
    lines_dir = DATA_DIR / "lines"
    if not lines_dir.exists() and os.getenv("FR_GUARDIAN_DATA"):
        lines_dir = (
            Path(os.environ["FR_GUARDIAN_DATA"]).parent / "lines"
        )  # read-only data-lane copy
    for path in sorted(lines_dir.glob("*.jsonl")):
        for raw in path.read_text(encoding="utf-8").splitlines():
            if raw.strip():
                lines += json.loads(raw).get("bubbles", [])
    return lines


def main() -> None:
    try:
        embedder = get_embedder()
    except Exception:  # noqa: BLE001 - no model download possible: fall back to hash
        import os

        from backend.app.embed import reset_embedder

        os.environ["FR_EMBED"] = "hash"
        reset_embedder()
        embedder = get_embedder()
    rows = load_rows()
    test = split_rows(rows)["test"]
    texts = [r["text"] for r in test]
    emb_note = f"embedder={embedder.name}"

    combined, lex_only, clf_only = (
        Guardian(use_moderation=False),  # local numbers only; moderation_compare.py covers OpenAI
        Guardian(use_classifier=False, use_moderation=False),
        Guardian(use_lexicon=False, use_moderation=False),
    )
    if combined.model() is None:
        emb_note += " (classifier artifact missing: lexicon only)"
    results = {}
    for name, g in (
        ("combined", combined),
        ("lexicon_only", lex_only),
        ("classifier_only", clf_only),
    ):
        preds = classify(g, texts)
        results[name] = (preds, score(test, preds))
        s = results[name][1]
        record(f"{name}.macro_f1", s["macro_f1"], len(test), notes=f"6 classes; {emb_note}")
        n_ask = sum(r["category"] == "asking_friend" for r in test)
        n_self = sum(r["category"] == "self_risk" for r in test)
        record(
            f"{name}.asking_friend_fpr", s["asking_fpr"], n_ask, notes="asking the friend flagged"
        )
        record(
            f"{name}.self_risk_recall", s["self_risk_recall"], n_self, notes="helper risk -> crisis"
        )

    preds, s = results["combined"]
    record("asking_friend_fpr", s["asking_fpr"], n_ask, notes=f"HEADLINE, combined; {emb_note}")
    record(
        "self_risk_recall", s["self_risk_recall"], n_self, notes=f"HEADLINE, combined; {emb_note}"
    )
    flagged_any = [
        p != "none" for p, r in zip(preds, test, strict=True) if r["category"] == "self_risk"
    ]
    record(
        "self_risk_flagged_any",
        sum(flagged_any) / max(1, n_self),
        n_self,
        notes="crisis or other flag",
    )
    benign = [r for r in test if r["category"] not in RISKY]
    fp_benign = [
        p != "none" for p, r in zip(preds, test, strict=True) if r["category"] not in RISKY
    ]
    record(
        "benign_fpr",
        sum(fp_benign) / max(1, len(benign)),
        len(benign),
        notes="asking+tricky+neutral",
    )
    for source in sorted({r["source_file"] for r in test}):
        idx = [i for i, r in enumerate(test) if r["source_file"] == source]
        sub = [test[i] for i in idx]
        ss = score(sub, [preds[i] for i in idx])
        tag = "data_lane" if source.startswith("guardian/") else "safety_lane"
        n_a = sum(r["category"] == "asking_friend" for r in sub)
        n_s = sum(r["category"] == "self_risk" for r in sub)
        record(
            f"test_{tag}.asking_friend_fpr", ss["asking_fpr"], n_a, notes=f"test rows from {source}"
        )
        record(
            f"test_{tag}.self_risk_recall",
            ss["self_risk_recall"],
            n_s,
            notes=f"test rows from {source}",
        )
        record(f"test_{tag}.macro_f1", ss["macro_f1"], len(sub), notes=f"test rows from {source}")
    for c, m in per_class(test, preds).items():
        for k in ("precision", "recall", "f1"):
            record(f"{c}.{k}", m[k], m["n"], notes="combined")

    # paired speaker-awareness set (hand-written for tests/unit/safety/test_speaker_awareness.py)
    sys.path.insert(0, str(ROOT / "tests" / "unit" / "safety"))
    try:
        from test_speaker_awareness import PAIRS

        ask_flag = [combined.check_user(a, []).action != "continue" for _, _, a in PAIRS]
        risk_ok = [combined.check_user(r, []).action != "continue" for r, _, _ in PAIRS]
        record("pairs.asking_flagged_rate", sum(ask_flag) / len(PAIRS), len(PAIRS), "pairs", "")
        record("pairs.risky_caught_rate", sum(risk_ok) / len(PAIRS), len(PAIRS), "pairs", "")
    except ImportError:
        pass

    hold_path = DATA_DIR / "guardian_extra" / "holdout.jsonl"
    if hold_path.exists():
        hold = [json.loads(x) for x in hold_path.read_text(encoding="utf-8").splitlines() if x]
        hp, hs = classify(combined, [r["text"] for r in hold]), None
        hs = score(hold, hp)
        note = "written after freezing; never tuned on"
        n_ha = sum(r["category"] == "asking_friend" for r in hold)
        n_hs = sum(r["category"] == "self_risk" for r in hold)
        record("holdout.asking_friend_fpr", hs["asking_fpr"], n_ha, "holdout", note)
        record("holdout.self_risk_recall", hs["self_risk_recall"], n_hs, "holdout", note)
        record("holdout.macro_f1", hs["macro_f1"], len(hold), "holdout", note)
        for r, p in zip(hold, hp, strict=True):
            if p != CATEGORY_TO_CLASS[r["category"]]:
                print(f"holdout miss: {r['category']} -> {p}: {r['text']}")

    rob_rows = [r for r in test if r["category"] in RISKY | {"asking_friend"}]
    for kind, by in robustness(combined, rob_rows).items():
        for label, value in by.items():
            record(f"robustness.{kind}.{label}", value, len(rob_rows), notes="decisions unchanged")

    p50, p95 = latency(combined, texts)
    record("latency_ms_p50", p50, len(texts) * 3, notes=f"check_user, CPU; {emb_note}")
    record("latency_ms_p95", p95, len(texts) * 3, notes="target < 50 ms")

    lines = friend_lines()
    flagged = [line for line in lines if combined.check_friend(line).action != "continue"]
    record("friend_lines_flagged", len(flagged), len(lines), "scenarios+line_bank", "should be 0")

    op = per_class(test, preds)["self_risk"]
    EVAL_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    pr_curve(
        combined, test, EVAL_REPORTS_DIR / "safety_pr_curve.png", (op["recall"], op["precision"])
    )

    out = EVAL_REPORTS_DIR / "safety_guardian.json"
    out.write_text(json.dumps(RECORDS, indent=1, ensure_ascii=False) + "\n")
    for r in RECORDS:
        if "." not in r["metric"] or r["metric"].startswith(
            ("combined", "lexicon", "classifier", "test_", "holdout", "pairs")
        ):
            print(f"{r['metric']:<34} {r['value']:>8}  n={r['n']:<4} {r['split']:<9} {r['notes']}")
    for r in RECORDS:
        if r["metric"].startswith("robustness."):
            print(f"{r['metric']:<44} {r['value']:>8}")
    print(f"wrote {out.relative_to(ROOT)} ({len(RECORDS)} records)")
    if flagged:
        print("friend lines flagged:", flagged[:5])


if __name__ == "__main__":
    main()
