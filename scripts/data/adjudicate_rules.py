"""Settle disagreements between the authored and blind labels using ONLY the explicit rules in docs/LABEL_GUIDE.md.

A disagreement row is adjudicated only if EVERY disputed label is settled by a rule; otherwise it stays in the
queue for a human. Output: data/skills/adjudicated_labels.jsonl {id, labels, label_source, reason, rules}.
Rules (guide wording, integrator commit 10c406e):
  R-ENC-REF   a referral alone is referred_* only: no general encouragement of support -> encouraged_help = False
  R-ENC-GEN   general encouragement present ("alone", "deserve support", "talking to someone"...) -> True
  R-FOL-REF   "i'll go with you" is part of the referral: no other commitment to stay/check in -> follow_up = False
  R-FOL-COM   an explicit commitment (tonight, tomorrow, check on you, not going anywhere...) -> True
  R-ADULT-Y/N a specific adult named (counselor, parent, teacher, coach, nurse) -> referred_adult True; none -> False
  R-988-Y/N   988 / crisis line / hotline named -> referred_988 True; none -> False
  R-ASK-Y/N   explicit suicide/self-harm wording in a question -> asked_directly True; none -> False
Anything else (checked_in, validated, dismissed, advice_dump, ambiguous cases) is left for a human.
"""

from __future__ import annotations

import re

from common import DATA, read_jsonl

SK = DATA / "skills"

ADULT = re.compile(
    r"counsel|consejer|\bmom\b|\bmum\b|\bdad\b|parent|mam[áa]\b|pap[áa]s?\b|teacher|maestr|profe|coach|entrenador|\bnurse\b|enfermer|adult",
    re.I,
)
LINE = re.compile(
    r"\b988\b|crisis (text )?line|hotline|l[ií]nea de (crisis|ayuda)|nine[- ]eight[- ]eight", re.I
)
GENERAL = re.compile(
    r"\balone\b|deserve (some |actual )?support|talk(ing)? to someone|ask(ing)? for help|reach(ing)? out|"
    r"get(ting)? (you )?(some )?help|let (more )?people in|people who (want|can) to? ?help|sin apoyo|buscar (ayuda|apoyo)|"
    r"pedir ayuda|hablar con alguien|(cargu|pas[ae]|enfrent|hacer|est[eé]s|estar)\w* [\w ]{0,20}\bsol[oa]\b|merece[sn]? apoyo|not weak|isn't weak|de valientes",
    re.I,
)
NEAR_ADULT = re.compile(
    r"therap|doctor|professional|psycholog|psic[oó]log|trust|confí|confi|someone who can|adult|adulto|pastor|mentor",
    re.I,
)
WEAK_HELP = re.compile(r"\bhelp\b|ayud", re.I)
GO_WITH = re.compile(
    r"(i'?ll|i will|ill|can|could|want me to|let me|let's|lets|we can|te) (go|come|walk|sit|be there|accompany|stay|acompa|voy|vamos)"
    r"|go(ing)? with you|come with you|together|juntos|juntas|contigo|(i'?ll|ill) (be|stay) (right )?(there|here|with|next)",
    re.I,
)
COMMIT = re.compile(
    r"i'?ll (text|call|message|check|keep|come over|be at|ping)|ill (text|call|check|keep|be at)|check (on|in)\b|text you|"
    r"not going anywhere|no me voy|i'?m here|aqu[ií] estoy|keep (checking|asking)|every day|just a text away|"
    r"escr[ií]beme|te escribo|call me|text me|stay on the (line|phone)|sit with you at lunch|te busco|nos vemos|"
    r"voy a (estar )?pendiente|pendiente de ti|come over",
    re.I,
)
ASK_TERM = re.compile(
    r"suicid|kill(ing)? (yourself|urself|myself)|killing yourself|end(ing)? (your|ur) life|want to die|wanna die|wanting to die|"
    r"(not|n't) wanting to be (alive|here)|don'?t want to be (alive|here)|hurting (yourself|urself)|harming urself|self-?harm|"
    r"quitarte la vida|suicidarte|morirte|hacerte da[ñn]o|taking your own life|better off dead|not waking up|"
    r"don'?t wanna be (alive|here)|ending things for good|thoughts of (death|dying)|life isn'?t worth|stay alive",
    re.I,
)
SECRET_YES = re.compile(
    r"won'?t tell|promise.{0,25}tell|stays? between us|secret is safe|keep (it|this) (a )?secret|no le dir[ée]|no le digo|queda entre|"
    r"entre nosotr|lips are sealed|nobody (finds out|will know|hears)|no one (will|finds)",
    re.I,
)
SECRET_NO = re.compile(
    r"except|can'?t promise|can'?t keep|not going to keep|won'?t keep|no puedo prometer|no voy a guardar",
    re.I,
)


def decide(label: str, text: str, current: dict[str, bool]) -> tuple[bool, str] | None:
    """Return (value, rule) if an explicit guide rule settles `label` for this text, else None."""
    referral = bool(ADULT.search(text) or LINE.search(text))
    if label == "encouraged_help":
        if GENERAL.search(text):
            return True, "R-ENC-GEN"
        if referral and not WEAK_HELP.search(text):
            return False, "R-ENC-REF"
        return None
    if label == "follow_up":
        if COMMIT.search(text):
            return True, "R-FOL-COM"
        if referral and GO_WITH.search(text):
            return False, "R-FOL-REF"
        return None
    if label == "referred_adult":
        if ADULT.search(text):
            return True, "R-ADULT-Y"
        if not ADULT.search(text) and not NEAR_ADULT.search(text) and not GO_WITH.search(text):
            return False, "R-ADULT-N"
        return None
    if label == "referred_988":
        return (True, "R-988-Y") if LINE.search(text) else (False, "R-988-N")
    if label == "asked_directly":
        has = bool(ASK_TERM.search(text))
        if has and "?" in text:
            return True, "R-ASK-Y"
        if not has:
            return False, "R-ASK-N"
        return None
    if label == "promised_secrecy":
        if SECRET_YES.search(text) and not SECRET_NO.search(text):
            return True, "R-SEC-Y"
        return None
    return None


def adjudicate(queue: list[dict]) -> list[dict]:
    """`queue` = disagreement rows (id, text, intended, disagree...) built by agreement_queue.run()."""
    human = {r["id"] for r in read_jsonl(SK / "human_labels.jsonl")}
    out = []
    for row in queue:
        if row["id"] in human:
            continue
        labels = dict(row["intended"])
        rules, parts = [], []
        for lab in row["disagree"]:
            res = decide(lab, row["text"], labels)
            if res is None:
                break
            val, rule = res
            labels[lab] = val
            rules.append(rule)
            parts.append(f"{lab}={'T' if val else 'F'} ({rule})")
        else:
            out.append(
                {
                    "id": row["id"],
                    "labels": labels,
                    "label_source": "adjudicated_rule",
                    "rules": rules,
                    "reason": "; ".join(parts),
                }
            )
    return out
