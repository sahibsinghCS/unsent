"""A chat never mixes languages: a friend is offered in a language only when both its translated
scenario text and its line bank exist; otherwise the session falls back to English."""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.content import get_scenario, load_lines, scenario_locales, scenario_text
from backend.app.main import app

client = TestClient(app)


def test_locales_need_both_text_and_line_bank():
    maya = get_scenario("after-the-breakup")
    assert scenario_locales(maya) == ["en", "es"]
    jordan = get_scenario("failing-chem")
    assert not load_lines("failing-chem", "es")
    assert scenario_locales(jordan) == ["en"]


def test_scenario_text_falls_back_to_english():
    maya = get_scenario("after-the-breakup")
    assert scenario_text(maya, "es").title == "Después de la ruptura"
    assert scenario_text(maya, "fr").title == maya.title
    jordan = get_scenario("failing-chem")
    assert scenario_text(jordan, "es").situation == jordan.situation


def test_scenarios_endpoint_lists_locales_and_localizes():
    by_id = {s["id"]: s for s in client.get("/api/scenarios", params={"lang": "es"}).json()}
    assert by_id["after-the-breakup"]["locales"] == ["en", "es"]
    assert by_id["after-the-breakup"]["title"] == "Después de la ruptura"
    assert by_id["failing-chem"]["locales"] == ["en"]
    assert by_id["failing-chem"]["title"] == get_scenario("failing-chem").title


def test_spanish_session_opens_in_spanish():
    view = client.post(
        "/api/sessions", json={"scenario_id": "after-the-breakup", "locale": "es"}
    ).json()
    assert view["locale"] == "es"
    assert view["nodes"][0]["bubbles"] == get_scenario("after-the-breakup").i18n["es"].opening


def test_unsupported_language_falls_back_to_english():
    view = client.post("/api/sessions", json={"scenario_id": "failing-chem", "locale": "es"}).json()
    assert view["locale"] == "en"
    assert view["nodes"][0]["bubbles"] == get_scenario("failing-chem").opening
