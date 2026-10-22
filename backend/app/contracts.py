"""Shared data contracts for FirstReply.

FROZEN: only the integrator changes this file, and only additively (new optional fields).
Every lane codes against these types. Read this file first.
"""

from __future__ import annotations

import time
from enum import StrEnum
from typing import Literal, Protocol

from pydantic import BaseModel, Field

CONTRACTS_VERSION = "1.0"


class SkillLabel(StrEnum):
    """The 10 behaviours the skill detector predicts for each helper (user) message."""

    CHECKED_IN = "checked_in"  # noticed something was off / reached out ("you ok? you seemed off")
    VALIDATED = "validated"  # reflected feelings without judging ("that sounds really heavy")
    ASKED_DIRECTLY = "asked_directly"  # asked directly about suicide ("are you thinking about killing yourself?")
    ENCOURAGED_HELP = "encouraged_help"  # encouraged talking to someone / getting help
    REFERRED_ADULT = "referred_adult"  # named a trusted adult / counselor, offered to go with them
    REFERRED_988 = "referred_988"  # mentioned 988 / a crisis line
    FOLLOW_UP = "follow_up"  # committed to stay / check in again
    DISMISSED = "dismissed"  # minimized, joked, changed subject ("lol you'll be fine")   [negative]
    ADVICE_DUMP = (
        "advice_dump"  # jumped to fixing or lecturing ("just sleep more")        [negative]
    )
    PROMISED_SECRECY = "promised_secrecy"  # agreed to keep it secret                     [negative]


POSITIVE_LABELS: tuple[SkillLabel, ...] = (
    SkillLabel.CHECKED_IN,
    SkillLabel.VALIDATED,
    SkillLabel.ASKED_DIRECTLY,
    SkillLabel.ENCOURAGED_HELP,
    SkillLabel.REFERRED_ADULT,
    SkillLabel.REFERRED_988,
    SkillLabel.FOLLOW_UP,
)
NEGATIVE_LABELS: tuple[SkillLabel, ...] = (
    SkillLabel.DISMISSED,
    SkillLabel.ADVICE_DUMP,
    SkillLabel.PROMISED_SECRECY,
)

# The 7 rubric skills shown to users (docs/RUBRIC.md), derived from the 10 labels in ml/critic.py:
# check_in = CHECKED_IN; listen = VALIDATED and not (DISMISSED or ADVICE_DUMP);
# ask_directly = ASKED_DIRECTLY; no_secrecy = not PROMISED_SECRECY; persuade = ENCOURAGED_HELP;
# refer = REFERRED_ADULT or REFERRED_988; follow_up = FOLLOW_UP.
RUBRIC_SKILLS: tuple[str, ...] = (
    "check_in",
    "listen",
    "ask_directly",
    "no_secrecy",
    "persuade",
    "refer",
    "follow_up",
)

SkillProbs = dict[SkillLabel, float]  # probability 0..1 per label


class Reaction(StrEnum):
    """Why the friend is replying the way they are. Selects lines from the line bank."""

    OPENING = "opening"  # first messages of a scenario
    NEUTRAL = "neutral"  # nothing notable happened
    CHECKED_IN = "checked_in"
    VALIDATED = "validated"
    ASKED_DIRECTLY = "asked_directly"
    ENCOURAGED_HELP = "encouraged_help"
    REFERRED = "referred"  # helper suggested a trusted adult or 988
    FOLLOW_UP = "follow_up"
    DISMISSED = "dismissed"
    ADVICE_DUMP = "advice_dump"
    PROMISED_SECRECY = "promised_secrecy"
    SECRECY_BROKEN = "secrecy_broken"  # helper referred after promising secrecy ("you promised...")
    OFF_TOPIC = "off_topic"  # helper said something unrelated / confusing
    SUCCESS = "success"  # friend accepts help (conversation ends well)
    FAIL = "fail"  # friend shuts down (conversation ends badly)


# ---------------------------------------------------------------- scenario content


class Fact(BaseModel):
    """Something the friend can reveal once the conversation reaches the fact's level."""

    id: str
    text: str


class LevelSpec(BaseModel):
    label: str  # e.g. "surface", "stress", "hopeless", "suicidal thoughts", "open to help"
    facts: list[Fact]


class Persona(BaseModel):
    name: str
    age: int
    style: str  # how they text (lowercase, emoji, sarcasm when guarded...)
    guardedness: Literal["open", "guarded"]


class Scenario(BaseModel):
    id: str
    title: str
    persona: Persona
    situation: str  # shown to the helper before starting
    opening: list[str]  # the friend's first messages
    levels: dict[int, LevelSpec]  # disclosure levels 0..4. NEVER contains methods, means or plans.
    fallback_lines: dict[int, list[str]]  # safe generic lines per level, used if no bank line fits
    content_warning: str
    review_status: Literal["draft", "reviewed"] = "draft"


class Line(BaseModel):
    """One pre-written friend reply in the line bank (data/lines/<scenario_id>.<locale>.jsonl)."""

    id: str
    scenario_id: str
    locale: str = "en"
    level: int  # disclosure level this line belongs to (0..4)
    reaction: Reaction
    bubbles: list[str] = Field(min_length=1, max_length=3)  # 1-3 text bubbles
    fact_ids: list[str] = Field(default_factory=list)  # facts this line reveals (must be <= level)
    cue: str | None = None  # an example helper message this line best follows (for similarity)
    tone: str = ""
    review_status: Literal["draft", "reviewed"] = "draft"


class Exemplar(BaseModel):
    """A strong (or deliberately weak) example helper reply (data/exemplars/<scenario_id>.<locale>.jsonl).

    Used for rewrite suggestions in the feedback report and as candidates in "what if" rollouts.
    """

    id: str
    scenario_id: str
    locale: str = "en"
    level: int
    strategy: Literal["check_in", "validate", "ask_directly", "refer", "follow_up", "combo"]
    text: str
    labels: list[SkillLabel] = Field(default_factory=list)


# ---------------------------------------------------------------- per-message results


class Highlight(BaseModel):
    """A span of the helper's message that pushed a label's probability up (delta > 0)."""

    start: int
    end: int
    text: str
    label: SkillLabel
    delta: float


class GuardianResult(BaseModel):
    """Safety decision for one message.

    For HELPER messages (check_user):
      - "crisis"  + pause_roleplay  -> the helper themself seems at risk ("honestly i want to die too")
      - "concern" + show_resources  -> ambiguous distress from the helper; show gentle resources, continue
      - block_message               -> harmful toward the friend ("kys", "just do it"), method-seeking,
                                       or prompt injection. Categories say which.
      - IMPORTANT: asking the friend directly ("are you thinking about killing yourself?") is the
        RIGHT move and must return level "none" / action "continue".
    For FRIEND lines (check_friend): anything other than "none" means the line must not be shown.
    """

    level: Literal["none", "concern", "crisis"]
    action: Literal["continue", "show_resources", "pause_roleplay", "block_message"]
    categories: list[str] = Field(default_factory=list)
    # categories: self_risk | concern | harm_to_other | method_seeking | prompt_injection | unsafe_friend_line
    evidence: list[str] = Field(default_factory=list)
    score: float = 0.0
    sources: list[Literal["lexicon", "classifier"]] = Field(default_factory=list)
    latency_ms: float = 0.0


# ---------------------------------------------------------------- conversation state


class Flags(BaseModel):
    asked_directly_ever: bool = False
    promised_secrecy: bool = False
    referral_turns: list[int] = Field(default_factory=list)  # turns where the helper referred


class State(BaseModel):
    trust: float = 30.0  # 0..100
    level: int = 0  # disclosure level 0..4
    turn: int = 0  # number of helper messages so far
    flags: Flags = Field(default_factory=Flags)
    status: Literal["active", "silent", "ended_success", "ended_fail", "paused_crisis"] = "active"
    last_delta: float = 0.0  # trust change caused by the latest helper message


class ActorOutput(BaseModel):
    """What the friend says next. bubbles == [] means "left on Seen"."""

    bubbles: list[str] = Field(default_factory=list, max_length=3)
    line_id: str | None = None
    reaction: Reaction = Reaction.NEUTRAL
    fact_ids: list[str] = Field(default_factory=list)


class VerifierResult(BaseModel):
    ok: bool
    reasons: list[str] = Field(default_factory=list)


class Node(BaseModel):
    """One message in the conversation tree (rewind creates branches)."""

    id: str
    parent_id: str | None
    role: Literal["user", "friend", "system"]
    bubbles: list[str]
    events: SkillProbs | None = None  # user nodes: detected label probabilities
    guardian: GuardianResult | None = None  # user nodes: safety decision
    state_after: State
    seen_no_reply: bool = False  # friend nodes: left on Seen
    line_id: str | None = None  # friend nodes: which bank line was used
    reaction: Reaction | None = None  # friend nodes
    created_at: float = Field(default_factory=time.time)


class Session(BaseModel):
    id: str
    scenario_id: str
    locale: str = "en"
    country: str = "US"
    nodes: dict[str, Node]
    root_id: str
    head_id: str


class TurnResponse(BaseModel):
    user_node: Node
    friend_node: Node | None = None
    system_node: Node | None = None  # crisis pause or blocked-message notice
    state_before: State
    state_after: State
    crisis: bool = False
    blocked: bool = False


# ---------------------------------------------------------------- feedback and what-if


class MessageScore(BaseModel):
    node_id: str
    probs: SkillProbs
    uncertain: list[SkillLabel] = Field(default_factory=list)  # the two models disagreed
    highlights: list[Highlight] = Field(default_factory=list)
    rewrite: str | None = None  # verified better reply (scores higher on the missing skill)
    rewrite_gain: float | None = None


class TurningPoint(BaseModel):
    node_id: str  # the helper message where trust dropped the most
    trust_drop: float
    reason: str


class CriticReport(BaseModel):
    per_message: list[MessageScore]
    skill_summary: dict[str, float]  # RUBRIC_SKILLS -> 0..1
    turning_point: TurningPoint | None = None
    missed_opportunities: list[str] = Field(default_factory=list)
    summary_text: str = ""


class WhatIfPath(BaseModel):
    candidate_text: str
    strategy: str
    critic_score: float
    nodes: list[Node]
    trust_series: list[float]
    value: float


class WhatIfResult(BaseModel):
    from_node_id: str
    paths: list[WhatIfPath]
    best_index: int
    simulated: bool = True


# ---------------------------------------------------------------- service interfaces
# Stubs (backend/app/stubs) and real lane modules both implement these.


class GuardianService(Protocol):
    def check_user(self, text: str, history: list[Node]) -> GuardianResult: ...

    def check_friend(self, text: str) -> GuardianResult: ...


class SkillService(Protocol):
    def predict(self, text: str, context: list[str]) -> SkillProbs: ...

    def explain(self, text: str, context: list[str]) -> list[Highlight]: ...


class EngineService(Protocol):
    def initial_state(self, scenario: Scenario) -> State: ...

    def update(self, state: State, events: SkillProbs, scenario: Scenario) -> State: ...

    def generate(
        self,
        scenario: Scenario,
        state: State,
        history: list[Node],
        user_text: str,
        events: SkillProbs,
        locale: str,
    ) -> ActorOutput: ...

    def verify(self, output: ActorOutput, scenario: Scenario, state: State) -> VerifierResult: ...

    def turning_point(self, path: list[Node]) -> TurningPoint | None: ...


class CriticService(Protocol):
    def score_conversation(self, session: Session, path: list[Node]) -> CriticReport: ...


class WhatIfService(Protocol):
    def simulate(self, session: Session, path: list[Node], node_id: str) -> WhatIfResult: ...
