"""Archive declarations must be exact before source rows are consumed."""

from __future__ import annotations

from collections.abc import Iterator
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.collection import (
    build_neotoma_download_archive_parts,
    write_neotoma_download_archive,
)


def source_row(identity: int = 1) -> dict[str, Any]:
    return {"site": {"dataset": {"datasetid": identity}}}


def forbidden_rows() -> Iterator[dict[str, Any]]:
    def refuse(_index: int) -> dict[str, Any]:
        raise AssertionError("source rows consumed before archive argument preflight")

    return map(refuse, [0])


@pytest.mark.parametrize("field", ["requested", "returned"])
@pytest.mark.parametrize("value", [True, False, 1.9, 1.0, "1", 0, -1])
def test_invalid_archive_id_never_becomes_a_different_declared_owner(
    tmp_path: Path, field: str, value: Any
) -> None:
    with pytest.raises(ValueError, match="positive integer"):
        write_neotoma_download_archive(
            tmp_path / "raw",
            requested_dataset_ids=[value] if field == "requested" else [1],
            downloaded_dataset_ids=[value] if field == "returned" else [1],
            download_rows=[source_row()],
        )
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("field", ["requested", "returned"])
def test_late_invalid_declaration_refuses_before_any_source_row(
    tmp_path: Path, field: str
) -> None:
    with pytest.raises(ValueError, match="positive integer"):
        write_neotoma_download_archive(
            tmp_path / "raw",
            requested_dataset_ids=[1, 0] if field == "requested" else [1],
            downloaded_dataset_ids=[1, 0] if field == "returned" else [1],
            download_rows=forbidden_rows(),
        )
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("limit", [True, False, 0, -1, 1.5, None, "1"])
@pytest.mark.parametrize("boundary", ["parts", "publication"])
def test_part_policy_refuses_before_materializing_the_input(
    tmp_path: Path, limit: Any, boundary: str
) -> None:
    with pytest.raises(ValueError, match="positive integer"):
        if boundary == "parts":
            build_neotoma_download_archive_parts(forbidden_rows(), rows_per_part=limit)
        else:
            write_neotoma_download_archive(
                tmp_path / "raw",
                requested_dataset_ids=[1],
                downloaded_dataset_ids=[1],
                download_rows=forbidden_rows(),
                rows_per_part=limit,
            )
    assert list(tmp_path.iterdir()) == []


def test_adjacent_large_native_ids_remain_exact_in_all_archive_members(
    tmp_path: Path,
) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nname="archive-fixture"\n')
    identities = [9007199254740993, 9007199254740994]
    manifest = write_neotoma_download_archive(
        tmp_path / "raw",
        requested_dataset_ids=iter(identities),
        downloaded_dataset_ids=iter(identities),
        download_rows=(source_row(value) for value in identities),
        rows_per_part=1,
    )
    document = json.loads(manifest.read_bytes())
    assert document["requested_dataset_ids"] == identities
    assert document["downloaded_dataset_ids"] == identities
    for index, identity in enumerate(identities, 1):
        part = json.loads((manifest.parent / f"part-{index:03}.json").read_bytes())
        assert part["downloaded_dataset_ids"] == [identity]
        assert part["rows"][0]["site"]["dataset"]["datasetid"] == identity
