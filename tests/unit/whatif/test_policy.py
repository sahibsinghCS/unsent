"""Later-turn policy: a simulated helper remembers what they already did."""

from __future__ import annotations

from backend.app import services
from backend.app.contracts import Exemplar, SkillLabel
from backend.app.whatif.rollout import WhatIf, shown_skills, split_at

from .conftest import WEAK_CHAT, new_session, play, user_ids

ASK = SkillLabel.ASKED_DIRECTLY


def _asks(path_nodes) -> int:
    return sum(
        1 for n in path_nodes if n.role == "user" and n.events and n.events.get(ASK, 0.0) >= 0.5
    )


def test_no_path_asks_directly_twice():
    chats = [WEAK_CHAT, ["are you thinking about killing yourself?", "lol you'll be fine"]]
    for scenario_id in ("after-the-breakup", "new-school", "giving-stuff-away"):
        for chat in chats:
            session = new_session(scenario_id)
            path = play(session, chat)
            for node_id in user_ids(path):
                base, _, _ = split_at(path, node_id)
                for p in WhatIf().simulate(session, path, node_id).paths:
                    assert _asks(base) + _asks(p.nodes) <= 1


def _ex(i: int, strategy: str, text: str) -> Exemplar:
    return Exemplar(
        id=f"p{i}", scenario_id="after-the-breakup", level=1, strategy=strategy, text=text
    )


def test_an_unshown_skill_beats_repeating_a_shown_one():
    """Validating again would gain more trust (+12) than following up (+5), but listening is done."""
    session = new_session()
    path = play(session, ["hey are you ok? you seemed off", "that sounds really hard, i'm sorry"])
    sim = WhatIf().simulator(session)
    state = path[-1].state_after
    pool = [
        _ex(1, "validate", "that sounds so hard, i'm sorry. that makes sense"),
        _ex(2, "follow_up", "i'll text you tomorrow"),
    ]
    assert "follow_up" in shown_skills(sim.predict([pool[1].text], [])[0])
    text, _ = sim.best_next(
        path, state, frozenset(), pool, set(), frozenset({"check_in", "listen"})
    )
    assert text == pool[1].text
    text, _ = sim.best_next(path, state, frozenset(), pool, set(), frozenset())
    assert text == pool[0].text  # with nothing shown yet, the bigger trust gain wins


def test_other_cards_continuations_are_tried_last():
    session = new_session()
    path = play(session, ["hey are you ok? you seemed off"])
    sim = WhatIf().simulator(session)
    pool = [
        _ex(1, "validate", "that sounds so hard, i'm sorry. that makes sense"),
        _ex(2, "validate", "that sounds really heavy, i'm sorry"),
    ]
    first, _ = sim.best_next(path, path[-1].state_after, frozenset(), pool, set())
    other = next(ex.text for ex in pool if ex.text != first)
    again, _ = sim.best_next(
        path, path[-1].state_after, frozenset(), pool, set(), elsewhere=frozenset({first})
    )
    assert again == other


def test_policy_is_deterministic():
    session = new_session()
    path = play(session, WEAK_CHAT)
    node_id = services.engine().turning_point(path).node_id
    runs = [WhatIf().simulate(session, path, node_id).model_dump() for _ in range(2)]
    assert runs[0] == runs[1]


def test_card_chip_matches_the_exemplar_strategy():
    from backend.app.whatif.candidates import STRATEGY_SKILL, card_skill, exemplar_skills

    ask = Exemplar(
        id="x",
        scenario_id="after-the-breakup",
        level=2,
        strategy="ask_directly",
        text="gracias por contármelo. ¿estás pensando en matarte?",
        labels=[SkillLabel.ASKED_DIRECTLY, SkillLabel.VALIDATED],
    )
    assert card_skill(ask, "listen") == "ask_directly"
    combo = ask.model_copy(update={"strategy": "combo"})
    assert card_skill(combo, "listen") == "listen"
    # every card of a real result: its chip is the exemplar's own strategy (or one of a combo's skills)
    from backend.app.content import load_exemplars
    from backend.app.whatif.candidates import SKILL_STRATEGY

    for locale in ("en", "es"):
        by_text = {ex.text: ex for ex in load_exemplars("after-the-breakup", locale)}
        session = new_session(locale=locale)
        chat = WEAK_CHAT if locale == "en" else ["hola, ¿estás bien?", "jaja ya se te pasará"]
        path = play(session, chat)
        for node_id in user_ids(path):
            for p in WhatIf().simulate(session, path, node_id).paths:
                ex = by_text[p.candidate_text]
                allowed = {SKILL_STRATEGY[s] for s in exemplar_skills(ex)}
                assert p.strategy in allowed, (p.strategy, ex.strategy)
                if ex.strategy in STRATEGY_SKILL:
                    assert p.strategy == SKILL_STRATEGY[STRATEGY_SKILL[ex.strategy]]
