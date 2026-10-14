"""Source custody and age-control scope guards for the published ABBO table."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.source_contracts.pangaea_abbo_age_controls import (
    validated_abbo_age_table,
)
from bijux_pollenomics_dev.source_completion.neotoma.abbo_age_controls import (
    DESCRIPTOR,
    verify_report,
)

ROOT = Path(__file__).resolve().parents[5]
REPORT = "docs/report/source-relations/neotoma/abbo-age-controls/report.json"


def report() -> dict[str, Any]:
    value: Any = json.loads((ROOT / REPORT).read_text())
    assert isinstance(value, dict)
    return value


def descriptor() -> dict[str, Any]:
    value: Any = json.loads((ROOT / DESCRIPTOR).read_text())
    assert isinstance(value, dict)
    return value


def test_retained_public_report_keeps_six_controls_and_no_sample_posterior() -> None:
    value = report()
    verify_report(value)
    assert len(value["controls"]) == 6
    assert value["sample_count_without_age_uncertainty_bounds"] == 107
    assert value["lra_admitted_samples"] == 0
    assert value["neotoma_core_top"]["independent_published_date"] is False


@pytest.mark.parametrize(
    "field, changed",
    [
        ("dataset_id", 19914),
        ("chronology_id", 11517),
        ("neotoma_age_model", "new fitted calibration"),
        ("neotoma_model_age_unit", "Radiocarbon years BP"),
        ("published_radiocarbon_date_count", 7),
        ("exact_depth_lab_age_error_matches", 5),
        ("sample_count_without_age_uncertainty_bounds", 106),
        ("sample_age_uncertainty_bounds", "posterior inferred from control bounds"),
        ("pollen_profile_sample_depths_matched", 106),
        ("lra_admitted_samples", 1),
        ("lra_admitted_samples", False),
    ],
)
def test_changed_native_source_scope_refuses(field: str, changed: object) -> None:
    value = report()
    value[field] = changed
    with pytest.raises(ReportRebuildError, match="scope or refusal"):
        verify_report(value)


def test_missing_published_control_refuses() -> None:
    value = report()
    value["controls"].pop()
    with pytest.raises(ReportRebuildError, match="six exact"):
        verify_report(value)


def test_unmatched_published_control_refuses() -> None:
    value = report()
    value["controls"][0]["published_date_fields_match"] = False
    with pytest.raises(ReportRebuildError, match="six exact"):
        verify_report(value)


def test_core_top_cannot_be_a_seventh_published_date() -> None:
    value = report()
    value["neotoma_core_top"]["independent_published_date"] = True
    with pytest.raises(ReportRebuildError, match="core top"):
        verify_report(value)


@pytest.mark.parametrize(
    "field, changed",
    [
        ("doi", "10.1594/PANGAEA.738429"),
        ("license", "CC-BY-3.0"),
        ("capture_custody", "established"),
        ("scientific_admission", True),
        ("scientific_admission", 0),
        ("source_id", "other/source"),
    ],
)
def test_changed_external_source_authority_refuses(
    tmp_path: Path, field: str, changed: object
) -> None:
    repository = tmp_path / "repository"
    path = repository / DESCRIPTOR
    path.parent.mkdir(parents=True)
    value = descriptor()
    value[field] = changed
    path.write_text(json.dumps(value))
    with pytest.raises(ReportRebuildError, match="identity or limits"):
        validated_abbo_age_table(repository, tmp_path / "source", DESCRIPTOR)


def test_wrong_physical_published_table_refuses(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    path = repository / DESCRIPTOR
    path.parent.mkdir(parents=True)
    value = descriptor()
    path.write_text(json.dumps(value))
    source_root = tmp_path / "source"
    table = source_root / value["source_id"] / value["table"]["path"]
    table.parent.mkdir(parents=True)
    table.write_bytes(b"x" * value["table"]["size"])
    with pytest.raises(ReportRebuildError):
        validated_abbo_age_table(repository, source_root, DESCRIPTOR)


def test_internal_source_store_refuses(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    path = repository / DESCRIPTOR
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(descriptor()))
    source_root = repository / "private-source"
    source_root.mkdir()
    with pytest.raises(ReportRebuildError, match="must be external"):
        validated_abbo_age_table(repository, source_root, DESCRIPTOR)


def test_boolean_table_size_refuses_before_source_reads(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    path = repository / DESCRIPTOR
    path.parent.mkdir(parents=True)
    value = copy.deepcopy(descriptor())
    value["table"]["size"] = True
    path.write_text(json.dumps(value))
    with pytest.raises(ReportRebuildError, match="identity or limits"):
        validated_abbo_age_table(repository, tmp_path / "missing-source", DESCRIPTOR)
