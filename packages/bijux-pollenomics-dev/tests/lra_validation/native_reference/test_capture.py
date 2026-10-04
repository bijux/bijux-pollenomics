"""Refuse altered native capture sources without native execution."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.lra_validation.native_reference import capture


def _write(path: Path, value: object) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, sort_keys=True).encode()
    path.write_bytes(payload)
    return {"sha256": hashlib.sha256(payload).hexdigest(), "size": len(payload)}


@pytest.fixture
def packet(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "repository"
    source = root / capture.CAPTURE_ROOT
    reports = [f"oracle/C{index:04d}.csv" for index in range(129)]
    raw = {
        name: _write(source / "capture" / name, {"value": name})
        for name in sorted(set(reports) | capture.EXTRA_RAW_MEMBERS)
    }
    receipt = _write(
        source / "capture/receipt.json",
        {
            "status": "passed",
            "fresh_R_executed": True,
            "release_certificate": False,
            "r_version": "4.6.0",
        },
    )
    archives = {}
    for index in range(5):
        name = f"source-archives/P{index}.tar.gz"
        archives[f"P{index}"] = {
            "path": name,
            "version": "1",
            **_write(source / name, {"archive": index}),
        }
    metadata = {
        "path": "public-acquisition.json",
        **_write(source / "public-acquisition.json", {"source": "fresh public"}),
    }
    spec = _write(
        source / "capture/capture.json",
        {
            "schema_version": "qualified-native-r-capture.v1",
            "source_revision": capture.CAPTURE_SOURCE_REVISION,
            "r_version": "4.6.0",
            "release_certificate": False,
            "core_passed": 43,
            "domains_passed": 23,
            "original_vectors_compared": 48,
            "fresh_public_archive_count": 5,
            "raw_members": raw,
            "report_source_members": sorted(reports),
            "execution_receipt": receipt,
            "public_archives": archives,
            "public_acquisition": metadata,
        },
    )
    monkeypatch.setattr(capture, "CAPTURE_MANIFEST_SHA256", spec["sha256"])
    return root


def test_exact_capture_is_read_only_and_keeps_extras(packet: Path) -> None:
    before = {p: p.read_bytes() for p in packet.rglob("*") if p.is_file()}
    selected = capture.validated_native_capture(packet)
    assert len(selected.report_source_members) == 129
    assert len(selected.raw_sha256) == 138
    assert len(selected.input_sha256) == 146
    assert not capture.EXTRA_RAW_MEMBERS.intersection(selected.report_source_members)
    assert {p: p.read_bytes() for p in packet.rglob("*") if p.is_file()} == before


@pytest.mark.parametrize(
    "relative",
    [
        "capture/capture.json",
        "capture/receipt.json",
        "capture/oracle/C0000.csv",
        "capture/oracle/R_stderr.log",
        "source-archives/P0.tar.gz",
        "public-acquisition.json",
    ],
)
def test_every_source_identity_refuses_mutation(packet: Path, relative: str) -> None:
    with (packet / capture.CAPTURE_ROOT / relative).open("ab") as stream:
        stream.write(b"changed")
    with pytest.raises(ValueError, match="differs|changed"):
        capture.validated_native_capture(packet)


@pytest.mark.parametrize(
    "operation", ["missing", "extra", "symlink", "directory-alias", "hardlink"]
)
def test_source_population_and_physical_aliases_refuse(
    packet: Path, operation: str
) -> None:
    source = packet / capture.CAPTURE_ROOT
    path = source / "capture/oracle/C0000.csv"
    if operation == "missing":
        path.unlink()
    elif operation == "extra":
        (source / "undeclared.csv").write_bytes(b"extra")
    elif operation == "symlink":
        path.unlink()
        path.symlink_to(source / "capture/oracle/C0001.csv")
    elif operation == "directory-alias":
        directory = path.parent
        moved = packet / "outside"
        directory.rename(moved)
        directory.symlink_to(moved, target_is_directory=True)
    else:
        os.link(path, packet / "shared-inode.csv")
    with pytest.raises((ValueError, OSError)):
        capture.validated_native_capture(packet)


def test_member_mutation_after_first_read_refuses(
    packet: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = capture._file
    target = f"{capture.CAPTURE_ROOT}/capture/oracle/C0000.csv"
    mutated = False

    def read(repository: Path, relative: str) -> bytes:
        nonlocal mutated
        result = original(repository, relative)
        if relative == target and not mutated:
            (repository / relative).write_bytes(b"after-read mutation")
            mutated = True
        return result

    monkeypatch.setattr(capture, "_file", read)
    with pytest.raises(ValueError, match="changed during validation"):
        capture.validated_native_capture(packet)


@pytest.mark.parametrize(
    "field,value",
    [
        ("core_passed", True),
        ("domains_passed", 22),
        ("original_vectors_compared", 47),
        ("fresh_public_archive_count", 4),
        ("release_certificate", True),
        ("r_version", "4.5.0"),
        ("source_revision", "c" * 40),
    ],
)
def test_reauthenticated_fixture_scope_corruption_refuses(
    packet: Path, monkeypatch: pytest.MonkeyPatch, field: str, value: object
) -> None:
    path = packet / capture.CAPTURE_ROOT / "capture/capture.json"
    record = json.loads(path.read_bytes())
    record[field] = value
    spec = _write(path, record)
    monkeypatch.setattr(capture, "CAPTURE_MANIFEST_SHA256", spec["sha256"])
    with pytest.raises(ValueError, match="scope is invalid"):
        capture.validated_native_capture(packet)
