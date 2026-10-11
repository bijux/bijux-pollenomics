from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import signal
import subprocess
from types import ModuleType, SimpleNamespace, TracebackType

import pytest

ROOT = Path(__file__).resolve().parents[4]


def _builder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[ModuleType, Path]:
    spec = importlib.util.spec_from_file_location(
        "briefing_builder", ROOT / "presentation/build.py"
    )
    assert spec is not None and spec.loader is not None
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    source = tmp_path / "presentation"
    source.mkdir()
    tex = source / "big-picture.tex"
    tex.write_text("reviewed source", encoding="utf-8")
    lock = source / "source-lock.json"
    lock.write_text(
        json.dumps(
            {
                "decks": list(builder.DECKS),
                "source_date_epoch": 0,
                "sources": {
                    "presentation/big-picture.tex": hashlib.sha256(
                        tex.read_bytes()
                    ).hexdigest()
                },
            }
        )
    )
    monkeypatch.setattr(builder, "ROOT", tmp_path)
    monkeypatch.setattr(builder, "HERE", source)
    monkeypatch.setattr(builder, "LOCK", lock)
    monkeypatch.setattr(builder, "sys", SimpleNamespace(argv=["build.py"], stderr=None))
    return builder, tex


def test_changed_source_refuses_before_starting_compiler(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    builder, tex = _builder(tmp_path, monkeypatch)
    tex.write_text("changed source", encoding="utf-8")
    assert builder.main() == 1
    assert not (tmp_path / "artifacts").exists()


def test_timeout_kills_compiler_group_and_retains_failure_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    builder, _ = _builder(tmp_path, monkeypatch)
    calls: list[tuple[int, signal.Signals]] = []

    class Compiler:
        pid = 12345
        expired = False

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
            if not self.expired:
                self.expired = True
                assert timeout == 180
                raise subprocess.TimeoutExpired("latexmk", timeout)
            return "retained compiler output", None

    def launch(*args: object, **kwargs: object) -> Compiler:
        assert kwargs["start_new_session"] is True
        return Compiler()

    monkeypatch.setattr(builder.subprocess, "Popen", launch)
    monkeypatch.setattr(builder.shutil, "which", lambda _: "/tex/latexmk")
    monkeypatch.setattr(builder.os, "killpg", lambda pid, sig: calls.append((pid, sig)))
    assert builder.main() == 124
    assert calls == [(12345, signal.SIGKILL)]
    log = tmp_path / "artifacts/jobs/presentation/big-picture/build.log"
    assert "retained compiler output" in log.read_text()
    assert "exceeded 180 seconds" in log.read_text()
    assert not (tmp_path / "presentation/big-picture.pdf").exists()
