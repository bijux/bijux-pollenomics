"""Keep captured native execution distinct from each comparison rebuild."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypedDict

import pytest

from bijux_pollenomics_dev.lra_validation.native_reference.capture import NativeCapture
from bijux_pollenomics_dev.source_completion.method_certification import (
    native_r_comparison as producer,
)


class _ConsumerDeclaration(TypedDict):
    owner_id: str
    role: str
    paths: list[str]
    producer_paths: list[str]
    producer_inputs: list[str]


@pytest.fixture
def comparison(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path, NativeCapture, list[tuple[Path, ...]]]:
    repository = tmp_path / "repository"
    repository.mkdir()
    maintained = (
        Path(__file__).resolve().parents[5] / "configs/ci/report-ownership.json"
    )
    policy = json.loads(maintained.read_text())
    declaration: _ConsumerDeclaration = next(
        row
        for row in policy["owners"]
        if row["owner_id"] == "method-certification/current-r-oracle/report-products"
    )
    assert len(declaration["producer_paths"]) == 95
    assert len(declaration["producer_inputs"]) == 280
    assert {name for name in declaration["producer_paths"] if name.endswith(".R")} == {
        "packages/bijux-pollenomics-lra/tests/reference/lra_oracle/r_support.R",
        "packages/bijux-pollenomics-lra/tests/reference/lra_oracle/source_domains.R",
    }
    for name in declaration["producer_paths"] + declaration["producer_inputs"]:
        path = repository / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"synthetic declared input")
    (repository / "configs/ci/report-ownership.json").write_text(
        json.dumps({"owners": [declaration]})
    )
    output = repository / "artifacts/owner/producer-output/source-products"
    output.parent.mkdir(parents=True)
    source = NativeCapture(
        repository / "capture",
        repository / "public-archives",
        "a" * 40,
        "b" * 64,
        (),
        {},
        {},
    )
    monkeypatch.setattr(producer, "validated_native_capture", lambda _: source)
    calls: list[tuple[Path, ...]] = []

    def summarize(*paths: Path) -> dict[str, Any]:
        calls.append(paths)
        paths[3].mkdir()
        (paths[3] / "source-replay.json").write_text(
            json.dumps(
                {
                    "fresh_R_executed": True,
                    "original_R_to_current_R_compared": 48,
                    "source_revision": "d" * 40,
                }
            )
        )
        (paths[3] / "native.csv").write_bytes(b"value\n0.5\n")
        report = {"fresh_R_executed": True, "original_R_to_current_R_compared": 48}
        (paths[3] / "report.json").write_text(json.dumps(report))
        return report

    monkeypatch.setattr(producer, "summarize", summarize)
    return repository, output, source, calls


def test_comparison_uses_capture_and_never_claims_new_r(
    comparison: tuple[Path, Path, NativeCapture, list[tuple[Path, ...]]],
) -> None:
    repository, output, source, calls = comparison
    result = producer.build(repository, output)
    assert calls == [
        (
            repository,
            source.directory,
            repository
            / "docs/report/method-certification/original-r-reference/reference-bundle",
            output.parent.parent / "native-comparison",
            source.source_archives,
        )
    ]
    for name in ("report.json", "source-replay.json"):
        report = json.loads((output / name).read_text())
        assert report["fresh_R_executed"] is True
        assert report["fresh_R_executed_for_this_comparison"] is False
        assert (
            report["current_python_expectations_regenerated_for_this_comparison"]
            is False
        )
        assert "consumer_source_revision" not in report
        assert "source_revision" not in report
        assert len(report["consumer_inputs"]["code_sha256"]) == 95
        assert (
            report["consumer_inputs"]["capture_manifest_sha256"]
            == source.manifest_sha256
        )
        assert "neither R nor Python expectations are newly executed" in report["scope"]
        raw = json.loads(
            (output.parent.parent / "native-comparison/source-replay.json").read_text()
        )
        assert raw["source_revision"] == "d" * 40
        assert "consumer_inputs" not in raw
        assert report["native_capture_source_revision"] == source.source_revision
        assert report["native_capture_manifest_sha256"] == source.manifest_sha256
        assert (
            report["native_source_acquisition"]
            == "fresh_public_locked_archive_acquisition"
        )
        assert report["original_R_to_current_R_compared"] == 48
    assert result == json.loads((output / "report.json").read_text())
    assert {p.name for p in output.iterdir()} == {"report.json", "source-replay.json"}
    assert (
        output.parent.parent / "native-comparison/native.csv"
    ).read_bytes() == b"value\n0.5\n"
    assert {
        p.relative_to(output.parent).as_posix()
        for p in output.parent.rglob("*")
        if p.is_file()
    } == {"source-products/report.json", "source-products/source-replay.json"}


@pytest.mark.parametrize("kind", ["directory", "file", "broken-alias"])
def test_existing_output_refuses_before_source_reads(
    comparison: tuple[Path, Path, NativeCapture, list[tuple[Path, ...]]],
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
) -> None:
    repository, output, _, calls = comparison
    if kind == "directory":
        output.mkdir()
    elif kind == "file":
        output.write_bytes(b"user product")
    else:
        output.symlink_to(output.with_name("absent"))
    with pytest.raises(ValueError, match="must be absent"):
        producer.build(repository, output)
    assert calls == []


def test_mutated_capture_refuses_before_publication(
    comparison: tuple[Path, Path, NativeCapture, list[tuple[Path, ...]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, output, before, _ = comparison
    calls = 0

    def validate(_: Path) -> NativeCapture:
        nonlocal calls
        calls += 1
        return (
            before
            if calls == 1
            else NativeCapture(
                before.directory,
                before.source_archives,
                "c" * 40,
                before.manifest_sha256,
                (),
                {},
                {},
            )
        )

    monkeypatch.setattr(producer, "validated_native_capture", validate)
    with pytest.raises(ValueError, match="changed during comparison"):
        producer.build(repository, output)
    assert not (output / "report.json").exists()
    assert "native_capture_manifest_sha256" not in json.loads(
        (output.parent.parent / "native-comparison/source-replay.json").read_text()
    )


def test_source_mismatch_preserves_failure_without_rerun(
    comparison: tuple[Path, Path, NativeCapture, list[tuple[Path, ...]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, output, _, _ = comparison

    def stale(*_: Path) -> dict[str, Any]:
        raise ValueError("Current R/Python input changed")

    monkeypatch.setattr(producer, "summarize", stale)
    with pytest.raises(ValueError, match="input changed"):
        producer.build(repository, output)
    assert not output.exists()


@pytest.mark.parametrize(
    "operation", ["source-route", "sidecar-collision", "parent-alias", "lexical-escape"]
)
def test_owned_destination_confinement_refuses(
    comparison: tuple[Path, Path, NativeCapture, list[tuple[Path, ...]]], operation: str
) -> None:
    repository, output, _, calls = comparison
    if operation == "source-route":
        output = repository / "data/producer-output/source-products"
        output.parent.mkdir(parents=True)
    elif operation == "sidecar-collision":
        (output.parent.parent / "native-comparison").mkdir()
    elif operation == "parent-alias":
        parent = output.parent
        moved = parent.with_name("real-producer")
        parent.rename(moved)
        parent.symlink_to(moved, target_is_directory=True)
    else:
        output = repository / "artifacts/../data/producer-output/source-products"
        output.parent.mkdir(parents=True)
    with pytest.raises(ValueError):
        producer.build(repository, output)
    assert calls == []
    assert not output.exists()


def test_consumer_head_stays_raw_while_governed_bytes_are_content_bound(
    comparison: tuple[Path, Path, NativeCapture, list[tuple[Path, ...]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, _, _, _ = comparison
    outputs: list[Path] = []
    for index, revision in enumerate(("c" * 40, "d" * 40)):

        def retained(*paths: Path, captured_revision: str = revision) -> dict[str, Any]:
            paths[3].mkdir()
            report = {
                "fresh_R_executed": True,
                "private_source_custody": ["raw classification"],
                "original_R_to_current_R_compared": 48,
            }
            (paths[3] / "report.json").write_text(json.dumps(report))
            (paths[3] / "source-replay.json").write_text(
                json.dumps(
                    {"source_revision": captured_revision, "fresh_R_executed": True}
                )
            )
            (paths[3] / "native.csv").write_bytes(b"value\n0.5\n")
            return report

        monkeypatch.setattr(producer, "summarize", retained)
        output = (
            repository / f"artifacts/consumer-{index}/producer-output/source-products"
        )
        output.parent.mkdir(parents=True)
        producer.build(repository, output)
        outputs.append(output)
        raw = json.loads(
            (output.parent.parent / "native-comparison/source-replay.json").read_text()
        )
        assert raw["source_revision"] == revision
        assert "consumer_inputs" not in raw
        assert json.loads(
            (output.parent.parent / "native-comparison/report.json").read_text()
        )["private_source_custody"] == ["raw classification"]
    for name in ("report.json", "source-replay.json"):
        assert (outputs[0] / name).read_bytes() == (outputs[1] / name).read_bytes()
        assert "private_source_custody" not in json.loads(
            (outputs[0] / name).read_text()
        )


@pytest.mark.parametrize(
    "name",
    [
        "data/method-certification/native-r/capture/oracle/C0000.csv",
        "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/native_reference/capture.py",
        "configs/ci/report-ownership.json",
    ],
)
def test_protected_consumer_mutation_refuses_publication(
    comparison: tuple[Path, Path, NativeCapture, list[tuple[Path, ...]]],
    monkeypatch: pytest.MonkeyPatch,
    name: str,
) -> None:
    repository, output, _, _ = comparison

    def changed(*paths: Path) -> dict[str, Any]:
        paths[3].mkdir()
        (paths[3] / "source-replay.json").write_text(
            json.dumps({"source_revision": "d" * 40})
        )
        path = repository / name
        if name.endswith(".json"):
            policy = json.loads(path.read_text())
            policy["changed"] = True
            path.write_text(json.dumps(policy))
        else:
            path.write_bytes(b"changed protected consumer bytes")
        return {}

    monkeypatch.setattr(producer, "summarize", changed)
    with pytest.raises(ValueError, match="source changed"):
        producer.build(repository, output)
    assert not output.exists()


@pytest.mark.parametrize(
    "condition",
    [
        "own-output",
        "overlap",
        "duplicate",
        "code-count",
        "missing-policy",
        "data-count",
        "alias",
        "escape",
    ],
)
def test_consumer_contract_refuses_before_comparison(
    comparison: tuple[Path, Path, NativeCapture, list[tuple[Path, ...]]],
    condition: str,
) -> None:
    repository, output, _, calls = comparison
    policy_path = repository / "configs/ci/report-ownership.json"
    policy = json.loads(policy_path.read_text())
    row = policy["owners"][0]
    if condition == "own-output":
        row["producer_inputs"][1] = row["paths"][0]
    elif condition == "overlap":
        row["producer_inputs"][1] = row["producer_paths"][0]
    elif condition == "duplicate":
        row["producer_paths"][0] = row["producer_paths"][1]
    elif condition == "code-count":
        row["producer_paths"].pop()
    elif condition == "missing-policy":
        row["producer_inputs"].remove("configs/ci/report-ownership.json")
    elif condition == "data-count":
        row["producer_inputs"].pop()
    elif condition == "escape":
        row["producer_inputs"][1] = "../outside"
    else:
        target = (
            repository / "data/method-certification/native-r/capture/oracle/C0000.csv"
        )
        target.unlink()
        target.symlink_to(repository / row["producer_paths"][0])
    policy_path.write_text(json.dumps(policy))
    with pytest.raises(ValueError):
        producer.build(repository, output)
    assert calls == []
    assert not output.exists()
