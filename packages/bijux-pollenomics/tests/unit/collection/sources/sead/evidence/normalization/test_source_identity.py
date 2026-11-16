"""Normalized source lineage must retain exact native key ownership."""

from __future__ import annotations

from copy import deepcopy
from typing import cast

import pytest

from bijux_pollenomics.collection.sources.sead.evidence.normalization.chronology_claims import (
    normalize_sead_chronology_claims,
)
from bijux_pollenomics.collection.sources.sead.evidence.normalization.temporal_evidence import (
    group_site_temporal_rows,
)


def _site() -> dict[str, object]:
    return {
        "site_id": "1",
        "site_uuid": "source-site",
        "analysis_entity_age_rows": [
            {
                "analysis_entity_age_id": "9007199254740993",
                "analysis_entity_id": "9007199254740993",
                "sample_group_id": "9007199254740993",
                "physical_sample_id": "9007199254740993",
                "dataset_id": "9007199254740993",
                "age": 1.4,
                "age_younger": 1.4,
                "age_older": 1.4,
                "time_start_bp": 1,
                "time_end_bp": 1,
            }
        ],
    }


def _age_row(site: dict[str, object]) -> dict[str, object]:
    return cast(list[dict[str, object]], site["analysis_entity_age_rows"])[0]


def test_normalized_claim_lineage_preserves_large_keys_and_original_source_values() -> (
    None
):
    site = _site()
    before = deepcopy(site)
    claims = normalize_sead_chronology_claims(
        [site], provenance_record_id="source-proof", build_id="source-build"
    )
    claim = claims[0]
    assert [
        claim[key]
        for key in (
            "analysis_entity_id",
            "analysis_value_id",
            "sample_group_id",
            "physical_sample_id",
            "dataset_id",
        )
    ] == [9007199254740993, None, 9007199254740993, 9007199254740993, 9007199254740993]
    assert claim["source_age_value"] == _age_row(site)
    assert claim["source_native_record_id"] == "9007199254740993"
    assert site == before


@pytest.mark.parametrize("invalid", [True, 1.4, "1.4", 0])
def test_invalid_native_lineage_key_refuses_instead_of_building_a_claim(
    invalid: object,
) -> None:
    site = _site()
    _age_row(site)["analysis_entity_id"] = invalid
    with pytest.raises(ValueError):
        normalize_sead_chronology_claims(
            [site], provenance_record_id="source-proof", build_id="source-build"
        )


@pytest.mark.parametrize("invalid", [True, 1.4, "1.4", 0])
def test_invalid_temporal_record_key_never_becomes_a_different_group_member(
    invalid: object,
) -> None:
    site = _site()
    _age_row(site)["analysis_entity_age_id"] = invalid
    with pytest.raises(ValueError):
        group_site_temporal_rows(site)


@pytest.mark.parametrize("invalid", [True, 1.4, "1.4", 0])
def test_invalid_native_record_key_refuses_instead_of_claiming_a_source_record(
    invalid: object,
) -> None:
    site = _site()
    _age_row(site)["analysis_entity_age_id"] = invalid
    with pytest.raises(ValueError):
        normalize_sead_chronology_claims(
            [site], provenance_record_id="source-proof", build_id="source-build"
        )


def test_missing_native_record_stays_a_refused_witness_without_zero_group_members() -> (
    None
):
    site = _site()
    _age_row(site)["analysis_entity_age_id"] = None
    claim = normalize_sead_chronology_claims(
        [site], provenance_record_id="source-proof", build_id="source-build"
    )[0]
    assert claim["source_native_record_id"] is None
    assert claim["chronology_eligibility"] == "refused"
    assert claim["source_age_value"]["analysis_entity_age_id"] is None
    assert group_site_temporal_rows(site) == []


def test_optional_missing_lineage_stays_null_without_changing_source_age_values() -> (
    None
):
    site = _site()
    _age_row(site)["dataset_id"] = None
    claim = normalize_sead_chronology_claims(
        [site], provenance_record_id="source-proof", build_id="source-build"
    )[0]
    assert claim["dataset_id"] is None
    assert claim["source_age_value"]["age"] == 1.4
    assert claim["source_age_value"]["dataset_id"] is None


def _comparable_site(native_record_id: object) -> dict[str, object]:
    return {
        "site_id": 1,
        "site_uuid": "native-site",
        "dating_range_rows": [
            {
                "analysis_dating_range_id": native_record_id,
                "analysis_entity_id": 2,
                "age_type": "Calibrated years BP",
                "time_start_bp": 100,
                "time_end_bp": 200,
            }
        ],
    }


@pytest.mark.parametrize("native_record_id", [1, "0001"])
def test_canonical_claim_identity_matches_timeline(native_record_id: object) -> None:
    site = _comparable_site(native_record_id)
    before = deepcopy(site)
    claim = normalize_sead_chronology_claims(
        [site], provenance_record_id="source-proof", build_id="source-build"
    )[0]
    group = group_site_temporal_rows(site)[0]
    assert (
        claim["chronology_claim_id"]
        == f"sead:native-site:{group['kind']}:{group['source_record_ids'][0]}"
    )
    assert claim["source_record_id"] == "1"
    assert claim["source_native_record_id"] == str(native_record_id)
    assert claim["source_age_value"]["analysis_dating_range_id"] == native_record_id
    assert site == before


def test_conflicting_native_aliases_refuse_instead_of_merging() -> None:
    site = _comparable_site(1)
    rows = cast(list[dict[str, object]], site["dating_range_rows"])
    rows.append(
        {
            **rows[0],
            "analysis_dating_range_id": "0001",
            "time_start_bp": 300,
            "time_end_bp": 400,
        }
    )
    before = deepcopy(site)
    with pytest.raises(ValueError, match="duplicated"):
        normalize_sead_chronology_claims(
            [site], provenance_record_id="source-proof", build_id="source-build"
        )
    assert site == before


def test_one_native_record_cannot_have_two_site_owners() -> None:
    first, second = _comparable_site(1), _comparable_site("0001")
    second["site_uuid"] = "another-native-site"
    second["site_id"] = 2
    with pytest.raises(ValueError, match="duplicated"):
        normalize_sead_chronology_claims(
            [first, second],
            provenance_record_id="source-proof",
            build_id="source-build",
        )
