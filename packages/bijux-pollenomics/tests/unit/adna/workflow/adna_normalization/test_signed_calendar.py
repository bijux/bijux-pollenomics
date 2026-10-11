"""Signed calendar source values remain distinct from query-domain admission."""

from __future__ import annotations

from types import SimpleNamespace
from typing import cast

import pytest

from bijux_pollenomics.adna.domain.models import AdnaSampleRecord
from bijux_pollenomics.adna.projects.sample_master.tables.european_cats.chronology import (
    _calendar_union_bp,
    _calendar_union_label,
)
from bijux_pollenomics.adna.workflow.normalization.chronology import (
    normalize_chronology_text,
)
from bijux_pollenomics.adna.workflow.runtime import (
    AdnaSampleQuery,
    sample_matches_query,
)
from bijux_pollenomics.core.temporal_semantics import (
    InvalidBpIntervalError,
    admit_bp_interval,
)


@pytest.mark.parametrize(
    ("source_text", "expected"),
    [
        ("1949 CE", (1, 1)),
        ("1950 CE", (0, 0)),
        ("1955 CE", (-5, -5)),
        ("2014 CE", (-64, -64)),
        ("1955-2014 CE", (-64, -5)),
        ("2014-1955 CE", (-64, -5)),
        ("1940-2014 CE", (-64, 10)),
        ("1 BCE", (1950, 1950)),
        ("1 CE", (1949, 1949)),
    ],
)
def test_calendar_normalization_preserves_sign_and_endpoint_order(
    source_text: str, expected: tuple[int, int]
) -> None:
    chronology = normalize_chronology_text(source_text, dating_basis="calendar")
    assert (chronology.time_start_bp, chronology.time_end_bp) == expected
    assert chronology.original_text == source_text


def test_primary_cat_calendar_endpoints_survive_without_probability_inference() -> None:
    # Primary Table S1 row 200 and S5 row 34 repeat one BAY01 specimen excluded from deep sequencing.
    source_text = "1955AD (95.4%) 2014AD"
    assert _calendar_union_bp(source_text) == (-64, -5)
    label = _calendar_union_label(source_text)
    assert label == "-64--5 BP"
    normalized = normalize_chronology_text(label, dating_basis="source_calendar")
    assert (normalized.time_start_bp, normalized.time_end_bp) == (-64, -5)


@pytest.mark.parametrize(
    ("source_text", "expected", "stddev"),
    [
        ("-50 BP", (-50, -50), ""),
        ("-5 ± 2 BP", (-5, -5), "2"),
        ("-5 +/- 2 BP", (-5, -5), "2"),
        ("-64--5 BP", (-64, -5), ""),
        ("-50-10 BP", (-50, 10), ""),
        ("5500 BP", (5500, 5500), ""),
    ],
)
def test_source_bp_parsing_does_not_discard_a_negative_sign(
    source_text: str, expected: tuple[int, int], stddev: str
) -> None:
    chronology = normalize_chronology_text(
        source_text, dating_basis="source_bp_unknown_age_scale"
    )
    assert (chronology.time_start_bp, chronology.time_end_bp) == expected
    assert chronology.date_stddev_bp == stddev
    assert chronology.dating_basis == "source_bp_unknown_age_scale"


def test_cat_signed_point_roundtrip_remains_negative() -> None:
    label = _calendar_union_label("2000AD")
    assert label == "-50 BP"
    chronology = normalize_chronology_text(label, dating_basis="calendar")
    assert chronology.time_start_bp == chronology.time_end_bp == -50


@pytest.mark.parametrize("source_text", ["modern", "20th century", "103.26±0.27pMC"])
def test_missing_calendar_endpoints_remain_unknown(source_text: str) -> None:
    assert _calendar_union_bp(source_text) is None
    chronology = normalize_chronology_text(source_text)
    assert chronology.time_start_bp is None
    assert chronology.time_end_bp is None


@pytest.mark.parametrize("source_text", [">-50 BP", "≤-5 BP"])
def test_censored_signed_source_claim_is_not_a_point(source_text: str) -> None:
    chronology = normalize_chronology_text(source_text)
    assert chronology.time_start_bp is None
    assert chronology.time_end_bp is None


@pytest.mark.parametrize("interval", [(-64, -5), (-64, 10), (-50, -50)])
def test_signed_source_bounds_do_not_enter_nonnegative_temporal_queries(
    interval: tuple[int, int],
) -> None:
    admission = admit_bp_interval(*interval)
    assert not admission.admitted
    assert admission.refusal_reason_code == "negative_bp"
    with pytest.raises(InvalidBpIntervalError):
        AdnaSampleQuery(time_start_bp=interval[0], time_end_bp=interval[1]).normalized()
    # Only the temporal branch is exercised; all other query criteria are absent.
    sample = cast(
        AdnaSampleRecord,
        SimpleNamespace(time_start_bp=interval[0], time_end_bp=interval[1]),
    )
    query = AdnaSampleQuery(time_start_bp=0, time_end_bp=100).normalized()
    assert not sample_matches_query(sample, query)


def test_actual_1950_reference_point_remains_admissible() -> None:
    chronology = normalize_chronology_text("1950 CE", dating_basis="calendar")
    assert admit_bp_interval(chronology.time_start_bp, chronology.time_end_bp).admitted
