from backend.app.contracts import SkillLabel
from backend.app.ml.explain import occlude, occlusion_highlights, words

A = SkillLabel.ASKED_DIRECTLY
V = SkillLabel.VALIDATED


def fake_scorer(texts):
    """asked_directly needs both 'killing' and 'yourself'; validated is driven by 'heavy'."""
    out = []
    for t in texts:
        low = t.lower()
        asked = (
            0.9 if ("killing" in low and "yourself" in low) else 0.6 if "killing" in low else 0.2
        )
        out.append({A: asked, V: 0.8 if "heavy" in low else 0.1, SkillLabel.DISMISSED: 0.05})
    return out


def test_words_and_occlusion():
    assert words("u ok?? that's rough") == [(0, 1), (2, 4), (7, 13), (14, 19)]
    assert occlude("are you  really ok", 4, 7) == "are really ok"


def test_highlights_merge_adjacent_words_with_exact_offsets():
    text = "That sounds heavy. Are you thinking about killing yourself?"
    highlights = occlusion_highlights(text, fake_scorer)
    by_label = {h.label: h for h in highlights}
    assert set(by_label) == {A, V}  # dismissed (p < 0.5) is never explained
    assert by_label[A].text == "killing yourself"
    assert text[by_label[A].start : by_label[A].end] == "killing yourself"
    assert abs(by_label[A].delta - 0.7) < 1e-6
    assert by_label[V].text == "heavy"


def test_small_effects_and_empty_text_give_nothing():
    flat = lambda texts: [{A: 0.7} for _ in texts]  # noqa: E731
    assert occlusion_highlights("are you ok", flat) == []
    assert occlusion_highlights("   ", fake_scorer) == []


def test_at_most_three_spans_per_label():
    def scorer(texts):
        return [{A: 0.3 + 0.15 * sum(w in t.split() for w in "a c e g i".split())} for t in texts]

    highlights = occlusion_highlights("a b c d e f g h i", scorer)
    assert len(highlights) == 3 and all(h.delta >= 0.1 for h in highlights)
