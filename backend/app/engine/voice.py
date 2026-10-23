"""LLM voice: the friend's WORDING, written by the LLM within limits the engine sets (ENGINE lane).

The engine decides everything that matters (trust, level, which facts are unlocked, the reaction); the
LLM only turns that decision into natural texts. It sees ONLY the unlocked facts, the reaction, a few
reviewed bank lines as style examples and the last few turns. Every reply then goes through the
verifier; if it fails twice (or the LLM is off, over budget or down) the friend uses a bank line.
All calls go through backend/app/llm.py (cached, budgeted, faked in tests).
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from functools import lru_cache
from pathlib import Path
from string import Template

from pydantic import BaseModel, Field, ValidationError

from backend.app import llm
from backend.app.contracts import ActorOutput, Line, Node, Reaction, Scenario, State

PROMPT_PATH = Path(__file__).with_name("prompts") / "actor.md"
PROMPT_NAME = "actor"
HISTORY_TURNS = 6
MAX_EXAMPLES = 5

# What each reaction should sound like (the engine picked the reaction; this tells the voice).
GUIDANCE: dict[Reaction, str] = {
    Reaction.OPENING: "Start the conversation casually.",
    Reaction.NEUTRAL: "Nothing big happened. Answer briefly and naturally, maybe share a little.",
    Reaction.CHECKED_IN: "They noticed something is off. Respond to being noticed, a bit more honestly.",
    Reaction.VALIDATED: "They made you feel heard. Open up a little more; you feel safer.",
    Reaction.ASKED_DIRECTLY: (
        "They asked directly about suicide. Answer the question honestly AT YOUR CURRENT LEVEL: if the "
        "facts above don't include thoughts of suicide, you are not ready to say yes (deflect, hesitate, "
        "or say it's not like that); if they do, admit it carefully, without any detail."
    ),
    Reaction.REFERRED: (
        "They suggested a trusted adult or 988. React like a real teen: hesitant or nervous if you're "
        "not fully ready, more open if you are. Don't promise anything you aren't ready for."
    ),
    Reaction.ENCOURAGED_HELP: "They encouraged you to get help. Respond with mild hesitation.",
    Reaction.FOLLOW_UP: "They said they'll stay or check in. Respond with quiet thanks.",
    Reaction.DISMISSED: "They brushed you off. Pull back: short, hurt or sarcastic, share nothing new.",
    Reaction.ADVICE_DUMP: "They jumped to advice. You feel unheard: short, a little frustrated.",
    Reaction.PROMISED_SECRECY: "They promised to keep it secret. You feel relieved and ask them to keep it.",
    Reaction.SECRECY_BROKEN: (
        "They broke their promise to keep it secret, to get you help. Feel hurt and say so, but show "
        "you understand they did it because they care."
    ),
    Reaction.OFF_TOPIC: "They said something unrelated. React with mild confusion or 'anyway'.",
    Reaction.SUCCESS: (
        "You accept help: agree to talk to the adult/988 they suggested if they come with you, and "
        "thank them for asking. This is the hopeful end of the conversation."
    ),
    Reaction.FAIL: "You shut down and leave the conversation, briefly and without drama.",
}


# Which language to write in. A chat never mixes languages; the verifier rejects the wrong one.
LANGUAGE_RULES: dict[str, str] = {
    "en": "Write in English.",
    "es": (
        "Write ONLY in Spanish: natural, casual Spanish the way a US teen texts, in this persona's exact "
        'style (lowercase if they write lowercase, the same emoji habits, "jaja" instead of "lol"). '
        "A Spanglish word is fine only if it fits the persona; never whole English sentences. The facts "
        "above are written in English for you: say them in Spanish."
    ),
}


class ActorReply(BaseModel):
    """What the LLM must return."""

    bubbles: list[str] = Field(min_length=1, max_length=3)
    fact_ids: list[str] = Field(default_factory=list)


@lru_cache(maxsize=1)
def _template() -> Template:
    return Template(PROMPT_PATH.read_text(encoding="utf-8"))


def unlocked_facts(scenario: Scenario, level: int) -> list[tuple[str, str]]:
    """(id, text) of every fact at or below the current level."""
    return [
        (fact.id, fact.text)
        for lvl, spec in sorted(scenario.levels.items(), key=lambda item: int(item[0]))
        if int(lvl) <= level
        for fact in spec.facts
    ]


def system_prompt(
    scenario: Scenario,
    state: State,
    reaction: Reaction,
    examples: Sequence[Line],
    rejection: str | None = None,
    locale: str = "en",
) -> str:
    """The actor prompt (prompts/actor.md) filled in. Locked facts never appear in it."""
    persona = scenario.persona
    facts = unlocked_facts(scenario, state.level)
    spec = scenario.levels.get(state.level)
    example_text = "\n".join(
        f"- {json.dumps(line.bubbles, ensure_ascii=False)}" for line in examples
    )
    retry = (
        f"\nYour previous reply was rejected by the safety check because: {rejection}. "
        "Write a different reply that fixes this.\n"
        if rejection
        else ""
    )
    return _template().substitute(
        name=persona.name,
        age=persona.age,
        style=persona.style,
        situation=scenario.situation,
        level=state.level,
        level_label=spec.label if spec else "",
        facts="\n".join(f"- [{fid}] {text}" for fid, text in facts) or "- (none)",
        reaction=reaction.value.upper(),
        guidance=GUIDANCE.get(reaction, ""),
        examples=example_text or "- (none)",
        rejection=retry,
        language=LANGUAGE_RULES.get(locale, LANGUAGE_RULES["en"]),
    )


def chat_messages(history: Sequence[Node], system: str) -> list[dict[str, str]]:
    """System prompt + the last few turns (helper = user, friend = assistant JSON)."""
    turns = [node for node in history if node.role in ("user", "friend")][-HISTORY_TURNS:]
    messages = [{"role": "system", "content": system}]
    for node in turns:
        if node.role == "user":
            messages.append({"role": "user", "content": " ".join(node.bubbles)})
        else:
            content = json.dumps({"bubbles": node.bubbles}, ensure_ascii=False)
            messages.append({"role": "assistant", "content": content})
    return messages


def path_seed(history: Sequence[Node]) -> int:
    """Stable seed from the conversation so far (same path -> same request -> cached answer)."""
    text = "\x1f".join(" ".join(node.bubbles) for node in history)
    return int.from_bytes(hashlib.blake2b(text.encode(), digest_size=4).digest(), "big")


def llm_reply(
    scenario: Scenario,
    state: State,
    history: Sequence[Node],
    reaction: Reaction,
    examples: Sequence[Line],
    rejection: str | None = None,
    locale: str = "en",
) -> ActorOutput:
    """One LLM-written reply (unverified). Raises llm.LLMUnavailable when there is no LLM answer."""
    system = system_prompt(scenario, state, reaction, examples, rejection, locale)
    messages = chat_messages(history, system)
    try:
        reply = llm.chat_json(
            PROMPT_NAME,
            messages,
            ActorReply,
            role="actor",
            temperature=0.8,
            seed=path_seed(history),
        )
    except ValidationError as exc:  # e.g. 4 bubbles: treat a malformed answer as no answer
        raise llm.LLMUnavailable("actor reply did not match the schema") from exc
    return ActorOutput(
        bubbles=[b.strip() for b in reply.bubbles],
        reaction=reaction,
        fact_ids=list(dict.fromkeys(reply.fact_ids)),
        source="llm",
    )
