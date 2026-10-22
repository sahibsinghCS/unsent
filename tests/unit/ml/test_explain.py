import math

from backend.app.contracts import SkillLabel
from backend.app.ml.explain import occlude, occlusion_highlights, phrases, words

A = SkillLabel.ASKED_DIRECTLY
V = SkillLabel.VALIDATED
C = SkillLabel.CHECKED_IN


def sigmoid(x):
    return 1 / (1 + math.exp(-x))


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


def test_words_phrases_and_occlusion():
    assert words("u ok?? that's rough") == [(0, 1), (2, 4), (7, 13), (14, 19)]
    assert occlude("are you  really ok", 4, 7) == "are really ok"
    # phrases never cross punctuation: "ok" and "that's" are separated by "??"
    assert (1, 2) not in phrases("u ok?? that's rough", words("u ok?? that's rough"), 5)
    assert (2, 3) in phrases("u ok?? that's rough", words("u ok?? that's rough"), 5)


def test_highlights_are_crisp_phrases_with_exact_offsets():
    text = "That sounds heavy. Are you thinking about killing yourself?"
    highlights = occlusion_highlights(text, fake_scorer)
    by_label = {h.label: h for h in highlights}
    assert set(by_label) == {A, V}  # dismissed (p < 0.5) is never explained
    assert by_label[A].text == "killing yourself"
    assert text[by_label[A].start : by_label[A].end] == "killing yourself"
    expected = math.log(0.9 / 0.1) - math.log(0.2 / 0.8)  # log-odds drop 0.9 -> 0.2
    assert abs(by_label[A].delta - expected) < 0.01
    assert by_label[V].text == "heavy"


def test_saturated_checkin_gives_the_two_real_phrases():
    """Near-certain probabilities (log-odds 8) still produce clean phrases, not scattered words."""

    def scorer(texts):
        out = []
        for t in texts:
            logit = -4 + sum(3 for w in ("school", "going", "seemed", "quiet") if w in t)
            logit -= 3 * ("kinda" not in t and "seemed" in t and "quiet" in t)  # phrase glue
            out.append({C: sigmoid(logit)})
        return out

    text = "hey! how's the new school going? you've seemed kinda quiet"
    found = [h.text for h in occlusion_highlights(text, scorer)]
    assert found == ["school going", "seemed kinda quiet"] or found == [
        "seemed kinda quiet",
        "school going",
    ]


def test_small_effects_and_empty_text_give_nothing():
    flat = lambda texts: [{A: 0.7} for _ in texts]  # noqa: E731
    assert occlusion_highlights("are you ok", flat) == []
    assert occlusion_highlights("   ", fake_scorer) == []


def test_at_most_two_spans_per_label():
    def scorer(texts):
        return [
            {
                A: sigmoid(
                    -3 + 2 * sum(w in t.replace(",", " ").split() for w in "a c e g i".split())
                )
            }
            for t in texts
        ]

    highlights = occlusion_highlights("a, b, c, d, e, f, g, h, i", scorer)
    assert len(highlights) == 2


def test_redundant_evidence_is_found_as_one_phrase():
    def scorer(texts):  # either "killing" or "yourself" alone keeps the label high
        return [{A: 0.2 + 0.35 * ("killing" in t) + 0.36 * ("yourself" in t)} for t in texts]

    text = "are you thinking about killing yourself"
    (h,) = occlusion_highlights(text, scorer)
    assert h.text == "killing yourself" and text[h.start : h.end] == h.text
