"""Published Solsø owner binds inputs and preserves the retained report writer."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import runpy
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.source_contracts import (
    pangaea_epd_age_table as table,
)
from bijux_pollenomics_dev.ci.report_rebuild.source_qualification import (
    validated_external_report_sources,
)
from bijux_pollenomics_dev.source_completion.denmark import (
    solsoe_epd_age_join as owner,
)


def _fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path, Path]:
    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / "artifacts").mkdir()
    source_root = tmp_path / "external"
    source = source_root / table.SOURCE_ID / table.TABLE
    source.parent.mkdir(parents=True)
    payload = b"explicit synthetic table bytes\n"
    source.write_bytes(payload)
    monkeypatch.setattr(table, "TABLE_SHA256", hashlib.sha256(payload).hexdigest())
    monkeypatch.setattr(table, "TABLE_SIZE", len(payload))
    descriptor = repository / owner.DESCRIPTOR
    descriptor.parent.mkdir(parents=True)
    descriptor.write_text(
        json.dumps(
            {
                "schema_version": table.SCHEMA,
                "source_id": table.SOURCE_ID,
                "table": {
                    "path": table.TABLE,
                    "sha256": table.TABLE_SHA256,
                    "size": table.TABLE_SIZE,
                },
                "doi": table.DOI,
                "license": "CC-BY-3.0",
                "capture_custody": "not_established",
                "scientific_admission": False,
            }
        )
    )
    for path in (*owner.REPOSITORY_INPUTS, owner.REPLAY):
        target = repository / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"{}\n")
    return repository, source_root, repository / "artifacts/products"


def test_exact_source_contract_preserves_limits(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, source_root, _ = _fixture(tmp_path, monkeypatch)
    result = validated_external_report_sources(
        repository, source_root, owner.DESCRIPTOR
    )
    assert set(result.inputs) == {
        owner.DESCRIPTOR.as_posix(),
        f"external/{table.SOURCE_ID}/{table.TABLE}",
    }
    assert result.directory == source_root / table.SOURCE_ID
    descriptor = json.loads((repository / owner.DESCRIPTOR).read_bytes())
    assert descriptor["capture_custody"] == "not_established"
    assert descriptor["scientific_admission"] is False


@pytest.mark.parametrize(
    "corruption",
    ("bytes", "doi", "license", "capture", "admission", "size_bool", "duplicate"),
)
def test_changed_source_or_descriptor_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, corruption: str
) -> None:
    repository, source_root, _ = _fixture(tmp_path, monkeypatch)
    path = repository / owner.DESCRIPTOR
    value = json.loads(path.read_bytes())
    if corruption == "bytes":
        (source_root / table.SOURCE_ID / table.TABLE).write_bytes(
            b"substituted source\n"
        )
    elif corruption == "duplicate":
        path.write_text('{"schema_version": "x", "schema_version": "y"}')
    else:
        field, changed = {
            "doi": ("doi", "10.1594/PANGAEA.739834"),
            "license": ("license", "CC-BY-4.0"),
            "capture": ("capture_custody", "established"),
            "admission": ("scientific_admission", 0),
        }.get(corruption, ("table", {**value["table"], "size": True}))
        value[field] = changed
        path.write_text(json.dumps(value))
    with pytest.raises(ReportRebuildError):
        validated_external_report_sources(repository, source_root, owner.DESCRIPTOR)


@pytest.mark.parametrize("alias", ("root", "table", "table_parent", "descriptor"))
def test_supplied_aliases_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, alias: str
) -> None:
    repository, source_root, _ = _fixture(tmp_path, monkeypatch)
    if alias == "root":
        supplied = tmp_path / "external-alias"
        supplied.symlink_to(source_root, target_is_directory=True)
        source_root = supplied
    else:
        path = {
            "table": source_root / table.SOURCE_ID / table.TABLE,
            "table_parent": source_root / table.SOURCE_ID,
            "descriptor": repository / owner.DESCRIPTOR,
        }[alias]
        physical = path.with_name(path.name + "-physical")
        path.rename(physical)
        path.symlink_to(physical, target_is_directory=physical.is_dir())
    with pytest.raises(ReportRebuildError):
        validated_external_report_sources(repository, source_root, owner.DESCRIPTOR)


def test_wrapper_preserves_writer_arguments_and_complete_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, source_root, output = _fixture(tmp_path, monkeypatch)
    report: dict[str, Any] = {
        "schema_version": "solsoe-published-epd-age-join.v1",
        "lra_admitted_samples": 0,
        "calibrated_sample_matches": 92,
        "core_depth_matches": {"SOLSOE81": 66, "SOLSOE83": 26},
        "source_label": "synthetic Solsø",
    }
    calls: list[tuple[Path, Path]] = []

    def join(root: Path, external: Path) -> dict[str, Any]:
        calls.append((root, external))
        assert not output.exists()
        return report

    monkeypatch.setattr(owner, "_join", join)
    assert owner.run(repository, source_root, owner.DESCRIPTOR, output) == report
    assert calls == [(repository, source_root / table.SOURCE_ID / table.TABLE)]
    assert (output / "report.json").read_bytes() == (
        json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    ).encode()
    assert set(output.iterdir()) == {output / "report.json"}
    assert not list(output.parent.glob(".products.*"))


@pytest.mark.parametrize(
    "corruption",
    (
        "source",
        "repository",
        "replay",
        "scope",
        "sample_bool",
        "sample_count",
        "cores",
        "rival_output",
    ),
)
def test_post_join_corruption_refused_before_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, corruption: str
) -> None:
    repository, source_root, output = _fixture(tmp_path, monkeypatch)
    report: dict[str, Any] = {
        "schema_version": "solsoe-published-epd-age-join.v1",
        "lra_admitted_samples": 0,
        "calibrated_sample_matches": 92,
        "core_depth_matches": {"SOLSOE81": 66, "SOLSOE83": 26},
    }

    def join(root: Path, external: Path) -> dict[str, Any]:
        if corruption == "scope":
            report["lra_admitted_samples"] = False
        elif corruption == "sample_bool":
            report["calibrated_sample_matches"] = True
        elif corruption == "sample_count":
            report["calibrated_sample_matches"] = 91
        elif corruption == "cores":
            report["core_depth_matches"] = {"SOLSOE81": 65, "SOLSOE83": 27}
        elif corruption == "source":
            external.write_bytes(b"changed")
        elif corruption == "repository":
            (root / owner.REPOSITORY_INPUTS[1]).write_bytes(b"changed")
        elif corruption == "replay":
            (root / owner.REPLAY).write_bytes(b"changed")
        elif corruption == "rival_output":
            output.mkdir()
            (output / "rival.txt").write_text("preserve rival")
        return report

    monkeypatch.setattr(owner, "_join", join)
    with pytest.raises(ReportRebuildError):
        owner.run(repository, source_root, owner.DESCRIPTOR, output)
    assert not list(output.parent.glob(".products.*"))
    if corruption == "rival_output":
        assert (output / "rival.txt").read_text() == "preserve rival"
    else:
        assert not output.exists()


def test_existing_join_is_called_without_its_cli_or_own_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, source_root, _ = _fixture(tmp_path, monkeypatch)
    published = source_root / table.SOURCE_ID / table.TABLE
    calls: list[tuple[Path, Path]] = []
    expected: dict[str, Any] = {
        "native_missing_value": None,
        "native_negative_bound": -40.91,
    }

    def join(root: Path, source: Path) -> dict[str, Any]:
        calls.append((root, source))
        return expected

    def load(path: str) -> dict[str, Any]:
        assert Path(path) == repository / owner.REPLAY
        return {"run": join}

    monkeypatch.setattr(runpy, "run_path", load)
    assert owner._join(repository, published) is expected
    assert calls == [(repository, published)]


@pytest.mark.parametrize("destination", ("tracked", "existing", "alias"))
def test_output_custody_refused_before_join(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, destination: str
) -> None:
    repository, source_root, output = _fixture(tmp_path, monkeypatch)
    if destination == "tracked":
        output = repository / "docs/report/products"
    elif destination == "existing":
        output.mkdir()
    else:
        parent = output.parent / "alias"
        parent.symlink_to(repository / "artifacts", target_is_directory=True)
        output = parent / "products"

    def forbidden(*args: Any) -> dict[str, Any]:
        pytest.fail("Join must not run for an invalid destination")

    monkeypatch.setattr(owner, "_join", forbidden)
    with pytest.raises(ReportRebuildError):
        owner.run(repository, source_root, owner.DESCRIPTOR, output)
