"""Refuse altered local science captures, invented rights and ambiguous physical stores."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.source_contracts import (
    literal_pair_counting as contract,
)


@pytest.fixture
def packet(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path, Path]:
    repository = tmp_path / "repository"
    repository.mkdir()
    root = repository / "artifacts/source-store"
    directory = root / contract.SOURCE_ID
    directory.mkdir(parents=True)
    report = {"family_native_sample_population": 3}
    raw = json.dumps(report).encode()
    (directory / "report.json").write_bytes(raw)
    observer = {
        "native_exit": 0,
        "all_native_samples": 3,
        "report_sha256": hashlib.sha256(raw).hexdigest(),
    }
    terminal = {
        "native_exit": 0,
        "plan_sha256": contract.PLAN_SHA256,
        "stages": [{"native_exit": 0, "timeout": False} for _ in range(5)],
    }
    for name, value in [
        ("terminal.json", terminal),
        ("independent-verification.json", observer),
        ("protocol.json", {}),
    ]:
        (directory / name).write_text(json.dumps(value))
    (directory / "method.md").write_text("Source-free custody fixture")
    members = [
        {
            "path": p.name,
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "size": p.stat().st_size,
        }
        for p in sorted(directory.iterdir())
    ]
    monkeypatch.setattr(contract, "MEMBERS", members)
    descriptor = Path("configs/ci/report-sources/pair.json")
    (repository / descriptor).parent.mkdir(parents=True)
    (repository / descriptor).write_text(json.dumps(contract.expected_descriptor()))
    return repository, root, descriptor


def test_exact_artifact_store_and_all_five_members_are_admitted(
    packet: tuple[Path, Path, Path],
) -> None:
    repository, root, descriptor = packet
    result = contract.validated_pair_counting_capture(repository, root, descriptor)
    assert result.directory == root / contract.SOURCE_ID and len(result.inputs) == 6
    assert (
        result.descriptor_sha256
        == hashlib.sha256((repository / descriptor).read_bytes()).hexdigest()
    )


@pytest.mark.parametrize(
    "name",
    [
        "report.json",
        "terminal.json",
        "independent-verification.json",
        "protocol.json",
        "method.md",
    ],
)
def test_any_member_change_refuses(packet: tuple[Path, Path, Path], name: str) -> None:
    repository, root, descriptor = packet
    with (root / contract.SOURCE_ID / name).open("ab") as stream:
        stream.write(b"changed")
    with pytest.raises(ReportRebuildError, match="bytes differ"):
        contract.validated_pair_counting_capture(repository, root, descriptor)


@pytest.mark.parametrize(
    "field,value",
    [
        ("scientific_admission", True),
        ("rights_admission", True),
        ("http_retrieval_claim", True),
        ("release_admission", 0),
        ("source_id", "another/source"),
        ("native_plan_sha256", "0" * 64),
        ("custody", "HTTP acquired"),
    ],
)
def test_invented_claim_or_source_identity_refuses(
    packet: tuple[Path, Path, Path], field: str, value: object
) -> None:
    repository, root, descriptor = packet
    payload = json.loads((repository / descriptor).read_bytes())
    payload[field] = value
    (repository / descriptor).write_text(json.dumps(payload))
    with pytest.raises(ReportRebuildError, match="identity or limits"):
        contract.validated_pair_counting_capture(repository, root, descriptor)


def test_descriptor_duplicate_key_refuses(packet: tuple[Path, Path, Path]) -> None:
    repository, root, descriptor = packet
    (repository / descriptor).write_text(
        '{"schema_version":"one","schema_version":"two"}'
    )
    with pytest.raises(ReportRebuildError, match="duplicate"):
        contract.validated_pair_counting_capture(repository, root, descriptor)


def test_nonartifact_repository_source_root_refuses(
    packet: tuple[Path, Path, Path],
) -> None:
    repository, _, descriptor = packet
    with pytest.raises(ReportRebuildError, match="explicit artifact or external"):
        contract.validated_pair_counting_capture(repository, repository, descriptor)


def test_symlink_member_refuses(
    packet: tuple[Path, Path, Path], tmp_path: Path
) -> None:
    repository, root, descriptor = packet
    member = root / contract.SOURCE_ID / "method.md"
    other = tmp_path / "method"
    other.write_bytes(member.read_bytes())
    member.unlink()
    member.symlink_to(other)
    with pytest.raises(ReportRebuildError, match="regular"):
        contract.validated_pair_counting_capture(repository, root, descriptor)
