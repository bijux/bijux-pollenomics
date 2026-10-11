"""The retained NFI schema source and published receipt remain byte bound."""

from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import sys

import pytest

from bijux_pollenomics_dev.source_completion.empd2_nfi_reference import (
    measurement_schema as schema,
)


def _workbook(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    root = tmp_path / "private"
    workbook = root / "reference-sources/empd2-nfi/nfi/swedish-plot-data.xlsx"
    workbook.parent.mkdir(parents=True)
    workbook.write_bytes(b"synthetic workbook bytes")
    monkeypatch.setattr(
        schema, "_SOURCE_SHA256", sha256(workbook.read_bytes()).hexdigest()
    )
    return root, workbook


class _Archive:
    def __init__(self, _path: Path) -> None:
        pass

    def __enter__(self) -> _Archive:
        return self

    def __exit__(self, *_errors: object) -> None:
        pass


def _parsers(monkeypatch: pytest.MonkeyPatch) -> None:
    headers = [f"Field{index:02d}" for index in range(47)]
    headers[:6] = schema._IDENTITY_HEADERS
    headers[25:30] = schema._BASAL_AREA_HEADERS
    dictionary = {
        "Inventory_Date": "Source inventory date",
        "PlotArea": "Circular plot r=7 => 153.94 m2",
        "LandUseClass": "Forestland according to FAO-definitions",
        **dict.fromkeys(schema._BASAL_AREA_HEADERS, "Basal area (m2/ha)"),
    }
    monkeypatch.setattr(schema, "ZipFile", _Archive)
    monkeypatch.setattr(schema, "_shared_strings", lambda _archive: [])
    monkeypatch.setattr(schema, "_dictionary", lambda _archive, _strings: dictionary)
    monkeypatch.setattr(schema, "_headers", lambda _archive, _strings: headers)
    monkeypatch.setattr(
        schema,
        "_plot_support",
        lambda _archive, _strings: {"plot_year_rows": 43_892},
    )


def test_build_refuses_workbook_mutation_after_decoding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, workbook = _workbook(tmp_path, monkeypatch)
    _parsers(monkeypatch)

    def mutate_after_read(_archive: _Archive, _strings: list[str]) -> dict[str, int]:
        workbook.write_bytes(b"changed workbook bytes")
        return {"plot_year_rows": 43_892}

    monkeypatch.setattr(schema, "_plot_support", mutate_after_read)
    with pytest.raises(ValueError, match="original source identity changed"):
        schema.build(root)


def test_source_refuses_symlinked_ancestor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, workbook = _workbook(tmp_path, monkeypatch)
    nested = workbook.parent
    relocated = root / "relocated"
    nested.rename(relocated)
    nested.symlink_to(relocated, target_is_directory=True)
    with pytest.raises(ValueError, match="source path contains a symlink"):
        schema.build(root)


def test_cli_refuses_preexisting_output_without_parsing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _ = _workbook(tmp_path, monkeypatch)
    output = tmp_path / "artifacts/schema.json"
    output.parent.mkdir()
    output.write_bytes(b"competing result")
    monkeypatch.setattr(
        sys,
        "argv",
        ["schema", "--private-source-store", str(root), "--output", str(output)],
    )

    def forbidden(_root: Path) -> dict[str, object]:
        raise AssertionError("Preexisting output reached source parsing")

    monkeypatch.setattr(schema, "build", forbidden)
    with pytest.raises(ValueError, match="Absent output file required"):
        schema.main()
    assert output.read_bytes() == b"competing result"


def test_cli_refuses_competitor_created_at_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _ = _workbook(tmp_path, monkeypatch)
    output = tmp_path / "artifacts/schema.json"
    output.parent.mkdir()
    monkeypatch.setattr(
        sys,
        "argv",
        ["schema", "--private-source-store", str(root), "--output", str(output)],
    )
    monkeypatch.setattr(schema, "build", lambda _root: {"schema_version": "fixture.1"})
    actual_link = os.link

    def competitor(stage: Path, destination: Path) -> None:
        destination.write_bytes(b"competing result")
        actual_link(stage, destination)

    monkeypatch.setattr(os, "link", competitor)
    with pytest.raises(FileExistsError):
        schema.main()
    assert output.read_bytes() == b"competing result"
    assert sorted(path.name for path in output.parent.iterdir()) == ["schema.json"]


def test_cli_refuses_source_drift_between_build_and_publish(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, workbook = _workbook(tmp_path, monkeypatch)
    output = tmp_path / "artifacts/schema.json"
    output.parent.mkdir()
    monkeypatch.setattr(
        sys,
        "argv",
        ["schema", "--private-source-store", str(root), "--output", str(output)],
    )

    def changed_build(_root: Path) -> dict[str, object]:
        workbook.write_bytes(b"changed workbook bytes")
        return {"schema_version": "fixture.1"}

    monkeypatch.setattr(schema, "build", changed_build)
    with pytest.raises(ValueError, match="original source identity changed"):
        schema.main()
    assert not output.exists()
    assert list(output.parent.iterdir()) == []


def test_cli_publishes_same_json_bytes_for_stable_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root, _ = _workbook(tmp_path, monkeypatch)
    output = tmp_path / "artifacts/schema.json"
    output.parent.mkdir()
    report = {
        "source_plot_support": {"plot_year_rows": 43_892},
        "workbook_header_count": 47,
    }
    monkeypatch.setattr(
        sys,
        "argv",
        ["schema", "--private-source-store", str(root), "--output", str(output)],
    )
    monkeypatch.setattr(schema, "build", lambda _root: report)
    schema.main()
    assert (
        output.read_bytes()
        == (json.dumps(report, indent=2, sort_keys=True) + "\n").encode()
    )
    assert json.loads(capsys.readouterr().out) == {"headers": 47, "outcomes": 0}


def test_cli_refuses_replaced_stage_during_source_recheck(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _ = _workbook(tmp_path, monkeypatch)
    output = tmp_path / "artifacts/schema.json"
    output.parent.mkdir()
    monkeypatch.setattr(
        sys,
        "argv",
        ["schema", "--private-source-store", str(root), "--output", str(output)],
    )
    monkeypatch.setattr(schema, "build", lambda _root: {"workbook_header_count": 47})
    actual_require = schema._require_source

    def replace_stage(source_root: Path) -> Path:
        stage = next(output.parent.glob(".schema.json.pending-*"))
        stage.unlink()
        stage.write_bytes(b"competing stage")
        return actual_require(source_root)

    monkeypatch.setattr(schema, "_require_source", replace_stage)
    with pytest.raises(ValueError, match="Owned NFI publication stage changed"):
        schema.main()
    assert not output.exists()
    assert [path.read_bytes() for path in output.parent.iterdir()] == [
        b"competing stage"
    ]


def test_cli_refuses_replaced_stage_inside_link(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _ = _workbook(tmp_path, monkeypatch)
    output = tmp_path / "artifacts/schema.json"
    output.parent.mkdir()
    monkeypatch.setattr(
        sys,
        "argv",
        ["schema", "--private-source-store", str(root), "--output", str(output)],
    )
    monkeypatch.setattr(schema, "build", lambda _root: {"workbook_header_count": 47})
    actual_link = os.link

    def replace_at_link(stage: Path, destination: Path) -> None:
        stage.unlink()
        stage.write_bytes(b"competing stage")
        actual_link(stage, destination)

    monkeypatch.setattr(os, "link", replace_at_link)
    with pytest.raises(ValueError, match="output differs from owned stage"):
        schema.main()
    assert output.read_bytes() == b"competing stage"
    assert [path.read_bytes() for path in output.parent.iterdir()] == [
        b"competing stage",
        b"competing stage",
    ]


def test_cli_preserves_competing_output_after_link(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _ = _workbook(tmp_path, monkeypatch)
    output = tmp_path / "artifacts/schema.json"
    output.parent.mkdir()
    monkeypatch.setattr(
        sys,
        "argv",
        ["schema", "--private-source-store", str(root), "--output", str(output)],
    )
    monkeypatch.setattr(schema, "build", lambda _root: {"workbook_header_count": 47})
    actual_require = schema._require_source
    calls = 0

    def replace_after_link(source_root: Path) -> Path:
        nonlocal calls
        calls += 1
        if calls == 2:
            output.unlink()
            output.write_bytes(b"competing output")
        return actual_require(source_root)

    monkeypatch.setattr(schema, "_require_source", replace_after_link)
    with pytest.raises(ValueError, match="output or stage changed before success"):
        schema.main()
    assert output.read_bytes() == b"competing output"
    assert sorted(path.name for path in output.parent.iterdir()) == ["schema.json"]
