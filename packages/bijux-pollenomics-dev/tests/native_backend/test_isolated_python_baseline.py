"""Keep isolated Python memory receipts tied to the retained scientific baseline."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess

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
RETAINED_COMMIT = "bf599b10a08781d85fb85b5b15d2501d498a2acf"
RETAINED_REPORT_SHA256 = (
    "1c5f2444bce9d941cf6e7fa45f8c61e0ed04afa067008ab085a3163007c2c17c"
)
RETAINED_SOURCE_MAP_SHA256 = (
    "bd882930abfd71bd70058aa1d465eb187cd404169f49b6a7931f126a7256b240"
)


def _retained_source_sha256(relative: str) -> str:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts or path.as_posix() != relative:
        raise ValueError("retained source path is not canonical and relative")
    result = subprocess.run(
        ["git", "show", f"{RETAINED_COMMIT}:{relative}"],
        cwd=REPOSITORY,
        check=True,
        capture_output=True,
        timeout=10,
    )
    return hashlib.sha256(result.stdout).hexdigest()


def _verify_retained_source_map(source_sha256: dict[str, str]) -> None:
    canonical = json.dumps(source_sha256, sort_keys=True, separators=(",", ":"))
    if (
        len(source_sha256) != 57
        or hashlib.sha256(canonical.encode()).hexdigest() != RETAINED_SOURCE_MAP_SHA256
    ):
        raise ValueError("retained historical source map differs")


def _verify_git_source_blobs(source_sha256: dict[str, str]) -> None:
    for relative, digest in source_sha256.items():
        if _retained_source_sha256(relative) != digest:
            raise ValueError(f"historical source identity differs: {relative}")


def test_scientific_digest_matches_retained_output() -> None:
    baseline = json.loads(BASELINE.read_text())
    for case in baseline["workloads"]:
        assert len(case["scientific_output_sha256"]) == 64
        assert len(case["nonfinite_single_call_sha256"]) == 64
        assert case["contract_sha256"] == _scientific_sha(case["contract"])


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
    report_bytes = GOVERNED.read_bytes()
    assert hashlib.sha256(report_bytes).hexdigest() == RETAINED_REPORT_SHA256
    report = json.loads(report_bytes)
    assert report["baseline_sha256"] == hashlib.sha256(baseline_bytes).hexdigest()
    assert report["repetitions_per_workload"] == 5
    assert report["adoption_decision"].startswith("none")
    _verify_retained_source_map(report["source_sha256"])
    assert report["source_paths_changed_since_retained_baseline"] == []
    assert not any(
        path.endswith("/_build_version.py") for path in report["source_sha256"]
    )
    assert "only the named workload fixture" in report["rss_semantics"]
    assert len(report["cases"]) == len(baseline["workloads"]) == 7
    for actual, retained in zip(report["cases"], baseline["workloads"], strict=True):
        expected = retained["scientific_output_sha256"]
        assert actual["name"] == retained["name"]
        assert actual["contract"] == retained["contract"]
        assert actual["retained_scientific_output_sha256"] == expected
        assert (
            actual["retained_nonfinite_semantics_sha256"]
            == retained["nonfinite_single_call_sha256"]
        )
        assert len(actual["observations"]) == 5
        assert all(
            item["scientific_output_sha256"] == expected
            and item["contract_sha256"] == retained["contract_sha256"]
            and item["nonfinite_semantics_sha256"]
            == actual["retained_nonfinite_semantics_sha256"]
            for item in actual["observations"]
        )


def test_retained_provenance_refuses_source_repin() -> None:
    report = json.loads(GOVERNED.read_bytes())
    current_api = "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/api.py"
    _verify_retained_source_map(report["source_sha256"])
    report["source_sha256"][current_api] = "0" * 64
    with pytest.raises(ValueError, match="retained historical source map differs"):
        _verify_retained_source_map(report["source_sha256"])


def test_retained_git_blobs_when_history_is_available() -> None:
    """Full-history checkouts can authenticate the original source bytes too."""
    try:
        present = subprocess.run(
            ["git", "cat-file", "-e", f"{RETAINED_COMMIT}^{{commit}}"],
            cwd=REPOSITORY,
            check=False,
            capture_output=True,
            timeout=10,
        )
    except FileNotFoundError:
        pytest.skip("Git is unavailable; report/source-map pins still checked")
    if present.returncode != 0:
        pytest.skip("shallow checkout lacks retained commit; pins still checked")
    report_bytes = GOVERNED.read_bytes()
    retained_report = subprocess.run(
        [
            "git",
            "show",
            f"{RETAINED_COMMIT}:docs/report/numerical-performance/python-isolated/report.json",
        ],
        cwd=REPOSITORY,
        check=True,
        capture_output=True,
        timeout=10,
    ).stdout
    assert report_bytes == retained_report
    _verify_git_source_blobs(json.loads(report_bytes)["source_sha256"])


@pytest.mark.parametrize("relative", ["../outside.py", "/absolute.py"])
def test_retained_provenance_refuses_escaped_source_path(relative: str) -> None:
    with pytest.raises(ValueError, match="canonical and relative"):
        _retained_source_sha256(relative)
