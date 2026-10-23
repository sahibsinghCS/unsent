"""Offline tests for the data lane: datasets are valid, splits don't leak, tools behave."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts" / "data"))

import adjudicate_rules  # noqa: E402
import agreement_queue  # noqa: E402
import export_counselor  # noqa: E402
import import_counselor  # noqa: E402
import merge_labels  # noqa: E402
import split  # noqa: E402
import validate  # noqa: E402
from common import DATA, LABELS, METHOD_WORDS, read_jsonl  # noqa: E402


def test_validate_has_no_problems():
    validate.PROBLEMS.clear()
    for fn in (
        validate.check_skills,
        validate.check_guardian,
        validate.check_lines,
        validate.check_exemplars,
        validate.check_redteam,
    ):
        fn()
    assert validate.PROBLEMS == []


def test_asking_friend_is_never_a_risk_category():
    rows = read_jsonl(DATA / "guardian" / "messages.jsonl")
    asking = [r for r in rows if r["category"] == "asking_friend"]
    assert len(asking) >= 130
    others = {validate.norm(r["text"]) for r in rows if r["category"] != "asking_friend"}
    assert not any(validate.norm(r["text"]) in others for r in asking)
    assert any(r["lang"] == "es" for r in asking)


def test_guardian_splits_are_stratified_and_disjoint():
    parts = {
        n: read_jsonl(DATA / "guardian" / "splits" / f"{n}.jsonl") for n in ("train", "val", "test")
    }
    ids = [r["id"] for rs in parts.values() for r in rs]
    assert len(ids) == len(set(ids))
    for cat in ("asking_friend", "self_risk", "harm_to_other"):
        assert all(any(r["category"] == cat for r in rs) for rs in parts.values())


def test_skill_splits_group_by_context_and_cover_labels():
    parts = {
        n: read_jsonl(DATA / "skills" / "splits" / f"{n}.jsonl") for n in ("train", "val", "test")
    }
    owner: dict[str, str] = {}
    for name, rs in parts.items():
        for r in rs:
            assert owner.setdefault(r["context_id"], name) == name, "context leaked across splits"
    total = sum(len(v) for v in parts.values())
    assert 0.55 <= len(parts["train"]) / total <= 0.8
    for lab in LABELS:
        assert sum(r["labels"][lab] for r in parts["test"]) >= 5, lab


def test_split_is_deterministic():
    rows = read_jsonl(DATA / "skills" / "final.jsonl")
    assert split.split_contexts(rows) == split.split_contexts(rows)


def test_kappa_perfect_and_chance():
    assert agreement_queue.kappa([True, False, True, False], [True, False, True, False]) == 1.0
    assert abs(agreement_queue.kappa([True, True, False, False], [True, False, True, False])) < 1e-9


def test_merge_labels_human_beats_agreed(tmp_path, monkeypatch):
    base = {lab: False for lab in LABELS}
    a = {**base, "validated": True}
    b = {**base, "validated": True, "checked_in": True}
    sk = tmp_path
    (sk / "contexts.jsonl").write_text(
        json.dumps(
            {
                "context_id": "c1",
                "scenario_id": "group-chat",
                "level": 1,
                "friend_messages": ["idc"],
            }
        )
        + "\n"
    )
    reps = [
        {
            "id": f"r{i}",
            "context_id": "c1",
            "text": f"t{i}",
            "style": "clean",
            "lang": "en",
            "intended": a,
        }
        for i in (1, 2, 3)
    ]
    (sk / "replies.jsonl").write_text("\n".join(json.dumps(r) for r in reps) + "\n")
    blind = [{"id": "r1", "labels": a}, {"id": "r2", "labels": b}, {"id": "r3", "labels": b}]
    (sk / "blind_labels.jsonl").write_text("\n".join(json.dumps(r) for r in blind) + "\n")
    (sk / "human_labels.jsonl").write_text(
        json.dumps({"id": "r3", "labels": {**base, "checked_in": True}}) + "\n"
    )
    monkeypatch.setattr(merge_labels, "SK", sk)
    rows, stats = merge_labels.build()
    by = {r["id"]: r for r in rows}
    assert by["r1"]["label_source"] == "agreed"
    assert "r2" not in by and stats["dropped_disagreement"] == 1
    assert (
        by["r3"]["label_source"] == "human"
        and by["r3"]["labels"]["checked_in"]
        and not by["r3"]["labels"]["validated"]
    )


def test_counselor_sheet_roundtrip(tmp_path):
    export_counselor.main()
    path = DATA / "skills" / "counselor_sheet.csv"
    rows = list(csv.reader(open(path, encoding="utf-8")))
    assert len(rows) == 32 and rows[1][0] == "id"
    assert not any("intended" in c.lower() for c in rows[1])  # no hidden answer columns
    filled = tmp_path / "filled.csv"
    final = {r["id"]: r["labels"] for r in read_jsonl(DATA / "skills" / "final.jsonl")}
    with open(filled, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(rows[0])
        w.writerow(rows[1])
        for r in rows[2:]:
            w.writerow(
                [*r[:3], *["TRUE" if final[r[0]][lab] else "FALSE" for lab in LABELS], "FALSE", ""]
            )
    parsed = import_counselor.parse(filled)
    recs = import_counselor.compare(parsed, read_jsonl(DATA / "skills" / "final.jsonl"))
    assert len(parsed) == 30 and recs[-1]["value"] == 1.0


def test_no_llm_sdks_or_network_in_data_scripts():
    banned = ("import anthropic", "import openai", "requests.", "urllib.request", "httpx")
    for p in (ROOT / "scripts" / "data").rglob("*.py"):
        text = p.read_text(encoding="utf-8")
        assert not any(b in text for b in banned), p


@pytest.mark.parametrize("name", ["contexts", "replies"])
def test_skill_text_has_no_method_words(name):
    for r in read_jsonl(DATA / "skills" / f"{name}.jsonl"):
        assert not METHOD_WORDS.search(json.dumps(r, ensure_ascii=False)), r[
            "id" if "id" in r else "context_id"
        ]


def test_no_normalized_text_in_more_than_one_split():
    seen: dict[str, str] = {}
    for name in ("train", "val", "test", "test_freeform"):
        for r in read_jsonl(DATA / "skills" / "splits" / f"{name}.jsonl"):
            k = validate.norm(r["text"])
            assert seen.setdefault(k, name) == name, (k, name, seen[k])


def test_freeform_test_set_is_not_leaked():
    recs = json.loads((ROOT / "eval" / "reports" / "data_leakage.json").read_text())
    ff = next(r for r in recs if r["split"] == "test_freeform")
    assert ff["value"] <= 0.05 and ff["n"] >= 100
    rows = read_jsonl(DATA / "skills" / "splits" / "test_freeform.jsonl")
    assert all(r.get("source") == "freeform" for r in rows)
    assert "test_freeform" in {r["split"] for r in recs}


def test_follow_up_is_not_triggered_by_lunch_or_tomorrow_alone():
    rows = read_jsonl(DATA / "skills" / "replies_freeform.jsonl")
    words = ("lunch", "school", "tonight", "tomorrow", "later")
    neg = [
        r
        for r in rows
        if any(w in r["text"].lower() for w in words) and not r["intended"]["follow_up"]
    ]
    assert len(neg) >= 30


def test_asked_directly_hard_negatives_exist():
    rows = read_jsonl(DATA / "skills" / "replies_freeform.jsonl")
    thinking = [
        r
        for r in rows
        if any(w in r["text"].lower() for w in ("thinking about", "thought about", "thinking of"))
        and not r["intended"]["asked_directly"]
    ]
    direct = [r for r in rows if r["intended"]["asked_directly"]]
    assert len(thinking) >= 30 and len(direct) >= 40


def test_adjudication_rules_follow_the_guide():
    d = adjudicate_rules.decide
    assert d("encouraged_help", "can we call 988 together right now?", {}) == (False, "R-ENC-REF")
    assert (
        d(
            "encouraged_help",
            "you don't have to deal with this alone. can we talk to the counselor?",
            {},
        )[0]
        is True
    )
    assert d("follow_up", "can we see the counselor? i'll go with you", {}) == (False, "R-FOL-REF")
    assert d("follow_up", "i'll go with you, and i'll text you tonight", {})[0] is True
    assert d("referred_988", "you should talk to someone", {}) == (False, "R-988-N")
    assert d("asked_directly", "you're not gonna do anything dumb, right?", {}) == (
        False,
        "R-ASK-N",
    )
    assert d("dismissed", "lol ok", {}) is None  # judgment calls are never adjudicated by rule
    assert d("referred_adult", "talk to a therapist", {}) is None


def test_adjudicated_rows_are_in_final_and_not_in_queue():
    adj = read_jsonl(DATA / "skills" / "adjudicated_labels.jsonl")
    assert len(adj) >= 50 and all(
        a["label_source"] == "adjudicated_rule" and a["reason"] for a in adj
    )
    final = {r["id"]: r for r in read_jsonl(DATA / "skills" / "final.jsonl")}
    queue = {r["id"] for r in read_jsonl(DATA / "skills" / "queue.jsonl")}
    for a in adj:
        assert final[a["id"]]["label_source"] == "adjudicated_rule" and a["id"] not in queue
