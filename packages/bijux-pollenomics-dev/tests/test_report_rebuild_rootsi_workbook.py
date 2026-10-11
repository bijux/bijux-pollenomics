"""Bind selected Rootsi workbook bytes while retaining scientific refusals."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild import rootsi_workbook
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import _checked_file
from bijux_pollenomics_dev.ci.report_rebuild.source_qualification import (
    validated_external_report_sources,
)

DESCRIPTOR = Path("configs/ci/qualified-report-sources/rootsi-bokesjon-workbook.json")


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _spec(path: Path, name: str) -> dict[str, Any]:
    payload = path.read_bytes()
    return {
        "path": name,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "size": len(payload),
    }


@pytest.fixture
def packet(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path, dict[str, Any], dict[str, Any]]:
    repository = tmp_path / "repository"
    store = tmp_path / "store"
    directory = store / rootsi_workbook.SOURCE_ID
    workbook = directory / rootsi_workbook.WORKBOOK
    workbook.parent.mkdir(parents=True)
    workbook.write_bytes(b"synthetic workbook bytes")
    workbook_spec = _spec(workbook, rootsi_workbook.WORKBOOK)
    archive_sha = "a" * 64
    other = [
        {
            "archive_member": f"rootsi/OTHER-{index:02d}.xls",
            "bytes": 1 if index < 77 else 4466176 - workbook_spec["size"] - 77,
            "sha256": hashlib.sha256(str(index).encode()).hexdigest(),
        }
        for index in range(78)
    ]
    members = sorted(
        [
            {
                "archive_member": rootsi_workbook.WORKBOOK,
                "bytes": workbook_spec["size"],
                "sha256": workbook_spec["sha256"],
            },
            *other,
        ],
        key=lambda row: row["archive_member"],
    )
    manifest: dict[str, Any] = {
        "schema_version": "rootsi-external-source-custody.v1",
        "archive_sha256": archive_sha,
        "workbook_count": 79,
        "total_workbook_bytes": 4466176,
        "source_rights_status": rootsi_workbook.RIGHTS,
        "historical_primary_input_authentication": rootsi_workbook.HISTORICAL_IDENTITY,
        "members": members,
    }
    manifest_file = directory / "manifest.json"
    _write(manifest_file, manifest)
    manifest_spec = _spec(manifest_file, "manifest.json")
    descriptor: dict[str, Any] = {
        "schema_version": rootsi_workbook.SCHEMA,
        "source_id": rootsi_workbook.SOURCE_ID,
        "archive_sha256": archive_sha,
        "manifest": manifest_spec,
        "workbook": workbook_spec,
        "source_rights_status": rootsi_workbook.RIGHTS,
        "historical_primary_input_authentication": rootsi_workbook.HISTORICAL_IDENTITY,
    }
    _write(repository / DESCRIPTOR, descriptor)
    monkeypatch.setattr(rootsi_workbook, "ARCHIVE_SHA256", archive_sha)
    monkeypatch.setattr(rootsi_workbook, "MANIFEST_SHA256", manifest_spec["sha256"])
    monkeypatch.setattr(rootsi_workbook, "MANIFEST_SIZE", manifest_spec["size"])
    monkeypatch.setattr(rootsi_workbook, "WORKBOOK_SHA256", workbook_spec["sha256"])
    monkeypatch.setattr(rootsi_workbook, "WORKBOOK_SIZE", workbook_spec["size"])
    return repository, store, descriptor, manifest


def test_exact_selected_packet_is_read_only_and_excludes_unconsumed_members(
    packet: tuple[Path, Path, dict[str, Any], dict[str, Any]],
) -> None:
    repository, store, _, _ = packet
    before = {
        path: path.read_bytes()
        for base in (repository, store)
        for path in base.rglob("*")
        if path.is_file()
    }
    selected = validated_external_report_sources(repository, store, DESCRIPTOR)
    assert set(selected.inputs) == {
        DESCRIPTOR.as_posix(),
        f"external/{rootsi_workbook.SOURCE_ID}/manifest.json",
        f"external/{rootsi_workbook.SOURCE_ID}/{rootsi_workbook.WORKBOOK}",
    }
    assert selected.directory == store / rootsi_workbook.SOURCE_ID
    assert before == {
        path: path.read_bytes()
        for base in (repository, store)
        for path in base.rglob("*")
        if path.is_file()
    }


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ("forged_manifest", "qualified source bytes differ"),
        ("coherent_member_forgery", "selected workbook differs"),
        ("descriptor_path_escape", "source file identity differs"),
        ("descriptor_rights_upgrade", "refusal posture differs"),
        ("manifest_rights_upgrade", "refusal differs"),
        ("historical_upgrade", "refusal posture differs"),
        ("workbook_bytes", "qualified source bytes differ"),
    ],
)
def test_forgery_and_posture_upgrades_are_refused(
    packet: tuple[Path, Path, dict[str, Any], dict[str, Any]],
    change: str,
    message: str,
) -> None:
    repository, store, descriptor, manifest = packet
    directory = store / rootsi_workbook.SOURCE_ID
    workbook = directory / rootsi_workbook.WORKBOOK
    if change == "forged_manifest":
        manifest["workbook_count"] = 78
        _write(directory / "manifest.json", manifest)
    elif change == "coherent_member_forgery":
        manifest["members"][0]["sha256"] = "0" * 64
        _write(directory / "manifest.json", manifest)
        descriptor["manifest"] = _spec(directory / "manifest.json", "manifest.json")
        _write(repository / DESCRIPTOR, descriptor)
        rootsi_workbook.MANIFEST_SHA256 = descriptor["manifest"]["sha256"]
        rootsi_workbook.MANIFEST_SIZE = descriptor["manifest"]["size"]
    elif change == "descriptor_path_escape":
        descriptor["workbook"]["path"] = "rootsi/../BOKE.xls"
        _write(repository / DESCRIPTOR, descriptor)
    elif change == "descriptor_rights_upgrade":
        descriptor["source_rights_status"] = "approved"
        _write(repository / DESCRIPTOR, descriptor)
    elif change == "manifest_rights_upgrade":
        manifest["source_rights_status"] = "approved"
        _write(directory / "manifest.json", manifest)
        descriptor["manifest"] = _spec(directory / "manifest.json", "manifest.json")
        _write(repository / DESCRIPTOR, descriptor)
        rootsi_workbook.MANIFEST_SHA256 = descriptor["manifest"]["sha256"]
        rootsi_workbook.MANIFEST_SIZE = descriptor["manifest"]["size"]
    elif change == "historical_upgrade":
        descriptor["historical_primary_input_authentication"] = "approved"
        _write(repository / DESCRIPTOR, descriptor)
    else:
        workbook.write_bytes(b"changed synthetic workbook")
    with pytest.raises(ReportRebuildError, match=message):
        validated_external_report_sources(repository, store, DESCRIPTOR)


def test_source_symlink_and_store_overlap_refuse(
    packet: tuple[Path, Path, dict[str, Any], dict[str, Any]], tmp_path: Path
) -> None:
    repository, store, _, _ = packet
    original = store / rootsi_workbook.SOURCE_ID / rootsi_workbook.WORKBOOK
    copy = tmp_path / "workbook-copy"
    copy.write_bytes(original.read_bytes())
    original.unlink()
    original.symlink_to(copy)
    with pytest.raises(ReportRebuildError, match="real regular path"):
        validated_external_report_sources(repository, store, DESCRIPTOR)
    with pytest.raises(ReportRebuildError, match="separate from repository"):
        validated_external_report_sources(repository, repository, DESCRIPTOR)


@pytest.mark.parametrize("target", ["manifest.json", "BOKE.xls"])
def test_source_changed_after_first_read_refuses(
    packet: tuple[Path, Path, dict[str, Any], dict[str, Any]],
    monkeypatch: pytest.MonkeyPatch,
    target: str,
) -> None:
    repository, store, _, _ = packet
    original_checked = _checked_file
    changed = False

    def change_after_read(directory: Path, spec: dict[str, Any]) -> Path:
        nonlocal changed
        path = original_checked(directory, spec)
        if path.name == target and not changed:
            path.write_bytes(b"changed after first qualified read")
            changed = True
        return path

    monkeypatch.setattr(rootsi_workbook, "_checked_file", change_after_read)
    with pytest.raises(ReportRebuildError, match="changed|bytes differ"):
        validated_external_report_sources(repository, store, DESCRIPTOR)
    assert changed
