"""Synthetic routing and refusal checks for qualified DALMUT depth allocation."""

from __future__ import annotations

from collections.abc import Callable
import hashlib
import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.ci.report_rebuild import configured_owner as owner_runner
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import (
    QualifiedReportSources,
)
from bijux_pollenomics_dev.source_completion.neotoma import legacyage_depth_allocation

OWNER_ID = (
    "source-relations/neotoma/legacyage-chronology/depth-allocation/report-products"
)
FILES = (
    "table-s4-original-chronology.csv",
    "table-s5-legacyage-chronology.csv",
)


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
    descriptor = Path("configs/ci/qualified-report-sources/depth-fixture.json")
    file_rows = []
    inputs = {}
    for name in FILES:
        source = directory / name
        source.write_text(f"synthetic {name}\n", encoding="utf-8")
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        file_rows.append({"path": name, "sha256": digest})
        inputs[f"external/legacyage/pangaea-933132/{name}"] = source
    descriptor_file = repository / descriptor
    descriptor_file.parent.mkdir(parents=True)
    descriptor_file.write_text(
        json.dumps({"source_id": "legacyage/pangaea-933132", "files": file_rows}),
        encoding="utf-8",
    )
    inputs[descriptor.as_posix()] = descriptor_file
    samples = repository / legacyage_depth_allocation.SAMPLES
    samples.parent.mkdir(parents=True)
    samples.write_text('{"rows": []}\n', encoding="utf-8")
    replay = repository / legacyage_depth_allocation.REPLAY
    replay.parent.mkdir(parents=True)
    replay.write_text(
        "import argparse\n"
        "from pathlib import Path\n"
        f"SOURCE_SHA256 = {repr({row['path']: row['sha256'] for row in file_rows})}\n"
        f"SAMPLES_SHA256 = {repr(hashlib.sha256(samples.read_bytes()).hexdigest())}\n"
        "def main():\n"
        "    parser = argparse.ArgumentParser()\n"
        "    parser.add_argument('--repository')\n"
        "    parser.add_argument('--source-dir')\n"
        "    parser.add_argument('--output', type=Path)\n"
        "    args = parser.parse_args()\n"
        "    args.output.mkdir()\n"
        "    (args.output / 'report.json').write_text(args.source_dir + '\\n')\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        legacyage_depth_allocation,
        "REPLAY_SHA256",
        hashlib.sha256(replay.read_bytes()).hexdigest(),
    )
    calls: list[tuple[Path, Path]] = []

    def qualify(
        _repository: Path, source_root: Path, descriptor_path: Path
    ) -> QualifiedReportSources:
        calls.append((source_root, descriptor_path))
        return QualifiedReportSources(directory, inputs, "a" * 64)

    monkeypatch.setattr(
        legacyage_depth_allocation, "validated_external_report_sources", qualify
    )
    return repository, root, descriptor, calls


def _arguments(
    repository: Path, root: Path, descriptor: Path, output: Path
) -> list[str]:
    return [
        "--repository",
        str(repository),
        "--source-root",
        str(root),
        "--source-descriptor",
        descriptor.as_posix(),
        "--output",
        str(output),
    ]


def test_depth_allocation_routes_only_s4_s5_to_absent_artifact(
    packet: tuple[Path, Path, Path, list[tuple[Path, Path]]],
) -> None:
    repository, root, descriptor, calls = packet
    output = repository / "artifacts" / "source-products"
    assert (
        legacyage_depth_allocation.main(
            _arguments(repository, root, descriptor, output)
        )
        == 0
    )
    assert calls == [(root, descriptor), (root, descriptor)]
    assert {path.name for path in output.iterdir()} == {"report.json"}
    assert (output / "report.json").read_text() == (
        str(root / "legacyage" / "pangaea-933132") + "\n"
    )


def test_depth_allocation_refuses_changed_replay_and_source_map(
    packet: tuple[Path, Path, Path, list[tuple[Path, Path]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, root, descriptor, _ = packet
    output = repository / "artifacts" / "source-products"
    original = legacyage_depth_allocation.REPLAY_SHA256
    monkeypatch.setattr(legacyage_depth_allocation, "REPLAY_SHA256", "0" * 64)
    with pytest.raises(ReportRebuildError, match="replay read set changed"):
        legacyage_depth_allocation.main(
            _arguments(repository, root, descriptor, output)
        )
    monkeypatch.setattr(legacyage_depth_allocation, "REPLAY_SHA256", original)
    descriptor_file = repository / descriptor
    changed = json.loads(descriptor_file.read_text())
    changed["files"][0]["sha256"] = "0" * 64
    descriptor_file.write_text(json.dumps(changed))
    with pytest.raises(ReportRebuildError, match="S4/S5 read set differs"):
        legacyage_depth_allocation.main(
            _arguments(repository, root, descriptor, output)
        )
    assert not output.exists()


def test_depth_allocation_refuses_output_traversal_and_post_replay_tamper(
    packet: tuple[Path, Path, Path, list[tuple[Path, Path]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, root, descriptor, _ = packet
    traversal = repository / "artifacts" / ".." / "docs" / "result"
    with pytest.raises(ReportRebuildError, match="not canonical"):
        legacyage_depth_allocation.main(
            _arguments(repository, root, descriptor, traversal)
        )
    assert not (repository / "docs" / "result").exists()
    original: Callable[[Path, Path, Path], QualifiedReportSources] = vars(
        legacyage_depth_allocation
    )["validated_external_report_sources"]
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
        legacyage_depth_allocation,
        "validated_external_report_sources",
        changed_after,
    )
    with pytest.raises(ReportRebuildError, match="declaration changed"):
        legacyage_depth_allocation.main(
            _arguments(
                repository,
                root,
                descriptor,
                repository / "artifacts" / "source-products",
            )
        )
    assert calls == 2


def test_depth_allocation_configuration_declares_distinct_s4_s5_contract(
    packet: tuple[Path, Path, Path, list[tuple[Path, Path]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, root, fixture_descriptor, _ = packet
    product_root = Path(__file__).resolve().parents[3]
    descriptor = legacyage_depth_allocation.DESCRIPTOR
    (repository / descriptor).write_bytes(
        (repository / fixture_descriptor).read_bytes()
    )
    for name in ("report-owner-execution.json", "report-ownership.json"):
        source = json.loads((product_root / "configs/ci" / name).read_text())
        row = next(row for row in source["owners"] if row["owner_id"] == OWNER_ID)
        (repository / "configs/ci" / name).write_text(
            json.dumps(
                {
                    **{key: value for key, value in source.items() if key != "owners"},
                    "owners": [row],
                }
            ),
            encoding="utf-8",
        )
    declared = json.loads(
        (repository / "configs/ci/report-ownership.json").read_text()
    )["owners"][0]
    assert declared["role"] == "generated_owner"
    assert descriptor.as_posix() in declared["producer_inputs"]
    assert legacyage_depth_allocation.REPLAY in declared["producer_paths"]
    for relative in declared["producer_paths"]:
        path = repository / relative
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# maintained producer dependency\n", encoding="utf-8")
    output = repository / declared["paths"][0]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("tracked output\n", encoding="utf-8")
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
        owner_runner.resolve_configured_owner(repository, OWNER_ID)
    selected = owner_runner.resolve_configured_owner(
        repository, OWNER_ID, source_root=root
    )
    assert selected.command[-6:-2] == (
        "--source-descriptor",
        descriptor.as_posix(),
        "--source-root",
        str(root),
    )
    assert selected.source_paths == {
        "source-products/report.json": "source-relations/neotoma/legacyage-chronology/depth-allocation/report.json"
    }
    assert set(selected.inputs) >= {
        descriptor.as_posix(),
        *{f"external/legacyage/pangaea-933132/{name}" for name in FILES},
    }
