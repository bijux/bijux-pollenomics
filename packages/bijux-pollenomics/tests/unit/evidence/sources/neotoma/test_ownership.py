"""Parent identity must survive source transport, not only row counts and hashes."""

from __future__ import annotations

import pytest

from bijux_pollenomics.evidence.sources.neotoma.ownership import NeotomaOwnershipIndex


def _index() -> NeotomaOwnershipIndex:
    index = NeotomaOwnershipIndex()
    index.validate_rows("sites", [{"site_id": "s", "country_code": "SE"}])
    index.validate_rows(
        "collection_units",
        [{"collection_unit_id": "u", "site_id": "s", "country_code": "SE"}],
    )
    index.validate_rows(
        "datasets",
        [
            {
                "dataset_id": "d",
                "collection_unit_id": "u",
                "site_id": "s",
                "country_code": "SE",
            }
        ],
    )
    index.validate_rows(
        "samples",
        [
            {
                "sample_id": "p",
                "dataset_id": "d",
                "collection_unit_id": "u",
                "site_id": "s",
                "country_code": "SE",
            }
        ],
    )
    index.validate_rows("variables", [{"variable_id": "v"}])
    return index


def _observation() -> dict[str, object]:
    return {
        "observation_id": "o",
        "sample_id": "p",
        "variable_id": "v",
        "dataset_id": "d",
        "collection_unit_id": "u",
        "site_id": "s",
        "country_code": "SE",
        "source_value": 0,
    }


def test_source_zero_and_null_chronology_are_preserved() -> None:
    index = _index()
    row = _observation()
    index.validate_rows("observations", [row])
    assert row["source_value"] == 0
    claim = {
        **row,
        "chronology_claim_id": "a",
        "subject_type": "sample",
        "subject_id": "p",
        "chronology_id": None,
    }
    index.validate_rows("age_claims", [claim])
    assert claim["chronology_id"] is None


@pytest.mark.parametrize(
    "field", ["site_id", "collection_unit_id", "dataset_id", "sample_id", "variable_id"]
)
def test_missing_parent_is_not_certified_by_other_metadata(field: str) -> None:
    row = _observation()
    row[field] = "absent"
    with pytest.raises(ValueError, match="missing parent"):
        _index().validate_rows("observations", [row])


def test_existing_wrong_parent_with_same_country_is_refused() -> None:
    index = _index()
    index.validate_rows("sites", [{"site_id": "other", "country_code": "SE"}])
    row = _observation()
    row["site_id"] = "other"
    with pytest.raises(ValueError, match="contradicts parent site_id"):
        index.validate_rows("observations", [row])


def test_source_country_cannot_disagree_with_its_parent() -> None:
    row = _observation()
    row["country_code"] = "NO"
    with pytest.raises(ValueError, match="contradicts parent country_code"):
        _index().validate_rows("observations", [row])


@pytest.mark.parametrize("field", ["chronology_id", "subject_type"])
def test_age_claim_cannot_omit_its_explicit_source_semantics(field: str) -> None:
    claim = {
        **_observation(),
        "chronology_claim_id": "a",
        "subject_type": "sample",
        "subject_id": "p",
        "chronology_id": None,
    }
    del claim[field]
    with pytest.raises(ValueError):
        _index().validate_rows("age_claims", [claim])
