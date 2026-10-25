"""HTTP API (mounted at /api). The frontend's only dependency; see /docs for the OpenAPI schema."""

from __future__ import annotations

import time

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from backend.app import llm, services
from backend.app.config import max_message_chars
from backend.app.content import (
    crisis_lines_for,
    get_scenario,
    is_custom,
    load_metrics,
    load_realmode,
    load_scenarios,
    owns_custom,
    remove_custom,
    resolve_headline,
    scenario_locales,
    scenario_text,
)
from backend.app.contracts import (
    CONTRACTS_VERSION,
    CriticReport,
    GuardianResult,
    Node,
    Reaction,
    Scenario,
    Session,
    State,
    TurnResponse,
    WhatIfResult,
)
from backend.app.custom_friend import FriendProblem, FriendRequest, create_friend
from backend.app.pipeline import run_turn
from backend.app.screenshots import AnalyzeRequest, AnalyzeResponse, ScreenshotProblem, analyze
from backend.app.session import create_session, new_id, path_to, rewind, store

router = APIRouter()
STARTED_AT = time.time()


class ScenarioSummary(BaseModel):
    id: str
    title: str
    persona_name: str
    persona_age: int
    guardedness: str
    situation: str
    content_warning: str
    review_status: str
    # languages this friend can be practiced in (see content.scenario_locales)
    locales: list[str] = ["en"]
    custom: bool = False  # written by the helper ("Add your own friend"); lives only in memory


class FriendResponse(BaseModel):
    friend: ScenarioSummary
    # "real_help": the story may be about a real friend (or the helper) at risk: show real help first
    notice: str | None = None
    # send back as X-Friend-Token to delete this friend (kept in the page's memory only)
    owner_token: str = ""


class CreateSessionRequest(BaseModel):
    scenario_id: str
    locale: str = "en"
    country: str = "US"


class SessionView(BaseModel):
    session_id: str
    scenario_id: str
    # the chat's language (English when the friend doesn't support the requested one)
    locale: str = "en"
    head_id: str
    root_id: str
    state: State
    nodes: list[Node]  # root -> head path


class MessageRequest(BaseModel):
    text: str = Field(min_length=1)
    parent_node_id: str | None = None  # reply from an earlier node (creates a branch)


class RewindRequest(BaseModel):
    node_id: str


class WhatIfRequest(BaseModel):
    node_id: str | None = None  # default: the critic's turning point


class TreeView(BaseModel):
    session_id: str
    root_id: str
    head_id: str
    nodes: list[Node]


class GuardianCheckRequest(BaseModel):
    text: str = Field(min_length=1)


def _session(session_id: str) -> Session:
    session = store.get(session_id)
    if session is None:
        raise HTTPException(
            404, "Session not found or expired (sessions are deleted after inactivity)."
        )
    return session


def _view(session: Session) -> SessionView:
    path = path_to(session)
    return SessionView(
        session_id=session.id,
        scenario_id=session.scenario_id,
        locale=session.locale,
        head_id=session.head_id,
        root_id=session.root_id,
        state=path[-1].state_after,
        nodes=path,
    )


@router.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "contracts_version": CONTRACTS_VERSION,
        "components": services.status(),
        "llm": llm.status(),
        "uptime_s": round(time.time() - STARTED_AT),
    }


@router.get("/scenarios", response_model=list[ScenarioSummary])
def scenarios(lang: str = "en") -> list[ScenarioSummary]:
    """Every scenario, with its text in `lang` where that friend supports it (English otherwise)."""
    return [_summary(s, lang) for s in load_scenarios().values()]


def _summary(scenario: Scenario, lang: str) -> ScenarioSummary:
    text = scenario_text(scenario, lang)
    custom = is_custom(scenario.id)
    return ScenarioSummary(
        id=scenario.id,
        title=text.title,
        persona_name=scenario.persona.name,
        persona_age=scenario.persona.age,
        guardedness=scenario.persona.guardedness,
        situation=text.situation,
        content_warning=text.content_warning,
        review_status="custom" if custom else scenario.review_status,
        locales=scenario_locales(scenario),
        custom=custom,
    )


@router.post("/friends", response_model=FriendResponse)
def add_friend(request: FriendRequest) -> FriendResponse:
    """A friend the helper describes. Kept in memory only, and expires like a session."""
    try:
        scenario, real_help, owner_token = create_friend(request)
    except FriendProblem as problem:
        raise HTTPException(422, problem.detail) from problem
    locale = scenario_locales(scenario)[0]
    return FriendResponse(
        friend=_summary(scenario, locale),
        notice="real_help" if real_help else None,
        owner_token=owner_token,
    )


@router.post("/friends/analyze", response_model=AnalyzeResponse)
def analyze_screenshots(request: AnalyzeRequest) -> AnalyzeResponse:
    """Read screenshots of a real conversation and draft a practice friend for the helper to review.
    Nothing is created or stored; the draft goes into the "Add your own friend" form."""
    try:
        return analyze(request)
    except ScreenshotProblem as problem:
        raise HTTPException(problem.status, problem.detail) from problem


@router.delete("/friends/{friend_id}", status_code=204)
def delete_friend(
    friend_id: str, x_friend_token: str = Header(default="", alias="X-Friend-Token")
) -> None:
    """Delete a custom friend now, with every chat practising it. Only the browser that created it
    (it holds the owner token) can; built-in friends can't be deleted."""
    if not is_custom(friend_id) or not owns_custom(friend_id, x_friend_token):
        raise HTTPException(404, "No such friend.")  # same answer either way: ids stay unguessable
    remove_custom(friend_id)
    store.drop_scenario(friend_id)


@router.get("/friends/{friend_id}", response_model=ScenarioSummary)
def get_friend(friend_id: str, lang: str = "en") -> ScenarioSummary:
    try:
        scenario = get_scenario(friend_id) if is_custom(friend_id) else None
    except KeyError:
        scenario = None
    if scenario is None:
        raise HTTPException(404, "This friend has expired.")
    return _summary(scenario, lang)


@router.post("/sessions", response_model=SessionView)
def start_session(request: CreateSessionRequest) -> SessionView:
    try:
        scenario = get_scenario(request.scenario_id)
    except KeyError as exc:
        raise HTTPException(404, f"Unknown scenario '{request.scenario_id}'.") from exc
    # Never a mixed-language chat: fall back to English when this friend can't be practiced in the language.
    locales = scenario_locales(scenario)
    locale = request.locale if request.locale in locales else locales[0]
    state = services.engine().initial_state(scenario)
    opening = Node(
        id=new_id("n"),
        parent_id=None,
        role="friend",
        bubbles=scenario_text(scenario, locale).opening,
        state_after=state,
        reaction=Reaction.OPENING,
    )
    session = create_session(scenario.id, locale, request.country, opening)
    store.put(session)
    return _view(session)


@router.get("/sessions/{session_id}", response_model=SessionView)
def get_session(session_id: str) -> SessionView:
    return _view(_session(session_id))


@router.post("/sessions/{session_id}/messages", response_model=TurnResponse)
def send_message(session_id: str, request: MessageRequest) -> TurnResponse:
    session = _session(session_id)
    text = request.text.strip()
    if not text:
        raise HTTPException(422, "Message is empty.")
    if len(text) > max_message_chars():
        raise HTTPException(422, f"Message is longer than {max_message_chars()} characters.")
    with store.turn_lock(session.id):
        target = request.parent_node_id or session.head_id
        if target not in session.nodes:
            raise HTTPException(404, "Unknown node.")
        # Check before moving the head, so a refused message leaves the conversation where it was.
        status = session.nodes[target].state_after.status
        if status not in ("active", "silent"):
            raise HTTPException(
                409, f"Conversation is {status}. Rewind to an earlier message or finish."
            )
        rewind(session, target)
        return run_turn(session, text)


@router.post("/sessions/{session_id}/rewind", response_model=SessionView)
def rewind_session(session_id: str, request: RewindRequest) -> SessionView:
    session = _session(session_id)
    with store.turn_lock(session.id):
        try:
            rewind(session, request.node_id)
        except KeyError as exc:
            raise HTTPException(404, "Unknown node.") from exc
        return _view(session)


@router.get("/sessions/{session_id}/tree", response_model=TreeView)
def tree(session_id: str) -> TreeView:
    session = _session(session_id)
    return TreeView(
        session_id=session.id,
        root_id=session.root_id,
        head_id=session.head_id,
        nodes=list(session.nodes.values()),
    )


@router.post("/sessions/{session_id}/finish", response_model=CriticReport)
def finish(session_id: str) -> CriticReport:
    session = _session(session_id)
    return services.critic().score_conversation(session, path_to(session))


@router.post("/sessions/{session_id}/whatif", response_model=WhatIfResult)
def whatif(session_id: str, request: WhatIfRequest) -> WhatIfResult:
    session = _session(session_id)
    path = path_to(session)
    node_id = request.node_id
    if node_id is None:
        turning = services.engine().turning_point(path)
        if turning is None:
            raise HTTPException(409, "No turning point yet: trust never dropped.")
        node_id = turning.node_id
    if node_id not in {node.id for node in path}:
        raise HTTPException(404, "Node is not on the current conversation path.")
    if _is_crisis_moment(path, node_id):
        raise HTTPException(
            409, "This message paused the practice for real help, so it has no what-if."
        )
    return services.whatif().simulate(session, path, node_id)


def _is_crisis_moment(path: list[Node], node_id: str) -> bool:
    """The helper's own crisis message (or the pause note after it) is never replayed as a mistake."""
    index = next(i for i, node in enumerate(path) if node.id == node_id)
    node = path[index]
    if node.role == "system" and index > 0:
        node = path[index - 1]
    return node.guardian is not None and node.guardian.action == "pause_roleplay"


@router.get("/realmode")
def realmode(lang: str = "en", country: str = "US") -> dict:
    """Fixed 'it's real right now' steps plus crisis lines. No AI involved."""
    return {**load_realmode(lang), "crisis": crisis_lines_for(country)}


@router.post("/guardian/check", response_model=GuardianResult)
def guardian_check(request: GuardianCheckRequest) -> GuardianResult:
    return services.guardian().check_user(request.text, [])


@router.get("/metrics")
def metrics() -> dict:
    """Every evaluation record in eval/reports/*.json (shown on the Transparency page)."""
    records = load_metrics()
    return {
        "components": services.status(),
        "headline": resolve_headline(records),
        "records": records,
    }
