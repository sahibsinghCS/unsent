"""Build docs/METRICS.md from every eval/reports/*.json (RED-TEAM lane). Run: make report

  uv run python scripts/report.py            -> docs/METRICS.md (headline + every record by lane)
  uv run python scripts/report.py --readme   -> also replaces the README block between
                                                <!-- METRICS:START --> and <!-- METRICS:END -->
  uv run python scripts/report.py --check    -> exit 1 if docs/METRICS.md is out of date

The judge-facing headline is defined once, in content/headline_metrics.json, and filled by
content.resolve_headline(): the How page, the README and METRICS.md all show the same numbers. Below it,
METRICS.md adds a red-team table and then every record, each with its n, split and notes, straight from
the report files (nothing is recomputed). Missing reports show as "not measured yet".
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.content import resolve_headline  # noqa: E402

REPORTS = ROOT / "eval" / "reports"
METRICS_MD = ROOT / "docs" / "METRICS.md"
README = ROOT / "README.md"
START, END = "<!-- METRICS:START -->", "<!-- METRICS:END -->"
LANE_ORDER = ("safety", "redteam", "ml", "engine", "data", "whatif", "deploy")
PROD = "[fastembed]"  # red-team splits name the embedder; the production one is the headline


@dataclass(frozen=True)
class Row:
    """One red-team table row: the newest record with this metric whose split starts with `split`."""

    label: str
    metric: str
    split: str
    style: str = "percent"  # percent | score | count | ms | usd


REDTEAM_ROWS: tuple[Row, ...] = (
    Row("Attack bank: Guardian did the expected thing", "attacks.match_rate", "attack_bank"),
    Row(
        "Attack bank: should be stopped but got through", "attacks.unsafe_miss_rate", "attack_bank"
    ),
    Row("Fuzzed messages still handled right", "fuzz.robustness", "guardian test split"),
    Row("I1 unsafe friend lines shown", "invariants.I1.violations", "attack_bank x", "count"),
    Row("I2 facts revealed too early", "invariants.I2.violations", "attack_bank x", "count"),
    Row(
        "I3 method/means words in friend lines",
        "invariants.I3.violations",
        "attack_bank x",
        "count",
    ),
    Row("I4 crisis turns mishandled", "invariants.I4.violations", "attack_bank x", "count"),
    Row("I5 blocked turns mishandled", "invariants.I5.violations", "attack_bank x", "count"),
    Row("I6 direct asks blocked or paused", "invariants.I6.violations", "attack_bank x", "count"),
    Row(
        "I7 injections that changed the friend",
        "invariants.I7.violations",
        "attack_bank x",
        "count",
    ),
    Row("Live: friend replies written by the LLM", "live.voice.llm", "live"),
    Row("Live: unsafe friend lines shown", "live.unsafe_friend_lines_shown", "live", "count"),
    Row(
        "Live: injection turns that hijacked the friend", "live.injection_success", "live", "count"
    ),
    Row("Live: turn latency p95", "live.turn_latency_ms_p95", "live", "ms"),
    Row("Live: estimated OpenAI cost", "live.cost_usd", "live", "usd"),
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


def fmt(value, style: str = "auto") -> str:
    if value is None:
        return "not measured yet"
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, dict | list):
        return f"({type(value).__name__} with {len(value)} entries; see the JSON)"
    if not isinstance(value, int | float):
        return cell(str(value))
    if style == "percent":
        return f"{value * 100:.1f}%"
    if style == "ms":
        return f"{value:.0f} ms" if value >= 10 else f"{value:.1f} ms"
    if style == "usd":
        return f"${value:.4f}"
    if style == "messages":
        return f"{value:g} messages"
    if style in ("count",) or isinstance(value, int):
        return f"{value:g}" if isinstance(value, float) else str(value)
    return f"{value:.3f}".rstrip("0").rstrip(".") if abs(value) < 1000 else f"{value:,.0f}"


def cell(text) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ").strip()


def short(text, limit: int = 110) -> str:
    text = cell(text)
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def headline_table(records: list[dict]) -> list[str]:
    """The shared headline (content/headline_metrics.json), English labels."""
    lines = ["| What | Result | Compared with | n | Split |", "|---|---|---|---|---|"]
    for item in resolve_headline(records):
        style = item.get("format", "score")
        value = fmt(item.get("value"), style) if item.get("found") else "not measured yet"
        base = item.get("baseline") or {}
        compared = ""
        if base:
            compared = f"{fmt(base.get('value'), style)} ({cell(base['label']['en'])})"
        result = f"**{value}**" if item.get("found") else value
        lines.append(
            f"| {cell(item['label']['en'])} | {result} | {compared} | {item.get('n') or ''} | "
            f"{cell(item['split'])} |"
        )
    return lines


def find_row(records: list[dict], row: Row, prefer: str = PROD) -> dict | None:
    hits = [
        r
        for r in records
        if r["lane"] == "redteam"
        and r["metric"] == row.metric
        and str(r.get("split", "")).startswith(row.split)
    ]
    preferred = [r for r in hits if prefer in str(r.get("split", ""))] or hits
    return max(preferred, key=lambda r: str(r.get("created", ""))) if preferred else None


def redteam_table(records: list[dict]) -> list[str]:
    lines = ["| What | Result | n | Split | Notes |", "|---|---|---|---|---|"]
    skip = find_row(records, Row("", "live.skipped", "live"))
    for row in REDTEAM_ROWS:
        r = find_row(records, row)
        if r is None and skip is not None and row.metric.startswith("live."):
            lines.append(f"| {row.label} | skipped | | live | {short(skip.get('notes', ''))} |")
        elif r is None:
            lines.append(f"| {row.label} | not measured yet | | | |")
        else:
            lines.append(
                f"| {row.label} | **{fmt(r['value'], row.style)}** | {r.get('n', '')} | "
                f"{cell(r.get('split', ''))} | {short(r.get('notes', ''))} |"
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
        "*Generated by `make report` (`scripts/report.py`) from `eval/reports/*.json`. Do not edit.*",
        "Every number comes with its sample size (n), the data split it was measured on, and notes.",
        "Red-team splits name the embedder: `[fastembed]` is the production setup, `[hash]` the offline",
        "test setup. How each number is measured: `docs/how/*.md`.",
        "",
        "## Headline",
        "",
        "*Defined in `content/headline_metrics.json`; the app's How page shows the same numbers.*",
        "",
        *headline_table(records),
        "",
        "## Red-team headline",
        "",
        "*Adversarial checks (`eval/redteam/`, explained in `docs/how/redteam.md`).*",
        "",
        *redteam_table(records),
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
            "**Red team** (attacks, fuzzing and multi-turn invariants; `docs/how/redteam.md`):",
            "",
            *redteam_table(records),
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
    parser.add_argument("--readme", action="store_true", help="also update the README block")
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
        text = README.read_text(encoding="utf-8")
        README.write_text(replace_readme(text, readme_block(records)), encoding="utf-8")
        print("updated the README metrics block")
    return 0


if __name__ == "__main__":
    sys.exit(main())
