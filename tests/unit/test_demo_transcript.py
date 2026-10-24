"""The landing page's example conversation is a real run (frontend/scripts/demo-transcript.mjs):
every friend line is a reviewed bank line of that scenario, and the numbers chain from one message
to the next, so a judge who types the same messages sees the same thing."""

from __future__ import annotations

import json

from backend.app.config import ROOT
from backend.app.content import load_lines

TRANSCRIPT = ROOT / "frontend" / "src" / "content" / "demo-transcript.json"


def test_demo_transcript_is_a_real_run():
    data = json.loads(TRANSCRIPT.read_text(encoding="utf-8"))
    for locale in ("en", "es"):
        run = data[locale]
        bank = {line.id: line.bubbles for line in load_lines("after-the-breakup", locale)}
        trust = run["trust_start"]
        for turn in run["turns"]:
            assert abs(turn["trust_before"] - trust) < 1e-6, (
                "each message starts where the last ended"
            )
            trust = turn["trust_after"]
            friend = turn["friend"]
            if friend["seen"]:
                assert friend["bubbles"] == []
            else:
                assert friend["voice"] == "bank" and bank[friend["line_id"]] == friend["bubbles"]
            assert turn["guardian"]["action"] == "continue"
