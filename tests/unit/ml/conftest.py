"""Shared fixtures for ML-lane tests: a tiny model trained on the seed set with hash embeddings."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from backend.app.embed import reset_embedder
from backend.app.ml.skill_detector import SkillDetector
from backend.app.ml.train import train

FIXTURES = Path(__file__).parent / "fixtures"
SEED = FIXTURES / "seed.jsonl"


@pytest.fixture(scope="session")
def seed_data_dir(tmp_path_factory) -> Path:
    """A data dir holding the seed set as final.jsonl (hash-split into train/val/test)."""
    data_dir = tmp_path_factory.mktemp("seed_data")
    shutil.copy(SEED, data_dir / "final.jsonl")
    return data_dir


@pytest.fixture(scope="session")
def trained_dir(seed_data_dir, tmp_path_factory) -> Path:
    """models dir with an artifact trained on the seed set (FR_EMBED=hash)."""
    reset_embedder()
    out = tmp_path_factory.mktemp("models")
    train(seed_data_dir, out, seed=0)
    return out


@pytest.fixture
def detector(trained_dir) -> SkillDetector:
    return SkillDetector(trained_dir)
