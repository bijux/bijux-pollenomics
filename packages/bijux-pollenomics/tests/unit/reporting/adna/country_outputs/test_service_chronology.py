"""Generated country-output chronology integration checks."""

from __future__ import annotations

import pytest
from bijux_pollenomics.core.repository import repository_data_root
from bijux_pollenomics.reporting.adna.country_outputs.service import (
    build_country_animal_output_bundle,
)

pytestmark = pytest.mark.generated_artifacts


def test_denmark_keeps_caveated_aurochs_chronology_out_of_domesticated_scope() -> None:
    bundle = build_country_animal_output_bundle(
        data_root=repository_data_root(__file__),
        country="Denmark",
        version="test",
        generated_on="1970-01-01",
    )
    lundby = next(
        row
        for row in bundle.localities
        if row["locality"] == "Lundby I"
        and row["animal_scope"] == "wild_or_progenitor_context"
    )

    assert (lundby["time_start_bp"], lundby["time_end_bp"]) == (6748, 7744)
    assert lundby["temporal_comparability_posture"] == ("numeric_interval_with_caveat")
    assert lundby["coordinate_confidence"] == "approximate"

    progenitor = next(
        row
        for row in bundle.species_rows
        if row["species_latin_name"] == "Bos taurus"
        and row["animal_scope"] == "wild_or_progenitor_context"
    )
    assert progenitor["oldest_signal_bp"] == 8173
    assert progenitor["youngest_signal_bp"] == 6748
    domesticated = [
        row
        for row in bundle.species_rows
        if row["species_latin_name"] == "Bos taurus"
        and row["animal_scope"] == "domesticated_core"
    ]
    assert all(row["oldest_signal_bp"] != 8173 for row in domesticated)
