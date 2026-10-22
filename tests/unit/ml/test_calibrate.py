import numpy as np

from backend.app.ml.calibrate import Stacker, expected_calibration_error, logit, reliability_curve


def test_logit_is_finite_at_the_edges():
    assert np.isfinite(logit(np.array([0.0, 1.0]))).all()


def test_stacker_falls_back_to_average_without_enough_positives():
    stacker = Stacker().fit(
        np.array([0.2, 0.9, 0.4]), np.array([0.4, 0.7, 0.2]), np.array([0, 1, 0])
    )
    assert stacker.fallback
    assert np.allclose(stacker.predict(np.array([0.2]), np.array([0.6])), [0.4])


def test_stacker_calibrates_overconfident_scores():
    rng = np.random.default_rng(0)
    true_p = rng.uniform(0, 1, 4000)
    y = (rng.uniform(0, 1, 4000) < true_p).astype(int)
    overconfident = 1 / (1 + np.exp(-3 * logit(true_p)))  # pushes probabilities toward 0 and 1
    stacker = Stacker().fit(overconfident, overconfident, y)
    calibrated = stacker.predict(overconfident, overconfident)
    assert expected_calibration_error(calibrated, y) < expected_calibration_error(overconfident, y)
    assert expected_calibration_error(calibrated, y) < 0.03


def test_reliability_curve_and_ece_on_perfect_predictions():
    probs = np.array([0.0, 0.0, 1.0, 1.0])
    y = np.array([0, 0, 1, 1])
    mean_pred, observed, counts = reliability_curve(probs, y)
    assert counts == [2, 2] and observed == [0.0, 1.0] and mean_pred == [0.0, 1.0]
    assert expected_calibration_error(probs, y) == 0.0
