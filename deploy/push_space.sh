#!/usr/bin/env bash
# Push the current commit to a Hugging Face Docker Space, with deploy/space-README.md as README.md.
#
#   export HF_TOKEN=hf_...            # a Hugging Face token with "write" access (never commit it)
#   deploy/push_space.sh <user>/<space-name>
#   deploy/push_space.sh <user>/<space-name> --dry-run   # list what would be uploaded, upload nothing
#
# It checks out HEAD into a temporary git worktree, swaps in the Space README there, and uploads only
# the files the Docker build needs. Your working copy is never changed. The upload goes through
# huggingface_hub (already installed), which stores binary files (the trained models) the way the
# Hub requires, so you don't need git-lfs. Files on the Space that are not in this commit are deleted,
# so the Space always mirrors exactly one commit of this repo.
set -euo pipefail

SPACE="${1:-}"
MODE="${2:-}"
if [[ -z "$SPACE" || "$SPACE" != */* ]]; then
  echo "usage: deploy/push_space.sh <hf-user>/<space-name> [--dry-run]" >&2
  exit 2
fi
if [[ "$MODE" != "--dry-run" && -z "${HF_TOKEN:-}" ]]; then
  echo "HF_TOKEN is not set. Create a write token at https://huggingface.co/settings/tokens" >&2
  echo "then run:  export HF_TOKEN=hf_...   (it is read from the environment, never printed)" >&2
  exit 2
fi

REPO="$(git rev-parse --show-toplevel)"
cd "$REPO"
SHA="$(git rev-parse --short HEAD)"
if [[ -n "$(git status --porcelain --untracked-files=no)" ]]; then
  echo "note: you have uncommitted changes; they are NOT deployed (only commit $SHA is)." >&2
fi

WORKTREE="$(mktemp -d "${TMPDIR:-/tmp}/firstreply-space.XXXXXX")"
cleanup() { git -C "$REPO" worktree remove --force "$WORKTREE" >/dev/null 2>&1 || rm -rf "$WORKTREE"; }
trap cleanup EXIT
git worktree add --detach --quiet "$WORKTREE" HEAD
cp deploy/space-README.md "$WORKTREE/README.md"

uv run --project "$REPO" --no-sync python - "$WORKTREE" "$SPACE" "$SHA" "$MODE" <<'PY'
import fnmatch
import sys
from pathlib import Path

folder, space, sha, mode = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
# Exactly what the Dockerfile copies, plus the Space README.
allow = [
    "README.md", "Dockerfile", ".dockerignore", "pyproject.toml", "uv.lock",
    "backend/**", "data/**", "content/**", "models/**", "eval/reports/**",
    "deploy/predownload.py", "frontend/*", "frontend/public/**", "frontend/scripts/**",
    "frontend/src/**",
]
ignore = ["**/__pycache__/**", "**/*.pyc", "frontend/screenshots/**", "frontend/node_modules/**"]
root = Path(folder)
files = sorted(
    p.relative_to(root).as_posix() for p in root.rglob("*")
    if p.is_file() and ".git" not in p.relative_to(root).parts
)
chosen = [
    f for f in files
    if any(fnmatch.fnmatch(f, a) for a in allow) and not any(fnmatch.fnmatch(f, i) for i in ignore)
]
size = sum((root / f).stat().st_size for f in chosen)
print(f"commit {sha}: {len(chosen)} files, {size / 1e6:.1f} MB -> https://huggingface.co/spaces/{space}")
if mode == "--dry-run":
    for f in chosen:
        print("  " + f)
    sys.exit(0)

from huggingface_hub import HfApi  # noqa: E402

api = HfApi()  # reads HF_TOKEN from the environment
api.upload_folder(
    repo_id=space,
    repo_type="space",
    folder_path=folder,
    allow_patterns=allow,
    ignore_patterns=ignore,
    delete_patterns=["*"],  # mirror this commit: remove files that are no longer part of it
    commit_message=f"Deploy FirstReply {sha}",
)
print(f"pushed. The Space now rebuilds (about 5-10 minutes): https://huggingface.co/spaces/{space}")
PY
