"""Country and period evidence-coverage tests."""

from __future__ import annotations

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
    }


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
