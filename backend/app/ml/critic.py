"""ML lane end-of-conversation critic.

For every helper message: calibrated label probabilities, "uncertain" flags (the two models disagree),
word highlights (occlusion) and, where a key skill was missing, a *verified* rewrite from the exemplar
bank. Then the 7-skill rubric summary, the engine's turning point and a short template summary.
Rewrites come from the human-written exemplar bank first. Only if no exemplar passes, the critic may ask
the LLM (backend/app/llm.py) for 2 candidates, and keeps one only if OUR detector scores it at least 0.2
higher on the missing skill and the Guardian passes it: "the AI suggests, our model verifies". With no
key (or FR_LLM=0) it is exemplars only. Summaries are templates.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path

from pydantic import BaseModel

from backend.app import content, llm, services
from backend.app.contracts import (
    CriticReport,
    Exemplar,
    Flags,
    MessageScore,
    Node,
    Session,
    SkillLabel,
    SkillProbs,
    State,
    TurningPoint,
)
from backend.app.embed import cosine, embed_one
from backend.app.ml.critic_text import TEXT, language_of, text_for
from backend.app.pipeline import friend_context

IMPLEMENTED = True

ON = 0.5  # a label counts as "done" at calibrated probability ≥ 0.5
MIN_REWRITE_GAIN = 0.2  # a rewrite must raise the missing skill by at least this much
MAX_CANDIDATES = 3  # exemplars tried per message before giving up
MAX_REWRITE_CHARS = 300
REWRITE_PROMPT = Path(__file__).parent / "prompts" / "rewrite.md"

SKILL_NAMES = TEXT["en"]["skill_names"]  # English names (kept for callers and tests)
MAX_SKILL_NOTES = 3
TIP_ORDER = ("ask_directly", "listen", "no_secrecy", "refer", "persuade", "check_in", "follow_up")


@dataclass(frozen=True)
class Target:
    """A skill that was missing at some message and the exemplar strategy that teaches it."""

    skill: str  # rubric skill that was missing
    strategy: str  # Exemplar.strategy
    labels: tuple[SkillLabel, ...]  # the rewrite is judged on max(p) over these
    reason_key: str  # key into critic_text TEXT[locale]["reasons"]
    improves: str  # rubric skill whose labels the rewrite gain is measured on (MessageScore.rewrite_skill)
    hint: str  # what the skill looks like (for the LLM prompt)

    def reason_text(self, locale: str = "en") -> str:
        return text_for(locale)["reasons"][self.reason_key]

    @property
    def reason(self) -> str:
        return self.reason_text("en")


ASK = Target(
    "ask_directly",
    "ask_directly",
    (SkillLabel.ASKED_DIRECTLY,),
    "ask",
    "ask_directly",
    "ask directly and calmly whether they are thinking about suicide or killing themselves.",
)
REFER = Target(
    "refer",
    "refer",
    (SkillLabel.REFERRED_ADULT, SkillLabel.REFERRED_988),
    "refer",
    "refer",
    "suggest a specific trusted adult (school counselor, parent, teacher) or 988, ideally offering to go with them.",
)
UNSECRET = Target(
    "no_secrecy",
    "refer",
    (SkillLabel.REFERRED_ADULT, SkillLabel.REFERRED_988),
    "unsecret",
    "refer",
    "say kindly that you can't keep this secret because you care, and suggest telling a trusted adult or 988 together.",
)
LISTEN = Target(
    "listen",
    "validate",
    (SkillLabel.VALIDATED,),
    "listen_dismissed",
    "listen",
    "reflect their feelings back without judging, fixing or giving advice.",
)
CHECK_IN = Target(
    "check_in",
    "check_in",
    (SkillLabel.CHECKED_IN,),
    "check_in",
    "check_in",
    "notice something seems off and ask how they're really doing.",
)


class RewriteCandidates(BaseModel):
    """JSON the LLM must return for the rewrite prompt."""

    candidates: list[str]


def target_score(probs: SkillProbs, target: Target) -> float:
    return max(probs.get(label, 0.0) for label in target.labels)


def missing_skill(probs: SkillProbs, before: State, first: bool) -> Target | None:
    """The most important skill this message should have shown but didn't (None if it was fine)."""
    p = lambda label: probs.get(label, 0.0)  # noqa: E731
    flags: Flags = before.flags
    if p(SkillLabel.PROMISED_SECRECY) >= ON:
        return UNSECRET
    dismissed, advice = p(SkillLabel.DISMISSED) >= ON, p(SkillLabel.ADVICE_DUMP) >= ON
    if dismissed or advice:
        key = (
            "listen_both"
            if dismissed and advice
            else "listen_dismissed"
            if dismissed
            else "listen_advice"
        )
        return replace(LISTEN, reason_key=key)
    if before.level >= 2 and not flags.asked_directly_ever and p(SkillLabel.ASKED_DIRECTLY) < ON:
        return ASK
    if (
        before.level >= 3
        and not flags.referral_turns
        and p(SkillLabel.ASKED_DIRECTLY) < ON
        and target_score(probs, REFER) < ON
    ):
        return REFER
    if first and max(p(SkillLabel.CHECKED_IN), p(SkillLabel.VALIDATED)) < ON:
        return CHECK_IN
    return None


def rubric_summary(all_probs: list[SkillProbs]) -> dict[str, float]:
    """The 7 rubric skills from the 10 labels (mapping in contracts.RUBRIC_SKILLS).

    Each skill is scored per message and the conversation gets its best message, except no_secrecy,
    which a single promise of secrecy breaks. "listen" is judged inside one message (validated and not
    dismissive/advice-dumping in that same message), so an early slip doesn't erase later listening.
    """

    def p(probs: SkillProbs, label: SkillLabel) -> float:
        return probs.get(label, 0.0)

    def peak(fn) -> float:
        return max((fn(probs) for probs in all_probs), default=0.0)

    summary = {
        "check_in": peak(lambda q: p(q, SkillLabel.CHECKED_IN)),
        "listen": peak(
            lambda q: (
                p(q, SkillLabel.VALIDATED)
                * (1.0 - max(p(q, SkillLabel.DISMISSED), p(q, SkillLabel.ADVICE_DUMP)))
            )
        ),
        "ask_directly": peak(lambda q: p(q, SkillLabel.ASKED_DIRECTLY)),
        "no_secrecy": 1.0 - peak(lambda q: p(q, SkillLabel.PROMISED_SECRECY)),
        "persuade": peak(lambda q: p(q, SkillLabel.ENCOURAGED_HELP)),
        "refer": peak(
            lambda q: max(p(q, SkillLabel.REFERRED_ADULT), p(q, SkillLabel.REFERRED_988))
        ),
        "follow_up": peak(lambda q: p(q, SkillLabel.FOLLOW_UP)),
    }
    return {skill: round(value, 4) for skill, value in summary.items()}


def rank_exemplars(
    exemplars: tuple[Exemplar, ...], target: Target, level: int, friend_last: str
) -> list[Exemplar]:
    """Exemplars teaching the target skill: nearest level first, then most similar to the friend."""
    matching = [
        ex
        for ex in exemplars
        if ex.strategy == target.strategy or any(label in ex.labels for label in target.labels)
    ]
    anchor = embed_one(friend_last) if friend_last else None

    def key(ex: Exemplar) -> tuple[int, float, str]:
        similarity = cosine(embed_one(ex.text), anchor) if anchor is not None else 0.0
        return (abs(ex.level - level), -similarity, ex.id)

    return sorted(matching, key=key)


class Critic:
    def __init__(self, detector=None, guardian=None, engine=None) -> None:
        self._detector, self._guardian, self._engine = detector, guardian, engine

    @property
    def detector(self):
        return self._detector or services.skills()

    @property
    def guardian(self):
        return self._guardian or services.guardian()

    @property
    def engine(self):
        return self._engine or services.engine()

    def score_conversation(self, session: Session, path: list[Node]) -> CriticReport:
        locale = session.locale
        words = text_for(locale)
        # Exemplars of the chat's own language only (never an English rewrite in a Spanish chat).
        exemplars = content.load_exemplars(session.scenario_id, locale)
        scores: list[MessageScore] = []
        missed: list[str] = []
        first = True
        for index, node in enumerate(path):
            if node.role != "user" or not node.bubbles or _blocked(node):
                continue
            text = " ".join(node.bubbles)
            context = friend_context(path[:index])
            before = path[index - 1].state_after if index else node.state_after
            score = self._score_message(node, text, context)
            target = missing_skill(score.probs, before, first)
            if target is not None:
                missed.append(
                    words["at"].format(text=_clip(text), reason=target.reason_text(locale))
                )
                self._add_rewrite(
                    score, target, exemplars, before.level, context, path[:index], text, locale
                )
            scores.append(score)
            first = False

        summary = rubric_summary([s.probs for s in scores])
        turning = self.engine.turning_point(path)
        if turning is not None and words["turning_reason"]:
            turning = turning.model_copy(update={"reason": words["turning_reason"]})
        # Every per-message note stays; whole-chat "never got to" notes are capped at the 3 most
        # important (TIP_ORDER), so a short chat isn't buried in a list of everything it didn't do.
        never = [skill for skill in TIP_ORDER if summary[skill] < ON][:MAX_SKILL_NOTES]
        missed.extend(missed_skill_text(skill, summary, locale) for skill in never)
        return CriticReport(
            per_message=scores,
            skill_summary=summary,
            turning_point=turning,
            missed_opportunities=_dedupe(missed),
            summary_text=summary_text(summary, turning, path, locale),
        )

    def _score_message(self, node: Node, text: str, context: list[str]) -> MessageScore:
        detector = self.detector
        probs = dict(node.events) if node.events else detector.predict(text, context)
        uncertain = detector.uncertain(text, context) if hasattr(detector, "uncertain") else []
        return MessageScore(
            node_id=node.id,
            probs=probs,
            uncertain=uncertain,
            highlights=detector.explain(text, context),
        )

    def _add_rewrite(
        self,
        score: MessageScore,
        target: Target,
        exemplars: tuple[Exemplar, ...],
        level: int,
        context: list[str],
        history: list[Node],
        text: str,
        locale: str = "en",
    ) -> None:
        """Attach a rewrite that measurably raises the missing skill and passes the Guardian.

        Exemplars first (human-written); the LLM only if none passes. Every candidate gets the same check.
        """
        friend_last = context[-1] if context else ""
        original = target_score(score.probs, target)
        ranked = rank_exemplars(exemplars, target, level, friend_last)[:MAX_CANDIDATES]
        for exemplar in ranked:
            gain = self._verified_gain(exemplar.text, target, original, context, history)
            if gain is not None:
                self._set_rewrite(score, exemplar.text, gain, "exemplar", target)
                return
        best: tuple[float, str] | None = None
        for candidate in llm_candidates(target, text, context, locale):
            gain = self._verified_gain(candidate, target, original, context, history)
            if gain is not None and (best is None or gain > best[0]):
                best = (gain, candidate)
        if best is not None:
            self._set_rewrite(score, best[1], best[0], "llm", target)

    def _verified_gain(
        self, text: str, target: Target, original: float, context: list[str], history: list[Node]
    ) -> float | None:
        """The candidate's gain on the target skill, or None if it gains < 0.2 or fails the Guardian."""
        gain = target_score(self._score_candidate(text, context), target) - original
        if gain < MIN_REWRITE_GAIN:
            return None
        if self.guardian.check_user(text, history).action != "continue":
            return None
        return gain

    def _score_candidate(self, text: str, context: list[str]) -> SkillProbs:
        """Score a rewrite candidate without starting a (wasted) background explanation for it."""
        detector = self.detector
        if hasattr(detector, "predict_many"):
            return detector.predict_many([text], context)[0]
        return detector.predict(text, context)

    @staticmethod
    def _set_rewrite(score: MessageScore, text: str, gain: float, source: str, target: Target):
        score.rewrite = text
        score.rewrite_gain = round(gain, 4)
        score.rewrite_source = source
        score.rewrite_skill = target.improves


def llm_candidates(
    target: Target, helper_text: str, context: list[str], locale: str = "en"
) -> list[str]:
    """Up to 2 LLM rewrite suggestions in the chat's language (unverified!), or [] if unavailable."""
    if not llm.enabled():
        return []
    system = (
        REWRITE_PROMPT.read_text(encoding="utf-8")
        .replace("{skill_hint}", target.hint)
        .replace("{language}", text_for(locale)["language"])
    )
    user = json.dumps(
        {
            "friend_said": context,
            "helper_replied": helper_text,
            "missing_skill": target.improves,
        },
        ensure_ascii=False,
    )
    try:
        answer = llm.chat_json(
            "rewrite",
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            RewriteCandidates,
            role="judge",
            temperature=0.4,
            seed=0,
            max_tokens=300,
        )
    except (llm.LLMUnavailable, ValueError):
        return []
    cleaned = [c.strip() for c in answer.candidates if isinstance(c, str) and c.strip()]
    want = "es" if locale == "es" else "en"
    return [
        c
        for c in cleaned
        if len(c) <= MAX_REWRITE_CHARS and c != helper_text.strip() and language_of(c) == want
    ][:2]


def summary_text(
    summary: dict[str, float], turning: TurningPoint | None, path: list[Node], locale: str = "en"
) -> str:
    """2–3 template sentences: best skill, turning point, one thing to try next time."""
    words = text_for(locale)
    ranked = sorted(
        (skill for skill in summary if skill != "no_secrecy"), key=lambda s: (-summary[s], s)
    )
    best = ranked[0] if ranked else None
    sentences = []
    ended_badly = bool(path) and path[-1].state_after.status == "ended_fail"
    if ended_badly:
        sentences.append(words["slipped"])
    elif best and summary[best] >= ON:
        sentences.append(words["strongest"].format(skill=words["skill_names"][best]))
    else:
        sentences.append(words["stayed"])
    if turning is None or round(turning.trust_drop) < 1:
        sentences.append(words["never_lost"])
    else:
        said = next((" ".join(n.bubbles) for n in path if n.id == turning.node_id), "")
        where = words["where"].format(said=_clip(said)) if said else ""
        sentences.append(words["pulled_back"].format(where=where, drop=f"{turning.trust_drop:.0f}"))
    tip = next((skill for skill in TIP_ORDER if summary.get(skill, 1.0) < ON), None)
    if tip == "persuade" and summary.get("refer", 0.0) >= ON:
        sentences.append(words["refer_tip"])
    elif tip:
        sentences.append(words["next"].format(tip=words["next_time"][tip]))
    else:
        sentences.append(words["covered_all"])
    return " ".join(sentences)


def missed_skill_text(skill: str, summary: dict[str, float], locale: str = "en") -> str:
    """One true sentence about a rubric skill the conversation never reached."""
    words = text_for(locale)
    if skill == "no_secrecy":
        return words["promised"]
    if skill == "persuade" and summary.get("refer", 0.0) >= ON:
        return words["referred_not_persuaded"]
    return words["never_got"].format(skill=words["skill_names"][skill])


def _blocked(node: Node) -> bool:
    return node.guardian is not None and node.guardian.action == "block_message"


def _clip(text: str, limit: int = 60) -> str:
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _dedupe(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def get_service() -> Critic:
    return Critic()
