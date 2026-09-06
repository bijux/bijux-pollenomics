from __future__ import annotations

import pytest
from bijux_pollenomics.adna import (
    AdnaSampleQuery,
    build_species_runtime_manifest,
    load_species_samples,
)
from bijux_pollenomics.adna import homo_sapiens as homo_sapiens_runtime
from bijux_pollenomics.adna.domain.models import (
    AdnaChronology,
    AdnaCoordinate,
    AdnaLocalityIdentity,
    AdnaSampleIdentity,
    AdnaSampleRecord,
)
from bijux_pollenomics.adna.workflow import runtime as adna_runtime
from bijux_pollenomics.core.temporal_semantics import InvalidBpIntervalError


def _sample_with_interval(
    younger_bp: int | None, older_bp: int | None
) -> AdnaSampleRecord:
    return AdnaSampleRecord(
        identity=AdnaSampleIdentity(
            namespace="test",
            stable_token="sample-1",
            accession_lineage=("sample-1",),
        ),
        locality_identity=AdnaLocalityIdentity(
            namespace="test-locality",
            stable_token="locality-1",
            locality_text="Test locality",
            political_entity="Sweden",
            source_anchor_tokens=("locality-1",),
        ),
        species_latin_name="Homo sapiens",
        species_common_name="human",
        source_family="test",
        source_release="test-release",
        record_modality="metadata_only",
        review_strength="curated_release_metadata",
        provenance_quality="release_manifest_pinned",
        master_id="sample-1",
        group_id="group-1",
        locality="Test locality",
        political_entity="Sweden",
        coordinates=AdnaCoordinate(
            latitude=59.0,
            longitude=18.0,
            latitude_text="59.0",
            longitude_text="18.0",
        ),
        publication="Test publication",
        year_first_published="2026",
        full_date="",
        chronology=AdnaChronology(
            original_text="test interval",
            time_start_bp=younger_bp,
            time_end_bp=older_bp,
            time_mean_bp=None,
        ),
        data_type="genome",
        molecular_sex="U",
        datasets=("test",),
    )


@pytest.mark.parametrize(
    ("younger_bp", "older_bp"),
    [
        (100, None),
        (None, 100),
        (200, 100),
        (-1, 100),
        (0, -1),
    ],
)
def test_sample_query_rejects_partial_reversed_or_negative_bp_intervals(
    younger_bp: int | None,
    older_bp: int | None,
) -> None:
    with pytest.raises(InvalidBpIntervalError):
        AdnaSampleQuery(
            time_start_bp=younger_bp,
            time_end_bp=older_bp,
        ).normalized()


@pytest.mark.parametrize(
    ("sample_interval", "query_interval", "expected"),
    [
        ((0, 0), (0, 0), True),
        ((100, 200), (200, 300), True),
        ((100, 200), (201, 300), False),
        ((100, 200), (0, 99), False),
    ],
)
def test_sample_query_uses_closed_canonical_bp_overlap(
    sample_interval: tuple[int, int],
    query_interval: tuple[int, int],
    expected: bool,
) -> None:
    sample = _sample_with_interval(*sample_interval)
    query = AdnaSampleQuery(
        time_start_bp=query_interval[0],
        time_end_bp=query_interval[1],
    ).normalized()

    assert adna_runtime.sample_matches_query(sample, query) is expected
    assert homo_sapiens_runtime.sample_matches_query(sample, query) is expected


@pytest.mark.parametrize(
    "sample_interval",
    [
        (100, None),
        (None, 100),
        (200, 100),
        (-1, 100),
        (None, None),
    ],
)
def test_temporal_query_refuses_malformed_or_missing_sample_interval(
    sample_interval: tuple[int | None, int | None],
) -> None:
    sample = _sample_with_interval(*sample_interval)
    query = AdnaSampleQuery(time_start_bp=0, time_end_bp=200).normalized()

    assert adna_runtime.sample_matches_query(sample, query) is False
    assert homo_sapiens_runtime.sample_matches_query(sample, query) is False


def test_homo_sapiens_uses_the_shared_sample_query_matcher() -> None:
    assert (
        homo_sapiens_runtime.sample_matches_query is adna_runtime.sample_matches_query
    )


def test_both_runtime_loaders_reject_open_ended_bp_queries_before_loading() -> None:
    manifest = build_species_runtime_manifest("Homo sapiens", version="v66")
    query = AdnaSampleQuery(time_start_bp=100, time_end_bp=None)

    with pytest.raises(InvalidBpIntervalError):
        load_species_samples(manifest, query=query)
    with pytest.raises(InvalidBpIntervalError):
        homo_sapiens_runtime.load_homo_sapiens_samples(
            manifest=manifest,
            query=query,
        )
