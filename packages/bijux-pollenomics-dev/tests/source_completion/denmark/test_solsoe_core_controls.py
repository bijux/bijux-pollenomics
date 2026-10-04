"""Primary Solsø owner binds inputs and preserves the retained report writer."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.source_contracts import (
    pangaea_age_controls as table,
)
from bijux_pollenomics_dev.ci.report_rebuild.source_qualification import (
    validated_external_report_sources,
)
from bijux_pollenomics_dev.source_completion import solsoe_core_age_lineage as retained
from bijux_pollenomics_dev.source_completion.denmark import (
    solsoe_core_controls as owner,
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
                "license": "CC-BY-NC-3.0",
                "capture_custody": "not_established",
                "scientific_admission": False,
            }
        )
    )
    for path in owner.REPOSITORY_INPUTS:
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
        "schema_version": "solsoe-primary-core-age-lineage.v1",
        "lra_admitted_samples": 0,
        "source_label": "synthetic Solsø",
    }
    calls: list[tuple[Path, Path]] = []

    def publish(root: Path, external: Path, stage: Path) -> dict[str, Any]:
        calls.append((root, external))
        assert not stage.exists() and stage.is_relative_to(repository / "artifacts")
        stage.mkdir()
        (stage / "report.json").write_text(json.dumps(report, indent=2) + "\n")
        return report

    monkeypatch.setattr(retained, "publish", publish)
    assert owner.run(repository, source_root, owner.DESCRIPTOR, output) == report
    assert calls == [(repository, source_root)]
    assert (output / "report.json").read_bytes() == (
        json.dumps(report, indent=2) + "\n"
    ).encode()
    assert set(output.iterdir()) == {output / "report.json"}
    assert not list(output.parent.glob(".products.*"))


@pytest.mark.parametrize(
    "corruption",
    (
        "source",
        "repository",
        "scope",
        "extra",
        "serialization",
        "report_alias",
        "rival_output",
    ),
)
def test_post_writer_corruption_refused_before_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, corruption: str
) -> None:
    repository, source_root, output = _fixture(tmp_path, monkeypatch)
    report: dict[str, Any] = {
        "schema_version": "solsoe-primary-core-age-lineage.v1",
        "lra_admitted_samples": 0,
    }

    def publish(root: Path, external: Path, stage: Path) -> dict[str, Any]:
        stage.mkdir()
        if corruption == "scope":
            report["lra_admitted_samples"] = False
        text = json.dumps(report, indent=2) + "\n"
        (stage / "report.json").write_text(text)
        if corruption == "source":
            (external / table.SOURCE_ID / table.TABLE).write_bytes(b"changed")
        elif corruption == "repository":
            (root / owner.REPOSITORY_INPUTS[1]).write_bytes(b"changed")
        elif corruption == "extra":
            (stage / "extra.json").write_text("{}")
        elif corruption == "serialization":
            (stage / "report.json").write_text("{}")
        elif corruption == "report_alias":
            (stage / "report.json").unlink()
            (stage / "report.json").symlink_to(root / owner.REPOSITORY_INPUTS[0])
        elif corruption == "rival_output":
            output.mkdir()
            (output / "rival.txt").write_text("preserve rival")
        return report

    monkeypatch.setattr(retained, "publish", publish)
    with pytest.raises(ReportRebuildError):
        owner.run(repository, source_root, owner.DESCRIPTOR, output)
    assert not list(output.parent.glob(".products.*"))
    if corruption == "rival_output":
        assert (output / "rival.txt").read_text() == "preserve rival"
    else:
        assert not output.exists()
