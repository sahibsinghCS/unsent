"""ML lane entry point for the skill detector.

Loads the trained two-model ensemble (models/skill_detector.joblib) lazily and returns calibrated
probabilities for the 10 SkillLabels. IMPLEMENTED is True only when a real artifact exists AND it was
trained with the same embedder that is active now (otherwise services.py keeps the keyword stub).
"""

from __future__ import annotations

import json
import threading
from pathlib import Path

import joblib

from backend.app.config import MODELS_DIR, embed_backend, embed_model_name
from backend.app.contracts import Highlight, SkillLabel, SkillProbs
from backend.app.embed import HashEmbedder, get_embedder
from backend.app.ml.explain import occlusion_highlights
from backend.app.ml.model import Components, SkillModel
from backend.app.ml.train import ARTIFACT, META

UNCERTAIN_GAP = 0.5  # |pA - pB| above this means the two models disagree


class EmbedderMismatchError(RuntimeError):
    """The artifact was trained with a different embedder than the one active now."""


def active_embedder_name() -> str:
    """Name of the embedder FR_EMBED selects, without loading the model."""
    return HashEmbedder.name if embed_backend() == "hash" else embed_model_name()


def artifact_ready(models_dir: Path = MODELS_DIR) -> bool:
    """True if a trained artifact exists and matches the active embedder."""
    meta_path = models_dir / META
    if not (models_dir / ARTIFACT).exists() or not meta_path.exists():
        return False
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return meta.get("embedder") == active_embedder_name()


IMPLEMENTED = artifact_ready()


def _context(context: list[str]) -> str:
    return context[-1] if context else ""


class SkillDetector:
    def __init__(self, models_dir: Path = MODELS_DIR) -> None:
        self.models_dir = models_dir
        self._model: SkillModel | None = None
        self._lock = threading.Lock()

    @property
    def model(self) -> SkillModel:
        with self._lock:
            if self._model is None:
                model: SkillModel = joblib.load(self.models_dir / ARTIFACT)
                active = get_embedder().name
                if model.embedder != active:
                    raise EmbedderMismatchError(
                        f"artifact trained with {model.embedder!r}, active embedder is {active!r}; "
                        "retrain with `make train` or set FR_EMBED to match"
                    )
                self._model = model
        return self._model

    def components(self, texts: list[str], context: list[str]) -> Components:
        """pA, pB and calibrated p for a batch of replies to the same friend context."""
        last = _context(context)
        return self.model.components(list(texts), [last] * len(texts))

    def _to_probs(self, row) -> SkillProbs:
        return {SkillLabel(label): float(row[j]) for j, label in enumerate(self.model.labels)}

    def predict_many(self, texts: list[str], context: list[str]) -> list[SkillProbs]:
        if not texts:
            return []
        return [self._to_probs(row) for row in self.components(texts, context).p]

    def predict(self, text: str, context: list[str]) -> SkillProbs:
        """Calibrated probability (0..1) for each of the 10 labels."""
        return self.predict_many([text], context)[0]

    def uncertain(self, text: str, context: list[str]) -> list[SkillLabel]:
        """Labels where Model A and Model B disagree by more than 0.5."""
        comp = self.components([text], context)
        gap = abs(comp.pa[0] - comp.pb[0])
        return [
            SkillLabel(label) for j, label in enumerate(self.model.labels) if gap[j] > UNCERTAIN_GAP
        ]

    def explain(self, text: str, context: list[str]) -> list[Highlight]:
        """Word highlights from leave-one-word-out occlusion on the calibrated probability."""
        return occlusion_highlights(text, lambda texts: self.predict_many(texts, context))


_service: SkillDetector | None = None


def get_service() -> SkillDetector:
    global _service
    if _service is None:
        _service = SkillDetector()
    return _service
