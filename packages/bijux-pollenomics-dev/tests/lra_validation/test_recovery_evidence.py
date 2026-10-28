"""Retain synthetic mismatches and poor interval coverage with exact custody."""

from pathlib import Path
import shutil
from typing import Any

import pytest

from bijux_pollenomics_dev.lra_validation.recovery_evidence import (
    PACKET,
    RECONSTRUCTION,
    build_recovery_evidence,
)


def _repository() -> Path:
    return Path(__file__).resolve().parents[4]


def test_every_noise_free_and_counting_case_is_preserved() -> None:
    report = build_recovery_evidence(_repository())
    assert report["reconstruction_source"]["denominators"]["attempted"] == 8
    assert len(report["reconstruction_cases"]) == 8
    assert (
        sum(case["inverse_crime_control"] for case in report["reconstruction_cases"])
        == 6
    )
    mismatched = [
        case
        for case in report["reconstruction_cases"]
        if not case["inverse_crime_control"]
    ]
    assert len(mismatched) == 2
    assert all(case["vegetation_mae_fraction"] > 0.06 for case in mismatched)
    assert sum(case["attempts"] for case in report["counting_cases"]) == 3000
    assert sum(len(case["metrics"]) for case in report["counting_cases"]) == 30
    assert (
        report["counting_source"]["independent_review"][
            "scalar_cover_and_variance_comparisons"
        ]
        == 60000
    )
    assert report["claims"]["coverage_certified"] is False
    assert report["claims"]["empirical_ecological_accuracy"] is False


def test_rare_taxon_and_misspecified_transport_failures_remain_visible() -> None:
    report = build_recovery_evidence(_repository())
    cases: dict[str, Any] = {
        case["case"]["name"]: case for case in report["counting_cases"]
    }
    rare = cases["rare_alnus_matched_counting"]["metrics"][0]
    assert rare["taxon"] == "Alnus.glutinosa"
    assert (rare["covered"], rare["accepted"]) == (427, 1000)
    assert rare["zero_standard_error_replicates"] == 525
    misspecified = cases["uniform_alnus_transport_misspecified"]["metrics"][0]
    assert (misspecified["covered"], misspecified["accepted"]) == (0, 1000)
    assert misspecified["bias"] < -0.03


@pytest.mark.parametrize(
    "member",
    [
        "report.json",
        "actual-multinomial-draws.jsonl",
        "replicate-taxon-results.csv",
        "independent-review.json",
    ],
)
def test_changed_retained_member_is_refused(tmp_path: Path, member: str) -> None:
    shutil.copytree(_repository() / PACKET, tmp_path / PACKET)
    target = tmp_path / PACKET / member
    target.write_bytes(target.read_bytes() + b" ")
    with pytest.raises(ValueError, match="identity differs"):
        build_recovery_evidence(tmp_path)


def test_symlinked_retained_member_is_refused(tmp_path: Path) -> None:
    shutil.copytree(_repository() / PACKET, tmp_path / PACKET)
    target = tmp_path / PACKET / "report.json"
    target.unlink()
    target.symlink_to(_repository() / PACKET / "report.json")
    with pytest.raises(ValueError, match="regular file"):
        build_recovery_evidence(tmp_path)


def test_changed_reconstruction_is_refused(tmp_path: Path) -> None:
    shutil.copytree(_repository() / PACKET, tmp_path / PACKET)
    target = tmp_path / RECONSTRUCTION
    target.parent.mkdir(parents=True)
    target.write_bytes((_repository() / RECONSTRUCTION).read_bytes() + b" ")
    with pytest.raises(ValueError, match="identity differs"):
        build_recovery_evidence(tmp_path)
