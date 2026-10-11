"""Native archive custody cannot imply a governed HYDE country partition."""

from __future__ import annotations

from typing import cast

import pytest

from bijux_pollenomics.governance.country_coverage.constants import (
    COUNT_FIELDS,
    COUNTRIES,
    COUNTRY_DIMENSIONS,
    HYDE_ASSIGNMENT_NOT_APPLIED,
    INPUT_PATHS,
    SOURCE_FAMILIES,
)
from bijux_pollenomics.governance.country_coverage.evidence.model import _cell
from bijux_pollenomics.governance.country_coverage.evidence.snapshots import (
    _source_snapshot_ids,
)


@pytest.mark.parametrize("dimension", COUNTRY_DIMENSIONS)
@pytest.mark.parametrize("country", COUNTRIES)
@pytest.mark.parametrize("value", [0, 42])
def test_counterfeit_hyde_evidence_cannot_admit_counts(
    dimension: str, country: str, value: int
) -> None:
    counts: dict[str, int | None] = dict.fromkeys(COUNT_FIELDS, value)
    cell = _cell(
        source_family="hyde",
        dimension=dimension,
        country_code=country,
        evidence={("hyde", dimension, country): counts},
        stage={
            "authority_status": "not_required",
            "authority_reasons": [],
            "blocking_reasons": [],
        },
        snapshot_id="sha256:" + "a" * 64,
        boundary_digest="sha256:" + "b" * 64,
        config_digest="sha256:" + "c" * 64,
        build_id="sha256:" + "d" * 64,
    )
    assert cell["availability_status"] == "blocked"
    assert cell["lifecycle_status"] == "refused"
    assert cell["source_snapshot_id"] is None
    assert cell["boundary_artifact_digest"] is None
    assert cell["counts"] == dict.fromkeys(COUNT_FIELDS)
    assert counts == dict.fromkeys(COUNT_FIELDS, value)
    assert cell["country_assignment_method"] == (
        None if dimension == "source_reported" else HYDE_ASSIGNMENT_NOT_APPLIED
    )
    assert set(cast(list[str], cell["reason_codes"])) == {
        dimension + "_partition_not_materialized",
        "hyde_native_country_projection_unverified",
    }


@pytest.mark.parametrize("forged_hyde_snapshot", [None, "not-a-hash", "a" * 64])
def test_no_hyde_country_snapshot_is_inferred_from_collection_claim(
    forged_hyde_snapshot: str | None,
) -> None:
    source_hashes: dict[str, object] = {
        source: {"snapshot_sha256": "a" * 64} for source in SOURCE_FAMILIES[:7]
    }
    source_hashes["hyde"] = {"snapshot_sha256": forged_hyde_snapshot}
    result = _source_snapshot_ids(
        {"source_hashes": source_hashes},
        {
            "data/neotoma/relational/reconciliation.json": {
                "source_snapshot_id": "sha256:" + "b" * 64
            },
            INPUT_PATHS[5]: {"acquisition_bundle_sha256": "sha256:" + "c" * 64},
        },
        {INPUT_PATHS[14]: b"independent animal evidence"},
    )
    assert tuple(result) == SOURCE_FAMILIES
    assert result["hyde"] is None
    assert all(
        result[source] is not None for source in SOURCE_FAMILIES if source != "hyde"
    )
