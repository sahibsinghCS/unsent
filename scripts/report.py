"""Build docs/METRICS.md from every eval/reports/*.json (RED-TEAM lane). Run: make report

  uv run python scripts/report.py            -> docs/METRICS.md (headline table + every record by lane)
  uv run python scripts/report.py --readme   -> also replaces the README block between
                                                <!-- METRICS:START --> and <!-- METRICS:END -->
  uv run python scripts/report.py --check    -> exit 1 if docs/METRICS.md is out of date

Every number is printed with its n, split and notes, straight from the report files: nothing here is
computed or rounded beyond display. A headline row whose report is missing says "not measured yet".
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "eval" / "reports"
METRICS_MD = ROOT / "docs" / "METRICS.md"
README = ROOT / "README.md"
START, END = "<!-- METRICS:START -->", "<!-- METRICS:END -->"
LANE_ORDER = ("safety", "redteam", "ml", "engine", "data", "whatif", "deploy")


@dataclass(frozen=True)
class Headline:
    label: str
    metric: str
    split: str | None = None  # exact split to pick, None = any
    note: str | None = None  # substring the notes must contain (e.g. "embed=fastembed")
    style: str = "pct"  # pct | num | ms | count | usd
    lane: str | None = None


# What a judge should see first. Order matters; each row names exactly which record it shows.
HEADLINES: tuple[Headline, ...] = (
    Headline(
        "Guardian: helper crisis caught (held-out test)",
        "combined.self_risk_recall",
        "test",
        lane="safety",
    ),
    Headline(
        "Guardian: asking the friend directly wrongly flagged",
        "asking_friend_fpr",
        "test",
        lane="safety",
    ),
    Headline("Guardian: any safe message wrongly flagged", "benign_fpr", "test", lane="safety"),
    Headline(
        "Red team: attack bank, Guardian did the expected thing",
        "attacks.match_rate",
        note="embed=fastembed",
        lane="redteam",
    ),
    Headline(
        "Red team: attacks that should be stopped but got through",
        "attacks.unsafe_miss_rate",
        note="embed=fastembed",
        lane="redteam",
    ),
    Headline(
        "Red team: fuzzed messages still handled right (test split)",
        "fuzz.robustness",
        "guardian test split",
        note="embed=fastembed",
        lane="redteam",
    ),
    Headline(
        "Red team: unsafe friend lines shown (I1)",
        "invariants.I1.violations",
        note="embed=fastembed",
        style="count",
        lane="redteam",
    ),
    Headline(
        "Red team: direct asks blocked or paused (I6)",
        "invariants.I6.violations",
        note="embed=fastembed",
        style="count",
        lane="redteam",
    ),
    Headline(
        "Red team: facts revealed too early (I2)",
        "invariants.I2.violations",
        note="embed=fastembed",
        style="count",
        lane="redteam",
    ),
    Headline(
        "Skill detector: macro-F1 on free-form replies",
        "macro_f1_ensemble",
        "test_freeform",
        style="num",
        lane="ml",
    ),
    Headline(
        "Keyword baseline: macro-F1 on the same replies",
        "macro_f1_keyword_baseline",
        "test_freeform",
        style="num",
        lane="ml",
    ),
    Headline(
        "Calibration error (ECE, lower is better)",
        "ece_after_calibration",
        "test_freeform",
        style="num",
        lane="ml",
    ),
    Headline(
        "'Uncertain' flag: share of decisions flagged",
        "uncertain_flag_rate",
        "test_freeform",
        lane="ml",
    ),
    Headline("Engine: pacing targets met", "pacing_targets_met", style="pct", lane="engine"),
    Headline("Guardian latency p95 (CPU)", "latency_ms_p95", "test", style="ms", lane="safety"),
    Headline("Live check: friend replies written by the LLM", "live.voice.llm", lane="redteam"),
    Headline(
        "Live check: unsafe friend lines shown",
        "live.unsafe_friend_lines_shown",
        style="count",
        lane="redteam",
    ),
    Headline(
        "Live check: turn latency p95", "live.turn_latency_ms_p95", style="ms", lane="redteam"
    ),
    Headline(
        "Live check: total estimated OpenAI cost", "live.cost_usd", style="usd", lane="redteam"
    ),
)


def load_records(reports: Path = REPORTS) -> list[dict]:
    """Every metric record in eval/reports/*.json; unreadable files are skipped, not fatal."""
    records: list[dict] = []
    for path in sorted(reports.glob("*.json")) if reports.exists() else []:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        for item in payload if isinstance(payload, list) else [payload]:
            if isinstance(item, dict) and "metric" in item:
                lane = item.get("lane") or path.stem.split("_")[0]
                records.append({**item, "lane": lane, "source": path.name})
    return records


def find(records: list[dict], h: Headline) -> dict | None:
    """The newest record for a headline row (exact metric, optional split / notes / lane filters)."""
    hits = [
        r
        for r in records
        if r["metric"] == h.metric
        and (h.split is None or r.get("split") == h.split)
        and (h.note is None or h.note in str(r.get("notes", "")))
        and (h.lane is None or r["lane"] == h.lane)
    ]
    return max(hits, key=lambda r: str(r.get("created", ""))) if hits else None


def fmt(value, style: str = "auto") -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, dict | list):
        return f"({type(value).__name__} with {len(value)} entries; see the JSON)"
    if not isinstance(value, int | float):
        return cell(str(value))
    if style == "pct":
        return f"{value * 100:.1f}%"
    if style == "ms":
        return f"{value:.0f} ms" if value >= 10 else f"{value:.1f} ms"
    if style == "usd":
        return f"${value:.4f}"
    if style == "count" or isinstance(value, int):
        return f"{value:g}" if isinstance(value, float) else str(value)
    return f"{value:.3f}".rstrip("0").rstrip(".") if abs(value) < 1000 else f"{value:,.0f}"


def cell(text: str) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ").strip()


def headline_table(records: list[dict]) -> list[str]:
    lines = ["| What | Result | n | Split | Notes |", "|---|---|---|---|---|"]
    live_skip = find(records, Headline("", "live.skipped", lane="redteam"))
    for h in HEADLINES:
        r = find(records, h)
        if r is None and live_skip is not None and h.metric.startswith("live."):
            lines.append(f"| {h.label} | skipped | | | {cell(live_skip.get('notes', ''))} |")
            continue
        if r is None:
            lines.append(f"| {h.label} | not measured yet | | | |")
            continue
        notes = cell(r.get("notes", ""))
        notes = notes if len(notes) <= 110 else notes[:107].rstrip() + "..."
        lines.append(
            f"| {h.label} | **{fmt(r['value'], h.style)}** | {r.get('n', '')} | "
            f"{cell(r.get('split', ''))} | {notes} (`{r['source']}`) |"
        )
    return lines


def lane_tables(records: list[dict]) -> list[str]:
    by_lane: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for r in records:
        by_lane[r["lane"]][r["source"]].append(r)
    lanes = sorted(by_lane, key=lambda x: (LANE_ORDER.index(x) if x in LANE_ORDER else 99, x))
    out: list[str] = []
    for lane in lanes:
        out += ["", f"## {lane}", ""]
        for source, rows in sorted(by_lane[lane].items()):
            out += [
                f"### `eval/reports/{source}`",
                "",
                "| Metric | Value | n | Split | Notes |",
                "|---|---|---|---|---|",
            ]
            for r in rows:
                out.append(
                    f"| `{cell(r['metric'])}` | {fmt(r.get('value'))} | {r.get('n', '')} | "
                    f"{cell(r.get('split', ''))} | {cell(r.get('notes', ''))} |"
                )
            out.append("")
    return out


def build_metrics(records: list[dict]) -> str:
    lines = [
        "# FirstReply metrics",
        "",
        "*Generated by `make report` (`scripts/report.py`) from `eval/reports/*.json`. Do not edit by hand.*",
        "Every number comes with its sample size (n), the data split it was measured on, and notes.",
        "Red-team rows say which embedder ran (`embed=fastembed` is the production setup, `embed=hash` the",
        "offline test setup). How each number is measured: `docs/how/*.md`.",
        "",
        "## Headline",
        "",
        *headline_table(records),
    ]
    if not records:
        lines += ["", "*No reports found in `eval/reports/` yet: run `make eval`.*"]
    lines += lane_tables(records)
    return "\n".join(lines).rstrip() + "\n"


def readme_block(records: list[dict]) -> str:
    return "\n".join(
        [
            START,
            *headline_table(records),
            "",
            "Every metric with n, split and notes: [`docs/METRICS.md`](docs/METRICS.md) "
            "(rebuilt by `make report`).",
            END,
        ]
    )


def replace_readme(text: str, block: str) -> str:
    """Swap only the marked block; the rest of the README is untouched."""
    start, end = text.find(START), text.find(END)
    if start == -1 or end == -1 or end < start:
        raise ValueError("README.md has no METRICS:START/END markers")
    return text[:start] + block + text[end + len(END) :]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--readme", action="store_true", help="also update the README metrics block"
    )
    parser.add_argument("--check", action="store_true", help="fail if docs/METRICS.md is stale")
    args = parser.parse_args(argv)
    records = load_records()
    content = build_metrics(records)
    if args.check:
        current = METRICS_MD.read_text(encoding="utf-8") if METRICS_MD.exists() else ""
        if current != content:
            print("docs/METRICS.md is out of date: run make report")
            return 1
        return 0
    METRICS_MD.write_text(content, encoding="utf-8")
    print(f"wrote {METRICS_MD.relative_to(ROOT)} ({len(records)} records)")
    if args.readme:
        README.write_text(
            replace_readme(README.read_text(encoding="utf-8"), readme_block(records)),
            encoding="utf-8",
        )
        print("updated the README metrics block")
    return 0


if __name__ == "__main__":
    sys.exit(main())
