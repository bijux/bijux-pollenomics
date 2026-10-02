"""Retained interval scoring follows the frozen-support boundary and custody."""

from __future__ import annotations

from pathlib import Path
import runpy
import sys

import pytest

from bijux_pollenomics_dev.source_completion.nordic import (
    dalmutladdo_interval_sensitivity as producer,
)


def _repository(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "repository"
    source = root / producer.PRODUCER
    source.parent.mkdir(parents=True)
    source.write_text("# retained source fixture\n")
    (root / "artifacts").mkdir()
    return root, source


@pytest.mark.parametrize("failure", (None, "freeze", "score"))
def test_fixed_stages_preserve_arguments_and_refusals(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str | None
) -> None:
    root, source = _repository(tmp_path)
    output = root / "artifacts/owner/source-products"
    calls: list[list[str]] = []

    def invoke(path: str, *, run_name: str) -> None:
        assert path == str(source) and run_name == "__main__"
        calls.append(list(sys.argv))
        if sys.argv[1] == failure:
            raise ValueError("retained source refusal")
        if sys.argv[1] == "freeze":
            output.mkdir(parents=True)
            (output / "protocol.json").write_text("frozen support\n")
        else:
            assert (output / "protocol.json").read_text() == "frozen support\n"

    monkeypatch.setattr(runpy, "run_path", invoke)
    original = sys.argv
    if failure:
        with pytest.raises(ValueError, match="retained source refusal"):
            producer.run(root, output)
    else:
        producer.run(root, output)
    assert sys.argv is original
    stages = ("freeze",) if failure == "freeze" else ("freeze", "score")
    assert calls == [
        [str(source), stage, "--repository", str(root), "--output", str(output)]
        for stage in stages
    ]


@pytest.mark.parametrize(
    "unsafe",
    (
        "existing",
        "outside",
        "source-link",
        "source-parent",
        "artifact-root",
        "ancestor",
    ),
)
def test_unsafe_custody_refused_before_either_stage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, unsafe: str
) -> None:
    root, source = _repository(tmp_path)
    output = root / "artifacts/owner/source-products"
    if unsafe == "existing":
        output.mkdir(parents=True)
    elif unsafe == "outside":
        output = tmp_path / "outside"
    elif unsafe == "source-link":
        target = root / "source.py"
        source.rename(target)
        source.symlink_to(target)
    elif unsafe == "source-parent":
        target = source.parent.with_name("retained-source")
        source.parent.rename(target)
        source.parent.symlink_to(target, target_is_directory=True)
    elif unsafe == "artifact-root":
        target = root / "artifact-target"
        (root / "artifacts").rename(target)
        (root / "artifacts").symlink_to(target, target_is_directory=True)
    else:
        target = root / "artifacts/retained-owner"
        target.mkdir()
        (root / "artifacts/owner").symlink_to(target, target_is_directory=True)
    calls: list[object] = []
    monkeypatch.setattr(runpy, "run_path", lambda *a, **k: calls.append(True))
    with pytest.raises(ValueError):
        producer.run(root, output)
    assert not calls


def test_real_replay_restores_arguments_and_retains_stage_output(
    tmp_path: Path,
) -> None:
    root, source = _repository(tmp_path)
    source.write_text(
        "import pathlib, sys\n"
        "output = pathlib.Path(sys.argv[sys.argv.index('--output') + 1])\n"
        "if sys.argv[1] == 'freeze':\n"
        "    output.mkdir(parents=True)\n"
        "    (output / 'protocol.json').write_text('source-frozen')\n"
        "else:\n"
        "    assert (output / 'protocol.json').read_text() == 'source-frozen'\n"
        "    (output / 'report.json').write_text('source-scored')\n"
    )
    original = sys.argv
    output = root / "artifacts/owner/source-products"
    producer.run(root, output)
    assert sys.argv is original
    assert (output / "report.json").read_text() == "source-scored"


def test_cli_requires_paths_and_has_no_stage_or_method_override() -> None:
    for args in (
        ["--repository", "."],
        ["--output", "artifacts/output"],
        ["--repository", ".", "--output", "artifacts/output", "--stage", "score"],
        ["--repository", ".", "--output", "artifacts/output", "--method", "nearest"],
    ):
        with pytest.raises(SystemExit, match="2"):
            producer.main(args)
