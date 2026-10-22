import json

import numpy as np
import pytest

from backend.app.ml.kappa import agreement, bootstrap_ci, cohen_kappa, main
from backend.app.ml.model import LABELS


def test_cohen_kappa_known_values():
    assert cohen_kappa([1, 0, 1, 0], [1, 0, 1, 0]) == 1.0
    # textbook 2x2: a=20 both yes, b=5, c=10, d=15 -> kappa = 0.4
    a = [1] * 25 + [0] * 25
    b = [1] * 20 + [0] * 5 + [1] * 10 + [0] * 15
    assert abs(cohen_kappa(a, b) - 0.4) < 1e-9
    assert cohen_kappa([0, 0, 0], [0, 0, 0]) == 1.0


def test_bootstrap_ci_is_seeded_and_contains_the_estimate():
    rng = np.random.default_rng(1)
    a = rng.integers(0, 2, 200)
    b = np.where(rng.uniform(size=200) < 0.8, a, 1 - a)
    low, high = bootstrap_ci(a, b, seed=0)
    assert (low, high) == bootstrap_ci(a, b, seed=0)
    assert low <= cohen_kappa(a, b) <= high


def rows(n, flip=()):
    out = []
    for i in range(n):
        labels = {label.value: (i + j) % 3 == 0 for j, label in enumerate(LABELS)}
        if i in flip:
            labels["validated"] = not labels["validated"]
        out.append({"id": f"r{i}", "labels": labels})
    return out


def test_agreement_matches_by_id_and_reports_each_label():
    result = agreement(rows(30), list(reversed(rows(30, flip={1, 2, 3}))) + [{"id": "zz"}])
    assert result["checked_in"]["kappa"] == 1.0
    assert result["validated"]["kappa"] < 1.0
    assert result["overall"]["n"] == 30
    assert set(result) == {label.value for label in LABELS} | {"overall"}
    with pytest.raises(ValueError):
        agreement(rows(3), [{"id": "nope", "labels": {}}])


def test_cli_writes_report(tmp_path):
    for name, data in (("ours", rows(20)), ("counselor", rows(20, flip={4}))):
        (tmp_path / f"{name}.jsonl").write_text("\n".join(json.dumps(r) for r in data))
    out = tmp_path / "ml_counselor.json"
    main(
        [
            "--ours",
            str(tmp_path / "ours.jsonl"),
            "--counselor",
            str(tmp_path / "counselor.jsonl"),
            "--out",
            str(out),
        ]
    )
    records = json.loads(out.read_text())
    overall = next(r for r in records if r["metric"] == "counselor_kappa_overall")
    assert overall["n"] == 20 and overall["lane"] == "ml" and len(overall["ci95"]) == 2
