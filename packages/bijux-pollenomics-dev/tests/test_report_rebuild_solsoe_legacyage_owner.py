"""Focused routing and refusal tests for the qualified Solsø LegacyAge owner."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.ci.report_rebuild import configured_owner as owner_runner
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import (
    QualifiedReportSources,
)
from bijux_pollenomics_dev.source_completion.denmark import solsoe_legacyage_depth_join


@pytest.fixture
def packet(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path, Path, list[tuple[Path, Path]]]:
    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / "artifacts").mkdir()
    root = tmp_path / "qualified-sources"
    directory = root / "legacyage" / "pangaea-933132"
    directory.mkdir(parents=True)
    descriptor = Path("configs/ci/qualified-report-sources/solsoe.json")
    external = {}
    files = []
    for name in (
        "table-s5-legacyage-chronology.csv",
        "table-s6-chronology-comparison.csv",
    ):
        path = directory / name
        path.write_text(f"{name}\n", encoding="utf-8")
        files.append(
            {"path": name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        )
        external[f"external/legacyage/pangaea-933132/{name}"] = path
    descriptor_file = repository / descriptor
    descriptor_file.parent.mkdir(parents=True)
    descriptor_file.write_text(
        json.dumps({"source_id": "legacyage/pangaea-933132", "files": files}),
        encoding="utf-8",
    )
    external[descriptor.as_posix()] = descriptor_file
    neotoma_sha = {}
    for name in ("age_claims", "samples"):
        path = (
            repository / "data/neotoma/relational/surfaces" / name / "part-00001.json"
        )
        path.parent.mkdir(parents=True)
        path.write_text('{"rows": []}\n', encoding="utf-8")
        neotoma_sha[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    replay = repository / solsoe_legacyage_depth_join.REPLAY
    replay.parent.mkdir(parents=True)
    replay.write_text(
        "import argparse\n"
        "from pathlib import Path\n"
        f"SOURCE_SHA = {repr({row['path']: row['sha256'] for row in files})}\n"
        f"NEOTOMA_SHA = {repr(neotoma_sha)}\n"
        "def main():\n"
        "    parser = argparse.ArgumentParser()\n"
        "    parser.add_argument('--repository')\n"
        "    parser.add_argument('--source-dir')\n"
        "    parser.add_argument('--output', type=Path)\n"
        "    args = parser.parse_args()\n"
        "    args.output.mkdir()\n"
        "    for name in ('refused-samples.csv', 'report.json', 'sample-depth-join.csv'):\n"
        "        (args.output / name).write_text(args.source_dir + '\\n')\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        solsoe_legacyage_depth_join,
        "REPLAY_SHA256",
        hashlib.sha256(replay.read_bytes()).hexdigest(),
    )
    calls: list[tuple[Path, Path]] = []

    def qualify(
        _repository: Path, source_root: Path, descriptor_path: Path
    ) -> QualifiedReportSources:
        calls.append((source_root, descriptor_path))
        return QualifiedReportSources(directory, external, "a" * 64)

    monkeypatch.setattr(
        solsoe_legacyage_depth_join, "validated_external_report_sources", qualify
    )
    return repository, root, descriptor, calls


def _arguments(
    repository: Path, root: Path, descriptor: Path, output: Path
) -> list[str]:
    return [
        "--repository",
        str(repository),
        "--source-descriptor",
        descriptor.as_posix(),
        "--source-root",
        str(root),
        "--output",
        str(output),
    ]


def test_solsoe_routes_explicit_descriptor_and_writes_only_artifact_outputs(
    packet: tuple[Path, Path, Path, list[tuple[Path, Path]]],
) -> None:
    repository, root, descriptor, calls = packet
    output = repository / "artifacts" / "owner" / "source-products"
    output.parent.mkdir()
    assert (
        solsoe_legacyage_depth_join.main(
            _arguments(repository, root, descriptor, output)
        )
        == 0
    )
    assert calls == [(root, descriptor), (root, descriptor)]
    assert {p.name for p in output.iterdir()} == {
        "refused-samples.csv",
        "report.json",
        "sample-depth-join.csv",
    }
    assert {p.read_text() for p in output.iterdir()} == {
        str(root / "legacyage" / "pangaea-933132") + "\n"
    }


def test_solsoe_refuses_changed_replay_before_execution(
    packet: tuple[Path, Path, Path, list[tuple[Path, Path]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, root, descriptor, _ = packet
    output = repository / "artifacts" / "source-products"
    monkeypatch.setattr(solsoe_legacyage_depth_join, "REPLAY_SHA256", "0" * 64)
    with pytest.raises(ReportRebuildError, match="read set changed"):
        solsoe_legacyage_depth_join.main(
            _arguments(repository, root, descriptor, output)
        )
    assert not output.exists()


def test_solsoe_refuses_descriptor_mismatch_and_traversal(
    packet: tuple[Path, Path, Path, list[tuple[Path, Path]]],
) -> None:
    repository, root, descriptor, _ = packet
    output = repository / "artifacts" / "source-products"
    descriptor_file = repository / descriptor
    payload = json.loads(descriptor_file.read_text(encoding="utf-8"))
    payload["files"][0]["sha256"] = "0" * 64
    descriptor_file.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ReportRebuildError, match="source read set differs"):
        solsoe_legacyage_depth_join.main(
            _arguments(repository, root, descriptor, output)
        )
    assert not output.exists()
    traversal = repository / "artifacts" / ".." / "docs" / "result"
    with pytest.raises(ReportRebuildError, match="not canonical"):
        solsoe_legacyage_depth_join.main(
            _arguments(repository, root, descriptor, traversal)
        )
    assert not (repository / "docs" / "result").exists()


def test_solsoe_configured_owner_binds_descriptor_and_three_outputs(
    packet: tuple[Path, Path, Path, list[tuple[Path, Path]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, root, descriptor, _ = packet
    declared_descriptor = solsoe_legacyage_depth_join.DESCRIPTOR
    (repository / declared_descriptor).write_bytes(
        (repository / descriptor).read_bytes()
    )
    descriptor = declared_descriptor
    fixture_root = Path(__file__).resolve().parents[3]
    owner_id = (
        "countries/denmark/solsoe-source-lineage/legacyage-chronology/report-products"
    )
    for filename in ("report-owner-execution.json", "report-ownership.json"):
        source = json.loads((fixture_root / "configs/ci" / filename).read_text())
        row = next(item for item in source["owners"] if item["owner_id"] == owner_id)
        destination = repository / "configs/ci" / filename
        destination.write_text(
            json.dumps(
                {
                    **{key: value for key, value in source.items() if key != "owners"},
                    "owners": [row],
                }
            ),
            encoding="utf-8",
        )
    declaration = json.loads(
        (repository / "configs/ci/report-ownership.json").read_text()
    )["owners"][0]
    assert declaration["role"] == "generated_owner"
    assert descriptor.as_posix() in declaration["producer_inputs"]
    assert solsoe_legacyage_depth_join.REPLAY in declaration["producer_paths"]
    for relative in declaration["producer_paths"]:
        path = repository / relative
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# maintained producer dependency\n", encoding="utf-8")
    for relative in declaration["paths"]:
        path = repository / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("tracked output\n", encoding="utf-8")
    directory = root / "legacyage" / "pangaea-933132"
    inputs = {descriptor.as_posix(): repository / descriptor}
    for path in directory.iterdir():
        inputs[f"external/legacyage/pangaea-933132/{path.name}"] = path
    monkeypatch.setattr(owner_runner, "check_report_ownership", lambda *_a, **_k: None)
    monkeypatch.setattr(
        owner_runner,
        "validated_external_report_sources",
        lambda *_a: QualifiedReportSources(directory, inputs, "a" * 64),
    )
    with pytest.raises(ReportRebuildError, match="requires --source-root"):
        owner_runner.resolve_configured_owner(repository, owner_id)
    selected = owner_runner.resolve_configured_owner(
        repository, owner_id, source_root=root
    )
    assert selected.command[-6:-2] == (
        "--source-descriptor",
        descriptor.as_posix(),
        "--source-root",
        str(root),
    )
    assert set(selected.source_paths) == {
        "source-products/refused-samples.csv",
        "source-products/report.json",
        "source-products/sample-depth-join.csv",
    }


def test_solsoe_refuses_changed_qualification_after_replay(
    packet: tuple[Path, Path, Path, list[tuple[Path, Path]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, root, descriptor, _ = packet
    output = repository / "artifacts" / "source-products"
    original = solsoe_legacyage_depth_join.validated_external_report_sources
    calls = 0

    def changed_after(
        repository_path: Path, source_root: Path, descriptor_path: Path
    ) -> QualifiedReportSources:
        nonlocal calls
        calls += 1
        qualified = original(repository_path, source_root, descriptor_path)
        return QualifiedReportSources(
            qualified.directory,
            qualified.inputs,
            ("a" if calls == 1 else "b") * 64,
        )

    monkeypatch.setattr(
        solsoe_legacyage_depth_join,
        "validated_external_report_sources",
        changed_after,
    )
    with pytest.raises(ReportRebuildError, match="declaration changed"):
        solsoe_legacyage_depth_join.main(
            _arguments(repository, root, descriptor, output)
        )
    assert calls == 2
