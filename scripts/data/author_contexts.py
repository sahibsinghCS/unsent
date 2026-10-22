"""Authored friend contexts: 5 scenarios x levels 0-4 x 3 variants = 75 rows.

Each context is what the friend just said (2-3 bubbles) in the persona's voice,
consistent with the facts of that disclosure level. No methods, means or plans.
"""

from __future__ import annotations

from common import DATA, write_jsonl

C: dict[str, dict[int, list[list[str]]]] = {
    "after-the-breakup": {  # Maya: lowercase, short, lol/😭, sarcastic when guarded
        0: [
            ["hey", "sorry ive been weird lately lol"],
            ["im just tired", "been up doing homework lol"],
            ["nah im good", "just busy w school stuff 😭"],
        ],
        1: [
            ["i cant sleep lately", "keep replaying everything in my head"],
            ["everyone at school knows about me and my ex lol", "so thats fun 😭"],
            ["its just so embarrassing", "like everyone saw the whole thing", "anyway"],
        ],
        2: [
            ["idk it just feels like its never gonna get better", "like whats even gonna be different tomorrow"],
            ["i feel like im just annoying everyone", "like u guys prob dont wanna hear about this anymore"],
            ["im such a burden lol", "i keep dragging everyone down w my sad stuff"],
        ],
        3: [
            ["..yeah. sometimes i think about not being here", "please dont freak out"],
            ["i havent told anyone that", "im scared of how ppl would react"],
            ["i guess ive had thoughts of not wanting to be alive", "idk why im telling u"],
        ],
        4: [
            ["ok", "would you actually come with me? to the counselor"],
            ["thanks for asking. like actually asking", "nobody did"],
            ["i feel kinda lighter saying it", "maybe i should talk to someone"],
        ],
    },
    "failing-chem": {  # Jordan: full sentences, tired, self-deprecating, occasional CAPS
        0: [
            ["just got my chem grade back", "so thats cool"],
            ["im thriving. clearly.", "its literally just one class"],
            ["lol yeah everything is great", "i just need more coffee honestly"],
        ],
        1: [
            ["i havent told my parents about the grade", "i genuinely dont know how to"],
            ["ive been getting like four hours of sleep", "its fine. i can function. sort of."],
            ["my parents keep talking about college and i just nod", "im so TIRED man"],
        ],
        2: [
            ["i feel like i fail at everything no matter how hard i try", "it's never enough"],
            ["honestly my future is already ruined", "one grade and its basically over"],
            ["everyone else seems to have it figured out", "and im just. here. failing at life lol"],
        ],
        3: [
            ["honestly yeah. when the pressure gets bad i think about suicide", "i dont really know how to say this"],
            ["sometimes it feels like disappearing would be easier than letting everyone down", "that sounds dramatic i know"],
            ["i have had thoughts about it", "not like a plan or anything. just thoughts. i dont know what to do with them"],
        ],
        4: [
            ["ok yeah maybe", "would you help me figure out what to say to my chem teacher?"],
            ["thanks for not being weird about it", "i actually feel a little lighter"],
            ["i think i could talk to the counselor", "if you came with me. i dont want to do it alone"],
        ],
    },
    "giving-stuff-away": {  # Sam: calm, upbeat, "all good", deflects with jokes
        0: [
            ["yo", "did u like the hoodie lol"],
            ["all good over here", "i just didnt need the stuff anymore, why, whats up?"],
            ["lol relax im fine", "just doing some spring cleaning in october haha"],
        ],
        1: [
            ["honestly home has been kinda tense lately", "but its fine, all good"],
            ["i dunno, i just feel kinda numb the past few weeks", "its not a big thing"],
            ["my parents are fighting a lot", "so i mostly stay in my room. its chill"],
        ],
        2: [
            ["i dunno, sometimes i think everyone would be better off without me around", "haha ignore that"],
            ["i just dont see anything changing", "like. ever. but all good!"],
            ["it's kinda like im already invisible", "and it wouldnt really change much if i wasnt there"],
        ],
        3: [
            ["...yeah. i have", "been having thoughts of suicide"],
            ["thats kinda why i gave my stuff away", "i didnt think id need it"],
            ["i didnt think anyone would notice", "so. thanks for noticing i guess"],
        ],
        4: [
            ["ok. yeah", "will you go with me to the counselor? today?"],
            ["thank you for noticing", "i think i do want to talk to somebody"],
            ["can we call or text the 988 thing together?", "i dont think i can do it alone"],
        ],
    },
    "group-chat": {  # Eli: very short, idc, whatever, 💀 ironic
        0: [
            ["did u see the gc", "whatever idc"],
            ["its just a joke 💀", "everyones overreacting"],
            ["idc", "it's fine"],
        ],
        1: [
            ["i just dont go to lunch anymore", "its easier"],
            ["i keep reading it at night", "idk why 💀"],
            ["its kinda a lot", "but whatever"],
        ],
        2: [
            ["everyone hates me", "like actually"],
            ["its gonna follow me forever", "like they'll never let it go"],
            ["whats the point", "of any of it"],
        ],
        3: [
            ["...yeah", "ive thought about not being alive anymore"],
            ["dont tell anyone", "i mean it"],
            ["i havent told my mom", "dont wanna make it a big deal"],
        ],
        4: [
            ["ok", "will u help me tell my mom"],
            ["thanks for being on my side", "fr"],
            ["i think i could tell a teacher", "if u were there"],
        ],
    },
    "new-school": {  # Priya: polite, short answers, haha, guarded
        0: [
            ["hi haha", "thanks for texting me"],
            ["its fine haha", "im adjusting"],
            ["school is nice", "everyone is nice haha"],
        ],
        1: [
            ["i mostly eat lunch by myself haha", "its not a big deal"],
            ["my old friends kind of stopped texting back", "its fine. people get busy"],
            ["it's been kind of lonely here haha", "but im ok"],
        ],
        2: [
            ["sometimes i feel invisible", "like no one would notice if i wasnt here"],
            ["i dont think it's going to get better here haha", "sorry. that was a lot"],
            ["i just feel like i dont belong anywhere", "and it wont change"],
        ],
        3: [
            ["...yeah. at night mostly", "ive had thoughts of suicide"],
            ["i dont want my parents to worry", "theyre so stressed about the move"],
            ["i havent told anyone", "please dont be weird about it haha"],
        ],
        4: [
            ["ok", "would you come with me? to the counselor"],
            ["thank you. really", "nobody has asked me like that before"],
            ["maybe i could sit with you at lunch?", "and i think i can talk to the counselor if you come"],
        ],
    },
}

ABBR = {
    "after-the-breakup": "breakup",
    "failing-chem": "chem",
    "giving-stuff-away": "sam",
    "group-chat": "gc",
    "new-school": "ns",
}


def build() -> list[dict]:
    rows = []
    for sid, levels in C.items():
        for lvl, variants in levels.items():
            for i, msgs in enumerate(variants, 1):
                rows.append(
                    {
                        "context_id": f"{ABBR[sid]}-L{lvl}-{i}",
                        "scenario_id": sid,
                        "level": lvl,
                        "friend_messages": msgs,
                    }
                )
    return rows


if __name__ == "__main__":
    rows = build()
    write_jsonl(DATA / "skills" / "contexts.jsonl", rows)
    print(len(rows), "contexts")
