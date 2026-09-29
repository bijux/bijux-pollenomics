"""Seed isolated animal materialization with its governed source inputs."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from .repository import REPOSITORY_ROOT


def copy_governed_adna_sources(data_root: Path) -> None:
    """Copy indexed captures and the pig coordinate source into an isolated root."""
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
