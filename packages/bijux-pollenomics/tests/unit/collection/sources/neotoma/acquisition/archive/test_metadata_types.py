"""Numerical archive declarations preserve native JSON integer types."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.neotoma.collection import (
    write_neotoma_download_archive,
)


@pytest.mark.parametrize("value", [True, 1.0])
@pytest.mark.parametrize(
    "owner,field",
    [
        ("manifest", "part_count"),
        ("manifest", "row_count"),
        ("manifest", "downloaded_dataset_count"),
        ("manifest", "requested_dataset_count"),
        ("record", "row_count"),
        ("record", "downloaded_dataset_count"),
        ("record", "part_number"),
        ("part", "row_count"),
        ("part", "downloaded_dataset_count"),
        ("part", "part_number"),
        ("part", "part_count"),
    ],
)
def test_numerically_equal_wrong_type_cannot_establish_archive_ownership(
    tmp_path: Path, owner: str, field: str, value: bool | float
) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nname="archive-fixture"\n')

    def publish() -> Path:
        return write_neotoma_download_archive(
            tmp_path / "raw",
            requested_dataset_ids=[7],
            downloaded_dataset_ids=[7],
            download_rows=[{"site": {"dataset": {"datasetid": 7}}}],
            rows_per_part=1,
        )

    manifest = publish()
    selected = manifest.parent / "part-001.json" if owner == "part" else manifest
    document = json.loads(selected.read_bytes())
    target = document["parts"][0] if owner == "record" else document
    target[field] = value
    selected.write_text(json.dumps(document))
    original = {path.name: path.read_bytes() for path in manifest.parent.iterdir()}
    with pytest.raises(ValueError, match="unowned or invalid source members"):
        publish()
    assert {
        path.name: path.read_bytes() for path in manifest.parent.iterdir()
    } == original
