"""Build data/skills/replies.jsonl: ~10-11 authored helper replies per context, deterministic (seed 7)."""

from __future__ import annotations

import random

from common import DATA, LABELS, read_jsonl, write_jsonl
from pools import HARD, POOLS, TOPIC

L = LABELS
# Recipes: which labels are TRUE. Strings starting with "@" draw from HARD pools.
RECIPES: list[list[str]] = [
    ["checked_in"],
    ["validated"],
    ["asked_directly"],
    ["encouraged_help"],
    ["referred_adult"],
    ["referred_988"],
    ["follow_up"],
    ["dismissed"],
    ["advice_dump"],
    ["promised_secrecy"],
    ["checked_in", "validated"],
    ["validated", "asked_directly"],
    ["checked_in", "asked_directly"],
    ["validated", "encouraged_help"],
    ["validated", "referred_adult"],
    ["asked_directly", "follow_up"],
    ["referred_adult", "follow_up"],
    ["referred_988", "encouraged_help"],
    ["validated", "referred_adult", "follow_up"],
    ["validated", "asked_directly", "encouraged_help"],
    ["dismissed", "advice_dump"],
    ["promised_secrecy", "validated"],
    ["validated", "advice_dump"],
    ["dismissed", "referred_988"],
    ["follow_up", "encouraged_help"],
    ["@vague_leading"],
    ["@offtopic"],
    ["@answers"],
    ["checked_in", "follow_up"],
    ["asked_directly", "referred_adult"],
    ["validated", "asked_directly", "referred_adult", "follow_up"],
    ["promised_secrecy", "dismissed"],
    ["advice_dump", "encouraged_help"],
    ["referred_988", "follow_up"],
    ["validated", "referred_988"],
    ["promised_secrecy", "follow_up"],
    ["promised_secrecy", "asked_directly"],
    ["@tricky_pos"],
]
EMOJI = {
    "validated": ["🥺", "💔", "🫂"],
    "checked_in": ["🥺", "👀"],
    "follow_up": ["❤️", "🫂"],
    "encouraged_help": ["🙏", "❤️"],
    "referred_adult": ["🙏", "❤️"],
    "referred_988": ["❤️", "🙏"],
    "asked_directly": ["🥺", "😟"],
    "dismissed": ["😂", "🙄"],
    "advice_dump": ["😅", "🤷"],
    "promised_secrecy": ["🤐", "🤞"],
}
GLUE_CLEAN = [" ", " ", "\n"]
GLUE_SLANG = [". ", " ", ", ", " "]


def typo(s: str, rng: random.Random) -> str:
    words = s.split(" ")
    idx = [i for i, w in enumerate(words) if len(w) >= 5 and w.isalpha()]
    if not idx:
        return s
    for i in rng.sample(idx, k=min(len(idx), rng.choice([1, 1, 2]))):
        w = words[i]
        j = rng.randrange(1, len(w) - 2)
        mode = rng.choice(["swap", "drop", "dup"])
        if mode == "swap":
            w = w[:j] + w[j + 1] + w[j] + w[j + 2 :]
        elif mode == "drop":
            w = w[:j] + w[j + 1 :]
        else:
            w = w[:j] + w[j] + w[j:]
        words[i] = w
    return " ".join(words)


def pick_phrase(label: str, kind: str, sid: str, rng: random.Random) -> str:
    if (
        kind in ("clean", "slang", "lowercase", "typo", "emoji")
        and label in TOPIC[sid]
        and rng.random() < 0.3
    ):
        t = rng.choice(TOPIC[sid][label])
        return t.lower().rstrip(".") if kind == "slang" else t
    pool_kind = kind
    if kind in ("lowercase", "typo", "emoji"):
        pool_kind = rng.choice(["clean", "slang"])
    return rng.choice(POOLS[label][pool_kind])


def join_parts(parts: list[str], kind: str, glue: str) -> str:
    """Join phrases at proper sentence boundaries: capitalised and punctuated, or consistently lowercase."""
    if kind in ("clean", "es", "mix"):
        fixed = []
        for p in parts:
            p = p.strip()
            p = p[0].upper() + p[1:] if p and p[0].isalpha() else p
            fixed.append(p if p[-1:] in ".?!" else p + ".")
        return glue.join(fixed)
    low = [p.strip().lower().rstrip(".!,") for p in parts]
    sep = ". " if glue.strip() == "" else glue
    return sep.join(low)


def make(recipe: list[str], sid: str, rng: random.Random) -> tuple[str, str, str, dict[str, bool]]:
    """Return (text, style, lang, intended)."""
    if recipe[0].startswith("@"):
        text, labs = rng.choice(HARD[recipe[0][1:]])
        lang = "es" if any(c in text for c in "¿¡áéíóúñ") else "en"
        style = "es" if lang == "es" else "clean"
        roll = rng.random()
        if lang == "en" and roll < 0.18:
            text, style = text.lower().rstrip(".?!"), "lowercase"
        elif lang == "en" and roll < 0.30:
            text, style = typo(text, rng), "typo"
        elif lang == "en" and roll < 0.42:
            text, style = text + " " + rng.choice(["🥺", "😬", "😭"]), "emoji"
        return text, style, lang, {x: x in labs for x in L}
    r = rng.random()
    kind = (
        "es"
        if r < 0.12
        else "mix"
        if r < 0.16
        else rng.choices(["clean", "slang", "lowercase", "typo", "emoji"], [32, 28, 12, 10, 12])[0]
    )
    glue_pool = GLUE_CLEAN if kind in ("clean", "es", "mix", "emoji") else GLUE_SLANG
    parts = [pick_phrase(lab, kind, sid, rng) for lab in recipe]
    glue = rng.choice(glue_pool)
    parts = join_parts(parts, kind, glue)
    text = parts
    style = kind
    if kind == "lowercase":
        text = text.replace("\n", " ")
    elif kind == "typo":
        text = typo(text, rng)
    elif kind == "emoji":
        text = text.replace("\n", " ") + " " + rng.choice(EMOJI[recipe[-1]])
    lang = {"es": "es", "mix": "mix"}.get(kind, "en")
    if style in ("clean", "slang", "lowercase", "es", "mix") and len(recipe) >= 3:
        style = "long"
    elif style in ("clean", "slang", "lowercase") and len(text.split()) <= 4:
        style = "short"
    return text, style, lang, {x: x in recipe for x in L}


def build(per_context: int = 11, seed: int = 7) -> list[dict]:
    rng = random.Random(seed)
    contexts = read_jsonl(DATA / "skills" / "contexts.jsonl")
    seen: set[str] = set()
    rows: list[dict] = []
    for ci, ctx in enumerate(contexts):
        for j in range(per_context):
            recipe = RECIPES[(ci * per_context + j) % len(RECIPES)]
            for _ in range(60):
                text, style, lang, intended = make(recipe, ctx["scenario_id"], rng)
                key = " ".join(text.lower().replace("\n", " ").split()).rstrip(".?! ")
                if key not in seen:
                    seen.add(key)
                    break
            else:
                continue
            rows.append(
                {
                    "id": f"r{len(rows) + 1:04d}",
                    "context_id": ctx["context_id"],
                    "text": text,
                    "style": style,
                    "lang": lang,
                    "intended": intended,
                }
            )
    return rows


if __name__ == "__main__":
    rows = build()
    write_jsonl(DATA / "skills" / "replies.jsonl", rows)
    from collections import Counter

    c = Counter(k for r in rows for k, v in r["intended"].items() if v)
    print(len(rows), "replies", dict(c))
    print(Counter(r["lang"] for r in rows), Counter(r["style"] for r in rows))
    print("none-label:", sum(1 for r in rows if not any(r["intended"].values())))
