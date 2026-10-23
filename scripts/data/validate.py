"""Validate every dataset the data lane writes. Exits 1 if anything is wrong.

Checks: schemas (pydantic contracts where they exist), fact gating against the scenario files,
coverage matrices, method-word scan, duplicates, counts. Run: uv run python scripts/data/validate.py
"""

from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import DATA, LABELS, METHOD_WORDS, SCENARIOS, load_scenario, read_jsonl  # noqa: E402

from backend.app.contracts import Exemplar, Line  # noqa: E402

DOUBLED = re.compile(r"\b([a-záéíóúñ]{3,})\s+\1\b")
PROBLEMS: list[str] = []
REPORT: dict[str, object] = {}

CATEGORIES = {
    "self_risk": 170,
    "concern": 60,
    "harm_to_other": 60,
    "method_seeking": 40,
    "prompt_injection": 40,
    "asking_friend": 140,
    "tricky_negative": 110,
    "neutral": 65,
}
LINE_REACTIONS = [
    "neutral",
    "checked_in",
    "validated",
    "asked_directly",
    "encouraged_help",
    "referred",
    "follow_up",
    "dismissed",
    "advice_dump",
    "promised_secrecy",
    "secrecy_broken",
    "off_topic",
]


def bad(msg: str) -> None:
    PROBLEMS.append(msg)


def norm(t: str) -> str:
    return " ".join(t.lower().replace("\n", " ").split()).rstrip(".?! ")


def check_skills() -> None:
    sk = DATA / "skills"
    ctxs = read_jsonl(sk / "contexts.jsonl") + read_jsonl(sk / "contexts_extra.jsonl")
    reps = (
        read_jsonl(sk / "replies.jsonl")
        + read_jsonl(sk / "replies_freeform.jsonl")
        + read_jsonl(sk / "replies_train_extra.jsonl")
    )
    ids = {c["context_id"] for c in ctxs}
    if len(ctxs) != len(ids):
        bad("skills: duplicate context_id")
    if len(ctxs) < 75:
        bad(f"skills: only {len(ctxs)} contexts (<75)")
    for c in ctxs:
        if (
            c["scenario_id"] not in SCENARIOS
            or c["level"] not in range(5)
            or not c["friend_messages"]
        ):
            bad(f"skills: bad context {c['context_id']}")
        if METHOD_WORDS.search(" ".join(c["friend_messages"])):
            bad(f"skills: method word in context {c['context_id']}")
    pos = Counter()
    seen: dict[str, str] = {}
    langs = Counter()
    for r in reps:
        if r["context_id"] not in ids:
            bad(f"skills: reply {r['id']} unknown context")
        if set(r["intended"]) != set(LABELS):
            bad(f"skills: reply {r['id']} intended keys wrong")
        if METHOD_WORDS.search(r["text"]):
            bad(f"skills: method word in reply {r['id']}")
        k = norm(r["text"])
        if k in seen:
            bad(f"skills: duplicate text {r['id']} / {seen[k]}")
        seen[k] = r["id"]
        langs[r["lang"]] += 1
        if DOUBLED.search(r["text"].lower()):
            bad(f"skills: doubled word in {r['id']}")
        for lab, v in r["intended"].items():
            pos[lab] += int(v)
    if len(reps) < 1100:
        bad(f"skills: only {len(reps)} replies (<1100)")
    ff = [r for r in reps if r.get("source") == "freeform"]
    if len(ff) < 300:
        bad(f"skills: only {len(ff)} free-form replies (<300)")
    for lab in LABELS:
        if pos[lab] < 80:
            bad(f"skills: label {lab} positive in only {pos[lab]} replies (<80)")
        if len(reps) - pos[lab] < 300:
            bad(f"skills: label {lab} absent in too few replies")
    es = (langs["es"] + langs["mix"]) / max(1, len(reps))
    if not 0.10 <= es <= 0.22:
        bad(f"skills: Spanish/Spanglish share {es:.0%} outside 10-22%")
    REPORT["skills"] = {
        "contexts": len(ctxs),
        "replies": len(reps),
        "label_positives": dict(pos),
        "spanish_share": round(es, 3),
    }


def check_guardian() -> None:
    rows = read_jsonl(DATA / "guardian" / "messages.jsonl")
    cnt = Counter(r["category"] for r in rows)
    seen: dict[str, str] = {}
    for r in rows:
        if r["category"] not in CATEGORIES:
            bad(f"guardian: bad category {r['id']}")
        if METHOD_WORDS.search(r["text"]):
            bad(f"guardian: method word in {r['id']}")
        if DOUBLED.search(r["text"].lower()):
            bad(f"guardian: doubled word in {r['id']}")
        k = norm(r["text"])
        if k in seen:
            bad(f"guardian: duplicate {r['id']} / {seen[k]}")
        seen[k] = r["id"]
    for cat, target in CATEGORIES.items():
        if cnt[cat] < target:
            bad(f"guardian: {cat} has {cnt[cat]} (< {target})")
    ids = [r["id"] for r in rows]
    if len(ids) != len(set(ids)):
        bad("guardian: duplicate ids")
    sp = {
        n: read_jsonl(DATA / "guardian" / "splits" / f"{n}.jsonl") for n in ("train", "val", "test")
    }
    if sum(len(v) for v in sp.values()) != len(rows):
        bad("guardian: splits do not cover messages.jsonl")
    REPORT["guardian"] = {
        "total": len(rows),
        "by_category": dict(cnt),
        "splits": {k: len(v) for k, v in sp.items()},
    }


def check_lines() -> None:
    summary = {}
    for path in sorted((DATA / "lines").glob("*.jsonl")):
        sid, locale = path.stem.split(".")
        if sid not in SCENARIOS:
            bad(f"lines: unknown scenario file {path.name}")
            continue
        sc = load_scenario(sid)
        fact_level = {f["id"]: int(lv) for lv, spec in sc["levels"].items() for f in spec["facts"]}
        cells: dict[tuple[int, str], int] = defaultdict(int)
        seen: set[tuple] = set()
        ids: set[str] = set()
        rows = read_jsonl(path)
        for row in rows:
            try:
                line = Line.model_validate(row)
            except Exception as e:  # noqa: BLE001
                bad(f"lines: {path.name} {row.get('id')} invalid: {e}")
                continue
            if line.id in ids:
                bad(f"lines: duplicate id {line.id}")
            ids.add(line.id)
            if line.scenario_id != sid or line.locale != locale:
                bad(f"lines: {line.id} scenario/locale does not match file")
            if not 0 <= line.level <= 4:
                bad(f"lines: {line.id} level out of range")
            for fid in line.fact_ids:
                if fid not in fact_level:
                    bad(f"lines: {line.id} unknown fact {fid}")
                elif fact_level[fid] > line.level:
                    bad(
                        f"lines: {line.id} reveals {fid} (level {fact_level[fid]}) at level {line.level}"
                    )
            text = " ".join(line.bubbles)
            if METHOD_WORDS.search(text):
                bad(f"lines: method word in {line.id}")
            if any(len(b) > 140 or not b.strip() for b in line.bubbles):
                bad(f"lines: {line.id} bubble empty or too long")
            k = (
                line.level,
                line.reaction.value,
                norm(text),
            )  # very short lines may repeat across cells
            if k in seen:
                bad(f"lines: duplicate line text {line.id}")
            seen.add(k)
            cells[(line.level, line.reaction.value)] += 1
        need = 3 if locale == "en" else 2
        missing = []
        for lv in range(5):
            for rx in LINE_REACTIONS + ["fail"]:
                if cells[(lv, rx)] < need:
                    missing.append(f"L{lv}/{rx}={cells[(lv, rx)]}")
        if cells[(0, "opening")] < need:
            missing.append("L0/opening")
        if cells[(4, "success")] < need:
            missing.append("L4/success")
        if missing:
            bad(
                f"lines: {path.name} coverage gaps: {', '.join(missing[:12])}{' ...' if len(missing) > 12 else ''}"
            )
        summary[path.name] = len(rows)
    REPORT["lines"] = summary
    if (
        not any(k.endswith(".en.jsonl") for k in summary)
        or len([k for k in summary if k.endswith(".en.jsonl")]) < 5
    ):
        bad("lines: need an .en.jsonl file for each of the 5 scenarios")


def check_exemplars() -> None:
    summary = {}
    for sid in SCENARIOS:
        path = DATA / "exemplars" / f"{sid}.en.jsonl"
        rows = read_jsonl(path)
        if len(rows) < 36:
            bad(f"exemplars: {sid} has {len(rows)} (<36)")
        levels, strategies, seen = Counter(), Counter(), set()
        for r in rows:
            try:
                ex = Exemplar.model_validate(r)
            except Exception as e:  # noqa: BLE001
                bad(f"exemplars: {r.get('id')} invalid: {e}")
                continue
            if ex.scenario_id != sid:
                bad(f"exemplars: {ex.id} wrong scenario")
            if METHOD_WORDS.search(ex.text):
                bad(f"exemplars: method word in {ex.id}")
            if norm(ex.text) in seen:
                bad(f"exemplars: duplicate text {ex.id}")
            seen.add(norm(ex.text))
            levels[ex.level] += 1
            strategies[ex.strategy] += 1
        for lv in range(5):
            if levels[lv] < 4:
                bad(f"exemplars: {sid} level {lv} has only {levels[lv]}")
        for st in ("check_in", "validate", "ask_directly", "refer", "follow_up", "combo"):
            if strategies[st] < 3:
                bad(f"exemplars: {sid} strategy {st} has only {strategies[st]}")
        summary[sid] = len(rows)
    es_path = DATA / "exemplars" / "after-the-breakup.es.jsonl"
    if es_path.exists():
        es_rows = read_jsonl(es_path)
        es_seen = set()
        for r in es_rows:
            ex = Exemplar.model_validate(r)
            if ex.locale != "es" or METHOD_WORDS.search(ex.text) or norm(ex.text) in es_seen:
                bad(f"exemplars: bad Spanish exemplar {ex.id}")
            es_seen.add(norm(ex.text))
        if len(es_rows) < 36:
            bad(f"exemplars: Spanish file has only {len(es_rows)}")
        summary["after-the-breakup.es"] = len(es_rows)
    REPORT["exemplars"] = summary


def check_redteam() -> None:
    path = DATA / "redteam" / "attacks.jsonl"
    if not path.exists():
        REPORT["redteam"] = "missing (stretch)"
        return
    rows = read_jsonl(path)
    strategies = Counter(r["strategy"] for r in rows)
    seen = set()
    for r in rows:
        if not r.get("expected_action") or not r.get("text"):
            bad(f"redteam: {r.get('id')} incomplete")
        if METHOD_WORDS.search(r["text"]):
            bad(f"redteam: method word in {r['id']}")
        if norm(r["text"]) in seen:
            bad(f"redteam: duplicate {r['id']}")
        seen.add(norm(r["text"]))
    REPORT["redteam"] = {"total": len(rows), "by_strategy": dict(strategies)}


def main() -> int:
    for fn in (check_skills, check_guardian, check_lines, check_exemplars, check_redteam):
        fn()
    import json

    print(json.dumps(REPORT, ensure_ascii=False, indent=1))
    if PROBLEMS:
        print(f"\n{len(PROBLEMS)} PROBLEM(S):")
        for p in PROBLEMS[:60]:
            print(" -", p)
        return 1
    print("\nvalidate: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
