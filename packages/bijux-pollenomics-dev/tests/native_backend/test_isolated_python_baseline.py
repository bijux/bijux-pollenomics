"""Keep isolated Python memory receipts tied to the retained scientific baseline."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.native_backend.isolated_python_baseline import (
    _peak_bytes,
    _scientific_sha,
    _summary,
    run,
    worker,
)

REPOSITORY = Path(__file__).resolve().parents[4]
BASELINE = REPOSITORY / "docs/report/numerical-performance/python-baseline/report.json"
GOVERNED = REPOSITORY / "docs/report/numerical-performance/python-isolated/report.json"


def test_scientific_digest_matches_retained_output() -> None:
    baseline = json.loads(BASELINE.read_text())
    for case in baseline["workloads"]:
        assert len(_scientific_sha(case["scientific_output"])) == 64
        assert case["identical_scientific_outputs"] is True


def test_summary_refuses_changed_output_and_nonfinite_meaning() -> None:
    observation = {
        "scientific_output_sha256": "a" * 64,
        "nonfinite_semantics_sha256": "c" * 64,
        "post_call_process_peak_rss_bytes": 12,
        "pre_call_process_peak_rss_bytes": 10,
        "observed_peak_increment_bytes": 2,
        "call_seconds": 0.1,
        "whole_worker_seconds": 0.2,
    }
    observations = [deepcopy(observation) for _ in range(5)]
    expected_missing = "c" * 64
    assert (
        _summary(observations, "a" * 64, expected_missing)[
            "median_process_peak_rss_bytes"
        ]
        == 12
    )
    observations[0]["scientific_output_sha256"] = "b" * 64
    with pytest.raises(ValueError, match="scientific output"):
        _summary(observations, "a" * 64, expected_missing)
    observations[0] = deepcopy(observation)
    observations[0]["nonfinite_semantics_sha256"] = "d" * 64
    with pytest.raises(ValueError, match="scientific output"):
        _summary(observations, "a" * 64, expected_missing)


def test_worker_requires_single_thread_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OMP_NUM_THREADS", raising=False)
    with pytest.raises(ValueError, match="thread variables"):
        worker("forward-validated")


def test_parent_requires_absent_repository_artifact_destination() -> None:
    with pytest.raises(ValueError, match="Absent repository artifact"):
        run(REPOSITORY, REPOSITORY / "docs/outside")
    with pytest.raises(ValueError, match="Absent repository artifact"):
        run(REPOSITORY, REPOSITORY / "artifacts")


def test_platform_peak_is_positive() -> None:
    assert _peak_bytes() > 0


def test_governed_workers_match_retained_scientific_outputs() -> None:
    baseline_bytes = BASELINE.read_bytes()
    baseline = json.loads(baseline_bytes)
    report = json.loads(GOVERNED.read_bytes())
    assert report["baseline_sha256"] == hashlib.sha256(baseline_bytes).hexdigest()
    assert report["repetitions_per_workload"] == 5
    assert report["adoption_decision"].startswith("none")
    assert all(
        hashlib.sha256((REPOSITORY / path).read_bytes()).hexdigest() == digest
        for path, digest in report["source_sha256"].items()
    )
    assert report["source_paths_changed_since_retained_baseline"] == [
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/provenance/manifest.py"
    ]
    assert len(report["cases"]) == len(baseline["workloads"]) == 7
    for actual, retained in zip(report["cases"], baseline["workloads"], strict=True):
        expected = _scientific_sha(retained["scientific_output"])
        assert actual["name"] == retained["name"]
        assert actual["contract"] == retained["contract"]
        assert actual["retained_scientific_output_sha256"] == expected
        assert actual["retained_nonfinite_semantics_sha256"] == _scientific_sha(
            retained["nonfinite_output_semantics"][0]
        )
        assert len(actual["observations"]) == 5
        assert all(
            item["scientific_output_sha256"] == expected
            and item["contract_sha256"] == _scientific_sha(retained["contract"])
            and item["nonfinite_semantics_sha256"]
            == actual["retained_nonfinite_semantics_sha256"]
            for item in actual["observations"]
        )
