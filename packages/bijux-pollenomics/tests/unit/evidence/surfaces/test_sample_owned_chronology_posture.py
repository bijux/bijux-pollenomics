"""Display hulls cannot remove caution for absent or refused sample chronology."""

from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace
from typing import cast

import pytest

from bijux_pollenomics.adna import AdnaSpeciesNormalizationBundle
from bijux_pollenomics.adna.domain.locality import summarize_sample_localities
from bijux_pollenomics.adna.domain.models import AdnaLocalitySummary
from bijux_pollenomics.evidence.surfaces.posture import _chronology_posture_for

from ...adna.domain.test_adna_temporal_query import _sample_with_interval


def _locality() -> AdnaLocalitySummary:
    young = _sample_with_interval(100, 110)
    old = replace(
        _sample_with_interval(300, 310),
        identity=replace(young.identity, stable_token="old-sample"),
    )
    return summarize_sample_localities((young, old))[0]


def _posture(localities: tuple[AdnaLocalitySummary, ...]) -> str:
    bundle = cast(AdnaSpeciesNormalizationBundle, SimpleNamespace(project_summaries=()))
    return _chronology_posture_for(bundle, localities)


def test_explicit_complete_source_sample_support_has_available_chronology() -> None:
    assert _posture((_locality(),)) == "mapped_locality_bp_windows_available"


@pytest.mark.parametrize("sample_count", [1, 2])
def test_hull_only_legacy_locality_retains_chronology_caution(
    sample_count: int,
) -> None:
    locality = _locality()
    locality = replace(
        locality,
        sample_count=sample_count,
        sample_ids=locality.sample_ids[:sample_count],
        sample_chronologies=(),
    )
    assert locality.time_start_bp is not None and locality.time_end_bp is not None
    assert _posture((locality,)) == "mapped_locality_points_with_partial_chronology"


@pytest.mark.parametrize("missing", [True, False])
def test_one_missing_or_refused_sample_retains_caution_despite_complete_hull(
    missing: bool,
) -> None:
    locality = _locality()
    support = locality.sample_chronologies[0]
    chronology = (
        replace(support.chronology, time_start_bp=None, time_end_bp=None)
        if missing
        else replace(support.chronology, refusal_reason_code="source_age_unresolved")
    )
    locality = replace(
        locality,
        sample_chronologies=(
            replace(support, chronology=chronology),
            locality.sample_chronologies[1],
        ),
    )
    assert _posture((locality,)) == "mapped_locality_points_with_partial_chronology"


def test_mixed_complete_and_hull_only_localities_retain_partial_posture() -> None:
    locality = _locality()
    legacy = replace(locality, sample_chronologies=())
    assert (
        _posture((locality, legacy)) == "mapped_locality_points_with_partial_chronology"
    )


def test_duplicate_owned_sample_support_is_not_complete_coverage() -> None:
    locality = _locality()
    support = locality.sample_chronologies[0]
    locality = replace(locality, sample_chronologies=(support, support))
    assert _posture((locality,)) == "mapped_locality_points_with_partial_chronology"


@pytest.mark.parametrize("declared_count", [0, 1, 3])
def test_declared_count_must_match_all_source_sample_ids(declared_count: int) -> None:
    locality = replace(_locality(), sample_count=declared_count)
    assert _posture((locality,)) == "mapped_locality_points_with_partial_chronology"


def test_extra_source_id_without_owned_support_remains_partial() -> None:
    locality = _locality()
    locality = replace(locality, sample_ids=(*locality.sample_ids, "unresolved-third"))
    assert _posture((locality,)) == "mapped_locality_points_with_partial_chronology"


def test_duplicate_source_ids_remain_partial() -> None:
    locality = _locality()
    locality = replace(locality, sample_ids=(locality.sample_ids[0],) * 2)
    assert _posture((locality,)) == "mapped_locality_points_with_partial_chronology"


@pytest.mark.parametrize("unresolved_id", ["", "  "])
def test_empty_or_whitespace_ids_cannot_establish_complete_source_support(
    unresolved_id: str,
) -> None:
    locality = _locality()
    first, second = locality.sample_chronologies
    locality = replace(
        locality,
        sample_ids=(unresolved_id, second.sample_id),
        sample_chronologies=(replace(first, sample_id=unresolved_id), second),
    )
    assert _posture((locality,)) == "mapped_locality_points_with_partial_chronology"


def test_extra_refused_support_cannot_hide_unmatched_member_denominator() -> None:
    locality = _locality()
    first = locality.sample_chronologies[0]
    extra = replace(
        first,
        sample_id="unresolved-third",
        chronology=replace(first.chronology, refusal_reason_code="unresolved_source"),
    )
    locality = replace(
        locality,
        sample_ids=(*locality.sample_ids, extra.sample_id),
        sample_chronologies=(*locality.sample_chronologies, extra),
    )
    assert _posture((locality,)) == "mapped_locality_points_with_partial_chronology"


@pytest.mark.parametrize("declared_count", [True, 1.0])
def test_count_requires_an_integer_without_boolean_or_float_coercion(
    declared_count: object,
) -> None:
    locality = summarize_sample_localities((_sample_with_interval(100, 110),))[0]
    locality = replace(locality, sample_count=cast(int, declared_count))
    assert _posture((locality,)) == "mapped_locality_points_with_partial_chronology"


@pytest.mark.parametrize("invalid_id", [None, 7, [], {}])
def test_nonstring_source_identity_refuses_without_coercion_or_type_error(
    invalid_id: object,
) -> None:
    locality = _locality()
    locality = replace(
        locality, sample_ids=(cast(str, invalid_id), locality.sample_ids[1])
    )
    assert _posture((locality,)) == "mapped_locality_points_with_partial_chronology"


@pytest.mark.parametrize("invalid_id", [None, 7, [], {}])
def test_nonstring_support_identity_refuses_without_coercion_or_type_error(
    invalid_id: object,
) -> None:
    locality = _locality()
    first, second = locality.sample_chronologies
    locality = replace(
        locality,
        sample_chronologies=(replace(first, sample_id=cast(str, invalid_id)), second),
    )
    assert _posture((locality,)) == "mapped_locality_points_with_partial_chronology"


@pytest.mark.parametrize("bounds", [(None, 110), (100, None)])
def test_partial_source_interval_retains_chronology_caution(
    bounds: tuple[int | None, int | None],
) -> None:
    locality = _locality()
    first, second = locality.sample_chronologies
    chronology = replace(
        first.chronology, time_start_bp=bounds[0], time_end_bp=bounds[1]
    )
    locality = replace(
        locality, sample_chronologies=(replace(first, chronology=chronology), second)
    )
    assert _posture((locality,)) == "mapped_locality_points_with_partial_chronology"
