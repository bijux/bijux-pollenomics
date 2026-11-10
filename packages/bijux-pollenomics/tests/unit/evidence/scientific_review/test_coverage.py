"""Country and period evidence-coverage tests."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace

import pytest

from bijux_pollenomics.adna import AdnaLocalitySummary
from bijux_pollenomics.adna.domain.models.localities import AdnaSampleChronologySupport
from bijux_pollenomics.evidence.scientific_review import (
    _build_country_coverage,
    _build_period_coverage,
)

from .support import locality, species_row


def test_country_coverage_does_not_assign_unmapped_animal_context() -> None:
    rows = _build_country_coverage(
        countries=("Sweden", "Norway"),
        direct_localities=(locality(country="Sweden"),),
        animal_localities=(),
        species_rows=(species_row(),),
    )

    animal_rows = [row for row in rows if row.species_latin_name == "Ovis aries"]
    assert len(animal_rows) == 2
    assert {row.country for row in animal_rows} == {"Sweden", "Norway"}
    assert all(row.mapped_locality_count == 0 for row in animal_rows)
    assert all(
        row.assignment_confidence == "not_country_assignable_from_current_runtime"
        for row in animal_rows
    )


def test_country_coverage_uses_only_matching_mapped_localities() -> None:
    sheep = species_row()
    rows = _build_country_coverage(
        countries=("Sweden", "Norway"),
        direct_localities=(),
        animal_localities=(
            locality(species="Ovis aries", country="Sweden"),
            locality(species="Bos taurus", country="Sweden"),
        ),
        species_rows=(sheep,),
    )

    by_country = {
        row.country: row for row in rows if row.species_latin_name == "Ovis aries"
    }
    assert by_country["Sweden"].mapped_locality_count == 1
    assert by_country["Sweden"].evidence_scope == "mapped_direct"
    assert by_country["Norway"].mapped_locality_count == 0
    assert by_country["Norway"].evidence_scope == "contextual"


def test_unresolved_chronology_is_not_coerced_into_the_zero_bp_bin() -> None:
    rows = _build_period_coverage(
        direct_localities=(locality(younger_bp=None, older_bp=None, mean_bp=None),),
        animal_localities=(),
        species_rows=(),
    )

    counts = {row.period_label: row.mapped_locality_count for row in rows}
    assert counts == {
        "0-1000 BP": 0,
        "1001-3000 BP": 0,
        "3001-6000 BP": 0,
        "6001+ BP": 0,
        "project_level_or_unresolved": 1,
    }
    assert sum(counts.values()) == 1
    unresolved = next(
        row for row in rows if row.period_label == "project_level_or_unresolved"
    )
    assert unresolved.contextual_project_count == 0
    assert (
        unresolved.chronology_confidence == "unresolved_or_cross_period_sample_support"
    )
    assert "absent or refused supports remain untested" in unresolved.caution_note


def test_mapped_animal_periods_remain_separate_from_project_context() -> None:
    rows = _build_period_coverage(
        direct_localities=(),
        animal_localities=(
            locality(
                species="Ovis aries",
                younger_bp=1001,
                older_bp=3000,
                mean_bp=2000,
            ),
        ),
        species_rows=(species_row(),),
    )

    sheep = [row for row in rows if row.species_latin_name == "Ovis aries"]
    assert len(sheep) == 1
    assert sheep[0].period_label == "1001-3000 BP"
    assert sheep[0].mapped_locality_count == 1
    assert sheep[0].contextual_project_count == 2
    assert sheep[0].evidence_scope == "mapped_direct"


@pytest.mark.parametrize(
    ("start", "end", "mean", "label"),
    ((100, 200, None, "0-1000 BP"), (900, 1100, 950, "project_level_or_unresolved")),
)
def test_human_period_partition_preserves_within_and_cross_bin_inputs(
    start: int,
    end: int,
    mean: int | None,
    label: str,
) -> None:
    source = locality(younger_bp=start, older_bp=end, mean_bp=mean)
    original = deepcopy(source.as_dict())
    rows = _build_period_coverage(
        direct_localities=(source,), animal_localities=(), species_rows=()
    )
    counts = {row.period_label: row.mapped_locality_count for row in rows}

    assert counts[label] == 1
    assert sum(counts.values()) == 1
    assert source.as_dict() == original
    if label == "0-1000 BP":
        assert "project_level_or_unresolved" not in counts
    else:
        assert (
            counts["0-1000 BP"] == 0
        )  # A within-bin mean cannot replace cross-bin support.


def test_human_period_partition_accounts_for_zero_unknown_refusal_and_crossing() -> (
    None
):
    refused = locality(younger_bp=100, older_bp=200, mean_bp=150)
    refused = replace(
        refused,
        chronology=replace(
            refused.chronology, refusal_reason_code="controlled_source_refusal"
        ),
    )
    sources: tuple[AdnaLocalitySummary, ...] = (
        locality(younger_bp=100, older_bp=200, mean_bp=150),
        locality(younger_bp=0, older_bp=0, mean_bp=0),
        locality(younger_bp=1001, older_bp=2000, mean_bp=1500),
        locality(younger_bp=900, older_bp=1100, mean_bp=950),
        locality(younger_bp=None, older_bp=None, mean_bp=0),
        refused,
    )
    # Give every independent input locality and its legacy sole child distinct identities.
    sources = tuple(
        replace(
            row,
            identity=replace(
                row.identity,
                stable_token=f"site-{index}",
                source_anchor_tokens=(f"sample-{index}",),
            ),
            sample_ids=(f"sample-{index}",),
        )
        for index, row in enumerate(sources)
    )
    original = [row.as_dict() for row in sources]
    rows = _build_period_coverage(
        direct_localities=sources, animal_localities=(), species_rows=()
    )
    counts = {row.period_label: row.mapped_locality_count for row in rows}

    assert counts == {
        "0-1000 BP": 2,
        "1001-3000 BP": 1,
        "3001-6000 BP": 0,
        "6001+ BP": 0,
        "project_level_or_unresolved": 3,
    }
    assert sum(counts.values()) == len(sources)
    assert [row.as_dict() for row in sources] == original
    assert all(row.contextual_project_count == 0 for row in rows)


@pytest.mark.parametrize(
    ("older_start", "older_end", "label"),
    ((900, 910, "0-1000 BP"), (2000, 2100, "project_level_or_unresolved")),
)
def test_disjoint_owned_supports_are_counted_once_without_forcing_a_period(
    older_start: int,
    older_end: int,
    label: str,
) -> None:
    source = locality(younger_bp=100, older_bp=older_end, mean_bp=105)
    young = AdnaSampleChronologySupport(
        "young",
        replace(
            source.chronology, time_start_bp=100, time_end_bp=110, time_mean_bp=105
        ),
    )
    old = AdnaSampleChronologySupport(
        "old",
        replace(
            source.chronology,
            time_start_bp=older_start,
            time_end_bp=older_end,
            time_mean_bp=older_start,
        ),
    )
    source = replace(
        source,
        sample_count=2,
        sample_ids=("young", "old"),
        sample_chronologies=(young, old),
    )
    original = source.as_dict()
    rows = _build_period_coverage(
        direct_localities=(source,), animal_localities=(), species_rows=()
    )
    counts = {row.period_label: row.mapped_locality_count for row in rows}

    assert counts[label] == 1 and sum(counts.values()) == 1
    assert source.as_dict() == original
    assert len(source.sample_chronologies) == 2
    if label == "project_level_or_unresolved":
        assert counts["0-1000 BP"] == 0
