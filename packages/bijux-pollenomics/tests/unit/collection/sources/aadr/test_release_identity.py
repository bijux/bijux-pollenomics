"""Native release identity must survive resolution before transport or output."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch

import pytest

from bijux_pollenomics.collection.sources import aadr


def metadata(
    file_id: object, *, filename: str = "v66.HO.aadr.PUB.anno"
) -> dict[str, Any]:
    return {"data": [{"files": [{"dataFile": {"filename": filename, "id": file_id}}]}]}


@pytest.mark.parametrize(
    "value", [True, False, 1.9, 1.0, None, [], {}, "1.9", "+1", " 1", "١"]
)
def test_native_file_identity_never_uses_lossy_integer_coercion(value: object) -> None:
    with pytest.raises(ValueError, match="file.*id|identity"):
        aadr.resolve_aadr_release("v66", metadata(value))


@pytest.mark.parametrize("value", [1, 9007199254740993, "9007199254740993", "00012"])
def test_exact_integer_ids_retain_original_source_metadata(value: int | str) -> None:
    source = metadata(value)
    original = deepcopy(source)
    resolution = aadr.resolve_aadr_release("v66", source)
    assert resolution.anno_files[0].file_id == int(value)
    assert type(resolution.anno_files[0].file_id) is int
    assert resolution.dataset_version == original["data"][0]
    assert source == original


@pytest.mark.parametrize(
    "version",
    [
        "../escaped",
        "absolute-release",
        "v66/nested",
        "v66\\nested",
        ".",
        "..",
        "",
        " v66",
        "v66\x00",
        None,
    ],
)
def test_release_component_refuses_before_transport_and_directory_creation(
    tmp_path: Path, version: object
) -> None:
    destination = tmp_path / "downloads"
    if version == "absolute-release":
        version = str(tmp_path / "escaped")
    with (
        patch.object(
            aadr, "fetch_release_history_metadata", return_value={"data": []}
        ) as fetch,
        patch.object(aadr, "fetch_binary") as binary,
        pytest.raises(ValueError, match="version|release"),
    ):
        aadr.download_aadr_anno_files(destination, cast(str, version))
    fetch.assert_not_called()
    binary.assert_not_called()
    assert list(tmp_path.iterdir()) == []


def test_unresolved_release_does_not_create_an_output_directory(tmp_path: Path) -> None:
    with (
        patch.object(aadr, "fetch_release_history_metadata", return_value={"data": []}),
        pytest.raises(ValueError, match="No public"),
    ):
        aadr.download_aadr_anno_files(tmp_path / "downloads", "v66")
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    "filename",
    [
        "v66.HO.aadr/../../foreign.anno",
        "v66.HO.aadr\\foreign.anno",
        "v66.HO.aadr\x00.anno",
    ],
)
def test_selected_source_filename_is_a_literal_flat_member(
    tmp_path: Path, filename: str
) -> None:
    with (
        patch.object(
            aadr,
            "fetch_release_history_metadata",
            return_value=metadata(12, filename=filename),
        ),
        patch.object(aadr, "fetch_binary", return_value=b"abc") as binary,
        pytest.raises(ValueError, match="filename|member"),
    ):
        aadr.download_aadr_anno_files(tmp_path / "downloads", "v66")
    binary.assert_not_called()
    assert list(tmp_path.iterdir()) == []


def test_one_native_file_cannot_impersonate_two_dataset_panels(tmp_path: Path) -> None:
    source = metadata(12)
    source["data"][0]["files"].append(
        {"dataFile": {"filename": "v66.1240K.aadr.PUB.anno", "id": 12}}
    )
    with (
        patch.object(aadr, "fetch_release_history_metadata", return_value=source),
        patch.object(aadr, "fetch_binary", return_value=b"abc") as binary,
        pytest.raises(ValueError, match="duplicate.*file|identity"),
    ):
        aadr.download_aadr_anno_files(tmp_path / "downloads", "v66")
    binary.assert_not_called()
    assert list(tmp_path.iterdir()) == []
