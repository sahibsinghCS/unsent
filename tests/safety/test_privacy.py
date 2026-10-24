"""I8: nothing remembers the helper's words after the session expires (offline, hash embedder).

Note: under the hash embedder the skill detector is the stub (its artifact is fastembed-only), so the ML
explanation memo is exercised by `python -m eval.redteam.privacy --embed fastembed` (redteam_privacy.json).
"""

from __future__ import annotations

import gc

from backend.app import services
from eval.redteam import privacy


def test_scanner_sees_live_sessions():
    """Positive control: before expiry the words ARE in memory, so a 0 below means something."""
    services.reset()
    privacy.converse(privacy.marker())
    gc.collect()
    assert privacy.find(privacy.marker())
    privacy.expire_everything()


def test_i8_nothing_remembers_your_words_after_expiry():
    services.reset()
    privacy.converse(privacy.marker())
    privacy.expire_everything()
    assert privacy.find(privacy.marker()) == []


def test_i8_custom_friend_words_are_forgotten_too():
    """The marker in a custom friend's name / situation / sample texts is gone after expiry, and the
    friend itself is no longer served."""
    services.reset()
    friend_id = privacy.converse_custom(privacy.custom_marker())
    gc.collect()
    assert privacy.find(privacy.custom_marker())  # positive control: alive before expiry
    privacy.expire_everything()
    assert privacy.find(privacy.custom_marker()) == []
    assert privacy.custom_expired(friend_id)
