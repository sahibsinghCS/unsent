"""Run the whole offline red-team harness: python -m eval.redteam [--embed hash|fastembed|both] [--pin]

Writes eval/reports/redteam_{attacks,invariants,fuzz_test,fuzz_all,privacy}.json and eval/redteam/results/*.json.
--pin refreshes the regression cases in tests/safety/pinned/ (always from the hash embedder, which is what
the tests use). The live OpenAI check is separate: python -m eval.redteam.live
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

from eval.redteam import common

PARTS = (
    ["eval.redteam.attacks"],
    ["eval.redteam.conversations"],
    ["eval.redteam.fuzz", "--split", "test"],
    ["eval.redteam.fuzz", "--split", "all"],
    ["eval.redteam.privacy"],
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--embed", default="auto", choices=["auto", "hash", "fastembed", "both"])
    parser.add_argument("--pin", action="store_true")
    args = parser.parse_args()
    embeds = ["hash", "fastembed"] if args.embed == "both" else [args.embed]
    env = {**os.environ, "PYTHONPATH": str(common.ROOT)}
    failed = 0
    for embed in embeds:
        for part in PARTS:  # one process per part: the embedder is chosen once per process
            cmd = [sys.executable, "-m", *part, "--embed", embed]
            print("==", " ".join(cmd[2:]), flush=True)
            failed += subprocess.run(cmd, cwd=common.ROOT, env=env).returncode != 0
    if args.pin:
        cmd = [sys.executable, "-m", "eval.redteam.pin"]
        failed += subprocess.run(cmd, cwd=common.ROOT, env=env).returncode != 0
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
