"""Archive identity indexes must not impose an order on native source rows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.collection import (
    write_neotoma_download_archive,
)


def _publish(raw: Path, identities: list[int], rows_per_part: int) -> Path:
    return write_neotoma_download_archive(
        raw,
        requested_dataset_ids=identities,
        downloaded_dataset_ids=identities,
        download_rows=[
            {"site": {"dataset": {"datasetid": identity}}} for identity in identities
        ],
        rows_per_part=rows_per_part,
    )


@pytest.mark.parametrize("rows_per_part", [1, 2, 3])
@pytest.mark.parametrize(
    "identities",
    [
        [9007199254740994, 9007199254740993, 7],
        [7, 9007199254740994, 9007199254740993],
        [7, 9007199254740993, 9007199254740994],
    ],
)
def test_source_order_survives_publication_and_owned_replacement(
    tmp_path: Path, identities: list[int], rows_per_part: int
) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nname="archive-fixture"\n')
    manifest = _publish(tmp_path / "raw", identities, rows_per_part)
    document = json.loads(manifest.read_bytes())
    assert document["downloaded_dataset_ids"] == [7, 9007199254740993, 9007199254740994]
    observed: list[int] = []
    for record in document["parts"]:
        part = json.loads((manifest.parent / record["filename"]).read_bytes())
        observed.extend(row["site"]["dataset"]["datasetid"] for row in part["rows"])
    assert observed == identities
    original = {path.name: path.read_bytes() for path in manifest.parent.iterdir()}
    assert _publish(tmp_path / "raw", identities, rows_per_part) == manifest
    assert {
        path.name: path.read_bytes() for path in manifest.parent.iterdir()
    } == original


@pytest.mark.parametrize("replacement_id", [7, 99])
def test_false_source_membership_cannot_become_owned_through_sorting(
    tmp_path: Path, replacement_id: int
) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nname="archive-fixture"\n')
    identities = [7, 8, 9]
    manifest = _publish(tmp_path / "raw", identities, 3)
    part_path = manifest.parent / "part-001.json"
    part: dict[str, Any] = json.loads(part_path.read_bytes())
    part["rows"][1]["site"]["dataset"]["datasetid"] = replacement_id
    part_path.write_text(json.dumps(part))
    prior = {path.name: path.read_bytes() for path in manifest.parent.iterdir()}
    with pytest.raises(ValueError, match="unowned or invalid source members"):
        _publish(tmp_path / "raw", identities, 3)
    assert {path.name: path.read_bytes() for path in manifest.parent.iterdir()} == prior
