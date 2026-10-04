"""Byte custody and historical/current producer distinctions without envelope math."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest

from bijux_pollenomics_dev.source_completion.essd import uncertainty_custody as subject


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def identity(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


@pytest.fixture
def case(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    repository = tmp_path / "repository"
    (repository / "artifacts/owner").mkdir(parents=True)
    for relative in (*subject.INPUTS, subject.WRITER):
        path = repository / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(relative.name.encode() + b"\n")
    upstream_outputs = {
        name: identity(repository / subject.PROVENANCE / name)
        for name in subject.PROVENANCE_OUTPUTS
    }
    write_json(
        repository / subject.PROVENANCE / "manifest.json",
        {
            "schema_version": "landclim-published-window-provenance-custody.v1",
            "outputs": upstream_outputs,
        },
    )
    history = {
        "schema_version": "landclim-published-window-uncertainty-custody.v1",
        "inputs": {
            subject.CORE.as_posix(): {"bytes": 31, "sha256": "1" * 64},
            (
                subject.PROVENANCE / "paper-correspondence.csv"
            ).as_posix(): upstream_outputs["paper-correspondence.csv"],
            (subject.PROVENANCE / "report.json").as_posix(): upstream_outputs[
                "report.json"
            ],
        },
        "outputs": {
            name: identity(repository / subject.TARGET / name)
            for name in subject.OUTPUTS
        },
        "historical_comparison": {
            "relation": "Retained comparison; historical raw inputs not established"
        },
        "admission": "descriptive mean plus one reported SE envelopes only; no significance or vegetation accuracy",
    }
    write_json(repository / subject.HISTORY, history)
    monkeypatch.setattr(
        subject, "HISTORY_SHA256", identity(repository / subject.HISTORY)["sha256"]
    )
    return repository, repository / "artifacts/owner/products"


def test_exact_metadata_and_historical_identity_are_distinct(
    case: tuple[Path, Path],
) -> None:
    repository, output = case
    before = {
        path: (repository / path).read_bytes()
        for path in (*subject.INPUTS, subject.WRITER)
    }
    subject.run(repository, output)
    assert {path.name for path in output.iterdir()} == {"manifest.json"}
    manifest = json.loads((output / "manifest.json").read_bytes())
    assert manifest["historical_producer_identity"] == {
        "path": subject.CORE.as_posix(),
        "bytes": 31,
        "sha256": "1" * 64,
    }
    assert manifest["inputs"][subject.CORE.as_posix()] == identity(
        repository / subject.CORE
    )
    assert (
        manifest["historical_producer_identity"]["sha256"]
        != manifest["inputs"][subject.CORE.as_posix()]["sha256"]
    )
    assert manifest["custody_scope"] == subject.SCOPE
    assert manifest["custody_writer"] == {
        "path": subject.WRITER.as_posix(),
        **identity(repository / subject.WRITER),
    }
    assert manifest["outputs"] == {
        name: identity(repository / subject.TARGET / name) for name in subject.OUTPUTS
    }
    assert {path: (repository / path).read_bytes() for path in before} == before
    assert not (repository / subject.TARGET / "manifest.json").exists()


@pytest.mark.parametrize(
    "mutation",
    [
        "history",
        "upstream-data",
        "retained-output",
        "source-alias",
        "parent-alias",
        "upstream-count-bool",
        "upstream-hash",
        "upstream-population",
        "historical-count-bool",
        "historical-population",
    ],
)
def test_corrupt_input_refused_before_publication(
    case: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    repository, output = case
    history_path = repository / subject.HISTORY
    upstream_path = repository / subject.PROVENANCE / "manifest.json"
    if mutation in {"history", "upstream-data", "retained-output"}:
        target = (
            history_path
            if mutation == "history"
            else repository
            / (
                subject.PROVENANCE / "report.json"
                if mutation == "upstream-data"
                else subject.TARGET / "REPORT.md"
            )
        )
        target.write_bytes(target.read_bytes() + b"corruption")
    elif mutation == "source-alias":
        source = repository / subject.TARGET / "REPORT.md"
        physical = repository / "physical.md"
        source.rename(physical)
        source.symlink_to(physical)
    elif mutation == "parent-alias":
        parent = repository / subject.PROVENANCE
        physical = repository / "physical"
        parent.rename(physical)
        parent.symlink_to(physical, target_is_directory=True)
    elif mutation.startswith("upstream-"):
        upstream = json.loads(upstream_path.read_bytes())
        if mutation == "upstream-count-bool":
            upstream["outputs"]["report.json"]["bytes"] = True
        elif mutation == "upstream-hash":
            upstream["outputs"]["report.json"]["sha256"] = "f" * 64
        else:
            upstream["outputs"]["foreign.json"] = {"bytes": 0, "sha256": "0" * 64}
        write_json(upstream_path, upstream)
    else:
        history = json.loads(history_path.read_bytes())
        if mutation == "historical-count-bool":
            history["outputs"]["report.json"]["bytes"] = True
        else:
            history["outputs"].pop("REPORT.md")
        write_json(history_path, history)
        monkeypatch.setattr(subject, "HISTORY_SHA256", identity(history_path)["sha256"])
    with pytest.raises(ValueError):
        subject.run(repository, output)
    assert not output.exists()


@pytest.mark.parametrize(
    "mutation",
    [
        "foreign",
        "existing",
        "alias",
        "parent-alias",
        "source-change",
        "destination-appeared",
    ],
)
def test_publication_boundary_and_prepost_refusals(
    case: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    repository, output = case
    if mutation == "foreign":
        output = repository / "docs/result"
    elif mutation == "existing":
        output.mkdir()
    elif mutation == "alias":
        output.symlink_to(repository / "absent")
    elif mutation == "parent-alias":
        parent = output.parent
        physical = repository / "physical"
        parent.rename(physical)
        parent.symlink_to(physical, target_is_directory=True)
    else:
        original = subject.build_manifest

        def mutate(root: Path) -> dict[str, object]:
            result = original(root)
            if mutation == "source-change":
                (repository / subject.CORE).write_bytes(b"source changed")
            else:
                output.mkdir()
            return result

        monkeypatch.setattr(subject, "build_manifest", mutate)
    with pytest.raises(ValueError):
        subject.run(repository, output)
    assert not (output / "manifest.json").exists()


@pytest.mark.parametrize("competitor", ["directory", "manifest", "replacement"])
def test_exclusive_publication_preserves_competing_destination(
    case: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch, competitor: str
) -> None:
    repository, output = case
    if competitor == "directory":
        native_mkdir = os.mkdir
        competitor_inode: list[int] = []

        def mkdir(
            path: str | bytes | Path, mode: int = 0o777, *, dir_fd: int | None = None
        ) -> None:
            if Path(os.fsdecode(path)) == output:
                native_mkdir(path, mode, dir_fd=dir_fd)
                competitor_inode.append(output.stat().st_ino)
            native_mkdir(path, mode, dir_fd=dir_fd)

        monkeypatch.setattr(os, "mkdir", mkdir)
        with pytest.raises(ValueError, match="destination appeared"):
            subject.run(repository, output)
        assert output.stat().st_ino == competitor_inode[0]
        assert list(output.iterdir()) == []
    else:
        native_link = os.link
        moved = output.parent / "reserved-directory"

        def link(
            source: str | bytes | Path,
            destination: str | bytes | Path,
            *,
            src_dir_fd: int | None = None,
            dst_dir_fd: int | None = None,
            follow_symlinks: bool = True,
        ) -> None:
            if competitor == "replacement":
                output.rename(moved)
                output.mkdir()
            (output / "manifest.json").write_bytes(b"competitor manifest")
            native_link(
                source,
                destination,
                src_dir_fd=src_dir_fd,
                dst_dir_fd=dst_dir_fd,
                follow_symlinks=follow_symlinks,
            )

        monkeypatch.setattr(os, "link", link)
        with pytest.raises(FileExistsError if competitor == "manifest" else ValueError):
            subject.run(repository, output)
        assert (output / "manifest.json").read_bytes() == b"competitor manifest"
        if competitor == "replacement":
            assert (moved / "manifest.json").is_file()
            assert (moved / "manifest.json").read_bytes() != b"competitor manifest"
    assert not (repository / subject.TARGET / "manifest.json").exists()
