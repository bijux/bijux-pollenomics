"""Check author-snapshot custody and configured family output routing."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import runpy
import shutil
from types import ModuleType

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import (
    QualifiedReportSources,
)

SOURCE = (
    Path(__file__).resolve().parents[3]
    / "src/bijux_pollenomics_dev/source_completion/pollen_reconstruction/buffered_author_pollen.py"
)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "bijux_pollenomics_dev.source_completion.pollen_reconstruction.buffered_author_pollen",
        SOURCE,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_original_replay_binds_all_candidate_source_roots(tmp_path: Path) -> None:
    """Child imports resolve dev, host and LRA from the same candidate tree."""
    replay = (
        Path(__file__).resolve().parents[5]
        / "docs/report/pollen-reconstruction/author-buffered-pollen/replay.py"
    )
    fixture = (
        tmp_path
        / "repo/docs/report/pollen-reconstruction/author-buffered-pollen/replay.py"
    )
    fixture.parent.mkdir(parents=True)
    shutil.copy2(replay, fixture)
    namespace = runpy.run_path(str(fixture), run_name="fixture_replay")
    expected = (
        tmp_path / "repo/packages/bijux-pollenomics-dev/src",
        tmp_path / "repo/packages/bijux-pollenomics/src",
        tmp_path / "repo/packages/bijux-pollenomics-lra/src",
    )
    assert namespace["SOURCE_ROOTS"] == expected
    assert os.pathsep.join(str(path) for path in expected) != str(expected[0])


@pytest.fixture
def setup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[ModuleType, Path, Path, Path, Path]:
    """Use a small qualified-source stand-in; never read author counts."""
    module = _module()
    repository = tmp_path / "repo"
    family = repository / module.FAMILY
    family.mkdir(parents=True)
    replay = family / "replay.py"
    replay.write_text("print('fixture replay')\n")
    manifest = family / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "private_source_manifest_sha256": "placeholder",
                "producer_sha256": {str(module.FAMILY / "replay.py"): _digest(replay)},
            }
        )
    )
    for relative in module.RUN_INPUTS:
        path = repository / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture retained reference\n")
    source_root = tmp_path / "sources"
    source_dir = source_root / "landclim/author-reference"
    source_dir.mkdir(parents=True)
    snapshot = source_dir / "snapshot-manifest.json"
    snapshot.write_text("fixture manifest\n")
    descriptor = repository / module.DESCRIPTOR
    descriptor.parent.mkdir(parents=True, exist_ok=True)
    descriptor.write_text("fixture descriptor\n")
    monkeypatch.setattr(module, "DESCRIPTOR_SHA256", _digest(descriptor))
    monkeypatch.setattr(module, "SOURCE_MANIFEST_SHA256", _digest(snapshot))
    monkeypatch.setattr(module, "REPLAY_SHA256", _digest(replay))
    manifest.write_text(
        json.dumps(
            {
                "private_source_manifest_sha256": _digest(snapshot),
                "producer_sha256": {str(module.FAMILY / "replay.py"): _digest(replay)},
            }
        )
    )
    monkeypatch.setattr(module, "MANIFEST_SHA256", _digest(manifest))
    qualified = QualifiedReportSources(
        source_dir,
        {
            module.DESCRIPTOR.as_posix(): descriptor,
            **{f"external/fixture-{index}": snapshot for index in range(194)},
        },
        _digest(descriptor),
    )
    monkeypatch.setattr(
        module, "validated_external_report_sources", lambda *_args: qualified
    )
    output = repository / "artifacts/owner/producer-output/source-products"
    output.parent.mkdir(parents=True)
    return module, repository, source_root, descriptor, output


def test_replay_retains_intermediate_outside_owned_output(
    setup: tuple[ModuleType, Path, Path, Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A successful replay leaves only owned products in the producer tree."""
    module, repository, source_root, _, output = setup
    commands: list[list[str]] = []

    def child(command: list[str], **kwargs: object) -> None:
        commands.append(command)
        assert kwargs["cwd"] == repository
        assert command[command.index("--source-root") + 1] == str(
            source_root / "landclim/author-reference"
        )
        output.mkdir()
        (output / "report.json").write_text("fixture output\n")
        work = output.parent / "source-products-work/local-site-mean"
        work.mkdir(parents=True)
        (work / "scores.csv").write_text("fixture intermediate\n")

    monkeypatch.setattr(module.subprocess, "run", child)
    module.run(repository, source_root, module.DESCRIPTOR, output)
    assert len(commands) == 1
    assert [path.name for path in output.parent.iterdir()] == ["source-products"]
    assert (
        output.parent.parent / "retained-work/local-site-mean/scores.csv"
    ).read_text() == "fixture intermediate\n"


@pytest.mark.parametrize("bad", ["descriptor", "output", "replay"])
def test_refuses_wrong_descriptor_reused_output_or_changed_replay(
    setup: tuple[ModuleType, Path, Path, Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    bad: str,
) -> None:
    """No child runs after a wrong source or destination identity."""
    module, repository, source_root, _, output = setup
    commands: list[list[str]] = []
    monkeypatch.setattr(
        module.subprocess, "run", lambda command, **_: commands.append(command)
    )
    descriptor = module.DESCRIPTOR
    if bad == "descriptor":
        descriptor = Path("configs/ci/qualified-report-sources/unreviewed.json")
    elif bad == "output":
        output.mkdir()
    else:
        (repository / module.FAMILY / "replay.py").write_text("changed\n")
    with pytest.raises((ValueError, ReportRebuildError)):
        module.run(repository, source_root, descriptor, output)
    assert not commands


def test_refuses_source_mutation_after_child(
    setup: tuple[ModuleType, Path, Path, Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A result cannot pass if a retained source changes during execution."""
    module, repository, source_root, descriptor, output = setup

    def child(_command: list[str], **_kwargs: object) -> None:
        output.mkdir()
        (output / "report.json").write_text("fixture output\n")
        descriptor.write_text("changed descriptor\n")

    monkeypatch.setattr(module.subprocess, "run", child)
    with pytest.raises(ValueError, match="source changed"):
        module.run(repository, source_root, module.DESCRIPTOR, output)
    assert not (output.parent.parent / "retained-work").exists()


def test_refuses_symlinked_intermediate(
    setup: tuple[ModuleType, Path, Path, Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The retained work tree cannot hide an outside file behind a link."""
    module, repository, source_root, _, output = setup

    def child(_command: list[str], **_kwargs: object) -> None:
        output.mkdir()
        (output / "report.json").write_text("fixture output\n")
        baseline = output.parent / "source-products-work/local-site-mean"
        baseline.mkdir(parents=True)
        (baseline / "scores.csv").write_text("fixture intermediate\n")
        (baseline / "outside.csv").symlink_to(repository / "configs")

    monkeypatch.setattr(module.subprocess, "run", child)
    with pytest.raises(ValueError, match="non-real"):
        module.run(repository, source_root, module.DESCRIPTOR, output)
    assert not (output.parent.parent / "retained-work").exists()
