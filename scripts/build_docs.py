"""Concatenate docs/how/*.md into HOW_IT_WORKS.md in a fixed order. Run: make docs"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORDER = ["platform", "safety", "engine", "data", "ml", "whatif", "frontend", "redteam", "deploy"]

if __name__ == "__main__":
    parts = [
        "# How Unsent works\n\n*Generated from docs/how/*.md by `make docs`. Edit those files, not this one.*\n"
    ]
    for name in ORDER:
        path = ROOT / "docs" / "how" / f"{name}.md"
        if path.exists():
            parts.append(path.read_text(encoding="utf-8").strip() + "\n")
    (ROOT / "HOW_IT_WORKS.md").write_text("\n\n---\n\n".join(parts), encoding="utf-8")
    print("wrote HOW_IT_WORKS.md")
