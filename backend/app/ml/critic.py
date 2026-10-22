"""ML lane end-of-conversation critic.

For every helper message: calibrated label probabilities, "uncertain" flags (the two models disagree),
word highlights (occlusion) and, where a key skill was missing, a *verified* rewrite from the exemplar
bank. Then the 7-skill rubric summary, the engine's turning point and a short template summary.
No AI text generation anywhere: rewrites are human-written exemplars, summaries are templates.
"""

from __future__ import annotations

from dataclasses import dataclass

from backend.app import content, services
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
from backend.app.pipeline import friend_context

IMPLEMENTED = True

ON = 0.5  # a label counts as "done" at calibrated probability ≥ 0.5
MIN_REWRITE_GAIN = 0.2  # a rewrite must raise the missing skill by at least this much
MAX_CANDIDATES = 3  # exemplars tried per message before giving up

SKILL_NAMES = {
    "check_in": "checking in",
    "listen": "listening without judging",
    "ask_directly": "asking directly about suicide",
    "no_secrecy": "not promising secrecy",
    "persuade": "encouraging them to get help",
    "refer": "connecting them to a trusted adult or 988",
    "follow_up": "following up",
}
NEXT_TIME = {
    "ask_directly": "when your friend sounds hopeless, ask them directly: "
    "“are you thinking about killing yourself?” Asking does not put the idea in their head.",
    "listen": "reflect what they said back (“that sounds really heavy”) before giving any advice.",
    "refer": "offer to go with them to a trusted adult like the school counselor, or text 988 together.",
    "no_secrecy": "don’t promise to keep it secret; say you care too much to keep it to yourself.",
    "persuade": "tell them they don’t have to handle this alone and that talking to someone helps.",
    "check_in": "open by noticing something is off: “you seemed really off today, you ok?”",
    "follow_up": "say when you’ll check in again, like “i’ll text you tonight.”",
}
TIP_ORDER = ("ask_directly", "listen", "no_secrecy", "refer", "persuade", "check_in", "follow_up")


@dataclass(frozen=True)
class Target:
    """A skill that was missing at some message and the exemplar strategy that teaches it."""

    skill: str  # rubric skill
    strategy: str  # Exemplar.strategy
    labels: tuple[SkillLabel, ...]  # the rewrite is judged on max(p) over these
    reason: str


ASK = Target(
    "ask_directly",
    "ask_directly",
    (SkillLabel.ASKED_DIRECTLY,),
    "your friend was sounding hopeless and you hadn't asked directly about suicide yet",
)
REFER = Target(
    "refer",
    "refer",
    (SkillLabel.REFERRED_ADULT, SkillLabel.REFERRED_988),
    "your friend had shared how bad it was and nobody had mentioned a trusted adult or 988",
)
UNSECRET = Target(
    "no_secrecy",
    "refer",
    (SkillLabel.REFERRED_ADULT, SkillLabel.REFERRED_988),
    "you promised to keep it secret; a safer reply brings in a trusted adult",
)
LISTEN = Target(
    "listen",
    "validate",
    (SkillLabel.VALIDATED,),
    "the reply brushed off or tried to fix the feeling instead of listening",
)
CHECK_IN = Target(
    "check_in", "check_in", (SkillLabel.CHECKED_IN,), "the first message didn't check in"
)


def target_score(probs: SkillProbs, target: Target) -> float:
    return max(probs.get(label, 0.0) for label in target.labels)


def missing_skill(probs: SkillProbs, before: State, first: bool) -> Target | None:
    """The most important skill this message should have shown but didn't (None if it was fine)."""
    p = lambda label: probs.get(label, 0.0)  # noqa: E731
    flags: Flags = before.flags
    if p(SkillLabel.PROMISED_SECRECY) >= ON:
        return UNSECRET
    if max(p(SkillLabel.DISMISSED), p(SkillLabel.ADVICE_DUMP)) >= ON:
        return LISTEN
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
    """The 7 rubric skills from the 10 labels (mapping in contracts.RUBRIC_SKILLS), peak over messages."""

    def peak(label: SkillLabel) -> float:
        return max((p.get(label, 0.0) for p in all_probs), default=0.0)

    negative = max(peak(SkillLabel.DISMISSED), peak(SkillLabel.ADVICE_DUMP))
    summary = {
        "check_in": peak(SkillLabel.CHECKED_IN),
        "listen": peak(SkillLabel.VALIDATED) * (1.0 - negative),
        "ask_directly": peak(SkillLabel.ASKED_DIRECTLY),
        "no_secrecy": 1.0 - peak(SkillLabel.PROMISED_SECRECY),
        "persuade": peak(SkillLabel.ENCOURAGED_HELP),
        "refer": max(peak(SkillLabel.REFERRED_ADULT), peak(SkillLabel.REFERRED_988)),
        "follow_up": peak(SkillLabel.FOLLOW_UP),
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
        exemplars = content.load_exemplars(session.scenario_id, session.locale)
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
                missed.append(f"At “{_clip(text)}”: {target.reason}.")
                self._add_rewrite(score, target, exemplars, before.level, context, path[:index])
            scores.append(score)
            first = False

        summary = rubric_summary([s.probs for s in scores])
        turning = self.engine.turning_point(path)
        for skill in TIP_ORDER:
            if summary[skill] < ON:
                missed.append(
                    "You promised to keep it secret."
                    if skill == "no_secrecy"
                    else f"You never got to {SKILL_NAMES[skill]}."
                )
        return CriticReport(
            per_message=scores,
            skill_summary=summary,
            turning_point=turning,
            missed_opportunities=_dedupe(missed),
            summary_text=summary_text(summary, turning, path),
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
    ) -> None:
        """Attach the best exemplar that measurably raises the missing skill and passes the Guardian."""
        friend_last = context[-1] if context else ""
        original = target_score(score.probs, target)
        for exemplar in rank_exemplars(exemplars, target, level, friend_last)[:MAX_CANDIDATES]:
            gain = target_score(self.detector.predict(exemplar.text, context), target) - original
            if gain < MIN_REWRITE_GAIN:
                continue
            if self.guardian.check_user(exemplar.text, history).action != "continue":
                continue
            score.rewrite = exemplar.text
            score.rewrite_gain = round(gain, 4)
            return


def summary_text(summary: dict[str, float], turning: TurningPoint | None, path: list[Node]) -> str:
    """2–3 template sentences: best skill, turning point, one thing to try next time."""
    ranked = sorted(
        (skill for skill in summary if skill != "no_secrecy"), key=lambda s: (-summary[s], s)
    )
    best = ranked[0] if ranked else None
    sentences = []
    if best and summary[best] >= ON:
        sentences.append(f"Your strongest skill was {SKILL_NAMES[best]}.")
    else:
        sentences.append("You stayed in the conversation, and that is where helping starts.")
    if turning is not None:
        said = next((" ".join(n.bubbles) for n in path if n.id == turning.node_id), "")
        where = f" after you said “{_clip(said)}”" if said else ""
        sentences.append(
            f"Your friend pulled back the most{where} (trust −{turning.trust_drop:.0f})."
        )
    tip = next((skill for skill in TIP_ORDER if summary.get(skill, 1.0) < ON), None)
    if tip:
        sentences.append(f"Next time, {NEXT_TIME[tip]}")
    else:
        sentences.append(
            "You covered every skill. Next time, try it with a friend who is more guarded."
        )
    return " ".join(sentences)


def _blocked(node: Node) -> bool:
    return node.guardian is not None and node.guardian.action == "block_message"


def _clip(text: str, limit: int = 60) -> str:
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _dedupe(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def get_service() -> Critic:
    return Critic()
