"""Atlas-public chronology admission tests."""

from __future__ import annotations

import pytest
from bijux_pollenomics.adna import AdnaChronology
from bijux_pollenomics.reporting.adna.atlas_evidence_rows.chronology import (
    _atlas_chronology_supports_publication,
    _atlas_public_chronology,
    _parse_chronology,
)


@pytest.mark.parametrize(
    ("precision_posture", "expected_posture"),
    [
        ("sample_precise_point", "numeric_interval"),
        ("sample_precise_interval", "numeric_interval"),
        ("sample_approximate_or_modeled", "numeric_interval_with_caveat"),
        ("contextual_interval", "numeric_interval_with_caveat"),
    ],
)
def test_complete_canonical_interval_is_retained_for_numeric_posture(
    precision_posture: str,
    expected_posture: str,
) -> None:
    chronology = AdnaChronology(
        original_text="accepted source chronology",
        time_start_bp=1000,
        time_end_bp=4700,
        time_mean_bp=2850,
        dating_basis="archaeological_context",
        evidence_class="archaeological_context_date",
        precision_posture=precision_posture,
    )

    public = _atlas_public_chronology(chronology)
    semantics = public.as_temporal_semantics(source_family="animal_adna")

    assert public == chronology
    assert semantics["comparability_posture"] == expected_posture
    assert (public.time_start_bp, public.time_end_bp) == (1000, 4700)
    assert _atlas_chronology_supports_publication(public)


@pytest.mark.parametrize(
    ("source_text", "time_bp"),
    [("4700 BP", 4700), ("1000 BP", 1000)],
)
def test_danish_pig_bp_points_retain_caveated_numeric_shape(
    source_text: str,
    time_bp: int,
) -> None:
    chronology = AdnaChronology(
        original_text=source_text,
        time_start_bp=time_bp,
        time_end_bp=time_bp,
        time_mean_bp=time_bp,
        dating_basis="archaeological_context",
        evidence_class="archaeological_context_date",
        precision_posture="sample_approximate_or_modeled",
    )

    public = _atlas_public_chronology(chronology)
    semantics = public.as_temporal_semantics(source_family="animal_adna")

    assert (
        public.time_start_bp,
        public.time_end_bp,
        public.time_mean_bp,
    ) == (time_bp, time_bp, time_bp)
    assert semantics["comparability_posture"] == "numeric_interval_with_caveat"
    assert _atlas_chronology_supports_publication(public)


def test_zero_bp_point_is_not_confused_with_missing_chronology() -> None:
    chronology = AdnaChronology(
        "present",
        0,
        0,
        0,
        dating_basis="modern_sampling",
        evidence_class="historical_or_recent_date",
        precision_posture="sample_precise_point",
    )

    public = _atlas_public_chronology(chronology)

    assert (public.time_start_bp, public.time_end_bp, public.time_mean_bp) == (0, 0, 0)


@pytest.mark.parametrize(
    ("start_bp", "end_bp", "precision_posture"),
    [
        (None, 4700, "sample_approximate_or_modeled"),
        (4700, None, "sample_precise_interval"),
        (4700, 1000, "sample_approximate_or_modeled"),
        (-1, 1000, "sample_precise_interval"),
        (1000, 4700, "broad_period_only"),
        (1000, 4700, "unresolved"),
    ],
)
def test_noncomparable_chronology_cannot_leak_numeric_fields(
    start_bp: int | None,
    end_bp: int | None,
    precision_posture: str,
) -> None:
    chronology = AdnaChronology(
        "context only",
        start_bp,
        end_bp,
        2000,
        evidence_class="archaeological_context_date",
        precision_posture=precision_posture,
    )

    public = _atlas_public_chronology(chronology)
    semantics = public.as_temporal_semantics(source_family="animal_adna")

    assert public.time_start_bp is None
    assert public.time_end_bp is None
    assert public.time_mean_bp is None
    assert semantics["comparability_posture"] == "contextual_label_only"
    if precision_posture in {"sample_precise_point", "sample_precise_interval"}:
        assert not _atlas_chronology_supports_publication(public)


def test_caveated_numeric_interval_does_not_publish_out_of_range_mean() -> None:
    chronology = AdnaChronology(
        "accepted interval with invalid mean",
        1000,
        4700,
        5000,
        dating_basis="archaeological_context",
        evidence_class="archaeological_context_date",
        precision_posture="sample_approximate_or_modeled",
    )

    public = _atlas_public_chronology(chronology)

    assert (public.time_start_bp, public.time_end_bp) == (1000, 4700)
    assert public.time_mean_bp is None


def test_numeric_interval_with_unresolved_evidence_cannot_reach_atlas() -> None:
    chronology = AdnaChronology(
        "numeric source text without resolved evidence",
        1000,
        4700,
        2850,
        dating_basis="archaeological_context",
        evidence_class="unresolved",
        precision_posture="sample_precise_interval",
    )

    public = _atlas_public_chronology(chronology)

    assert not _atlas_chronology_supports_publication(chronology)
    assert (
        public.time_start_bp,
        public.time_end_bp,
        public.time_mean_bp,
    ) == (None, None, None)


def test_atlas_publication_requires_source_chronology_text_and_supported_semantics() -> (
    None
):
    supported = AdnaChronology(
        "Late Neolithic",
        None,
        None,
        None,
        dating_basis="archaeological_period",
        evidence_class="archaeological_context_date",
        precision_posture="broad_period_only",
    )
    unresolved = AdnaChronology(
        "source text without resolved semantics",
        None,
        None,
        None,
        evidence_class="unresolved",
        precision_posture="unresolved",
    )

    assert _atlas_chronology_supports_publication(supported)
    assert not _atlas_chronology_supports_publication(unresolved)


@pytest.mark.parametrize(
    ("evidence_class", "precision_posture"),
    [
        ("unresolved", "broad_period_only"),
        ("archaeological_context_date", "unresolved"),
    ],
)
def test_either_unresolved_chronology_dimension_refuses_publication(
    evidence_class: str,
    precision_posture: str,
) -> None:
    chronology = AdnaChronology(
        "source chronology remains unresolved",
        None,
        None,
        None,
        evidence_class=evidence_class,
        precision_posture=precision_posture,
    )

    assert not _atlas_chronology_supports_publication(chronology)


@pytest.mark.parametrize(
    ("dating_basis", "evidence_class", "precision_posture"),
    [
        ("invented_basis", "archaeological_context_date", "broad_period_only"),
        ("archaeological_period", "invented_evidence", "broad_period_only"),
        ("archaeological_period", "broad_period_label", "invented_precision"),
        ("unknown", "broad_period_label", "broad_period_only"),
        ("not_yet_curated", "broad_period_label", "broad_period_only"),
    ],
)
def test_unknown_or_uncurated_chronology_vocabulary_refuses_publication(
    dating_basis: str,
    evidence_class: str,
    precision_posture: str,
) -> None:
    chronology = AdnaChronology(
        "source chronology",
        None,
        None,
        None,
        dating_basis=dating_basis,
        evidence_class=evidence_class,
        precision_posture=precision_posture,
    )

    assert not _atlas_chronology_supports_publication(chronology)


def test_null_chronology_text_does_not_become_the_literal_string_none() -> None:
    parsed = _parse_chronology(
        {
            "original_text": None,
            "date_stddev_bp": None,
            "dating_basis": None,
            "evidence_class": None,
            "precision_posture": None,
        }
    )

    assert parsed.original_text == ""
    assert parsed.date_stddev_bp == ""
    assert parsed.dating_basis == "unknown"
    assert parsed.evidence_class == "unresolved"
    assert parsed.precision_posture == "unresolved"
    assert not _atlas_chronology_supports_publication(parsed)
