"""Keep source custody, atomic publication and Galician scientific refusals."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from importlib.machinery import ModuleSpec
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.source_completion.adna import (
    galician_sample_review as account,
)

ORIGINAL_PRODUCER = account._producer


@dataclass(frozen=True)
class Packet:
    repository: Path
    output: Path
    core: Path
    source: Path


@pytest.fixture
def packet(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Packet:
    repository = tmp_path / "repository"
    (repository / "artifacts").mkdir(parents=True)
    core = repository / account.CORE_PATH
    core.parent.mkdir(parents=True)
    core.write_bytes(b"original producer fixture")
    source = repository / "data/source.json"
    source.parent.mkdir()
    source.write_bytes(b"immutable fixture source")
    monkeypatch.setattr(account, "REPOSITORY_INPUTS", (Path("data/source.json"),))
    monkeypatch.setattr(account, "_producer", lambda root: core)
    monkeypatch.setattr(account, "write_galician_sample_species_review", _publish)
    return Packet(repository, repository / "artifacts/result", core, source)


def _publish(repository: Path, output: Path) -> None:
    assert (repository / "data/source.json").read_bytes()
    output.mkdir()
    (output / "samples.csv").write_bytes(b"source-owned samples\n")
    (output / "report.json").write_text(
        json.dumps(
            {
                "schema_version": "galician-cattle-sample-species-review.v1",
                "project_accession": "PRJNA705960",
                "sample_count": 11,
                "sample_species_counts": {"Bos primigenius": 3, "Bos taurus": 8},
                "admission_posture": account.ADMISSION,
            }
        ),
        encoding="utf-8",
    )


def _absent(packet: Packet) -> None:
    assert not packet.output.exists()
    assert list((packet.repository / "artifacts").iterdir()) == []


def test_atomic_account_preserves_source_bytes(packet: Packet) -> None:
    before = (packet.source.read_bytes(), packet.core.read_bytes())
    account.run(packet.repository, packet.output)
    assert {path.name for path in packet.output.iterdir()} == set(account.OUTPUTS)
    assert (packet.source.read_bytes(), packet.core.read_bytes()) == before
    report = json.loads((packet.output / "report.json").read_bytes())
    assert report["sample_species_counts"] == {"Bos primigenius": 3, "Bos taurus": 8}
    assert report["admission_posture"] == account.ADMISSION


@pytest.mark.parametrize("mutation", ["missing", "symlink", "directory"])
def test_invalid_source_refuses_before_writer(
    packet: Packet, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    packet.source.unlink()
    if mutation == "symlink":
        packet.source.symlink_to(packet.core)
    elif mutation == "directory":
        packet.source.mkdir()

    def refused(repository: Path, output: Path) -> None:
        raise AssertionError("writer must not run")

    monkeypatch.setattr(account, "write_galician_sample_species_review", refused)
    with pytest.raises(ReportRebuildError, match="regular|unreadable"):
        account.run(packet.repository, packet.output)
    _absent(packet)


@pytest.mark.parametrize("mutation", ["source", "core", "source-link"])
def test_changed_input_refuses_before_publication(
    packet: Packet, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    def drift(repository: Path, output: Path) -> None:
        _publish(repository, output)
        if mutation == "source-link":
            packet.source.unlink()
            packet.source.symlink_to(packet.core)
        else:
            (packet.source if mutation == "source" else packet.core).write_bytes(
                b"changed"
            )

    monkeypatch.setattr(account, "write_galician_sample_species_review", drift)
    with pytest.raises((ReportRebuildError, ValueError), match="regular|changed"):
        account.run(packet.repository, packet.output)
    _absent(packet)


@pytest.mark.parametrize(
    "mutation", ["extra", "missing", "symlink", "species", "admission", "count"]
)
def test_incomplete_or_promoted_output_refuses_atomically(
    packet: Packet, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    def changed(repository: Path, output: Path) -> None:
        _publish(repository, output)
        if mutation == "extra":
            (output / "unexpected.json").write_text("{}")
        elif mutation == "missing":
            (output / "samples.csv").unlink()
        elif mutation == "symlink":
            (output / "samples.csv").unlink()
            (output / "samples.csv").symlink_to(packet.source)
        else:
            report = json.loads((output / "report.json").read_bytes())
            if mutation == "species":
                report["sample_species_counts"] = {"Bos taurus": 11}
            elif mutation == "admission":
                report["admission_posture"]["atlas_point_admitted"] = True
            else:
                report["sample_count"] = True
            (output / "report.json").write_text(json.dumps(report))

    monkeypatch.setattr(account, "write_galician_sample_species_review", changed)
    with pytest.raises(
        (ReportRebuildError, ValueError), match="regular|population|accounting"
    ):
        account.run(packet.repository, packet.output)
    _absent(packet)


def test_writer_exception_leaves_no_output(
    packet: Packet, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(repository: Path, output: Path) -> None:
        _publish(repository, output)
        raise RuntimeError("original refusal")

    monkeypatch.setattr(account, "write_galician_sample_species_review", fail)
    with pytest.raises(RuntimeError, match="original refusal"):
        account.run(packet.repository, packet.output)
    _absent(packet)


def test_absent_guard_preserves_racing_existing_output(
    packet: Packet, monkeypatch: pytest.MonkeyPatch
) -> None:
    def occupied(repository: Path, output: Path) -> None:
        _publish(repository, output)
        packet.output.mkdir()
        (packet.output / "sentinel").write_bytes(b"user content")

    monkeypatch.setattr(account, "write_galician_sample_species_review", occupied)
    with pytest.raises(ReportRebuildError, match="absent"):
        account.run(packet.repository, packet.output)
    assert (packet.output / "sentinel").read_bytes() == b"user content"
    assert [path.name for path in packet.output.parent.iterdir()] == ["result"]


@pytest.mark.parametrize("destination", ["outside", "existing", "parent-link"])
def test_destination_guard_refuses_before_production(
    packet: Packet, destination: str
) -> None:
    output = packet.output
    if destination == "outside":
        output = packet.repository / "docs/report"
    elif destination == "existing":
        output.mkdir()
    else:
        link = packet.repository / "artifacts/linked"
        link.symlink_to(packet.repository / "data", target_is_directory=True)
        output = link / "result"
    with pytest.raises(ReportRebuildError):
        account.run(packet.repository, output)


def test_actual_original_writer_retains_governed_bytes() -> None:
    root = next(
        parent
        for parent in Path(__file__).parents
        if (parent / "configs/pytest.ini").is_file()
    )
    with TemporaryDirectory(
        prefix="galician-sample-review-", dir=root / "artifacts"
    ) as directory:
        output = Path(directory) / "products"
        account.run(root, output)
        family = root / "docs/report/source-relations/dna-scope/galician-cattle-samples"
        for name in sorted(account.OUTPUTS):
            assert (output / name).read_bytes() == (family / name).read_bytes()
        report = json.loads((output / "report.json").read_bytes())
        assert report["sample_count"] == 11
        assert report["paper_specimen_count"] == 18
        assert report["admission_posture"] == account.ADMISSION


@pytest.mark.parametrize("mutation", ["origin", "missing", "hash", "data-root"])
def test_original_producer_identity_refuses_foreign_sources(
    packet: Packet, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    origin = packet.core if mutation != "origin" else packet.source
    spec = ModuleSpec(account.CORE, loader=None, origin=str(origin))
    monkeypatch.setattr(
        importlib.util,
        "find_spec",
        lambda name: None if mutation == "missing" else spec,
    )
    monkeypatch.setattr(
        account,
        "CORE_SHA256",
        "0" * 64
        if mutation == "hash"
        else hashlib.sha256(packet.core.read_bytes()).hexdigest(),
    )
    monkeypatch.setattr(
        account,
        "repository_data_root",
        lambda path: (
            packet.repository / ("foreign-data" if mutation == "data-root" else "data")
        ),
    )
    with pytest.raises(ValueError, match="producer identity"):
        ORIGINAL_PRODUCER(packet.repository)
    _absent(packet)


def test_indirect_source_ancestor_refuses(packet: Packet) -> None:
    directory = packet.source.parent
    target = directory.with_name("original-data")
    directory.rename(target)
    directory.symlink_to(target, target_is_directory=True)
    with pytest.raises(ReportRebuildError, match="non-real ancestor"):
        account.run(packet.repository, packet.output)
    _absent(packet)


def test_cli_uses_explicit_repository_and_destination(
    packet: Packet, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[Path, Path]] = []

    def observe(repository: Path, output: Path) -> None:
        calls.append((repository, output))

    monkeypatch.setattr(account, "run", observe)
    monkeypatch.setattr(
        "sys.argv",
        [
            "galician-samples",
            "--repository",
            str(packet.repository),
            "--output",
            str(packet.output),
        ],
    )
    assert account.main() == 0
    assert calls == [(packet.repository, packet.output)]
