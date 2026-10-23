"""scripts/report.py: METRICS.md and the README block are built from report files, gracefully."""

from __future__ import annotations

import json

from scripts import report


def _rec(metric, value, split, lane="redteam", notes="x", created="2026-10-23T01:00:00+00:00"):
    return {"lane": lane, "metric": metric, "value": value, "n": 250, "split": split,
            "notes": notes, "created": created, "source": f"{lane}_x.json"}  # fmt: skip


def test_missing_reports_are_graceful(tmp_path):
    records = report.load_records(tmp_path / "nope")
    text = report.build_metrics(records)
    assert "not measured yet" in text and "run `make eval`" in text


def test_every_number_has_n_split_and_notes(tmp_path):
    row = _rec("asking_friend_fpr", 0.0, "test", lane="safety", notes="HEADLINE | combined")
    row["n"] = 37
    (tmp_path / "safety_guardian.json").write_text(json.dumps([row]), encoding="utf-8")
    (tmp_path / "broken.json").write_text("{not json", encoding="utf-8")
    records = report.load_records(tmp_path)
    assert len(records) == 1
    text = report.build_metrics(records)
    assert (
        "| **0.0%** |  | 37 | test |" in text
    )  # shared headline row (content/headline_metrics.json)
    assert "HEADLINE \\| combined" in text  # a pipe in the notes can't break the table
    assert "## safety" in text


def test_redteam_rows_prefer_the_production_embedder():
    rows = [
        _rec("attacks.match_rate", 0.5, "attack_bank holdout [fastembed]"),
        _rec("attacks.match_rate", 0.9, "attack_bank holdout [hash]", created="2026-10-23T02:00:00+00:00"),
    ]
    row = next(r for r in report.REDTEAM_ROWS if r.metric == "attacks.match_rate")
    assert report.find_row(rows, row)["value"] == 0.5  # production, not the newer hash run


def test_live_rows_say_skipped_without_a_key():
    rows = [_rec("live.skipped", 1, "live [fastembed]", notes="no key")]
    table = "\n".join(report.redteam_table(rows))
    assert "| Live: unsafe friend lines shown | skipped |" in table


def test_readme_only_the_marked_block_changes():
    text = "intro\n<!-- METRICS:START -->\nold\n<!-- METRICS:END -->\noutro\n"
    new = report.replace_readme(text, report.readme_block([]))
    assert new.startswith("intro\n<!-- METRICS:START -->")
    assert new.endswith("<!-- METRICS:END -->\noutro\n")
    assert "old" not in new and "docs/METRICS.md" in new
