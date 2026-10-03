"""Confine the retained two-grid candidate and author snapshot as one source set."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from bijux_pollenomics_dev.ci.report_rebuild import landclim_two_grid_packet as subject
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import (
    QualifiedReportSources,
)
from bijux_pollenomics_dev.ci.report_rebuild.source_qualification import (
    validated_external_report_sources,
)


@dataclass(frozen=True)
class Packet:
    repository: Path
    source_root: Path
    descriptor: Path
    run: Path


@pytest.fixture
def packet(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Packet:
    repository = tmp_path / "repository"
    source_root = tmp_path / "source"
    run = source_root / subject.SOURCE_ID / subject.RUN_PATH
    run.mkdir(parents=True)
    author_file = repository / subject.AUTHOR_DESCRIPTOR
    author_file.parent.mkdir(parents=True)
    author_file.write_bytes(b"author descriptor")
    author_sha = hashlib.sha256(author_file.read_bytes()).hexdigest()
    monkeypatch.setattr(subject, "AUTHOR_DESCRIPTOR_SHA256", author_sha)
    files = []
    for number in range(subject.FILE_COUNT):
        path = run / f"file-{number:03d}.json"
        path.write_bytes(f"value-{number}".encode())
        files.append(
            {
                "path": path.name,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "size": path.stat().st_size,
            }
        )
    descriptor = Path(
        "configs/ci/qualified-report-sources/landclim-two-grid-example.json"
    )
    target = repository / descriptor
    target.write_text(
        json.dumps(
            {
                "schema_version": subject.SCHEMA,
                "source_id": subject.SOURCE_ID,
                "run_path": subject.RUN_PATH,
                "author_descriptor": subject.AUTHOR_DESCRIPTOR.as_posix(),
                "author_descriptor_sha256": author_sha,
                "file_count": subject.FILE_COUNT,
                "files": files,
            }
        )
    )
    author_reference = source_root / "landclim/author-reference/reference/receipt.json"
    author_reference.parent.mkdir(parents=True)
    author_reference.write_bytes(b"retained author receipt")
    monkeypatch.setattr(
        subject,
        "validated_author_snapshot",
        lambda *_: QualifiedReportSources(
            source_root / "landclim/author-reference",
            {
                "external/landclim/author-reference/reference/receipt.json": author_reference
            },
            author_sha,
        ),
    )
    return Packet(repository, source_root, descriptor, run)


def validate(packet: Packet) -> QualifiedReportSources:
    return subject.validated_landclim_two_grid_packet(
        packet.repository, packet.source_root, packet.descriptor
    )


def test_unselected_packet_does_not_enter_source_dispatch_imports() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            "import sys; import bijux_pollenomics_dev.ci.report_rebuild.source_qualification; "
            "assert 'bijux_pollenomics_dev.ci.report_rebuild.landclim_two_grid_packet' "
            "not in sys.modules",
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr


def test_packet_schema_loads_only_on_selected_dispatch(packet: Packet) -> None:
    qualified = validated_external_report_sources(
        packet.repository, packet.source_root, packet.descriptor
    )
    assert len(qualified.inputs) == subject.FILE_COUNT + 2


def test_exact_population_and_author_receipt(packet: Packet) -> None:
    qualified = validate(packet)
    assert len(qualified.inputs) == subject.FILE_COUNT + 2
    assert (
        qualified.inputs[
            f"external/{subject.SOURCE_ID}/{subject.RUN_PATH}/file-000.json"
        ]
        == packet.run / "file-000.json"
    )
    assert (
        qualified.inputs[packet.descriptor.as_posix()]
        == packet.repository / packet.descriptor
    )


def test_changed_candidate_file_refused(packet: Packet) -> None:
    (packet.run / "file-000.json").write_bytes(b"changed")
    with pytest.raises(ReportRebuildError, match="bytes differ"):
        validate(packet)


def test_extra_candidate_file_refused(packet: Packet) -> None:
    (packet.run / "extra.json").write_bytes(b"extra")
    with pytest.raises(ReportRebuildError, match="population differs"):
        validate(packet)


def test_linked_candidate_refused(packet: Packet) -> None:
    source = packet.run / "file-000.json"
    source.rename(packet.run / "saved.json")
    source.symlink_to("saved.json")
    with pytest.raises(ReportRebuildError, match="real regular path"):
        validate(packet)


def test_changed_author_descriptor_refused(packet: Packet) -> None:
    (packet.repository / subject.AUTHOR_DESCRIPTOR).write_bytes(b"changed")
    with pytest.raises(ReportRebuildError, match="author descriptor identity"):
        validate(packet)


def test_duplicate_candidate_name_refused(packet: Packet) -> None:
    target = packet.repository / packet.descriptor
    value = json.loads(target.read_text())
    value["files"][1]["path"] = value["files"][0]["path"]
    target.write_text(json.dumps(value))
    with pytest.raises(ReportRebuildError, match="sorted and unique"):
        validate(packet)
