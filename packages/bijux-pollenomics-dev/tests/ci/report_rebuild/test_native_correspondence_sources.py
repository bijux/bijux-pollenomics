"""Refuse source substitutions and admission upgrades in native report adapters."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import (
    QualifiedReportSources,
)
from bijux_pollenomics_dev.ci.report_rebuild.source_contracts import (
    pangaea_abbo_profile as profile,
)
from bijux_pollenomics_dev.ci.report_rebuild.source_contracts import (
    rootsi_native_workbooks as native,
)


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


@pytest.fixture
def packet(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path, Path, dict[str, Any]]:
    repository, store = tmp_path / "repository", tmp_path / "store"
    directory = store / "landclim/rootsi-workbooks"
    member = directory / "rootsi/ABB.xls"
    member.parent.mkdir(parents=True)
    payload = b"explicit synthetic workbook, never parsed"
    member.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    spec = {"path": "rootsi/ABB.xls", "size": len(payload), "sha256": digest}
    descriptor = Path(
        "configs/ci/qualified-report-sources/rootsi-abborrtjarne-workbook.json"
    )
    write(
        repository / descriptor,
        {
            "schema_version": native.SCHEMA,
            "base_descriptor": native.BASE_DESCRIPTOR.as_posix(),
            "workbook": spec,
        },
    )
    write(repository / native.BASE_DESCRIPTOR, {"scope": "synthetic upstream fixture"})
    write(
        directory / "manifest.json",
        {
            "members": [
                {
                    "archive_member": spec["path"],
                    "bytes": spec["size"],
                    "sha256": digest,
                }
            ]
        },
    )
    monkeypatch.setattr(native, "MEMBERS", {"rootsi/ABB.xls": (len(payload), digest)})
    qualified = QualifiedReportSources(
        directory,
        {
            native.BASE_DESCRIPTOR.as_posix(): repository / native.BASE_DESCRIPTOR,
            "external/landclim/rootsi-workbooks/manifest.json": directory
            / "manifest.json",
        },
        "a" * 64,
    )
    monkeypatch.setattr(
        native, "validated_rootsi_bokesjon_workbook", lambda *_: qualified
    )
    return repository, store, descriptor, spec


def test_selected_member_preserves_upstream_custody_and_exact_bytes(
    packet: tuple[Path, Path, Path, dict[str, Any]],
) -> None:
    repository, store, descriptor, spec = packet
    result = native.validated_rootsi_native_workbook(repository, store, descriptor)
    assert result.inputs[descriptor.as_posix()] == repository / descriptor
    assert set(result.inputs) == {
        native.BASE_DESCRIPTOR.as_posix(),
        descriptor.as_posix(),
        "external/landclim/rootsi-workbooks/manifest.json",
        "external/landclim/rootsi-workbooks/rootsi/ABB.xls",
    }
    assert (
        hashlib.sha256(
            result.inputs[
                "external/landclim/rootsi-workbooks/rootsi/ABB.xls"
            ].read_bytes()
        ).hexdigest()
        == spec["sha256"]
    )


@pytest.mark.parametrize(
    "change",
    [
        "unknown_member",
        "bool_size",
        "digest",
        "extra_rights",
        "base_override",
        "manifest_member",
        "workbook_bytes",
        "source_symlink",
    ],
)
def test_native_source_substitutions_refuse(
    packet: tuple[Path, Path, Path, dict[str, Any]], change: str
) -> None:
    repository, store, descriptor, spec = packet
    value = json.loads((repository / descriptor).read_bytes())
    member = store / "landclim/rootsi-workbooks" / spec["path"]
    if change == "unknown_member":
        value["workbook"]["path"] = "rootsi/OTHER.xls"
    elif change == "bool_size":
        value["workbook"]["size"] = True
    elif change == "digest":
        value["workbook"]["sha256"] = "b" * 64
    elif change == "extra_rights":
        value["source_rights_status"] = "approved"
    elif change == "base_override":
        value["base_descriptor"] = "configs/other.json"
    elif change == "manifest_member":
        write(member.parent.parent / "manifest.json", {"members": []})
    elif change == "workbook_bytes":
        member.write_bytes(b"changed")
    elif change == "source_symlink":
        replacement = member.parent / "replacement"
        member.rename(replacement)
        member.symlink_to(replacement)
    write(repository / descriptor, value)
    with pytest.raises(ReportRebuildError):
        native.validated_rootsi_native_workbook(repository, store, descriptor)


def test_upstream_rights_refusal_is_not_bypassed(
    packet: tuple[Path, Path, Path, dict[str, Any]], monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, store, descriptor, _ = packet

    def refuse(*_: object) -> QualifiedReportSources:
        raise ReportRebuildError("Rootsi descriptor custody or refusal posture differs")

    monkeypatch.setattr(native, "validated_rootsi_bokesjon_workbook", refuse)
    with pytest.raises(ReportRebuildError, match="refusal posture"):
        native.validated_rootsi_native_workbook(repository, store, descriptor)


@pytest.fixture
def profile_packet(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path, Path, dict[str, Any]]:
    repository, store = tmp_path / "repository", tmp_path / "store"
    table = store / profile.SOURCE_ID / profile.TABLE
    table.parent.mkdir(parents=True)
    table.write_bytes(b"explicit synthetic profile, never interpreted")
    payload = table.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    monkeypatch.setattr(profile, "TABLE_SHA256", digest)
    monkeypatch.setattr(profile, "TABLE_SIZE", len(payload))
    descriptor = Path("configs/ci/qualified-report-sources/abbo-pollen-profile.json")
    value = {
        "schema_version": profile.SCHEMA,
        "source_id": profile.SOURCE_ID,
        "table": {"path": profile.TABLE, "size": len(payload), "sha256": digest},
        "doi": profile.DOI,
        "license": "CC-BY-NC-3.0",
        "capture_custody": "not_established",
        "scientific_admission": False,
    }
    write(repository / descriptor, value)
    return repository, store, descriptor, value


def test_profile_exact_custody_remains_non_admission(
    profile_packet: tuple[Path, Path, Path, dict[str, Any]],
) -> None:
    repository, store, descriptor, _ = profile_packet
    result = profile.validated_abbo_profile(repository, store, descriptor)
    assert set(result.inputs) == {
        descriptor.as_posix(),
        f"external/{profile.SOURCE_ID}/{profile.TABLE}",
    }


@pytest.mark.parametrize(
    "field",
    [
        "scientific_admission",
        "capture_custody",
        "license",
        "doi",
        "table_size",
        "table_digest",
        "table_path",
    ],
)
def test_profile_descriptor_upgrades_and_substitutions_refuse(
    profile_packet: tuple[Path, Path, Path, dict[str, Any]], field: str
) -> None:
    repository, store, descriptor, value = profile_packet
    if field == "scientific_admission":
        value[field] = 0
    elif field == "table_size":
        value["table"]["size"] = True
    elif field == "table_digest":
        value["table"]["sha256"] = "b" * 64
    elif field == "table_path":
        value["table"]["path"] = "../foreign.tsv"
    else:
        value[field] = "invented"
    write(repository / descriptor, value)
    with pytest.raises(ReportRebuildError):
        profile.validated_abbo_profile(repository, store, descriptor)


def test_profile_bytes_and_store_overlap_refuse(
    profile_packet: tuple[Path, Path, Path, dict[str, Any]],
) -> None:
    repository, store, descriptor, _ = profile_packet
    with pytest.raises(ReportRebuildError, match="external"):
        profile.validated_abbo_profile(repository, repository, descriptor)
    (store / profile.SOURCE_ID / profile.TABLE).write_bytes(b"changed")
    with pytest.raises(ReportRebuildError, match="bytes differ"):
        profile.validated_abbo_profile(repository, store, descriptor)
