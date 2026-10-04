"""Preserve source column coordinates and refuse malformed printed constants."""

from __future__ import annotations

import copy
from pathlib import Path
import sys
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.love import paper_tables as writer


def printed() -> str:
    """Create independent identity-row fractions and PPE ratios, with a wrapped header."""
    columns = (
        "Lakes",
        "Alnus",
        "Betula",
        "Corylus",
        "Fagus",
        "Fraxinus",
        "Pinus",
        "Tilia",
        "Ulmus",
        "Grasses",
        "Secale",
    )
    widths = [index * 12 for index in range(11)]
    header = "".join(
        name.ljust(12) if name != "Tilia" else " " * 12 for name in columns
    )
    wrapped = " " * widths[7] + "Tilia"
    rows = [
        " ".join(
            [str(index + 1), *["1" if column == index else "0" for column in range(11)]]
        )
        for index in range(11)
    ]
    taxa = [
        f"{name} 0.025 {index + 1} {(index + 1) / 10:g}"
        for index, name in enumerate(columns[1:])
    ]
    page = "\n".join(
        [
            "6 of 11",
            "Table 1.",
            header,
            wrapped,
            *rows,
            "Table 2.",
            "Taxon Fall Speed PPE PPE SD",
            *taxa,
            "3. Results",
        ]
    )
    return "\f".join(["source page"] * 5 + [page] + ["source page"] * 5) + "\f"


def test_positioned_wrapped_header_and_all151_cells() -> None:
    table, parameters = writer.parse_tables(printed())
    assert table["columns"][7] == "Tilia"
    assert len(table["map_units"]) == 11 and len(parameters) == 10
    for index, row in enumerate(table["map_units"]):
        assert row["map_unit"] == index + 1
        assert list(row["fractions"].values()) == [
            int(axis == index) for axis in range(11)
        ]
    for index, row in enumerate(parameters, 1):
        assert row["fall_speed_as_published"] == 0.025
        assert row["relative_pollen_productivity"] == index
        assert row["ppe_sd"] == index / 10


@pytest.mark.parametrize(
    "change",
    [
        "page",
        "boundary",
        "coordinate",
        "column",
        "row-width",
        "fraction",
        "nonfinite",
        "negative",
        "taxon-order",
        "duplicate-taxon",
        "sd",
    ],
)
def test_printed_identity_and_value_corruptions_refuse(change: str) -> None:
    text = printed()
    if change == "page":
        text = text.replace("6 of 11", "7 of 11")
    elif change == "boundary":
        text = text.replace("Table 2.", "Other table.")
    elif change == "coordinate":
        text = text.replace("11 0 0 0 0 0 0 0 0 0 0 1", "10 0 0 0 0 0 0 0 0 0 0 1")
    elif change == "column":
        text = text.replace("Tilia", "Other", 1)
    elif change == "row-width":
        text = text.replace("1 1 0 0 0 0 0 0 0 0 0 0", "1 1 0 0 0 0 0 0 0 0 0")
    elif change == "fraction":
        text = text.replace("1 1 0 0 0 0 0 0 0 0 0 0", "1 0.9 0 0 0 0 0 0 0 0 0 0")
    elif change == "nonfinite":
        text = text.replace("Alnus 0.025", "Alnus nan")
    elif change == "negative":
        text = text.replace("Alnus 0.025", "Alnus -0.025")
    elif change == "taxon-order":
        text = text.replace(
            "Alnus 0.025 1 0.1\nBetula 0.025 2 0.2",
            "Betula 0.025 2 0.2\nAlnus 0.025 1 0.1",
        )
    elif change == "duplicate-taxon":
        text = text.replace("Betula 0.025 2 0.2", "Alnus 0.025 2 0.2")
    else:
        text = text.replace("Alnus 0.025 1 0.1", "Alnus 0.025 1 0.2")
    with pytest.raises(ValueError):
        writer.parse_tables(text)


@pytest.mark.parametrize(
    "kind", ["leaf-alias", "parent-alias", "hardlink", "changed-bytes"]
)
def test_public_input_boundary_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    path = tmp_path / "data/love/paper/source.json"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"controlled")
    if kind == "leaf-alias":
        path.unlink()
        path.symlink_to(tmp_path / "missing")
    elif kind == "parent-alias":
        path.parent.rename(tmp_path / "real")
        path.parent.symlink_to(tmp_path / "real", target_is_directory=True)
    elif kind == "hardlink":
        import os

        os.link(path, tmp_path / "other")
    with pytest.raises(ValueError):
        writer._snapshot(tmp_path)


def test_final_source_mutation_refuses(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    source: dict[str, Any] = {
        "doi": "test",
        "publisher_pdf_url": "test",
        "pdf": {"path": "input.pdf", "sha256": "0" * 64, "bytes": 1},
        "text": {"path": "input.txt", "sha256": "1" * 64},
        "license": "CC-BY-4.0",
        "license_url": "test",
    }
    before = {"input.txt": printed().encode()}
    calls = 0

    def snapshot(_: Path) -> tuple[dict[str, Any], dict[str, bytes]]:
        nonlocal calls
        calls += 1
        return copy.deepcopy(source), before if calls == 1 else {
            "input.txt": b"changed"
        }

    monkeypatch.setattr(writer, "_snapshot", snapshot)
    with pytest.raises(ValueError, match="changed during"):
        writer.build(tmp_path)


def test_artifact_writer_refuses_existing_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "artifacts/existing.json"
    output.parent.mkdir()
    output.write_bytes(b"user")
    monkeypatch.setattr(writer, "build", lambda repository: {})
    monkeypatch.setattr(
        sys,
        "argv",
        ["paper_tables", "--repository", str(tmp_path), "--output", str(output)],
    )
    with pytest.raises(FileExistsError):
        writer.main()
    assert output.read_bytes() == b"user"


def test_overflowing_printed_decimal_refuses() -> None:
    with pytest.raises(ValueError, match="finite"):
        writer._numeric("9" * 400 + ".0")
