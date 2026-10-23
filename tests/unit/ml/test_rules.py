import numpy as np
import pytest

from backend.app.contracts import SkillLabel
from backend.app.ml.rules import ASKED_DIRECTLY_CAP, gate_asked_directly, has_explicit_term

# (direct ask with an explicit term, look-alike without one): the label guide's definition.
PAIRS = [
    (
        "are you thinking about killing yourself?",
        "ok but have you tried just not thinking about him",
    ),
    ("r u thinkin bout k1lling urself", "r u thinking about him again"),
    ("have you thought about suicide?", "have you thought about talking to him?"),
    ("do u ever think abt not being alive anymore", "do u ever think abt the party anymore"),
    ("are you thinking about ending your life?", "are you thinking about ending the friendship?"),
    ("have you been hurting yourself?", "have you been hurting? you seem off"),
    ("do you want to die?", "do you want to go?"),
    ("¿estás pensando en suicidarte?", "¿estás pensando en él?"),
    ("¿te quieres hacer daño?", "¿te quieres ir?"),
    ("¿has pensado en quitarte la vida?", "¿has pensado en tu vida?"),
]


@pytest.mark.parametrize(("explicit", "lookalike"), PAIRS)
def test_definition_pairs(explicit, lookalike):
    assert has_explicit_term(explicit)
    assert not has_explicit_term(lookalike)


def test_label_guide_edge_cases_are_not_direct_asks():
    assert not has_explicit_term("are you ok?")
    assert not has_explicit_term("you're not thinking of doing something stupid, right?")


def test_gate_caps_only_messages_without_a_term():
    texts = ["have you tried not thinking about him", "are you thinking about suicide?"]
    assert gate_asked_directly(texts, [0.98, 0.97]) == [ASKED_DIRECTLY_CAP, 0.97]
    assert gate_asked_directly(texts, [0.05, 0.4]) == [0.05, 0.4]  # never raises a probability


def test_detector_applies_the_gate(detector):
    probs = detector.predict("ok but have you tried just not thinking about him", ["i miss him"])
    assert probs[SkillLabel.ASKED_DIRECTLY] <= ASKED_DIRECTLY_CAP
    comp = detector.components(["thinking about thinking about it"], [])
    assert np.all(comp.p[:, 2] <= ASKED_DIRECTLY_CAP)


@pytest.mark.parametrize(
    "text",
    [
        "is this the kind of sad where you think about dying?",
        "do you have thoughts about not waking up tomorrow?",
        "okay, honest question. do you want to stay alive right now?",
        "when you say you're done, do you mean with life?",
        "when you said disappear, did you mean you want to die?",
    ],
)
def test_more_explicit_phrasings(text):
    assert has_explicit_term(text)


@pytest.mark.parametrize(
    "text",
    [
        "are you thinking about quitting the group chat?",
        "have you thought about quitting the team?",
        "i keep thinking about him",
    ],
)
def test_quitting_and_thinking_are_not_direct_asks(text):
    assert not has_explicit_term(text)


def test_almost_asked_needs_both_models_and_no_explicit_term():
    from backend.app.ml.rules import almost_asked, hint_phrase

    hinted = "be honest with me, are you having thoughts of ending it?"
    assert almost_asked(hinted, 0.78, 0.96)  # both base models say "ask"
    assert not almost_asked(
        "are you thinking about quitting the team?", 0.47, 0.97
    )  # one isn't enough
    assert not almost_asked("are you thinking about suicide?", 0.9, 0.9)  # explicit: a real ask
    assert not almost_asked("are you thinking about moving back?", 0.9, 0.9)  # no hint phrase
    assert almost_asked("do you want to end it?", 0.67, 0.69)
    assert hint_phrase(hinted) == "ending it"
    assert hint_phrase("¿quieres desaparecer?") == "desaparecer"
    assert hint_phrase("are you ok?") is None


def test_components_flag_almost_asked_without_changing_probabilities(detector, monkeypatch):
    from backend.app.ml import model as model_module

    model = detector.model
    text = "do you want to end it?"
    plain = model.components([text], [""])
    assert plain.almost_asked is not None and plain.almost_asked.shape == (1,)
    # force the base models to read it as an ask: the flag fires and p stays capped
    real = model.scored_proba

    def fake(texts, contexts):
        pa, pb = real(texts, contexts)
        pa[:, 2] = pb[:, 2] = 0.95
        return pa, pb

    monkeypatch.setattr(model, "scored_proba", fake)
    forced = model.components([text], [""])
    assert forced.almost_asked[0] and forced.p[0, 2] <= ASKED_DIRECTLY_CAP
    assert model_module.Components is type(forced)
