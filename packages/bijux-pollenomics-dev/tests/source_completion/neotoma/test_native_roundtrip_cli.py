"""Native hierarchy reports preserve the maintained writer's bytes and refusals."""

from __future__ import annotations

from pathlib import Path
import runpy

import pytest

from bijux_pollenomics_dev.source_completion.neotoma import native_roundtrip as adapter


def _repository(tmp_path: Path) -> tuple[Path, Path]:
    repo = tmp_path / "repository"
    source = repo / adapter.PRODUCER
    source.parent.mkdir(parents=True)
    source.write_text("# source fixture\n")
    (repo / "artifacts").mkdir()
    return repo, source


@pytest.mark.parametrize("fails", (False, True))
def test_native_stdout_and_failure_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fails: bool
) -> None:
    repo, source = _repository(tmp_path)
    calls: list[tuple[str, str]] = []

    def writer() -> None:
        print('{"status": "complete", "source": "é"}')
        if fails:
            raise SystemExit(1)

    def load(path: str, *, run_name: str) -> dict[str, object]:
        calls.append((path, run_name))
        return {"main": writer}

    monkeypatch.setattr(runpy, "run_path", load)
    output = repo / "artifacts/owner/report.json"
    if fails:
        with pytest.raises(SystemExit, match="1"):
            adapter.run(repo, output)
        assert not output.exists()
    else:
        adapter.run(repo, output)
        assert output.read_bytes() == '{"status": "complete", "source": "é"}\n'.encode()
    assert calls == [(str(source), "_native_roundtrip_owner")]


@pytest.mark.parametrize(
    "unsafe",
    (
        "existing",
        "outside",
        "source-link",
        "source-parent-link",
        "artifact-link",
        "output-parent-link",
    ),
)
def test_unsafe_source_or_destination_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, unsafe: str
) -> None:
    repo, source = _repository(tmp_path)
    output = repo / "artifacts/owner/report.json"
    if unsafe == "existing":
        output.parent.mkdir()
        output.write_text("existing")
    elif unsafe == "outside":
        output = tmp_path / "outside.json"
    elif unsafe == "source-link":
        other = repo / "other.py"
        other.write_text(source.read_text())
        source.unlink()
        source.symlink_to(other)
    elif unsafe == "source-parent-link":
        other = source.parent.with_name("native-source")
        source.parent.rename(other)
        source.parent.symlink_to(other, target_is_directory=True)
    elif unsafe == "artifact-link":
        (repo / "artifacts").rename(repo / "artifact-target")
        (repo / "artifacts").symlink_to(
            repo / "artifact-target", target_is_directory=True
        )
    else:
        target = repo / "artifacts/target"
        target.mkdir()
        output.parent.symlink_to(target, target_is_directory=True)
    called: list[object] = []
    monkeypatch.setattr(runpy, "run_path", lambda *a, **k: called.append(True))
    with pytest.raises(ValueError, match="invalid|symlink|outside|absent"):
        adapter.run(repo, output)
    assert not called
