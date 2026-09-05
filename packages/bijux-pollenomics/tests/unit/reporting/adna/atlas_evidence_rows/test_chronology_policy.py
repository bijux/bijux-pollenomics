"""Atlas-public chronology admission tests."""

from __future__ import annotations

import pytest

from bijux_pollenomics.adna import AdnaChronology
from bijux_pollenomics.reporting.adna.atlas_evidence_rows import (
    _atlas_public_chronology,
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


def test_zero_bp_point_is_not_confused_with_missing_chronology() -> None:
    chronology = AdnaChronology(
        "present",
        0,
        0,
        0,
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
