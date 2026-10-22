"""Fail if a lane branch changes files outside the paths it owns (ownership.yaml).

Usage:
  uv run python scripts/check_ownership.py --lane engine          # in a lane session
  uv run python scripts/check_ownership.py --branch wt/engine --base origin/main
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def glob_to_regex(pattern: str) -> re.Pattern[str]:
    """Translate a glob with ** (any depth), * (within a path segment) and ? into a regex."""
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out += "(?:.*/)?"
            i += 3
        elif pattern.startswith("**", i):
            out += ".*"
            i += 2
        elif pattern[i] == "*":
            out += "[^/]*"
            i += 1
        elif pattern[i] == "?":
            out += "[^/]"
            i += 1
        else:
            out += re.escape(pattern[i])
            i += 1
    return re.compile(f"^{out}$")


def is_allowed(path: str, patterns: list[str]) -> bool:
    return any(glob_to_regex(p).match(path) for p in patterns)


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


def changed_files(base: str) -> list[str]:
    merge_base = git("merge-base", "HEAD", base)
    committed = git("diff", "--name-only", f"{merge_base}..HEAD").splitlines()
    uncommitted = git("diff", "--name-only", "HEAD").splitlines()
    untracked = git("ls-files", "--others", "--exclude-standard").splitlines()
    return sorted({f for f in committed + uncommitted + untracked if f})


def main() -> int:
    config = yaml.safe_load((ROOT / "ownership.yaml").read_text())
    parser = argparse.ArgumentParser()
    parser.add_argument("--lane", help="lane name, e.g. engine")
    parser.add_argument("--branch", help="branch name, e.g. wt/engine (default: current branch)")
    parser.add_argument("--base", help="ref to diff against (default: origin/<integration_branch>)")
    args = parser.parse_args()

    branch = args.branch or git("rev-parse", "--abbrev-ref", "HEAD")
    lane = args.lane or (branch.split("/", 1)[1] if branch.startswith("wt/") else None)
    if lane is None or lane not in config["lanes"]:
        print(f"ownership: '{branch}' is not a lane branch (integrator). Nothing to check.")
        return 0

    base = args.base or f"origin/{config['integration_branch']}"
    try:
        files = changed_files(base)
    except subprocess.CalledProcessError:
        subprocess.run(
            ["git", "fetch", "origin", config["integration_branch"]], cwd=ROOT, check=False
        )
        files = changed_files(base)

    patterns = config["lanes"][lane]
    violations = [f for f in files if not is_allowed(f, patterns)]
    if violations:
        print(f"ownership: lane '{lane}' changed files it does not own:")
        for f in violations:
            print(f"  - {f}")
        print("Move the change into your lane, or write a Request in wt-notes/<lane>.md.")
        return 1
    print(f"ownership: OK ({len(files)} changed files, all inside lane '{lane}').")
    return 0


if __name__ == "__main__":
    sys.exit(main())
