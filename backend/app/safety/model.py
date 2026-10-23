"""The Guardian's trained classifier and the rule that combines it with the lexicon (SAFETY lane).

Features: sentence embedding of the normalized text, joined with character n-gram TF-IDF (2-5).
Model: one multinomial logistic regression over the six Guardian classes.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
from scipy import sparse

from backend.app.safety.lexicon import LexiconResult

ARTIFACTS = Path(__file__).with_name("artifacts")
CLASSES = ["none", "concern", "self_risk", "harm_to_other", "method_seeking", "prompt_injection"]
BLOCK_CLASSES = ("harm_to_other", "method_seeking", "prompt_injection")
# Dataset categories that are SAFE map to "none" for training.
CATEGORY_TO_CLASS = {
    "asking_friend": "none",
    "tricky_negative": "none",
    "neutral": "none",
    **{c: c for c in CLASSES},
}
HASH_EMBEDDER = "hash-char-ngrams-512"
EMBED_WEIGHT = 1.0  # scales the dense embedding block against the TF-IDF block


@dataclass
class Thresholds:
    """Classifier probability cut-offs, chosen on the validation split by train_guardian."""

    crisis: float = 0.60  # p(self_risk) at or above this -> crisis
    concern: float = 0.45  # p(self_risk) + p(concern) at or above this -> concern
    block: float = 0.70  # p(harm/method/injection) at or above this -> block
    veto: float = 0.97  # if the lexicon saw an allowed phrase, the classifier needs this much


@dataclass
class Decision:
    level: str = "none"
    action: str = "continue"
    categories: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    score: float = 0.0
    sources: list[str] = field(default_factory=list)


def artifact_paths(embedder_name: str) -> tuple[Path, Path]:
    """Model + meta file for an embedder. Tests (hash embedder) get their own small artifact."""
    stem = "guardian.hash" if embedder_name == HASH_EMBEDDER else "guardian"
    return ARTIFACTS / f"{stem}.joblib", ARTIFACTS / f"{stem}.meta.json"


def featurize(texts: list[str], vectorizer, embedder) -> sparse.csr_matrix:
    """normalized texts -> [embedding | char TF-IDF] sparse matrix."""
    dense = embedder.embed(list(texts)) * EMBED_WEIGHT
    return sparse.hstack([sparse.csr_matrix(dense), vectorizer.transform(texts)]).tocsr()


class GuardianModel:
    """Loaded classifier. Refuses to load if it was trained with a different embedder."""

    def __init__(self, vectorizer, clf, meta: dict, embedder) -> None:
        self.vectorizer, self.clf, self.meta, self.embedder = vectorizer, clf, meta, embedder
        self.thresholds = Thresholds(**meta.get("thresholds", {}))

    @classmethod
    def load(cls, embedder) -> tuple[GuardianModel | None, str]:
        """(model, note). Model is None (lexicon-only) if missing or built for another embedder."""
        import joblib

        model_path, meta_path = artifact_paths(embedder.name)
        if not model_path.exists() or not meta_path.exists():
            return None, f"no classifier artifact for embedder {embedder.name}; lexicon only"
        meta = json.loads(meta_path.read_text())
        if meta.get("embedder") != embedder.name:
            return (
                None,
                f"artifact embedder {meta.get('embedder')} != {embedder.name}; lexicon only",
            )
        bundle = joblib.load(model_path)
        return cls(bundle["vectorizer"], bundle["clf"], meta, embedder), "classifier loaded"

    def predict_proba(self, normalized_texts: list[str]) -> list[dict[str, float]]:
        probs = self.clf.predict_proba(featurize(normalized_texts, self.vectorizer, self.embedder))
        order = list(self.clf.classes_)
        return [{c: float(row[order.index(c)]) for c in CLASSES} for row in probs]


def decide(lex: LexiconResult | None, probs: dict[str, float] | None, th: Thresholds) -> Decision:
    """Combine lexicon and classifier. Priority: crisis > block > concern > none.

    The lexicon is trusted when it fires (it is speaker-aware and human-reviewed). The classifier
    catches phrasings the lexicon has never seen, but if the lexicon found an ALLOWED phrase
    (asking the friend, everyday hyperbole) and nothing risky, the classifier needs th.veto
    confidence to overrule it. This protects the skill we teach.
    """
    d = Decision()
    lex_cats = lex.categories if lex else []
    vetoed = bool(lex and lex.allowed and not lex.hits)
    need = (lambda t: max(t, th.veto)) if vetoed else (lambda t: t)

    clf_cat, clf_score = None, 0.0
    if probs:
        p_self, p_concern = probs["self_risk"], probs["concern"]
        best_block = max(BLOCK_CLASSES, key=lambda c: probs[c])
        if p_self >= need(th.crisis):
            clf_cat, clf_score = "self_risk", p_self
        elif probs[best_block] >= need(th.block):
            clf_cat, clf_score = best_block, probs[best_block]
        elif p_self + p_concern >= need(th.concern):
            clf_cat, clf_score = "concern", p_self + p_concern

    def take(category: str, source_lex: bool) -> None:
        d.categories.append(category)
        if lex and source_lex:
            d.evidence += [h.phrase for h in lex.hits if h.category == category]
            if "lexicon" not in d.sources:
                d.sources.append("lexicon")
        if clf_cat == category:
            d.evidence.append(f"classifier p({category})={clf_score:.2f}")
            if "classifier" not in d.sources:
                d.sources.append("classifier")

    found = set(lex_cats) | ({clf_cat} if clf_cat else set())
    lex_block = set(lex_cats) & set(BLOCK_CLASSES)
    if clf_cat == "self_risk" and lex_block and "self_risk" not in lex_cats and clf_score < th.veto:
        # "go kms" is aimed at the friend: a lexicon block outranks a classifier-only crisis guess
        found.discard("self_risk")
    if "self_risk" in found:
        d.level, d.action = "crisis", "pause_roleplay"
        take("self_risk", "self_risk" in lex_cats)
    elif found & set(BLOCK_CLASSES):
        d.level, d.action = "none", "block_message"
        for cat in BLOCK_CLASSES:
            if cat in found:
                take(cat, cat in lex_cats)
    elif "concern" in found:
        d.level, d.action = "concern", "show_resources"
        take("concern", "concern" in lex_cats)

    if d.categories:
        d.score = max(0.99 if "lexicon" in d.sources else 0.0, clf_score)
    elif probs:
        d.score = max(probs[c] for c in CLASSES if c != "none")
    d.evidence = list(dict.fromkeys(d.evidence))[:6]
    return d


def save_meta(meta_path: Path, meta: dict, thresholds: Thresholds) -> None:
    meta = {**meta, "thresholds": asdict(thresholds)}
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")


def as_dense(x) -> np.ndarray:
    return x.toarray() if sparse.issparse(x) else np.asarray(x)
