"""Keep identified source owners separate from downstream evidence admission."""

from __future__ import annotations

import pytest

from bijux_pollenomics.adna.projects.sample_master.tables.goat_canary import (
    _build_goat_canary_rows,
)
from bijux_pollenomics.adna.sources.archive import build_archive_project_catalog
from bijux_pollenomics.adna.species.definitions import resolve_species_definition


@pytest.mark.parametrize("chronology", ["", "-", "100-200 BP"])
def test_identified_goat_survives_missing_chronology(chronology: str) -> None:
    project = next(
        row
        for row in build_archive_project_catalog()
        if row.project_accession == "PRJEB90261"
    )
    rows = _build_goat_canary_rows(
        species=resolve_species_definition("Capra hircus"),
        project=project,
        source_path="synthetic-owner-table.xlsx",
        rows=(
            ("Synthetic owner table",),
            (
                "Sample ID",
                "Archaeological site",
                "RCD available from the same sample, stratigrafic unit or site",
            ),
            ("OWNER-A", "Source locality", chronology),
            ("", "Unidentified entry", "100-200 BP"),
        ),
    )

    assert len(rows) == 1
    owner = rows[0]
    assert owner.preferred_sample_label == "OWNER-A"
    assert owner.archive_native_sample_id == ""
    assert owner.sample_lineage_locator == "Table S2!row3"
    assert owner.locality_text == "Source locality"
    assert owner.chronology_text == ("" if chronology in {"", "-"} else chronology)
