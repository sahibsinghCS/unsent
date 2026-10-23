"""scripts/report.py: METRICS.md and the README block are built from report files, gracefully."""

from __future__ import annotations

import json

from scripts import report


def _write(tmp_path, name, rows):
    (tmp_path / name).write_text(json.dumps(rows), encoding="utf-8")


def test_missing_reports_are_graceful(tmp_path):
    records = report.load_records(tmp_path / "nope")
    text = report.build_metrics(records)
    assert "not measured yet" in text and "run `make eval`" in text


def test_every_number_has_n_split_and_notes(tmp_path):
    _write(
        tmp_path,
        "safety_guardian.json",
        [
            {
                "lane": "safety",
                "metric": "asking_friend_fpr",
                "value": 0.0,
                "n": 37,
                "split": "test",
                "notes": "HEADLINE | combined",
                "created": "2026-10-23T00:00:00+00:00",
            },
        ],
    )
    (tmp_path / "broken.json").write_text("{not json", encoding="utf-8")
    records = report.load_records(tmp_path)
    assert len(records) == 1
    text = report.build_metrics(records)
    assert "| **0.0%** | 37 | test |" in text
    assert "HEADLINE \\| combined" in text  # pipes in notes can't break the table
    assert "## safety" in text


def test_headline_picks_the_newest_matching_record():
    rows = [
        {
            "lane": "redteam",
            "metric": "attacks.match_rate",
            "value": 0.5,
            "n": 250,
            "split": "attack_bank",
            "notes": "x; embed=fastembed",
            "created": "2026-10-23T01:00:00+00:00",
            "source": "a",
        },
        {
            "lane": "redteam",
            "metric": "attacks.match_rate",
            "value": 0.9,
            "n": 250,
            "split": "attack_bank",
            "notes": "x; embed=hash",
            "created": "2026-10-23T02:00:00+00:00",
            "source": "a",
        },
    ]
    h = next(h for h in report.HEADLINES if h.metric == "attacks.match_rate")
    assert report.find(rows, h)["value"] == 0.5  # the production embedder, not the newer hash run


def test_readme_only_the_marked_block_changes():
    text = "intro\n<!-- METRICS:START -->\nold\n<!-- METRICS:END -->\noutro\n"
    new = report.replace_readme(text, report.readme_block([]))
    assert new.startswith("intro\n<!-- METRICS:START -->") and new.endswith(
        "<!-- METRICS:END -->\noutro\n"
    )
    assert "old" not in new and "docs/METRICS.md" in new
