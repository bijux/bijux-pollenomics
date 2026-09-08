"""Chronology, uncertainty, and scenario assessment tests."""

from __future__ import annotations

from bijux_pollenomics.evidence.scientific_review import (
    _build_chronology_overlaps,
    _build_scenarios,
    _build_uncertainties,
)

from .support import context_point, locality, species_row


def test_chronology_partition_reconciles_every_direct_locality() -> None:
    rows = _build_chronology_overlaps(
        direct_localities=(
            locality(younger_bp=100, older_bp=200),
            locality(younger_bp=400, older_bp=500),
            locality(younger_bp=500, older_bp=400),
        ),
        animal_localities=(),
        context_points=(context_point(younger_bp=150, older_bp=300),),
        species_rows=(),
    )

    human = rows[0]
    assert human.overlapping_direct_localities == 1
    assert human.non_overlapping_direct_localities == 1
    assert human.noncomparable_records == 1
    assert (
        human.overlapping_direct_localities
        + human.non_overlapping_direct_localities
        + human.noncomparable_records
        == 3
    )


def test_project_level_animals_remain_explicitly_noncomparable() -> None:
    rows = _build_chronology_overlaps(
        direct_localities=(),
        animal_localities=(),
        context_points=(context_point(),),
        species_rows=(species_row(),),
    )

    animal = next(row for row in rows if row.species_latin_name == "Ovis aries")
    assert animal.overlap_status == "not_comparable_project_level_only"
    assert animal.noncomparable_records == 2
    assert animal.overlapping_direct_localities == 0
    assert animal.non_overlapping_direct_localities == 0


def test_mixed_species_blockers_raise_species_uncertainty_to_high() -> None:
    rows = _build_uncertainties(
        direct_localities=(),
        animal_localities=(),
        species_rows=(
            species_row(blocking_reasons=("mixed_species_rule_unresolved",)),
        ),
    )

    species_assignment = next(
        row for row in rows if row.uncertainty_kind == "species_assignment"
    )
    assert species_assignment.severity == "high"
    assert {row.uncertainty_kind for row in rows} == {
        "species_assignment",
        "locality_precision",
        "date_precision",
    }


def test_approximate_human_coordinates_are_visible_as_uncertainty() -> None:
    rows = _build_uncertainties(
        direct_localities=(locality(coordinate_confidence="approximate"),),
        animal_localities=(),
        species_rows=(),
    )
    assert len(rows) == 1
    assert rows[0].subject == "Homo sapiens"
    assert rows[0].uncertainty_kind == "locality_precision"


def test_scenarios_never_promote_exploration_to_causal_inference() -> None:
    chronology = _build_chronology_overlaps(
        direct_localities=(locality(),),
        animal_localities=(),
        context_points=(context_point(),),
        species_rows=(species_row(),),
    )
    scenarios = _build_scenarios(
        direct_localities=(locality(),),
        animal_localities=(),
        species_rows=(species_row(),),
        chronology_overlaps=chronology,
    )

    by_key = {row.scenario_key: row for row in scenarios}
    assert by_key["nordic_farming_arrival"].current_posture == "exploratory_only"
    assert by_key["lake_selection_for_domestication_signal"].current_posture == (
        "exploratory_only"
    )
    assert by_key["cattle_management_split"].claim_scope == "descriptive"
    assert "field_sampling_gate_not_cleared" in (
        by_key["lake_selection_for_domestication_signal"].blockers
    )
