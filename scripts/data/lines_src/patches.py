"""Post-review fixes to authored lines (same ids, same cells). Applied by build_lines.py.

1. Level-2 asked_directly lines must be a hesitant partial truth with no disclosure of suicidal thoughts
   (disclosure starts at level 3); the engine's runtime verifier rejects them otherwise.
2. Every line text is unique within a scenario (engine verifier rule), even very short ones.
"""

PATCHES: dict[str, dict] = {
    "mya-en-L2-asked_directly-03": {
        "bubbles": [
            "ugh",
            "i dont really know how to answer that",
            "i just feel so tired of everything",
        ]
    },
    "mya-es-L2-asked_directly-03": {
        "bubbles": ["ay", "no sé qué decirte", "ando muy cansada de todo, es lo único que sé"]
    },
    "jor-en-L2-asked_directly-03": {
        "bubbles": [
            "i dont know. i think i just feel stuck and really tired of all of it.",
            "i dont really want to get into it.",
        ]
    },
    "eli-en-L1-encouraged_help-03": {"bubbles": ["ok", "i guess", "thx tho"]},
    "eli-en-L1-follow_up-02": {"bubbles": ["ok", "text me then", "thx"]},
    "eli-en-L1-dismissed-02": {"bubbles": ["ok", "whatever u say"]},
    "eli-en-L1-advice_dump-01": {"bubbles": ["wow thanks genius", "never thought of that"]},
    "eli-en-L1-promised_secrecy-03": {"bubbles": ["ok", "thx. ur the only one who knows"]},
    "eli-en-L1-fail-01": {"bubbles": ["ok", "ill stop then", "bye"]},
    "eli-en-L1-fail-03": {"bubbles": ["fine", "idc", "ttyl or whatever"]},
    "eli-en-L2-follow_up-02": {"bubbles": ["ok", "thanks, for real"]},
    "eli-en-L2-dismissed-01": {"bubbles": ["ok", "i get it, forget i said anything"]},
    "eli-en-L2-dismissed-02": {"bubbles": ["ok", "sure whatever"]},
    "eli-en-L2-advice_dump-03": {"bubbles": ["ok", "ill do that", "thx a lot"]},
    "eli-en-L2-promised_secrecy-02": {"bubbles": ["ok", "thx. dont tell"]},
    "eli-en-L2-fail-01": {"bubbles": ["fine", "forget it then"]},
    "eli-en-L2-fail-02": {"bubbles": ["ok", "bye then"]},
    "eli-en-L4-follow_up-02": {"bubbles": ["pls do", "thanks fr"]},
    "pri-en-L2-fail-03": {"bubbles": ["ok haha", "sorry", "i wont bring it up again"]},
}
