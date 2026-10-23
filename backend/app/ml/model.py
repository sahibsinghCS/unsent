"""The trained skill-detector model: Model A (embeddings + LR), Model B (TF-IDF n-grams + LR) and the
per-label stacker. This object is what `train.py` saves with joblib and `skill_detector.py` loads.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import numpy as np
from scipy.special import expit
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion

from backend.app.contracts import POSITIVE_LABELS, SkillLabel
from backend.app.embed import embed
from backend.app.ml.calibrate import Stacker
from backend.app.ml.rules import gate_asked_directly
from backend.app.ml.uncertainty import DEFAULT_BAND

LABELS: tuple[SkillLabel, ...] = tuple(SkillLabel)


class ConstantModel:
    """Predicts the training prior when a label has only one class in the training data."""

    def __init__(self, prior: float) -> None:
        self.prior = prior

    def predict_proba(self, x) -> np.ndarray:
        n = x.shape[0]
        return np.column_stack([np.full(n, 1 - self.prior), np.full(n, self.prior)])


def stacked_proba(models: dict[str, object], labels: tuple[str, ...], x) -> np.ndarray:
    """All labels' probabilities in one matrix product (same math as each LR's predict_proba)."""
    weights, bias, constant = [], [], {}
    for j, label in enumerate(labels):
        model = models[label]
        if isinstance(model, ConstantModel):
            constant[j] = model.prior
            weights.append(np.zeros(x.shape[1]))
            bias.append(0.0)
        else:
            weights.append(model.coef_[0])
            bias.append(float(model.intercept_[0]))
    probs = expit(np.asarray(x @ np.column_stack(weights)) + np.array(bias))
    for j, prior in constant.items():
        probs[:, j] = prior
    return probs


def fit_binary(x, y: np.ndarray, c: float, seed: int):
    """One balanced LogisticRegression, or a ConstantModel if y has a single class."""
    y = np.asarray(y, dtype=int)
    if y.min() == y.max():
        return ConstantModel(float(y.mean()))
    clf = LogisticRegression(C=c, class_weight="balanced", max_iter=3000, random_state=seed)
    return clf.fit(x, y)


def make_vectorizer() -> FeatureUnion:
    """Model B features: character n-grams inside word boundaries (robust to typos/slang) + word n-grams."""
    return FeatureUnion(
        [
            (
                "char",
                TfidfVectorizer(
                    analyzer="char_wb",
                    ngram_range=(2, 5),
                    lowercase=True,
                    sublinear_tf=True,
                    min_df=2,
                    max_features=30000,
                ),
            ),
            (
                "word",
                TfidfVectorizer(
                    analyzer="word",
                    ngram_range=(1, 2),
                    lowercase=True,
                    sublinear_tf=True,
                    token_pattern=r"(?u)\b\w+\b",
                    max_features=10000,
                ),
            ),
        ]
    )


SENTENCE_END = re.compile(r"(?<=[.!?…])\s+|\n+")


def sentences(text: str) -> list[str]:
    """The message's sentences (only if there are 2+, each with 2+ words); [] for one-sentence messages."""
    parts = [p.strip() for p in SENTENCE_END.split(text) if len(p.split()) >= 2]
    return parts if len(parts) >= 2 else []


def embed_features(texts: list[str], contexts: list[str]) -> np.ndarray:
    """Model A features: embed(reply) ⊕ embed(friend's last message); an empty context is a zero vector."""
    reply = embed(texts)
    unique = sorted({c for c in contexts if c})
    lookup = dict(zip(unique, embed(unique), strict=True)) if unique else {}
    ctx = np.zeros_like(reply)
    for row, context in enumerate(contexts):
        if context:
            ctx[row] = lookup[context]
    return np.hstack([reply, ctx])


@dataclass
class Components:
    """Probabilities (n_rows × 10 labels) from each stage."""

    pa: np.ndarray
    pb: np.ndarray
    p: np.ndarray


@dataclass
class SkillModel:
    embedder: str
    seed: int = 0
    c_a: float = 1.0
    c_b: float = 4.0
    labels: tuple[str, ...] = tuple(label.value for label in LABELS)
    vectorizer: FeatureUnion = field(default_factory=make_vectorizer)
    model_a: dict[str, object] = field(default_factory=dict)
    model_b: dict[str, object] = field(default_factory=dict)
    stackers: dict[str, Stacker] = field(default_factory=dict)
    uncertain_band: tuple[float, float] = DEFAULT_BAND  # tuned on val in train.py
    pooling: bool = False  # clause pooling for positive labels (see pooled_proba); decided on val

    def fit_base(self, texts: list[str], contexts: list[str], y: np.ndarray) -> SkillModel:
        """Fit Model A and Model B on the training split. y is (n_rows × 10) of 0/1."""
        xa = embed_features(texts, contexts)
        xb = self.vectorizer.fit_transform(texts)
        for j, label in enumerate(self.labels):
            self.model_a[label] = fit_binary(xa, y[:, j], self.c_a, self.seed)
            self.model_b[label] = fit_binary(xb, y[:, j], self.c_b, self.seed)
        return self

    def fit_stackers(self, texts: list[str], contexts: list[str], y: np.ndarray) -> SkillModel:
        """Fit the per-label Platt stacker on the validation split (never on training rows)."""
        pa, pb = self.scored_proba(texts, contexts)
        for j, label in enumerate(self.labels):
            self.stackers[label] = Stacker(self.seed).fit(pa[:, j], pb[:, j], y[:, j])
        return self

    def base_proba(self, texts: list[str], contexts: list[str]) -> tuple[np.ndarray, np.ndarray]:
        xa = embed_features(texts, contexts)
        xb = self.vectorizer.transform(texts)
        return stacked_proba(self.model_a, self.labels, xa), stacked_proba(
            self.model_b, self.labels, xb
        )

    def pooled_proba(self, texts: list[str], contexts: list[str]) -> tuple[np.ndarray, np.ndarray]:
        """Score the whole message and each of its sentences; POSITIVE labels take the max.

        "i'm really glad you told me. can we talk to the counselor?" then keeps "validated" from its
        first sentence instead of letting the referral dilute it. Negative labels (dismissed, advice,
        secrecy) stay on the whole message, so "i won't tell anyone... except the counselor" can't
        become a promise of secrecy.
        """
        owners, segment_texts, segment_contexts = [], [], []
        for row, (text, context) in enumerate(zip(texts, contexts, strict=True)):
            for segment in [text, *sentences(text)]:
                owners.append(row)
                segment_texts.append(segment)
                segment_contexts.append(context)
        pa_all, pb_all = self.base_proba(segment_texts, segment_contexts)
        owners_arr = np.array(owners)
        whole = np.array([owners.index(row) for row in range(len(texts))])
        pa, pb = pa_all[whole].copy(), pb_all[whole].copy()
        positive = [
            j for j, label in enumerate(self.labels) if SkillLabel(label) in POSITIVE_LABELS
        ]
        for row in range(len(texts)):
            rows = owners_arr == row
            pa[row, positive] = pa_all[rows][:, positive].max(axis=0)
            pb[row, positive] = pb_all[rows][:, positive].max(axis=0)
        return pa, pb

    def scored_proba(self, texts: list[str], contexts: list[str]) -> tuple[np.ndarray, np.ndarray]:
        """Model A and B probabilities as the stacker sees them (pooled or whole-message)."""
        if getattr(self, "pooling", False):
            return self.pooled_proba(texts, contexts)
        return self.base_proba(texts, contexts)

    def components(self, texts: list[str], contexts: list[str]) -> Components:
        pa, pb = self.scored_proba(texts, contexts)
        p = np.column_stack(
            [
                self.stackers[label].predict(pa[:, j], pb[:, j])
                for j, label in enumerate(self.labels)
            ]
        )
        # ML + a rule from the label definition (see ml/rules.py); Model A and B stay raw.
        j = self.labels.index(SkillLabel.ASKED_DIRECTLY.value)
        p[:, j] = gate_asked_directly(texts, list(p[:, j]))
        return Components(pa=pa, pb=pb, p=p)
