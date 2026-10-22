"""The trained skill-detector model: Model A (embeddings + LR), Model B (TF-IDF n-grams + LR) and the
per-label stacker. This object is what `train.py` saves with joblib and `skill_detector.py` loads.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion

from backend.app.contracts import SkillLabel
from backend.app.embed import embed
from backend.app.ml.calibrate import Stacker
from backend.app.ml.rules import gate_asked_directly

LABELS: tuple[SkillLabel, ...] = tuple(SkillLabel)


class ConstantModel:
    """Predicts the training prior when a label has only one class in the training data."""

    def __init__(self, prior: float) -> None:
        self.prior = prior

    def predict_proba(self, x) -> np.ndarray:
        n = x.shape[0]
        return np.column_stack([np.full(n, 1 - self.prior), np.full(n, self.prior)])


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
        pa, pb = self.base_proba(texts, contexts)
        for j, label in enumerate(self.labels):
            self.stackers[label] = Stacker(self.seed).fit(pa[:, j], pb[:, j], y[:, j])
        return self

    def base_proba(self, texts: list[str], contexts: list[str]) -> tuple[np.ndarray, np.ndarray]:
        xa = embed_features(texts, contexts)
        xb = self.vectorizer.transform(texts)
        pa = np.column_stack([self.model_a[label].predict_proba(xa)[:, 1] for label in self.labels])
        pb = np.column_stack([self.model_b[label].predict_proba(xb)[:, 1] for label in self.labels])
        return pa, pb

    def components(self, texts: list[str], contexts: list[str]) -> Components:
        pa, pb = self.base_proba(texts, contexts)
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
