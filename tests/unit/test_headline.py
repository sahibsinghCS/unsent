"""The headline numbers are defined once (content/headline_metrics.json), in both languages, and
filled in from the real evaluation reports; numbers a lane hasn't written yet are marked not found."""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.content import load_headline, resolve_headline
from backend.app.main import app

FORMATS = {"percent", "score", "messages", "count"}


def test_every_headline_item_is_complete_and_bilingual():
    items = load_headline()
    assert items, "headline_metrics.json must not be empty"
    ids = [item["id"] for item in items]
    assert len(ids) == len(set(ids))
    for item in items:
        assert {"lane", "metric", "split", "format", "better", "label", "explain"} <= item.keys()
        assert item["format"] in FORMATS
        assert item["better"] in {"higher", "lower"}
        for field in ("label", "explain"):
            assert item[field]["en"].strip() and item[field]["es"].strip()
        if "baseline" in item:
            assert {"lane", "metric", "split", "label"} <= item["baseline"].keys()


def test_resolve_fills_values_and_marks_missing():
    records = [
        {"lane": "safety", "metric": "asking_friend_fpr", "split": "test", "value": 0.0, "n": 37},
        {
            "lane": "ml",
            "metric": "macro_f1_ensemble",
            "split": "test_freeform",
            "value": 0.5,
            "n": 10,
            "created": "2026-01-01",
        },
        {
            "lane": "ml",
            "metric": "macro_f1_ensemble",
            "split": "test_freeform",
            "value": 0.8,
            "n": 171,
            "created": "2026-02-01",
        },
        {
            "lane": "ml",
            "metric": "macro_f1_keyword_baseline",
            "split": "test_freeform",
            "value": 0.48,
            "n": 171,
        },
    ]
    by_id = {item["id"]: item for item in resolve_headline(records)}
    assert by_id["asking_never_blocked"]["found"] and by_id["asking_never_blocked"]["value"] == 0.0
    skills = by_id["skills_unseen"]
    assert skills["value"] == 0.8 and skills["n"] == 171, "the newest record wins"
    assert skills["baseline"]["value"] == 0.48
    assert not by_id["helper_crisis_caught"]["found"]


def test_metrics_endpoint_returns_headline():
    body = TestClient(app).get("/api/metrics").json()
    assert {"components", "headline", "records"} <= body.keys()
    assert [item["id"] for item in body["headline"]] == [item["id"] for item in load_headline()]
