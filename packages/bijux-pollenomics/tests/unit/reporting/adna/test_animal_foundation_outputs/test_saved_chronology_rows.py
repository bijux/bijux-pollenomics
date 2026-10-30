"""Saved chronology publication must retain exact owners without source rebuilding."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from bijux_pollenomics.reporting.adna.foundation_outputs.chronology import (
    build_animal_sample_chronology_review,
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
