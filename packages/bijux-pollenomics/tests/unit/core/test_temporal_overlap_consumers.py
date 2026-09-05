from __future__ import annotations

import pytest

from bijux_pollenomics.adna import (
    AdnaChronology,
    AdnaCoordinate,
    AdnaLocalityIdentity,
    AdnaLocalitySummary,
)
from bijux_pollenomics.analysis.lake_evidence_richness import (
    _intervals_overlap as lake_intervals_overlap,
)
from bijux_pollenomics.analysis.sweden_land_use_synthesis import (
    _intervals_overlap as synthesis_intervals_overlap,
)
from bijux_pollenomics.collection.contracts.models import ContextPointRecord
from bijux_pollenomics.evidence.scientific_review import _locality_overlaps_point
from bijux_pollenomics.reporting.adna.comparison_contracts import (
    build_animal_comparison_contract_payload,
    govern_animal_comparison_payload,
)
from bijux_pollenomics.reporting.adna.public_outputs import (
    _build_farming_history_scenario,
    _build_first_appearance_by_country,
    _first_signal_bp,
    _interval_from_row,
    _normalize_interval,
)
from bijux_pollenomics.reporting.adna.public_outputs import (
    _intervals_overlap as reporting_intervals_overlap,
)


def test_overlap_consumers_preserve_zero_and_closed_endpoint_touch() -> None:
    assert synthesis_intervals_overlap(0, 100, 100, 200)
    assert lake_intervals_overlap(0, 100, 100, 200)
    assert reporting_intervals_overlap((0, 100), (100, 200))
    assert _locality_overlaps_point(
        _locality(younger_bp=0, older_bp=100),
        _context_point(younger_bp=100, older_bp=200),
    )


def test_overlap_consumers_refuse_reversed_intervals() -> None:
    assert not synthesis_intervals_overlap(100, 0, 0, 100)
    assert not lake_intervals_overlap(100, 0, 0, 100)
    assert not reporting_intervals_overlap((100, 0), (0, 100))
    assert not _locality_overlaps_point(
        _locality(younger_bp=100, older_bp=0),
        _context_point(younger_bp=0, older_bp=100),
    )
    assert not _locality_overlaps_point(
        _locality(younger_bp=0, older_bp=100),
        _context_point(younger_bp=100, older_bp=0),
    )


def test_overlap_consumers_refuse_negative_intervals() -> None:
    assert not synthesis_intervals_overlap(-1, 100, 0, 100)
    assert not lake_intervals_overlap(-1, 100, 0, 100)
    assert not reporting_intervals_overlap((-1, 100), (0, 100))
    assert not _locality_overlaps_point(
        _locality(younger_bp=-1, older_bp=100),
        _context_point(younger_bp=0, older_bp=100),
    )


def test_overlap_consumers_refuse_missing_and_partial_intervals() -> None:
    assert not synthesis_intervals_overlap(None, None, 0, 100)
    assert not synthesis_intervals_overlap(0, None, 0, 100)
    assert not lake_intervals_overlap(None, None, 0, 100)
    assert not lake_intervals_overlap(0, None, 0, 100)
    assert not _locality_overlaps_point(
        _locality(younger_bp=None, older_bp=None),
        _context_point(younger_bp=0, older_bp=100),
    )
    assert not _locality_overlaps_point(
        _locality(younger_bp=0, older_bp=None),
        _context_point(younger_bp=0, older_bp=100),
    )


def test_reporting_interval_normalization_never_repairs_invalid_bounds() -> None:
    assert _normalize_interval(0, 100, 50) == (0, 100)
    assert _normalize_interval(None, None, 0) == (0, 0)
    assert _normalize_interval(100, 0, 50) is None
    assert _normalize_interval(0, None, 0) is None
    assert _normalize_interval(-1, 100, 50) is None


def test_reporting_interval_parser_refuses_text_and_preserves_numeric_zero() -> None:
    assert (
        _interval_from_row({"time_start_bp": "relative period", "time_end_bp": "100"})
        is None
    )
    assert _interval_from_row({"time_start_bp": "0", "time_end_bp": "100"}) == (
        0,
        100,
    )


def test_animal_comparison_contracts_are_exact_versioned_and_noncausal() -> None:
    first = build_animal_comparison_contract_payload()
    second = build_animal_comparison_contract_payload()

    assert first == second
    assert first["schema_version"] == "animal-comparison-contract-registry.v1"
    assert first["contract_count"] == 2
    contracts = {row["contract_id"]: row for row in first["contracts"]}
    assert set(contracts) == {
        "animal-human-chronology-overlap",
        "animal-pollen-chronology-overlap",
    }
    for contract in contracts.values():
        assert contract["contract_version"] == "1.1.0"
        assert contract["contract_digest"].startswith("sha256:")
        assert contract["qualified_scientific_review_required"] is True
        assert any("causation" in claim for claim in contract["prohibited_claims"])


def test_human_overlap_is_implemented_unverified_until_qualified_review() -> None:
    payload = govern_animal_comparison_payload(
        {
            "schema_version": "animal-human-chronology-overlap.v1",
            "rows": [
                {
                    "human_locality_count": 4,
                    "overlapping_human_localities": 1,
                    "non_overlapping_human_localities": 2,
                    "noncomparable_human_localities": 1,
                }
            ],
        },
        contract_id="animal-human-chronology-overlap",
    )

    assert payload["comparison_disposition"] == {
        "status": "implemented_unverified",
        "reason_codes": ["qualified_comparison_review_missing"],
        "right_record_comparison_denominator": 4,
        "comparable_right_record_comparison_denominator": 3,
        "qualified_scientific_review_required": True,
    }


def test_pollen_overlap_refuses_unavailable_context_instead_of_claiming_zero() -> None:
    payload = govern_animal_comparison_payload(
        {
            "schema_version": "animal-pollen-chronology-overlap.v1",
            "rows": [
                {
                    "pollen_record_count": 0,
                    "overlapping_pollen_records": 0,
                    "non_overlapping_pollen_records": 0,
                    "noncomparable_pollen_records": 0,
                }
            ],
        },
        contract_id="animal-pollen-chronology-overlap",
    )

    disposition = payload["comparison_disposition"]
    assert disposition["status"] == "refused"
    assert "required_comparison_dimension_unavailable" in disposition["reason_codes"]


def test_comparison_contract_rejects_unreconciled_denominator() -> None:
    with pytest.raises(ValueError, match="denominator does not reconcile"):
        govern_animal_comparison_payload(
            {
                "schema_version": "animal-human-chronology-overlap.v1",
                "rows": [
                    {
                        "human_locality_count": 3,
                        "overlapping_human_localities": 1,
                        "non_overlapping_human_localities": 1,
                        "noncomparable_human_localities": 0,
                    }
                ],
            },
            contract_id="animal-human-chronology-overlap",
        )


def test_first_appearance_refuses_missing_chronology_without_coercing_zero() -> None:
    common = {
        "species_latin_name": "Bos taurus",
        "species_common_name": "cattle",
        "animal_scope": "domesticated_core",
        "time_label": "fixture",
        "project_accession": "PRJTEST",
        "locality": "Test",
        "country_assignment_confidence": "exact",
    }
    payload = _build_first_appearance_by_country(
        [
            {
                "country": "Sweden",
                "localities": [
                    {
                        **common,
                        "time_start_bp": None,
                        "time_end_bp": None,
                        "time_mean_bp": None,
                    },
                    {
                        **common,
                        "time_start_bp": 0,
                        "time_end_bp": 0,
                        "time_mean_bp": 0,
                    },
                ],
            }
        ]
    )

    assert _first_signal_bp(common) is None
    assert payload["rows"][0]["first_signal_bp"] == 0
    assert payload["reconciliation"] == {
        "input_locality_count": 2,
        "dated_locality_count": 1,
        "undated_locality_count": 1,
        "refusal_reason_counts": {"chronology_unavailable": 1},
    }


def test_farming_scenario_selects_globally_oldest_signal_not_first_country() -> None:
    first_appearance = {
        "rows": [
            {
                "country": "Denmark",
                "species_latin_name": "Bos taurus",
                "first_signal_bp": 100,
                "time_label": "100 BP",
                "project_accession": "PRJYOUNG",
            },
            {
                "country": "Sweden",
                "species_latin_name": "Capra hircus",
                "first_signal_bp": 5_000,
                "time_label": "5000 BP",
                "project_accession": "PRJOLD",
            },
        ]
    }
    scenario = _build_farming_history_scenario(
        coverage_payload={"rows": []},
        human_overlap_payload={"rows": []},
        pollen_overlap_payload={"rows": []},
        first_appearance_payload=first_appearance,
    )

    statement = scenario["support_statements"][0]
    assert "Capra hircus" in statement
    assert "Sweden" in statement
    assert "PRJOLD" in statement


def _locality(*, younger_bp: int | None, older_bp: int | None) -> AdnaLocalitySummary:
    return AdnaLocalitySummary(
        identity=AdnaLocalityIdentity(
            namespace="test-locality",
            stable_token="test-locality:one",
            locality_text="Test locality",
            political_entity="Sweden",
            source_anchor_tokens=("sample-1",),
        ),
        species_latin_name="Homo sapiens",
        species_common_name="human",
        source_family="fixture",
        source_releases=("fixture-v1",),
        record_modalities=("fixture",),
        review_strengths=("fixture",),
        provenance_qualities=("fixture",),
        locality="Test locality",
        coordinates=AdnaCoordinate(
            latitude=59.0,
            longitude=18.0,
            latitude_text="59.0",
            longitude_text="18.0",
            confidence="exact",
        ),
        sample_count=1,
        sample_ids=("sample-1",),
        datasets=("fixture",),
        chronology=AdnaChronology(
            original_text="fixture",
            time_start_bp=younger_bp,
            time_end_bp=older_bp,
            time_mean_bp=None,
        ),
        sample_namespace="test-sample",
    )


def _context_point(
    *, younger_bp: int | None, older_bp: int | None
) -> ContextPointRecord:
    return ContextPointRecord(
        source="fixture",
        layer_key="fixture",
        layer_label="Fixture",
        category="context",
        country="Sweden",
        record_id="context-1",
        name="Context",
        latitude=59.0,
        longitude=18.0,
        geometry_type="Point",
        subtitle="fixture",
        description="fixture",
        source_url="https://example.test/context-1",
        record_count=1,
        popup_rows=(),
        time_start_bp=younger_bp,
        time_end_bp=older_bp,
    )
