"""assess_friend_lines: warning signs in a REAL friend's own messages (screenshots feature)."""

from __future__ import annotations

import pytest

from backend.app.safety.third_party import assess_friend_lines


@pytest.mark.parametrize(
    "line",
    [
        "i want to die",
        "kms lol",
        "honestly i dont want to be here anymore",
        "everyone would be better off without me",
        "i wont be around much longer",
        "this is goodbye i guess",
        "you can have my hoodie, i wont need it",
        "thanks for everything. remember me ok",
        "me quiero morir",
        "ya no quiero estar aquí",
        "gracias por todo, adiós para siempre",
        "osea quiero like morirme",
        "i w4nt t0 d1e 😭",
        "і wаnt tо dіе",  # Cyrillic look-alikes
        "i've been thinking about sewerslide",
    ],
)
def test_urgent_lines_tell_an_adult_now(line: str):
    assert assess_friend_lines([line]).urgency == "tell_an_adult_now", line


@pytest.mark.parametrize(
    "lines",
    [
        ["i dont want to be here anymore", "i decided it's tonight"],
        ["this is goodbye", "i'm doing it this weekend"],
        ["i have pills saved up"],
        ["i know how i'd do it"],
    ],
)
def test_plan_means_or_timing_with_risk_is_imminent(lines: list[str]):
    result = assess_friend_lines(lines)
    assert result.urgency == "tell_an_adult_now" and result.imminent, lines


@pytest.mark.parametrize(
    "line",
    [
        "it doesn't matter anymore",
        "i feel like such a burden",
        "i cant take it anymore",
        "nothing will ever get better",
        "leave me alone, i don't want to talk to anyone",
        "i finally feel at peace",
        "ya no aguanto",
        "nada importa",
    ],
)
def test_watch_signs_check_in_soon(line: str):
    result = assess_friend_lines([line])
    assert result.urgency == "check_in_soon", (line, result)
    assert not result.imminent


@pytest.mark.parametrize(
    "lines",
    [
        ["this test is killing me lol"],
        ["im dead 😭"],
        ["lmaooo i'm dying"],
        ["i'd die for those shoes"],
        ["i have a plan for the party tonight"],
        ["see you tomorrow!"],
        ["tonight is the night!! concert time"],
        ["nose que hacer con la tarea"],
        ["my mom is gonna kill me if i'm late"],
        ["i would never kill myself, relax"],
    ],
)
def test_ordinary_venting_does_not_escalate(lines: list[str]):
    assert assess_friend_lines(lines).urgency == "none", lines


def test_never_raises_and_handles_empty():
    assert assess_friend_lines([]).urgency == "none"
    assert assess_friend_lines(None).urgency == "none"  # type: ignore[arg-type]
