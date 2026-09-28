"""Shared immutable catalog workspace fixtures."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from bijux_pollenomics.adna.species.tracked_data import (
    materialize_tracked_species_adna,
)
from tests.support.repository import REPOSITORY_ROOT


def _copy_governed_source_artifacts(data_root: Path) -> None:
    """Give the isolated producer the archived source files it consumes."""
    source_root = REPOSITORY_ROOT / "data"
    index_path = (
        source_root
        / "adna"
        / "governance"
        / "source_library"
        / "source_artifact_index.json"
    )
    rows = json.loads(index_path.read_text(encoding="utf-8"))["rows"]
    for row in rows:
        if row["fetch_status"] != "archived":
            continue
        relative_path = Path(row.get("storage_path") or row["local_path"])
        source_path = source_root / relative_path
        target_path = data_root / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)
        metadata_path = source_path.with_name(source_path.name + ".metadata.json")
        if metadata_path.is_file():
            shutil.copy2(
                metadata_path,
                target_path.with_name(target_path.name + ".metadata.json"),
            )
    pig_coordinate_evidence = Path(
        "adna/species/sus_scrofa_domesticus/raw/site_coordinate_evidence.json"
    )
    target_path = data_root / pig_coordinate_evidence
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_root / pig_coordinate_evidence, target_path)


@pytest.fixture(scope="package")
def catalog_data_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Materialize tracked animal evidence once for read-only catalog tests."""
    data_root = tmp_path_factory.mktemp("animal-audit-catalogs") / "data"
    _copy_governed_source_artifacts(data_root)
    materialize_tracked_species_adna(data_root)
    return data_root


@pytest.fixture
def report_root(tmp_path: Path) -> Path:
    """Return an isolated mutable report root."""
    return tmp_path / "docs" / "report"
