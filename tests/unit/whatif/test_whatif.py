"""What-if service: candidates, rollouts, scores, determinism, safety and locale handling."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from backend.app import services
from backend.app.content import read_jsonl
from backend.app.contracts import NEGATIVE_LABELS, Exemplar, GuardianResult, SkillLabel, State
from backend.app.embed import cosine, embed_one
from backend.app.main import app
from backend.app.ml.critic import Critic
from backend.app.whatif import candidates as cands
from backend.app.whatif.rollout import HORIZON, WhatIf, actual_outcome, path_value

from .conftest import WEAK_CHAT, new_session, play, user_ids

FIXTURES = Path(__file__).parent / "fixtures"


def _weak():
    session = new_session()
    path = play(session, WEAK_CHAT)
    node_id = services.engine().turning_point(path).node_id
    return session, path, node_id


def _dump(result):
    return result.model_dump()


def test_three_diverse_verified_paths():
    session, path, node_id = _weak()
    result = WhatIf().simulate(session, path, node_id)
    assert result.simulated and result.from_node_id == node_id
    assert len(result.paths) == 3
    assert len({p.strategy for p in result.paths}) == 3
    texts = [p.candidate_text for p in result.paths]
    for i, a in enumerate(texts):
        for b in texts[i + 1 :]:
            assert cosine(embed_one(a), embed_one(b)) < cands.NEAR_DUPLICATE
    start = path[[n.id for n in path].index(node_id) - 1].state_after
    before = start.trust
    for p in result.paths:
        assert 0.0 <= p.critic_score <= 1.0 and p.critic_score > 0.2
        assert p.trust_series[0] == before
        users = [n for n in p.nodes if n.role == "user"]
        assert 1 <= len(users) <= HORIZON + 1
        assert users[0].bubbles == [p.candidate_text]
        assert len(p.trust_series) == len(users) + 1
        assert len({u.bubbles[0] for u in users}) == len(users)  # never repeats a text
        assert all(n.voice in ("bank", "fallback", None) for n in p.nodes)
        assert p.value == path_value(start, users[-1].state_after, len(users))


def test_paths_stop_at_an_ending():
    session, path, node_id = _weak()
    for p in WhatIf().simulate(session, path, node_id).paths:
        statuses = [n.state_after.status for n in p.nodes if n.role == "user"]
        ended = [i for i, s in enumerate(statuses) if s.startswith("ended")]
        assert not ended or ended[0] == len(statuses) - 1


def test_deterministic_across_runs_and_instances():
    session, path, node_id = _weak()
    first = _dump(WhatIf().simulate(session, path, node_id))
    assert first == _dump(WhatIf().simulate(session, path, node_id))
    services.reset()
    assert first == _dump(WhatIf().simulate(session, path, node_id))


def test_critic_rewrite_is_candidate_one():
    session, path, node_id = _weak()
    report = Critic().score_conversation(session, path)
    rewrite = next(m for m in report.per_message if m.node_id == node_id).rewrite
    assert rewrite is not None
    result = WhatIf().simulate(session, path, node_id)
    assert result.paths[0].candidate_text == rewrite


def test_every_candidate_and_friend_line_is_safe():
    guardian = services.guardian()
    for scenario_id in ("after-the-breakup", "failing-chem", "group-chat"):
        session = new_session(scenario_id)
        path = play(session, WEAK_CHAT)
        for node_id in user_ids(path):
            for p in WhatIf().simulate(session, path, node_id).paths:
                for node in p.nodes:
                    for bubble in node.bubbles:
                        if node.role == "user":
                            assert guardian.check_user(bubble, []).action == "continue"
                        else:
                            assert guardian.check_friend(bubble).level == "none"


class BlockingGuardian:
    """The real Guardian, except it blocks one chosen text."""

    def __init__(self, blocked: str) -> None:
        self.blocked, self.real = blocked, services.guardian()

    def check_user(self, text, history):
        if text == self.blocked:
            return GuardianResult(
                level="none", action="block_message", categories=["harm_to_other"]
            )
        return self.real.check_user(text, history)

    def check_friend(self, text):
        return self.real.check_friend(text)


def test_guardian_blocked_candidates_are_never_used():
    session, path, node_id = _weak()
    picked = WhatIf().simulate(session, path, node_id).paths[1].candidate_text
    result = WhatIf(guardian=BlockingGuardian(picked)).simulate(session, path, node_id)
    assert picked not in [u.bubbles[0] for p in result.paths for u in p.nodes if u.role == "user"]


def test_candidates_must_beat_the_original_on_their_skill():
    session, path, node_id = _weak()
    original = next(n for n in path if n.id == node_id)
    detector = services.skills()
    for p in WhatIf().simulate(session, path, node_id).paths:
        skill = {v: k for k, v in cands.SKILL_STRATEGY.items()}[p.strategy]
        context = [
            b
            for n in path[: [x.id for x in path].index(node_id)]
            if n.role == "friend"
            for b in n.bubbles
        ][-2:]
        new = round(cands.skill_score(detector.predict(p.candidate_text, context), skill), 4)
        assert new == p.critic_score
        assert p.critic_score - cands.skill_score(original.events, skill) >= cands.MIN_GAIN


def test_a_reply_that_already_did_everything_gets_no_fake_candidates():
    """If no exemplar beats the original on the skill it teaches, nothing is invented."""
    session, path, node_id = _weak()
    original = next(n for n in path if n.id == node_id)
    strong = {label: 0.0 if label in NEGATIVE_LABELS else 0.99 for label in SkillLabel}
    picked = cands.select(
        [
            Exemplar(
                id="e1",
                scenario_id="x",
                level=1,
                strategy="validate",
                text="that sounds really hard, i'm sorry",
            )
        ],
        "x",
        {**original.events, **strong},
        State(level=1),
        False,
        [],
        [],
        [],
        lambda texts: [services.skills().predict(t, []) for t in texts],
        services.guardian(),
    )
    assert picked == []


def test_path_value_formula_and_best_index():
    start = State(trust=40, level=1)
    assert path_value(start, State(trust=60, level=2), 1) == 70
    assert (
        path_value(start, State(trust=80, level=4, status="ended_success"), 2) == 80 + 30 + 25 - 10
    )
    assert path_value(start, State(trust=5, level=0, status="ended_fail"), 3) == 5 - 10 - 25 - 20
    session, path, node_id = _weak()
    result = WhatIf().simulate(session, path, node_id)
    values = [p.value for p in result.paths]
    assert result.best_index == values.index(max(values))  # first index wins ties


def test_best_path_beats_what_was_actually_said():
    session, path, node_id = _weak()
    result = WhatIf().simulate(session, path, node_id)
    actual, _ = actual_outcome(path, node_id)
    assert result.paths[result.best_index].value > actual


class SpanishDetector:
    """Tiny fake detector that understands the Spanish fixture exemplars."""

    KEYS = {
        "suena muy": SkillLabel.VALIDATED,
        "suicid": SkillLabel.ASKED_DIRECTLY,
        "consejera": SkillLabel.REFERRED_ADULT,
        "esta noche": SkillLabel.FOLLOW_UP,
    }

    def predict(self, text, context):
        probs = {label: 0.01 for label in SkillLabel}
        for key, label in self.KEYS.items():
            if key in text.lower():
                probs[label] = 0.95
        return probs


def _spanish_exemplars(scenario_id, locale):
    path = FIXTURES / f"{scenario_id}.{locale}.jsonl"
    return [Exemplar.model_validate(r) for r in read_jsonl(path)] if path.exists() else []


def test_spanish_session_uses_only_spanish_exemplars_and_lines():
    session = new_session(locale="es")
    path = play(session, ["hola, ¿estás bien?", "ok", "jaja ya se te pasará"])
    service = WhatIf(detector=SpanishDetector(), exemplars=_spanish_exemplars)
    spanish = {r["text"] for r in read_jsonl(FIXTURES / "after-the-breakup.es.jsonl")}
    es_lines = {b for ln in services.engine().bank("after-the-breakup", "es") for b in ln.bubbles}
    result = service.simulate(session, path, user_ids(path)[-1])
    assert result.paths
    for p in result.paths:
        assert p.candidate_text in spanish
        for node in p.nodes:
            if node.role == "user":
                assert node.bubbles[0] in spanish
            elif node.voice == "bank":
                assert set(node.bubbles) <= es_lines


def test_no_exemplars_in_the_locale_means_no_english_fallback():
    session = new_session(locale="es")
    path = play(session, ["hola, ¿estás bien?", "jaja ya se te pasará"])
    service = WhatIf(detector=SpanishDetector(), exemplars=lambda s, loc: [])
    result = service.simulate(session, path, user_ids(path)[-1])
    assert result.paths == [] and result.best_index == 0


def test_api_returns_real_paths():
    client = TestClient(app)
    sid = client.post(
        "/api/sessions", json={"scenario_id": "after-the-breakup", "locale": "en"}
    ).json()["session_id"]
    for text in WEAK_CHAT:
        client.post(f"/api/sessions/{sid}/messages", json={"text": text})
    assert client.get("/api/health").json()["components"]["whatif"] == "real"
    body = client.post(f"/api/sessions/{sid}/whatif", json={}).json()
    assert len(body["paths"]) == 3 and body["simulated"] is True
    assert {p["strategy"] for p in body["paths"]} <= set(cands.SKILL_STRATEGY.values())


def test_custom_friend_gets_a_valid_result():
    """'Add your own friend': what-if uses the shared custom bank (no exemplars yet means no cards)."""
    client = TestClient(app)
    friend = client.post(
        "/api/friends",
        json={"name": "Sam", "situation": "my friend has been really quiet since moving here"},
    ).json()["friend"]
    sid = client.post("/api/sessions", json={"scenario_id": friend["id"], "locale": "en"}).json()[
        "session_id"
    ]
    for text in WEAK_CHAT:
        client.post(f"/api/sessions/{sid}/messages", json={"text": text})
    response = client.post(f"/api/sessions/{sid}/whatif", json={})
    assert response.status_code == 200
    body = response.json()
    assert len(body["paths"]) <= 3 and body["simulated"] is True
    guardian = services.guardian()
    for p in body["paths"]:
        for node in p["nodes"]:
            if node["role"] == "friend":
                assert all(guardian.check_friend(b).level == "none" for b in node["bubbles"])


def test_custom_friend_rollout_with_exemplars():
    """With exemplars in the shared custom bank, a custom friend gets real simulated paths."""
    from backend.app.content import custom_template, load_exemplars, register_custom

    scenario = custom_template().model_copy(update={"id": "custom-test-whatif"})
    register_custom(scenario)
    session = new_session(scenario.id)
    path = play(session, WEAK_CHAT)
    stand_in = lambda _sid, loc: load_exemplars("new-school", loc)  # noqa: E731
    node_id = services.engine().turning_point(path).node_id
    result = WhatIf(exemplars=stand_in).simulate(session, path, node_id)
    assert result.paths
    guardian = services.guardian()
    for p in result.paths:
        for node in p.nodes:
            if node.role == "friend":
                assert all(guardian.check_friend(b).level == "none" for b in node.bubbles)
