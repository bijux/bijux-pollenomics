"""Reject duplicate frozen radius predictions despite an unchanged key set."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

REPOSITORY = Path(__file__).resolve().parents[5]


def _verifier() -> ModuleType:
    path = REPOSITORY / "docs/report/pollen-reconstruction/verify_report.py"
    spec = importlib.util.spec_from_file_location("radius_report_verifier", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_duplicate_prediction_refused_before_score_comparison(tmp_path: Path) -> None:
    module = _verifier()
    original = (
        REPOSITORY
        / "docs/report/pollen-reconstruction/author-lra-constrained/radius-sensitivity"
    )
    study = tmp_path / "author-lra-constrained/radius-sensitivity"
    (study / "frozen").mkdir(parents=True)
    (study / "scored").mkdir()
    frozen = json.loads((original / "frozen/predictions.json").read_text())
    assert len(frozen["rows"]) == 126
    frozen["rows"].append(dict(frozen["rows"][0]))
    path = study / "frozen/predictions.json"
    path.write_text(json.dumps(frozen))
    report = json.loads((original / "scored/report.json").read_text())
    report["prediction_freeze_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    (study / "scored/report.json").write_text(json.dumps(report))
    (study / "scored/scores.csv").write_bytes(
        (original / "scored/scores.csv").read_bytes()
    )
    module.__dict__["REPORT_DIR"] = tmp_path
    with pytest.raises(ValueError, match="author radius sensitivity rows differ"):
        module.verify_author_radius_sensitivity()
    assert not (study / "paired").exists()
