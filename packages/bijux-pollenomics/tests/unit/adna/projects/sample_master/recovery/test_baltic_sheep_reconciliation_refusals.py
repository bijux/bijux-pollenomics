"""Official-source contracts for the Baltic ancient-sheep samples."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import shutil

import pytest

from bijux_pollenomics.adna.projects.sample_master.tables.baltic_sheep import (
    ARTICLE_SOURCE_PATH,
    ENA_SAMPLE_SOURCE_DIRECTORY,
    load_baltic_sheep_official_evidence,
    reconcile_baltic_sheep_official_evidence,
)
from bijux_pollenomics.adna.workflow.source_artifacts import (
    resolve_source_artifact_path,
)
from tests.support.repository import REPOSITORY_ROOT

pytestmark = pytest.mark.generated_artifacts

DATA_ROOT = REPOSITORY_ROOT / "data"
WORKBOOK_SOURCE_PATH = (
    "data/adna/governance/source_library/papers/10.1093-gbe-evae114/"
    "supplementary/SupplementaryTables_Revision2.xlsx"
)
ARCHIVE_SOURCE_PATH = (
    "data/adna/governance/source_library/projects/PRJEB59481/archive_metadata.html"
)


def _article_payload() -> bytes:
    return (DATA_ROOT / ARTICLE_SOURCE_PATH.removeprefix("data/")).read_bytes()


def _ena_payload(accession: str) -> bytes:
    return (
        DATA_ROOT
        / ENA_SAMPLE_SOURCE_DIRECTORY.removeprefix("data/")
        / f"{accession}.xml"
    ).read_bytes()


def _copy_source_artifact(output_root: Path, repository_path: str) -> None:
    destination = output_root / repository_path.removeprefix("data/")
    destination.parent.mkdir(parents=True, exist_ok=True)
    logical_source = DATA_ROOT / repository_path.removeprefix("data/")
    storage_source = resolve_source_artifact_path(logical_source)
    storage_destination = (
        destination.with_suffix(destination.suffix + ".gz")
        if storage_source.suffix == ".gz"
        else destination
    )
    shutil.copy2(storage_source, storage_destination)
    receipt_source = logical_source.with_suffix(
        logical_source.suffix + ".metadata.json"
    )
    if receipt_source.is_file():
        receipt_destination = destination.with_suffix(
            destination.suffix + ".metadata.json"
        )
        shutil.copy2(receipt_source, receipt_destination)


def _copy_official_source_bundle(output_root: Path) -> None:
    _copy_source_artifact(output_root, ARTICLE_SOURCE_PATH)
    for suffix in range(1, 6):
        _copy_source_artifact(
            output_root,
            f"{ENA_SAMPLE_SOURCE_DIRECTORY}/SAMEA11296029{suffix}.xml",
        )


def test_reconciliation_refuses_missing_and_cross_contaminated_rows() -> None:
    bundle = load_baltic_sheep_official_evidence(DATA_ROOT)
    with pytest.raises(ValueError, match="ENA evidence denominator drift"):
        reconcile_baltic_sheep_official_evidence(
            tuple(row.archive for row in bundle.samples[:-1]),
            tuple(row.chronology for row in bundle.samples),
        )

    archive_rows = [row.archive for row in bundle.samples]
    archive_rows[0] = replace(archive_rows[0], site_name="Stora Förvar")
    with pytest.raises(ValueError, match="source locality conflict"):
        reconcile_baltic_sheep_official_evidence(
            tuple(archive_rows), tuple(row.chronology for row in bundle.samples)
        )
