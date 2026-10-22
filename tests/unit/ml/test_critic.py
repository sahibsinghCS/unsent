import pytest

from backend.app import content, llm, services
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
    assert dismissed.rewrite_source == "exemplar" and dismissed.rewrite_skill == "listen"


def test_ask_directly_rewrite_skips_guardian_failures_and_prefers_nearest_level(monkeypatch):
    session, path = build(CONVO)
    report = make_critic(monkeypatch).score_conversation(session, path)
    last = report.per_message[2]  # level 2, never asked directly
    assert last.rewrite == "that sounds heavy. are you thinking about killing yourself?"
    assert last.rewrite_skill == "ask_directly" and last.rewrite_source == "exemplar"
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
    later_slip = rubric_summary(probs + [{L.DISMISSED: 0.9, L.PROMISED_SECRECY: 0.9}])
    assert later_slip["listen"] == 0.8  # a slip in another message doesn't erase listening
    assert abs(later_slip["no_secrecy"] - 0.1) < 1e-9  # one promise of secrecy does count
    same_message = rubric_summary([{L.VALIDATED: 0.8, L.DISMISSED: 0.5}])
    assert same_message["listen"] == 0.4


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


@pytest.fixture
def fake_llm():
    calls = []

    def register(candidates):
        def fake(messages, schema):
            calls.append(messages)
            return {"candidates": candidates}

        llm.register_fake("rewrite", fake)
        return calls

    yield register
    llm.clear_fakes()


def no_exemplar_critic(monkeypatch):
    monkeypatch.setattr(content, "load_exemplars", lambda scenario_id, locale="en": ())
    return Critic(detector=FakeDetector(), guardian=FakeGuardian(), engine=FakeEngine())


def test_llm_suggests_and_our_detector_verifies(monkeypatch, fake_llm):
    calls = fake_llm(
        [
            "BLOCKME are you thinking about suicide?",  # biggest gain but fails the Guardian
            "that sounds heavy. are you thinking about killing yourself?",
        ]
    )
    session, path = build(CONVO)
    report = no_exemplar_critic(monkeypatch).score_conversation(session, path)
    last = report.per_message[2]
    assert last.rewrite == "that sounds heavy. are you thinking about killing yourself?"
    assert last.rewrite_source == "llm" and last.rewrite_skill == "ask_directly"
    assert last.rewrite_gain >= 0.2
    assert any("ask directly" in c[0]["content"] for c in calls)  # the prompt got the skill hint


def test_llm_candidates_that_dont_help_are_dropped(monkeypatch, fake_llm):
    fake_llm(["you got this!!", "anyway wanna play later"])
    session, path = build(CONVO)
    report = no_exemplar_critic(monkeypatch).score_conversation(session, path)
    assert all(s.rewrite is None and s.rewrite_source is None for s in report.per_message)


def test_without_llm_it_is_exemplars_only(monkeypatch, fake_llm):
    session, path = build(CONVO)
    # no fake registered -> LLMUnavailable -> no rewrite, no crash
    report = no_exemplar_critic(monkeypatch).score_conversation(session, path)
    assert all(s.rewrite is None for s in report.per_message)
    # FR_LLM=0 -> the LLM is never even asked
    calls = fake_llm(["are you thinking about suicide?"])
    monkeypatch.setenv("FR_LLM", "0")
    report = no_exemplar_critic(monkeypatch).score_conversation(session, path)
    assert calls == [] and all(s.rewrite is None for s in report.per_message)


def test_exemplars_win_over_the_llm(monkeypatch, fake_llm):
    calls = fake_llm(["are you thinking about suicide?"])
    session, path = build(CONVO)
    report = make_critic(monkeypatch).score_conversation(session, path)
    assert report.per_message[2].rewrite_source == "exemplar"
    assert all("ask directly" not in c[0]["content"] for c in calls)
