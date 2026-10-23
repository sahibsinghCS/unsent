import json
import shutil

from tests.unit.ml.conftest import SEED


def test_run_eval_writes_report_and_figures(trained_dir, seed_data_dir, tmp_path):
    from eval.skills.run_eval import main

    data_dir = tmp_path / "data"
    shutil.copytree(seed_data_dir, data_dir)
    shutil.copy(SEED, data_dir / "survey_real.jsonl")  # extra test sets are evaluated separately
    (data_dir / "splits").mkdir()
    shutil.copy(SEED, data_dir / "splits" / "test_freeform.jsonl")
    report = tmp_path / "ml_skills.json"
    figures = tmp_path / "fig"
    args = ["--data-dir", str(data_dir), "--models-dir", str(trained_dir)]
    assert main([*args, "--report", str(report), "--figures", str(figures)]) == 0

    records = json.loads(report.read_text())
    splits = {r["split"] for r in records}
    assert splits == {"val", "test", "test_freeform", "survey_real"}
    metrics = {r["metric"] for r in records if r["split"] == "test"}
    assert {
        "macro_f1_keyword_baseline",
        "macro_f1_model_a",
        "macro_f1_model_b",
        "macro_f1_ensemble",
        "ece_before_calibration",
        "ece_after_calibration",
        "f1_asked_directly",
    } <= metrics
    assert all(r["n"] > 0 and r["lane"] == "ml" for r in records)
    assert {"brier_after_calibration", "uncertain_flag_rate"} <= metrics
    for name in ("reliability.png", "confusion.png", "f1_comparison.png", "results.json"):
        assert (figures / name).stat().st_size > 0
    assert (figures / "f1_comparison_freeform.png").stat().st_size > 0
    results = json.loads((figures / "results.json").read_text())
    assert len(results["probes"]) >= 14 and all("ok" in p for p in results["probes"])
    assert all(e["truth"] != (e["p"] >= 0.5) for e in results["test_freeform"]["errors"])


def test_run_eval_skips_without_artifact(tmp_path):
    from eval.skills.run_eval import main

    assert main(["--models-dir", str(tmp_path)]) == 0


def test_unseen_rows_drops_texts_seen_in_training():
    from backend.app.ml.evaluate import unseen_rows

    test = [{"text": "You OK??"}, {"text": "that sounds hard"}]
    assert unseen_rows(test, [{"text": "you ok"}]) == [{"text": "that sounds hard"}]
