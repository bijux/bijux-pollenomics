"""Saved chronology publication must retain exact owners without source rebuilding."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from bijux_pollenomics.reporting.adna.foundation_outputs.chronology import (
    _published_temporal_feature_findings,
    build_animal_sample_chronology_review,
    build_animal_temporal_comparison_review,
)


def _rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    chronology = [
        {
            "project_accession": "PRJEB90141",
            "repo_stable_sample_id": "prjeb90141:source-label",
            "sample_identity_resolution": "ambiguous",
            "chronology_text": "source interval remains unchanged",
            "chronology_strength": "sample_owned_interval",
            "chronology_evidence_class": "archaeological_context_date",
            "chronology_precision_posture": "contextual_interval",
            "chronology_normalization_status": "normalized_interval",
        }
    ]
    provenance = [
        {
            "project_accession": "PRJEB90141",
            "repo_stable_sample_id": "prjeb90141:source-label",
            "temporal_semantics": {"comparability_posture": "numeric_interval"},
        }
    ]
    return chronology, provenance


def test_saved_review_retains_identity_refusal_and_never_opens_sources() -> None:
    chronology, provenance = _rows()
    before = deepcopy((chronology, provenance))
    owner = "bijux_pollenomics.reporting.adna.foundation_outputs.chronology"
    with (
        patch(f"{owner}.build_sample_chronology_review_rows") as source_rows,
        patch(f"{owner}.build_sample_chronology_provenance_rows") as source_provenance,
    ):
        result = build_animal_sample_chronology_review(
            data_root=Path("unused-governed-data"),
            chronology_rows=chronology,
            provenance_rows=provenance,
        )
        source_rows.assert_not_called()
        source_provenance.assert_not_called()
    assert result["rows"] == chronology
    assert result["row_count"] == 1
    assert result["strength_counts"]["sample_owned_interval"] == 1
    assert result["normalization_counts"]["normalized_interval"] == 1
    assert result["comparability_counts"] == {"numeric_interval": 1}
    assert (chronology, provenance) == before


def test_default_review_still_uses_both_source_builders() -> None:
    chronology, provenance = _rows()
    data_root = Path("source-governed-data")
    owner = "bijux_pollenomics.reporting.adna.foundation_outputs.chronology"
    with (
        patch(
            f"{owner}.build_sample_chronology_review_rows", return_value=chronology
        ) as source_rows,
        patch(
            f"{owner}.build_sample_chronology_provenance_rows", return_value=provenance
        ) as source_provenance,
    ):
        result = build_animal_sample_chronology_review(data_root=data_root)
        source_rows.assert_called_once_with(data_root)
        source_provenance.assert_called_once_with(data_root)
    assert result["rows"] == chronology
    assert result["row_count"] == 1
    assert result["comparability_counts"] == {"numeric_interval": 1}


@pytest.mark.parametrize("missing", ["chronology", "provenance"])
def test_saved_review_refuses_partial_population_before_source_access(
    missing: str,
) -> None:
    chronology, provenance = _rows()
    with pytest.raises(ValueError, match="both supplied row populations"):
        build_animal_sample_chronology_review(
            data_root=Path("unavailable-governed-data"),
            chronology_rows=None if missing == "chronology" else chronology,
            provenance_rows=None if missing == "provenance" else provenance,
        )


@pytest.mark.parametrize("change", ["project", "sample", "duplicate", "missing"])
def test_saved_review_refuses_mixed_or_duplicate_source_owners(change: str) -> None:
    chronology, provenance = _rows()
    if change == "project":
        provenance[0]["project_accession"] = "PRJEB59481"
    elif change == "sample":
        provenance[0]["repo_stable_sample_id"] = "prjeb90141:different-label"
    elif change == "duplicate":
        provenance.append(dict(provenance[0]))
    else:
        provenance.clear()
    with pytest.raises(ValueError, match="owner populations differ"):
        build_animal_sample_chronology_review(
            data_root=Path("unused-governed-data"),
            chronology_rows=chronology,
            provenance_rows=provenance,
        )


def test_temporal_comparison_uses_saved_context_and_preserves_missing_dates() -> None:
    _, provenance = _rows()
    provenance[0]["temporal_semantics"] = {
        "comparability_posture": "numeric_interval_with_caveat",
        "time_start_bp": 3480,
        "time_end_bp": 3580,
    }
    provenance.append(
        {
            "project_accession": "PRJEB90261",
            "repo_stable_sample_id": "prjeb90261:undated-source-owner",
            "temporal_semantics": {"comparability_posture": "contextual_label_only"},
        }
    )
    before = deepcopy(provenance)
    owner = "bijux_pollenomics.reporting.adna.foundation_outputs.chronology"
    with (
        patch(f"{owner}.build_sample_chronology_provenance_rows") as source,
        patch(f"{owner}._load_json_if_present", return_value={}),
        patch(f"{owner}._published_temporal_feature_findings", return_value=[]),
    ):
        result = build_animal_temporal_comparison_review(
            data_root=Path("unavailable-source-data"),
            report_root=Path("unused-report"),
            provenance_rows=provenance,
        )
        source.assert_not_called()
    assert result["family_rows"][0]["row_count"] == 2
    assert result["family_rows"][0]["comparability_counts"] == {
        "numeric_interval_with_caveat": 1,
        "contextual_label_only": 1,
    }
    assert len(result["unsafe_comparison_findings"]) == 1
    assert provenance == before


def test_temporal_comparison_refuses_duplicate_saved_owners() -> None:
    _, provenance = _rows()
    provenance.append(deepcopy(provenance[0]))
    with pytest.raises(ValueError, match="unique provenance owners"):
        build_animal_temporal_comparison_review(
            data_root=Path("unavailable-source-data"),
            report_root=Path("unused-report"),
            provenance_rows=provenance,
        )


@pytest.mark.parametrize("supplied_empty", [False, True])
def test_temporal_comparison_distinguishes_default_and_empty_saved_population(
    supplied_empty: bool,
) -> None:
    _, provenance = _rows()
    data_root = Path("unused-source-data")
    owner = "bijux_pollenomics.reporting.adna.foundation_outputs.chronology"
    with (
        patch(
            f"{owner}.build_sample_chronology_provenance_rows", return_value=provenance
        ) as source,
        patch(f"{owner}._load_json_if_present", return_value={}),
        patch(f"{owner}._published_temporal_feature_findings", return_value=[]),
    ):
        result = build_animal_temporal_comparison_review(
            data_root=data_root,
            report_root=Path("unused-report"),
            provenance_rows=[] if supplied_empty else None,
        )
        if supplied_empty:
            source.assert_not_called()
            assert result["family_rows"][0]["row_count"] == 0
        else:
            source.assert_called_once_with(data_root)
            assert result["family_rows"][0]["row_count"] == 1


@pytest.mark.parametrize(
    "change", ["valid", "missing", "duplicate", "unowned", "hull_only"]
)
def test_published_locality_guard_requires_valid_owned_child_intervals(
    tmp_path: Path, change: str
) -> None:
    properties: dict[str, Any] = {
        "feature_id": "source-locality",
        "chronology_role": "locality_sample_coverage_hull",
        "sample_ids": ["source-sample"],
        "sample_count": 1,
        "sample_chronologies": [
            {
                "schema_version": "adna-sample-chronology-support.v1",
                "sample_id": "source-sample",
                "chronology": {
                    "original_text": "source context: 10-20 BP",
                    "time_start_bp": 10,
                    "time_end_bp": 20,
                    "time_mean_bp": 15,
                    "dating_basis": "archaeological_context",
                    "evidence_class": "archaeological_context_date",
                    "precision_posture": "contextual_interval",
                    "refusal_reason_code": "",
                },
            }
        ],
        "time_start_bp": 10,
        "time_end_bp": 20,
        "time_mean_bp": 15,
        "temporal_semantics": {
            "schema_version": "temporal-semantics.v1",
            "comparability_posture": "contextual_label_only",
        },
    }
    if change == "missing":
        properties["sample_chronologies"] = []
    elif change == "duplicate":
        properties["sample_chronologies"] *= 2
    elif change == "unowned":
        properties["sample_chronologies"][0]["sample_id"] = "another-sample"
    elif change == "hull_only":
        del properties["sample_chronologies"]
    (tmp_path / "world_animal_localities.geojson").write_text(
        json.dumps({"features": [{"properties": properties}]})
    )
    findings = _published_temporal_feature_findings(tmp_path)
    if change == "valid":
        assert findings == []
    else:
        assert len(findings) == 1
        assert "contextual-only chronology still exposes numeric" in findings[0]
