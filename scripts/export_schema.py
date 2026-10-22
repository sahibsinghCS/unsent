"""Write JSON Schemas for the content files (data/scenarios/_schema.json etc). Run: make schema"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.contracts import Exemplar, Line, Scenario  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TARGETS = {
    ROOT / "data" / "scenarios" / "_schema.json": Scenario,
    ROOT / "docs" / "schemas" / "line.schema.json": Line,
    ROOT / "docs" / "schemas" / "exemplar.schema.json": Exemplar,
}

if __name__ == "__main__":
    for path, model in TARGETS.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(model.model_json_schema(), indent=2) + "\n")
        print("wrote", path.relative_to(ROOT))
