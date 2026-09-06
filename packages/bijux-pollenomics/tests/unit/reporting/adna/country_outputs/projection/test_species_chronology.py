"""Canonical BP extrema for country species summaries."""

from __future__ import annotations

from bijux_pollenomics.reporting.adna.country_outputs.projection.species import (
    build_species_rows,
)
from bijux_pollenomics.reporting.adna.country_outputs.projection.summaries import (
    published_chronology_value,
)


def test_species_extrema_use_younger_to_older_bp_interval_direction() -> None:
    partial = _locality("partial", younger_bp=1, older_bp=99_999)
    partial.pop("time_start_bp")
    rows = build_species_rows(
        "Sweden",
        [
            _locality("recent", younger_bp=0, older_bp=100),
            _locality("ancient", younger_bp=4944, older_bp=4961),
            partial,
            _locality("reversed", younger_bp=6000, older_bp=5000),
            _locality("boolean", younger_bp=True, older_bp=True),
        ],
        [],
    )

    assert len(rows) == 1
    assert rows[0]["oldest_signal_bp"] == 4961
    assert rows[0]["youngest_signal_bp"] == 0


def test_species_rows_keep_domesticated_and_progenitor_scopes_separate() -> None:
    domesticated = _locality("domestic cattle", younger_bp=1000, older_bp=1200)
    domesticated["species_latin_name"] = "Bos taurus"
    domesticated["species_common_name"] = "cattle"
    progenitor = _locality("aurochs", younger_bp=7000, older_bp=8000)
    progenitor["species_latin_name"] = "Bos taurus"
    progenitor["species_common_name"] = "cattle"
    progenitor["animal_scope"] = "wild_or_progenitor_context"
    progenitor["project_accession"] = "PRJEB75467"

    rows = build_species_rows("Denmark", [domesticated, progenitor], [])

    assert {
        (row["animal_scope"], row["mapped_locality_count"], row["oldest_signal_bp"])
        for row in rows
    } == {
        ("domesticated_core", 1, 1200),
        ("wild_or_progenitor_context", 1, 8000),
    }


def test_country_outputs_publish_admitted_caveated_numeric_chronology() -> None:
    assert published_chronology_value(7296, "sample_approximate_or_modeled") == 7296
    assert published_chronology_value(4700, "contextual_interval") == 4700
    assert published_chronology_value(0, "sample_precise_point") == 0
    assert published_chronology_value(5000, "broad_period_only") is None
    assert published_chronology_value(None, "sample_approximate_or_modeled") is None


def _locality(
    locality: str,
    *,
    younger_bp: int,
    older_bp: int,
) -> dict[str, object]:
    return {
        "species_latin_name": "Equus caballus",
        "species_common_name": "horse",
        "animal_scope": "domesticated_core",
        "project_accession": "PRJEB_TEST",
        "country_assignment_confidence": "exact",
        "coordinate_basis": "supplementary_table_coordinates",
        "coordinate_confidence": "exact",
        "time_start_bp": younger_bp,
        "time_end_bp": older_bp,
        "sample_count": 1,
        "locality": locality,
    }
