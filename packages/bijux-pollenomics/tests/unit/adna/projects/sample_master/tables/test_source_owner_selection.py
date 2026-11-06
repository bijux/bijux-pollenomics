"""Keep identified source owners separate from downstream evidence admission."""

from __future__ import annotations

import pytest

from bijux_pollenomics.adna.projects.sample_master.tables.goat_canary import (
    _build_goat_canary_rows,
)
from bijux_pollenomics.adna.projects.sample_master.tables.horse_nature import (
    _build_horse_nature_rows,
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


@pytest.mark.parametrize(
    ("publication", "included"),
    [
        ("this study", True),
        ("this study + Fages et al. (2019)", True),
        ("this study + Gaunitz et al. (2018)", True),
        ("Fages et al. (2019)", False),
        ("Gaunitz et al. (2018)", False),
        ("this study + unqualified source", False),
        ("", False),
    ],
)
def test_new_horse_sequencing_retains_prior_publication_overlap(
    publication: str, included: bool
) -> None:
    project = next(
        row
        for row in build_archive_project_catalog()
        if row.project_accession == "PRJEB44430"
    )
    rows = _build_horse_nature_rows(
        species=resolve_species_definition("Equus caballus"),
        project=project,
        source_path="synthetic-sequencing-table.xlsx",
        rows=(
            (),
            (),
            (),
            (),
            ("SampleName", "Publication", "AgeEstimate (BP)"),
            ("OWNER-A", publication, "100"),
            ("", publication, "100"),
        ),
        archive_sample_labels={"ownera": "SAMEA100"},
    )

    assert len(rows) == int(included)
    if included:
        assert rows[0].preferred_sample_label == "OWNER-A"
        assert publication in rows[0].sample_lineage_excerpt
        assert rows[0].sample_lineage_locator == "SI Table 1!row6"
        assert rows[0].chronology_text == "100 BP"
