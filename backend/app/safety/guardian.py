"""SAFETY lane entry point: the real Guardian.

check_user(helper message):  normalize -> speaker-aware lexicon -> trained classifier -> combine.
check_friend(friend line):   normalize -> unsafe-friend-line lexicon (plans, means, encouragement,
                             graphic detail, persona breaks). Anything flagged is never shown.

It works lexicon-only when the classifier artifact is missing or was built with a different
embedder, and it never raises: on an internal error it fails SAFE (resources for the helper,
the friend line blocked).
"""

from __future__ import annotations

import logging
import threading
import time

from backend.app.contracts import GuardianResult, Node
from backend.app.safety.lexicon import Hit, get_lexicon
from backend.app.safety.model import Decision, GuardianModel, Thresholds, decide
from backend.app.safety.normalizer import normalize

IMPLEMENTED = True
log = logging.getLogger(__name__)


class Guardian:
    def __init__(self, use_classifier: bool = True, use_lexicon: bool = True) -> None:
        self.use_classifier, self.use_lexicon = use_classifier, use_lexicon
        self._model: GuardianModel | None = None
        self._model_note = "not loaded"
        self._loaded = False
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ model loading
    def model(self) -> GuardianModel | None:
        """Lazy-load the classifier once; None means lexicon-only."""
        if not self.use_classifier:
            return None
        with self._lock:
            if not self._loaded:
                self._loaded = True
                try:
                    from backend.app.embed import get_embedder

                    self._model, self._model_note = GuardianModel.load(get_embedder())
                except Exception as exc:  # noqa: BLE001 - any load problem means lexicon-only
                    self._model, self._model_note = None, f"classifier unavailable: {exc}"
                log.info("guardian: %s", self._model_note)
        return self._model

    @property
    def thresholds(self) -> Thresholds:
        model = self.model()
        return model.thresholds if model else Thresholds()

    # ------------------------------------------------------------------ helper messages
    def check_user(self, text: str, history: list[Node]) -> GuardianResult:
        """Decide what to do with one HELPER message. Never raises."""
        start = time.perf_counter()
        try:
            decision = self._decide_user(text or "", history or [])
            return _result(decision, start)
        except Exception:  # noqa: BLE001 - fail safe, never crash the turn
            log.exception("guardian.check_user failed; failing safe")
            return GuardianResult(
                level="concern",
                action="show_resources",
                categories=["concern"],
                evidence=["guardian error: failed safe"],
                latency_ms=(time.perf_counter() - start) * 1000,
            )

    def _decide_user(self, text: str, history: list[Node]) -> Decision:
        norm = normalize(text)
        if not norm.text:
            return Decision()
        lexicon = get_lexicon()
        lex = lexicon.scan(norm) if self.use_lexicon else None
        if lex is not None and not lex.hits and lexicon.is_agreement(norm):
            shared = _friend_risk(history)
            if shared:
                lex.hits.append(Hit("concern", f"agreed with: {shared}", "me too after friend"))
            else:  # "same lol" about a test or a game is just small talk
                lex.allowed.append(Hit("agreement", norm.text, "friend shared nothing risky"))
        model = self.model()
        probs = model.predict_proba([norm.text])[0] if model else None
        return decide(lex, probs, model.thresholds if model else Thresholds())

    # ------------------------------------------------------------------ friend lines
    def check_friend(self, text: str) -> GuardianResult:
        """Flag a FRIEND line that must never be shown. Never raises (errors block the line)."""
        start = time.perf_counter()
        try:
            lex = get_lexicon().scan_friend(normalize(text or ""))
            if not lex.hits:
                return GuardianResult(
                    level="none", action="continue", latency_ms=_ms(start), sources=["lexicon"]
                )
            return GuardianResult(
                level="concern",
                action="block_message",
                categories=["unsafe_friend_line"],
                evidence=list(dict.fromkeys(f"{h.phrase} ({h.reason})" for h in lex.hits)),
                score=0.99,
                sources=["lexicon"],
                latency_ms=_ms(start),
            )
        except Exception:  # noqa: BLE001
            log.exception("guardian.check_friend failed; blocking the line")
            return GuardianResult(
                level="concern",
                action="block_message",
                categories=["unsafe_friend_line"],
                evidence=["guardian error: failed safe"],
                latency_ms=_ms(start),
            )


def _friend_risk(history: list[Node]) -> str | None:
    """The last friend message's risky phrase, if it shared suicidal thoughts or distress."""
    for node in reversed(history):
        if node.role == "friend" and node.bubbles:
            hits = get_lexicon().scan(" ".join(node.bubbles)).hits
            risky = [h for h in hits if h.category in ("self_risk", "concern")]
            return risky[0].phrase if risky else None
    return None


def _ms(start: float) -> float:
    return (time.perf_counter() - start) * 1000


def _result(d: Decision, start: float) -> GuardianResult:
    return GuardianResult(
        level=d.level,
        action=d.action,
        categories=d.categories,
        evidence=d.evidence,
        score=round(d.score, 4),
        sources=d.sources,
        latency_ms=_ms(start),
    )


_service: Guardian | None = None


def get_service() -> Guardian:
    """Shared Guardian (the classifier loads once)."""
    global _service
    if _service is None:
        _service = Guardian()
    return _service
