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
