"""Fail-closed tests for complete pig source-evidence reconciliation."""

from __future__ import annotations

from dataclasses import replace

import pytest

from bijux_pollenomics.adna.projects.sample_master.tables.pig_panel import (
    _build_pig_panel_rows,
    build_pig_panel_join_audit,
    load_pig_site_coordinate_evidence,
)
from bijux_pollenomics.adna.sources.archive import build_species_archive_projects
from bijux_pollenomics.adna.species.definitions import resolve_species_definition

from .support import (
    ARCHIVE_SOURCE_PATH,
    DATA_ROOT,
    MODERN_WORKBOOK_SOURCE_PATH,
    WORKBOOK_SOURCE_PATH,
    governed_inputs,
)

pytestmark = pytest.mark.generated_artifacts


def _audit(
    ancient_rows: tuple[tuple[str, ...], ...],
    modern_rows: tuple[tuple[str, ...], ...],
    archive_text: str,
) -> None:
    build_pig_panel_join_audit(
        source_path=WORKBOOK_SOURCE_PATH,
        rows=ancient_rows,
        modern_source_path=MODERN_WORKBOOK_SOURCE_PATH,
        modern_rows=modern_rows,
        archive_source_path=ARCHIVE_SOURCE_PATH,
        archive_text=archive_text,
    )


def _replace_cell(
    rows: tuple[tuple[str, ...], ...], row_index: int, column_index: int, value: str
) -> tuple[tuple[str, ...], ...]:
    mutable_rows = [list(row) for row in rows]
    mutable_rows[row_index][column_index] = value
    return tuple(tuple(row) for row in mutable_rows)


def test_ancient_and_modern_header_drift_are_refused() -> None:
    ancient_rows, modern_rows, archive_text = governed_inputs()

    with pytest.raises(ValueError, match="ancient workbook header drift"):
        _audit(
            _replace_cell(ancient_rows, 0, 28, "Mean age"),
            modern_rows,
            archive_text,
        )
    with pytest.raises(ValueError, match="modern workbook header drift"):
        _audit(
            ancient_rows,
            _replace_cell(modern_rows, 0, 4, "Sample accession"),
            archive_text,
        )


def test_ambiguous_archive_label_join_is_refused() -> None:
    ancient_rows, modern_rows, archive_text = governed_inputs()

    with pytest.raises(ValueError, match="AA015 maps to multiple archive samples"):
        _audit(
            ancient_rows,
            modern_rows,
            archive_text.replace("SAMEA5160867", "SAMEA9999999", 1),
        )


def test_missing_or_duplicate_ancient_workbook_identity_is_refused() -> None:
    ancient_rows, modern_rows, archive_text = governed_inputs()
    missing = tuple(row for row in ancient_rows if not row or row[0] != "AA016")
    duplicate = (
        *ancient_rows,
        next(row for row in ancient_rows if row and row[0] == "AA016"),
    )

    with pytest.raises(ValueError, match="AA016.*0"):
        _audit(missing, modern_rows, archive_text)
    with pytest.raises(ValueError, match="AA016.*2"):
        _audit(duplicate, modern_rows, archive_text)


def test_missing_or_duplicate_modern_accession_is_refused() -> None:
    ancient_rows, modern_rows, archive_text = governed_inputs()
    missing = tuple(
        row for row in modern_rows if len(row) <= 4 or row[4] != "SAMEA5772927"
    )
    duplicate = (
        *modern_rows,
        next(row for row in modern_rows if len(row) > 4 and row[4] == "SAMEA5772927"),
    )

    with pytest.raises(ValueError, match="SAMEA5772927.*0"):
        _audit(ancient_rows, missing, archive_text)
    with pytest.raises(ValueError, match="SAMEA5772927.*2"):
        _audit(ancient_rows, duplicate, archive_text)


def test_archive_denominator_drift_is_refused() -> None:
    ancient_rows, modern_rows, archive_text = governed_inputs()
    reduced_archive = "\n".join(
        line for line in archive_text.splitlines() if "SAMEA5772927" not in line
    )

    with pytest.raises(ValueError, match="archive sample denominator drift"):
        _audit(ancient_rows, modern_rows, reduced_archive)


def test_coordinate_evidence_cannot_widen_the_two_governed_anchors() -> None:
    ancient_rows, modern_rows, archive_text = governed_inputs()
    bundso = load_pig_site_coordinate_evidence(DATA_ROOT)[0]

    with pytest.raises(ValueError, match="widens governed anchors"):
        build_pig_panel_join_audit(
            source_path=WORKBOOK_SOURCE_PATH,
            rows=ancient_rows,
            modern_source_path=MODERN_WORKBOOK_SOURCE_PATH,
            modern_rows=modern_rows,
            archive_source_path=ARCHIVE_SOURCE_PATH,
            archive_text=archive_text,
            coordinate_evidence=(replace(bundso, sample_label="AA014"),),
        )


@pytest.mark.parametrize("sample_label", ("AA015", "AA016"))
@pytest.mark.parametrize(
    "statuses",
    (
        ("Wild", "Wild", "Wild"),
        ("Unknown", "Unknown", "Unknown"),
        ("Domestic", "Wild", "Unknown"),
    ),
    ids=("wild", "unknown", "discordant"),
)
def test_governed_anchor_classification_drift_blocks_master_publication_path(
    sample_label: str, statuses: tuple[str, str, str]
) -> None:
    ancient_rows, modern_rows, archive_text = governed_inputs()
    mutable_rows = [list(row) for row in ancient_rows]
    row_index = next(
        index
        for index, row in enumerate(mutable_rows)
        if row and row[0] == sample_label
    )
    for column_index, status in zip((33, 37, 38), statuses, strict=True):
        mutable_rows[row_index][column_index] = status
    species = resolve_species_definition("Sus scrofa domesticus")
    project = next(
        project
        for project in build_species_archive_projects(species.latin_name)
        if project.project_accession == "PRJEB30282"
    )

    with pytest.raises(
        ValueError,
        match=f"Governed pig anchor {sample_label} domestication claims drift",
    ):
        _build_pig_panel_rows(
            species=species,
            project=project,
            source_path=WORKBOOK_SOURCE_PATH,
            rows=tuple(tuple(row) for row in mutable_rows),
            modern_source_path=MODERN_WORKBOOK_SOURCE_PATH,
            modern_rows=modern_rows,
            archive_source_path=ARCHIVE_SOURCE_PATH,
            archive_text=archive_text,
            coordinate_evidence=load_pig_site_coordinate_evidence(DATA_ROOT),
        )
