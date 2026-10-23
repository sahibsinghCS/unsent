"""Train the Guardian classifier (SAFETY lane). Run: make guardian-train

  1. load labeled helper messages (data lane + data/guardian_extra), seeded stratified split
  2. features = embedding(normalized text) + char_wb TF-IDF (2-5)
  3. multinomial logistic regression over {none, concern, self_risk, harm_to_other,
     method_seeking, prompt_injection}; asking_friend / tricky_negative / neutral -> "none"
  4. choose thresholds on VAL so the combined Guardian (lexicon + classifier) reaches
     self_risk recall >= 0.95 with asking_friend false positives <= 2%
  5. save artifacts/guardian[.hash].joblib + .meta.json (records the embedder; small)

By default it trains one artifact per embedder: the real multilingual model (used by the app)
and the hash embedder (used by offline tests). Use --embedder hash|fastembed to train just one.
"""

from __future__ import annotations

import argparse
import itertools
import json
import os
import time
from datetime import UTC, datetime

import joblib
import numpy as np
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from backend.app.embed import get_embedder, reset_embedder
from backend.app.safety.dataset import SEED, load_rows, sources, split_rows
from backend.app.safety.lexicon import get_lexicon
from backend.app.safety.model import (
    ARTIFACTS,
    CATEGORY_TO_CLASS,
    CLASSES,
    GuardianModel,
    Thresholds,
    artifact_paths,
    decide,
    featurize,
    save_meta,
)
from backend.app.safety.normalizer import normalize

RECALL_TARGET = 0.95
ASKING_FPR_TARGET = 0.02
RISK = {"self_risk", "concern", "harm_to_other", "method_seeking", "prompt_injection"}


def predicted_class(decision) -> str:
    """Map a Guardian decision to one class for scoring."""
    if decision.level == "crisis":
        return "self_risk"
    if decision.action == "block_message":
        return decision.categories[0] if decision.categories else "harm_to_other"
    if decision.level == "concern":
        return "concern"
    return "none"


def score(rows: list[dict], preds: list[str]) -> dict:
    """Headline numbers: self_risk recall (as crisis), asking_friend FPR, macro F1 over classes."""
    gold = [CATEGORY_TO_CLASS[r["category"]] for r in rows]
    self_idx = [i for i, r in enumerate(rows) if r["category"] == "self_risk"]
    ask_idx = [i for i, r in enumerate(rows) if r["category"] == "asking_friend"]
    recall = np.mean([preds[i] == "self_risk" for i in self_idx]) if self_idx else 1.0
    fpr = np.mean([preds[i] != "none" for i in ask_idx]) if ask_idx else 0.0
    f1s = []
    for c in CLASSES:
        tp = sum(g == c and p == c for g, p in zip(gold, preds, strict=True))
        fp = sum(g != c and p == c for g, p in zip(gold, preds, strict=True))
        fn = sum(g == c and p != c for g, p in zip(gold, preds, strict=True))
        f1s.append(2 * tp / (2 * tp + fp + fn) if tp + fp + fn else 1.0)
    return {
        "self_risk_recall": float(recall),
        "asking_fpr": float(fpr),
        "macro_f1": float(np.mean(f1s)),
    }


def choose_thresholds(rows: list[dict], lex: list, probs: list[dict]) -> tuple[Thresholds, dict]:
    """Grid-search thresholds on val: meet both targets, then maximise macro F1."""
    best, best_key = None, None
    grid = itertools.product(
        np.arange(0.20, 0.95, 0.05),  # crisis
        np.arange(0.40, 0.96, 0.05),  # block
        np.arange(0.50, 0.95, 0.05),  # concern: the classifier alone needs at least even odds
        (0.90, 0.95, 0.99),  # veto
    )
    for crisis, block, concern, veto in grid:
        th = Thresholds(*(round(float(x), 2) for x in (crisis, concern, block, veto)))
        preds = [predicted_class(decide(lx, p, th)) for lx, p in zip(lex, probs, strict=True)]
        s = score(rows, preds)
        ok = s["self_risk_recall"] >= RECALL_TARGET and s["asking_fpr"] <= ASKING_FPR_TARGET
        # targets first, then F1, then fewer asking-friend FPs, then higher (stricter) thresholds
        key = (ok, s["macro_f1"], -s["asking_fpr"], s["self_risk_recall"], block + concern + veto)
        if best_key is None or key > best_key:
            best, best_key = (th, {**s, "targets_met": ok}), key
    return best


def train_one(rows_by_split: dict[str, list[dict]]) -> dict:
    """Train + tune + save for the CURRENT embedder. Returns the meta dict."""
    embedder = get_embedder()
    started = time.perf_counter()
    norm = {k: [normalize(r["text"]).text for r in v] for k, v in rows_by_split.items()}
    y_train = [CATEGORY_TO_CLASS[r["category"]] for r in rows_by_split["train"]]

    vectorizer = TfidfVectorizer(
        analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True, min_df=2, max_features=12000
    )
    vectorizer.fit(norm["train"])
    clf = LogisticRegression(C=8.0, class_weight="balanced", max_iter=4000, random_state=SEED)
    clf.fit(featurize(norm["train"], vectorizer, embedder), y_train)

    model = GuardianModel(vectorizer, clf, {"embedder": embedder.name}, embedder)
    lexicon = get_lexicon()
    val_lex = [lexicon.scan(t) for t in norm["val"]]
    val_probs = model.predict_proba(norm["val"])
    thresholds, val_scores = choose_thresholds(rows_by_split["val"], val_lex, val_probs)

    ARTIFACTS.mkdir(exist_ok=True)
    model_path, meta_path = artifact_paths(embedder.name)
    joblib.dump({"vectorizer": vectorizer, "clf": clf}, model_path, compress=3)
    meta = {
        "embedder": embedder.name,
        "classes": CLASSES,
        "features": "embedding(normalized) + char_wb tfidf 2-5 (max 12000)",
        "model": "LogisticRegression(multinomial, C=8, class_weight=balanced)",
        "seed": SEED,
        "n": {k: len(v) for k, v in rows_by_split.items()},
        "sources": [f"{p.parent.name}/{p.name}" for p in sources()],
        "val": val_scores,
        "targets": {"self_risk_recall": RECALL_TARGET, "asking_fpr": ASKING_FPR_TARGET},
        "sklearn": sklearn.__version__,
        "train_seconds": round(time.perf_counter() - started, 1),
        "size_kb": round(model_path.stat().st_size / 1024, 1),
        "created": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    save_meta(meta_path, meta, thresholds)
    return {**meta, "thresholds": thresholds.__dict__}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--embedder", choices=["all", "hash", "fastembed"], default="all")
    args = parser.parse_args()
    rows = load_rows()
    if not rows:
        raise SystemExit("no Guardian data found (data/guardian or data/guardian_extra)")
    splits = split_rows(rows)
    backends = ["hash", "fastembed"] if args.embedder == "all" else [args.embedder]
    for backend in backends:
        os.environ["FR_EMBED"] = backend
        reset_embedder()
        try:
            meta = train_one(splits)
        except Exception as exc:  # noqa: BLE001 - e.g. the model can't be downloaded offline
            print(f"[{backend}] skipped: {exc}")
            continue
        print(
            f"[{backend}] {json.dumps({k: meta[k] for k in ('n', 'val', 'thresholds', 'size_kb')})}"
        )


if __name__ == "__main__":
    main()
