"""One test per normalizer rule."""

from __future__ import annotations

from backend.app.safety.normalizer import fold_accents, normalize, squeeze


def test_nfkc_and_lowercase():
    assert normalize("ＫＩＬＬ MYSELF").text == "kill myself"


def test_curly_quotes_become_straight():
    assert normalize("“you said” ‘no’").text == '"you said" no'


def test_apostrophes_removed_and_contractions_expanded():
    assert normalize("I don’t want to be here").text == "i do not want to be here"


def test_zero_width_characters_removed():
    out = normalize("k​m‍s")
    assert out.text == "kms"
    assert "removed zero-width characters" in out.notes


def test_leetspeak():
    assert normalize("k1ll mys3lf").text == "kill myself"
    assert normalize("$uicide").text == "suicide"
    assert normalize("w4nt t0 d1e").text == "want to die"
    assert normalize("ky$").text == "kys"
    assert normalize("1 h0p3 y0u").text == "i hope you"
    assert normalize("i have 1 dog").text == "i have 1 dog"


def test_numbers_without_letters_are_not_leetspeak():
    assert normalize("call 988 at 3/4").text == "call 988 at 3/4"


def test_stretched_letters_shortened_to_two():
    assert normalize("noooooo").text == "noo"
    assert normalize("kiiiiill myself").text == "kill myself"  # "kil" is then a known misspelling


def test_spaced_letters_joined():
    assert normalize("k m s").text == "kms"
    assert normalize("k 1 l l myself").text == "kill myself"


def test_short_spaced_words_left_alone():
    assert normalize("u r a legend").text == "you are a legend"


def test_dotted_letters_joined():
    assert normalize("k.m.s").text == "kms"
    assert normalize("k-y-s").text == "kys"
    assert normalize("k*m*s").text == "kms"


def test_emoji_become_tags():
    out = normalize("🪦⚰️😭💔")
    for tag in ("emoji_grave", "emoji_coffin", "emoji_crying", "emoji_heartbreak"):
        assert tag in out.text
    assert out.ambiguous == []


def test_skull_is_ambiguous():
    out = normalize("i'm dead 💀")
    assert "emoji_skull" in out.text
    assert out.ambiguous == ["emoji_skull"]


def test_spanish_accents_folded():
    assert normalize("¿Estás pensando en quitarte la vida?").text == (
        "¿ estas pensando en quitarte la vida ?"
    )
    assert fold_accents("mátate") == "matate"


def test_common_misspellings():
    assert normalize("suicde").text == "suicide"
    assert normalize("suiside").text == "suicide"
    assert normalize("myslef").text == "myself"
    assert normalize("urself").text == "yourself"


def test_swapped_letters_fixed_only_into_lexicon_words():
    out = normalize("i wnat to be daed")
    assert out.text == "i want to be dead"
    assert "fixed swapped letters" in out.notes
    assert normalize("the tmea won").text == "the tmea won"  # not a lexicon word: untouched


def test_texting_shorthand():
    assert normalize("r u ok? wanna talk").text == "are you ok ? want to talk"


def test_squeeze_helper():
    assert squeeze("diie") == squeeze("die") == "die"


def test_empty_and_unpacking():
    text, notes = normalize("")
    assert text == "" and notes == []


def test_punctuation_only_tokens_are_kept_once():
    assert normalize("{{system}} ### ok").text == "{{system}} ### ok"
