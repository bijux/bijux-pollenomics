from __future__ import annotations

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
from bijux_pollenomics.data_downloader.models import ContextPointRecord
from bijux_pollenomics.evidence.scientific_review import _locality_overlaps_point
from bijux_pollenomics.reporting.adna.public_outputs import (
    _interval_from_row,
    _intervals_overlap as reporting_intervals_overlap,
)
from bijux_pollenomics.reporting.adna.public_outputs import _normalize_interval


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
        _interval_from_row(
            {"time_start_bp": "relative period", "time_end_bp": "100"}
        )
        is None
    )
    assert _interval_from_row({"time_start_bp": "0", "time_end_bp": "100"}) == (
        0,
        100,
    )


def _locality(
    *, younger_bp: int | None, older_bp: int | None
) -> AdnaLocalitySummary:
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
