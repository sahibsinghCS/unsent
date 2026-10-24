"""The landing page's example conversation is a real run: every friend line is a reviewed bank line
of that scenario, and the numbers chain from one message to the next."""

from __future__ import annotations

import json

from backend.app.config import CONTENT_DIR
from backend.app.content import load_lines


def test_demo_transcript_is_a_real_run():
    data = json.loads((CONTENT_DIR / "demo_transcript.json").read_text(encoding="utf-8"))
    for locale in ("en", "es"):
        run = data[locale]
        bank = {line.id: line.bubbles for line in load_lines(run["scenario"], locale)}
        trust = 30
        for turn in run["turns"]:
            assert turn["trust_before"] == trust, "each message starts where the last one ended"
            trust = turn["trust_after"]
            if turn["seen"]:
                assert turn["friend"] == []
            else:
                assert bank[turn["line_id"]] == turn["friend"], "friend words are a reviewed line"
            assert turn["guardian"] == "continue"


def test_frontend_bundles_the_same_transcript():
    bundled = CONTENT_DIR.parent / "frontend" / "src" / "content" / "demo_transcript.json"
    assert bundled.read_bytes() == (CONTENT_DIR / "demo_transcript.json").read_bytes(), (
        "run `npm run build` in frontend/ (sync-content) after `make demo-transcript`"
    )
