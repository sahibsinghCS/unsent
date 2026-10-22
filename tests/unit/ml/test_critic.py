from backend.app import content, services
from backend.app.contracts import (
    RUBRIC_SKILLS,
    CriticReport,
    Exemplar,
    Flags,
    GuardianResult,
    Node,
    Session,
    SkillLabel,
    State,
    TurningPoint,
)
from backend.app.ml import critic as critic_module
from backend.app.ml.critic import Critic, missing_skill, rubric_summary

L = SkillLabel
RULES = {
    "killing yourself": L.ASKED_DIRECTLY,
    "suicide": L.ASKED_DIRECTLY,
    "counselor": L.REFERRED_ADULT,
    "988": L.REFERRED_988,
    "sounds": L.VALIDATED,
    "you ok": L.CHECKED_IN,
    "lol": L.DISMISSED,
    "won't tell": L.PROMISED_SECRECY,
    "tonight": L.FOLLOW_UP,
}


class FakeDetector:
    def __init__(self):
        self.calls = []

    def predict(self, text, context):
        self.calls.append(text)
        low = text.lower()
        return {label: 0.05 for label in L} | {
            label: 0.9 for key, label in RULES.items() if key in low
        }

    def explain(self, text, context):
        return []

    def uncertain(self, text, context):
        return [L.VALIDATED] if "maybe" in text else []


class FakeGuardian:
    def check_user(self, text, history):
        bad = "BLOCKME" in text
        return GuardianResult(
            level="none", action="block_message" if bad else "continue", categories=[]
        )


class FakeEngine:
    def turning_point(self, path):
        worst = min((n for n in path if n.role == "user"), key=lambda n: n.state_after.last_delta)
        return TurningPoint(node_id=worst.id, trust_drop=-worst.state_after.last_delta, reason="r")


def ex(i, level, strategy, text, labels=()):
    return Exemplar(
        id=f"ex{i}", scenario_id="s", level=level, strategy=strategy, text=text, labels=list(labels)
    )


EXEMPLARS = (
    ex(1, 2, "ask_directly", "BLOCKME are you thinking about suicide?"),  # fails the Guardian
    ex(2, 2, "ask_directly", "that sounds heavy. are you thinking about killing yourself?"),
    ex(3, 0, "ask_directly", "are you thinking about suicide? asked too early"),
    ex(4, 1, "validate", "that sounds really hard"),
    ex(5, 3, "refer", "can we go to the counselor together?"),
)


def build(messages):
    """messages: (role, text, level_after, trust_delta, flags)."""
    nodes, parent = [], None
    for i, (role, text, level, delta, flags) in enumerate(messages):
        node = Node(
            id=f"n{i}",
            parent_id=parent,
            role=role,
            bubbles=[text],
            state_after=State(level=level, last_delta=delta, flags=flags or Flags()),
        )
        nodes.append(node)
        parent = node.id
    session = Session(
        id="s1", scenario_id="s", nodes={n.id: n for n in nodes}, root_id="n0", head_id=parent
    )
    return session, nodes


CONVO = [
    ("friend", "whatever im fine", 0, 0, None),
    ("user", "hey you ok?", 1, 5, None),
    ("friend", "honestly whats the point of anything", 2, 0, None),
    ("user", "lol you'll be fine", 2, -12, None),
    ("friend", "yeah whatever", 2, 0, None),
    ("user", "i'm here for you", 2, 2, None),
]


def make_critic(monkeypatch, detector=None):
    monkeypatch.setattr(content, "load_exemplars", lambda scenario_id, locale="en": EXEMPLARS)
    return Critic(detector=detector or FakeDetector(), guardian=FakeGuardian(), engine=FakeEngine())


def test_report_shape_and_summary(monkeypatch):
    session, path = build(CONVO)
    report = make_critic(monkeypatch).score_conversation(session, path)
    assert isinstance(report, CriticReport)
    assert [s.node_id for s in report.per_message] == ["n1", "n3", "n5"]
    assert set(report.skill_summary) == set(RUBRIC_SKILLS)
    assert report.skill_summary["check_in"] == 0.9
    assert report.skill_summary["listen"] < 0.5
    assert report.turning_point.node_id == "n3"
    assert "you'll be fine" in report.summary_text and "checking in" in report.summary_text
    assert 2 <= report.summary_text.count(".") + report.summary_text.count("?")


def test_dismissive_message_gets_a_verified_validating_rewrite(monkeypatch):
    session, path = build(CONVO)
    report = make_critic(monkeypatch).score_conversation(session, path)
    dismissed = report.per_message[1]
    assert dismissed.rewrite == "that sounds really hard"
    assert abs(dismissed.rewrite_gain - 0.85) < 1e-6


def test_ask_directly_rewrite_skips_guardian_failures_and_prefers_nearest_level(monkeypatch):
    session, path = build(CONVO)
    report = make_critic(monkeypatch).score_conversation(session, path)
    last = report.per_message[2]  # level 2, never asked directly
    assert last.rewrite == "that sounds heavy. are you thinking about killing yourself?"
    assert any("hadn't asked directly" in m for m in report.missed_opportunities)


def test_no_rewrite_when_gain_is_too_small(monkeypatch):
    class Stubborn(FakeDetector):
        def predict(self, text, context):
            return {label: 0.4 for label in L}

    session, path = build(CONVO)
    report = make_critic(monkeypatch, Stubborn()).score_conversation(session, path)
    assert all(s.rewrite is None and s.rewrite_gain is None for s in report.per_message)


def test_uses_node_events_when_present(monkeypatch):
    convo = list(CONVO)
    session, path = build(convo)
    path[1].events = {label: 0.0 for label in L} | {L.FOLLOW_UP: 0.77}
    report = make_critic(monkeypatch).score_conversation(session, path)
    assert report.per_message[0].probs[L.FOLLOW_UP] == 0.77


def test_blocked_messages_are_not_scored(monkeypatch):
    session, path = build(CONVO)
    path[3].guardian = GuardianResult(level="none", action="block_message")
    report = make_critic(monkeypatch).score_conversation(session, path)
    assert "n3" not in [s.node_id for s in report.per_message]


def test_missing_skill_rules():
    base = {label: 0.0 for label in L}
    calm = State(level=2)
    assert missing_skill(base | {L.PROMISED_SECRECY: 0.9}, calm, False).skill == "no_secrecy"
    assert missing_skill(base | {L.ADVICE_DUMP: 0.9}, calm, False).skill == "listen"
    assert missing_skill(base, calm, False).skill == "ask_directly"
    asked = State(level=3, flags=Flags(asked_directly_ever=True))
    assert missing_skill(base, asked, False).skill == "refer"
    referred = State(level=3, flags=Flags(asked_directly_ever=True, referral_turns=[2]))
    assert missing_skill(base, referred, False) is None
    assert missing_skill(base, State(level=0), True).skill == "check_in"
    assert missing_skill(base | {L.ASKED_DIRECTLY: 0.9}, calm, False) is None


def test_rubric_mapping():
    probs = [{label: 0.0 for label in L} | {L.VALIDATED: 0.8, L.REFERRED_988: 0.7}]
    summary = rubric_summary(probs)
    assert summary["listen"] == 0.8 and summary["refer"] == 0.7 and summary["no_secrecy"] == 1.0
    summary = rubric_summary(probs + [{L.DISMISSED: 0.5, L.PROMISED_SECRECY: 0.9}])
    assert summary["listen"] == 0.4 and abs(summary["no_secrecy"] - 0.1) < 1e-9


def test_critic_with_trained_detector_and_services(monkeypatch, detector):
    monkeypatch.setattr(content, "load_exemplars", lambda scenario_id, locale="en": EXEMPLARS)
    session, path = build(CONVO)
    report = Critic(detector=detector).score_conversation(session, path)
    assert len(report.per_message) == 3
    for score in report.per_message:
        assert set(score.probs) == set(L)
        if score.rewrite is not None:
            assert score.rewrite_gain >= 0.2


def test_registry_uses_the_real_critic():
    assert critic_module.IMPLEMENTED
    assert isinstance(services.critic(), Critic)
