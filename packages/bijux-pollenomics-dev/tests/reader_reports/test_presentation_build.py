"""Current compilation uses five Git inputs, never a cited-report hash inventory."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import signal
import subprocess
from types import ModuleType, SimpleNamespace, TracebackType
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[4]
REVISION = "a" * 40


def _builder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[ModuleType, Path]:
    spec = importlib.util.spec_from_file_location(
        "briefing_builder", ROOT / "presentation/build.py"
    )
    assert spec is not None and spec.loader is not None
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    root = tmp_path / "repository"
    source = root / "presentation"
    source.mkdir(parents=True)
    for name in builder.COMPILED_INPUTS:
        (root / name).write_text("Explicit synthetic compiled input\n")
    for name in builder.DECKS:
        (source / f"{name}.pdf").write_bytes(b"old retained PDF")
    manifest = root / "reports/exports/site-downloads.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        json.dumps(
            {
                "schema_version": "scientific-reader-downloads.v1",
                "inputs": {
                    "presentation/source-lock.json": "old historical identity",
                    "reports/raw.json": "unchanged raw identity",
                },
                "files": [
                    {
                        "path": f"presentation/{name}.pdf",
                        "source_sha256": "old source hash",
                    }
                    for name in builder.DECKS
                ]
                + [
                    {
                        "path": "reports/raw.pdf",
                        "sha256": "retained distributed identity",
                    }
                ],
            }
        )
    )
    snapshot = {name: (root / name).read_bytes() for name in builder.COMPILED_INPUTS}

    def git(*args: str) -> bytes:
        if args[0] == "rev-parse":
            return (REVISION + "\n").encode()
        if args[0] == "merge-base":
            assert args == ("merge-base", "--is-ancestor", REVISION, "HEAD")
            return b""
        if args[0] == "ls-tree":
            return f"100644 blob {'c' * 40}\t{args[-1]}\n".encode()
        if args == ("show", "-s", "--format=%ct", REVISION):
            return b"123\n"
        assert args[0] == "show"
        revision, name = args[1].split(":", 1)
        assert revision == REVISION
        return bytes(snapshot[name])

    monkeypatch.setattr(builder, "ROOT", root)
    monkeypatch.setattr(builder, "HERE", source)
    monkeypatch.setattr(builder, "MANIFEST", manifest)
    monkeypatch.setattr(builder, "_git", git)
    monkeypatch.setattr(builder, "sys", SimpleNamespace(argv=["build.py"], stderr=None))
    return builder, source / "big-picture.tex"


def compiler(
    builder: ModuleType, monkeypatch: pytest.MonkeyPatch, outcome: str = "success"
) -> list[list[str]]:
    launches = []

    class Compiler:
        pid = 12345
        expired = False
        returncode: int | None = 0

        def __init__(self, argv: list[str], **kwargs: Any) -> None:
            assert kwargs["start_new_session"] is True
            assert kwargs["env"]["SOURCE_DATE_EPOCH"] == "123"
            self.argv = argv
            launches.append(argv)

        def __enter__(self) -> Compiler:
            return self

        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            traceback: TracebackType | None,
        ) -> None:
            pass

        def communicate(self, timeout: float | None = None) -> tuple[str, None]:
            if outcome == "timeout" and not self.expired:
                self.expired = True
                assert timeout == 180
                raise subprocess.TimeoutExpired("latexmk", timeout)
            if outcome == "timeout":
                return "retained compiler output", None
            name = Path(self.argv[-1]).stem
            output = builder.ROOT / self.argv[-2].removeprefix("-outdir=")
            if outcome == "nonzero" or (outcome == "partial" and len(launches) == 2):
                self.returncode = 7
                return "failed compiler", None
            if outcome == "incomplete":
                self.returncode = None
            if outcome != "missing_pdf":
                (output / f"{name}.pdf").write_bytes(b"%PDF-" + b"x" * 1200)
            if outcome != "missing_recorder":
                lines = [
                    f"INPUT presentation/{name}.tex",
                    "INPUT presentation/shared.tex",
                ]
                (output / f"{name}.aux").write_text("generated auxiliary")
                lines.append(f"INPUT {output / (name + '.aux')}")
                runtime = builder.ROOT.parent / "tex-runtime" / "system-font.tfm"
                runtime.parent.mkdir(exist_ok=True)
                runtime.write_bytes(b"Synthetic external TeX runtime resource")
                lines.append(f"INPUT {runtime}")
                if outcome == "undeclared":
                    (builder.ROOT / "reports/unlisted.tex").write_text(
                        "undeclared source"
                    )
                    lines.append("INPUT reports/unlisted.tex")
                if outcome == "wrong_deck":
                    lines.append(
                        "INPUT presentation/developer.tex"
                        if name != "developer"
                        else "INPUT presentation/big-picture.tex"
                    )
                if outcome == "alias":
                    alias = output / "shared-alias.tex"
                    alias.symlink_to(builder.HERE / "shared.tex")
                    lines.append(f"INPUT {alias}")
                (output / f"{name}.fls").write_text("\n".join(lines))
            if outcome == "source_changed" and len(launches) == 3:
                (builder.HERE / "shared.tex").write_text(
                    "changed during compiler execution"
                )
            return "retained compiler output", None

    monkeypatch.setattr(builder.subprocess, "Popen", Compiler)
    monkeypatch.setattr(builder.shutil, "which", lambda _: "/tex/latexmk")
    return launches


def test_changed_source_refuses_before_starting_compiler(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    builder, tex = _builder(tmp_path, monkeypatch)
    tex.write_text("changed source")
    assert builder.main() == 1
    assert not (builder.ROOT / "artifacts").exists()


def test_timeout_kills_compiler_group_and_retains_failure_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    builder, _ = _builder(tmp_path, monkeypatch)
    compiler(builder, monkeypatch, "timeout")
    calls = []
    monkeypatch.setattr(builder.os, "killpg", lambda pid, sig: calls.append((pid, sig)))
    before = builder.MANIFEST.read_bytes()
    assert builder.main() == 124
    assert calls == [(12345, signal.SIGKILL)]
    log = builder.ROOT / "artifacts/jobs/presentation/big-picture/build.log"
    assert (
        "retained compiler output" in log.read_text()
        and "exceeded 180 seconds" in log.read_text()
    )
    assert builder.MANIFEST.read_bytes() == before
    assert (builder.HERE / "big-picture.pdf").read_bytes() == b"old retained PDF"


def test_success_records_git_input_identity_and_preserves_raw_pdf_inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    builder, _ = _builder(tmp_path, monkeypatch)
    calls = compiler(builder, monkeypatch)
    assert builder.main() == 0
    actual = json.loads(builder.MANIFEST.read_bytes())
    assert actual["deck_build"]["source_revision"] == REVISION
    assert actual["deck_build"]["inputs"] == list(builder.COMPILED_INPUTS)
    assert actual["deck_build"]["source_date_epoch"] == 123
    assert actual["deck_build"]["compilers"] == [
        {"deck": name, "argv": argv, "actual_exit": 0}
        for name, argv in zip(builder.DECKS, calls, strict=True)
    ]
    assert actual["inputs"] == {"reports/raw.json": "unchanged raw identity"}
    assert actual["files"][-1] == {
        "path": "reports/raw.pdf",
        "sha256": "retained distributed identity",
    }
    assert all("source_sha256" not in row for row in actual["files"][:3])


@pytest.mark.parametrize(
    "outcome",
    [
        "nonzero",
        "partial",
        "incomplete",
        "missing_pdf",
        "missing_recorder",
        "undeclared",
        "wrong_deck",
        "alias",
        "source_changed",
    ],
)
def test_incomplete_or_unadmitted_compilation_never_publishes_new_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, outcome: str
) -> None:
    builder, _ = _builder(tmp_path, monkeypatch)
    compiler(builder, monkeypatch, outcome)
    before = builder.MANIFEST.read_bytes()
    assert builder.main() != 0
    assert builder.MANIFEST.read_bytes() == before
    assert all(
        (builder.HERE / f"{name}.pdf").read_bytes() == b"old retained PDF"
        for name in builder.DECKS
    )


@pytest.mark.parametrize("failure", ["missing", "nonancestor", "untracked"])
def test_source_identity_refuses_missing_or_unreachable_input_history(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    builder, tex = _builder(tmp_path, monkeypatch)
    if failure == "missing":
        tex.unlink()
    original = builder._git

    def git(*args: str) -> bytes:
        if failure == "nonancestor" and args[0] == "merge-base":
            raise subprocess.CalledProcessError(1, ["git", *args])
        if failure == "untracked" and args[0] == "ls-tree":
            return b""
        return bytes(original(*args))

    monkeypatch.setattr(builder, "_git", git)
    assert builder.main() == 1
