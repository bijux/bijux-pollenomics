from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
import socket
import sys
import time
import venv

import pytest

from bijux_pollenomics_dev.ci.atlas_media import AtlasMediaError, process_execution


def test_bounded_argv_resolves_executable_and_captures_bytes(tmp_path: Path) -> None:
    completed = process_execution.run_bounded_argv(
        (sys.executable, "-c", "import sys;sys.stdout.buffer.write(b'bounded')"),
        cwd=tmp_path,
        timeout_seconds=5,
    )

    assert completed.command[0] == os.path.abspath(sys.executable)
    assert completed.returncode == 0
    assert completed.stdout == b"bounded"
    assert completed.stderr == b""
    assert completed.timed_out is False
    assert completed.termination == "not_required"


@pytest.mark.parametrize(
    "command",
    [(), ("definitely-not-a-bijux-executable",), (sys.executable, "bad\0argument")],
)
def test_bounded_argv_rejects_invalid_or_unavailable_commands(
    tmp_path: Path, command: tuple[str, ...]
) -> None:
    with pytest.raises(process_execution.BoundedProcessError):
        process_execution.run_bounded_argv(
            command,
            cwd=tmp_path,
            timeout_seconds=5,
        )


def test_bounded_argv_rejects_output_over_configured_limit(tmp_path: Path) -> None:
    with pytest.raises(process_execution.BoundedProcessError, match="stdout exceeded"):
        process_execution.run_bounded_argv(
            (sys.executable, "-c", "print('12345', end='')"),
            cwd=tmp_path,
            timeout_seconds=5,
            max_output_bytes=4,
        )


def test_logged_command_timeout_is_bounded_and_receipted(tmp_path: Path) -> None:
    root = tmp_path / "artifacts/media"
    root.mkdir(parents=True)
    stdout_path = root / "bounded.stdout.log"
    stderr_path = root / "bounded.stderr.log"

    with pytest.raises(AtlasMediaError, match="exceeded"):
        process_execution._run_logged(
            (sys.executable, "-c", "import time; time.sleep(2)"),
            cwd=tmp_path,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            timeout_seconds=0.05,
        )

    receipt = json.loads((root / "bounded.execution.json").read_text(encoding="utf-8"))
    assert receipt["command"] == [
        os.path.abspath(sys.executable),
        "-c",
        "import time; time.sleep(2)",
    ]
    assert receipt["timed_out"] is True
    assert receipt["exit_status"] is None
    assert receipt["duration_seconds"] < 1


def _announcing_descendant(port: int, *, resist_term: bool = False) -> str:
    setup = "import os,signal,socket,time;" if resist_term else "import os,socket,time;"
    if resist_term:
        setup += "signal.signal(signal.SIGTERM,signal.SIG_IGN);"
    return (
        setup + f"ready=socket.create_connection(('127.0.0.1',{port}),timeout=5);"
        "ready.sendall((str(os.getpid())+'\\n').encode('ascii'));ready.close();"
        "time.sleep(60)"
    )


def _wait_for_descendant_before_termination(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[socket.socket, list[tuple[int, float]]]:
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    listener.setblocking(False)
    ready_children: list[tuple[int, float]] = []
    terminate = process_execution._terminate_async_process_tree

    async def terminate_after_ready(
        process: asyncio.subprocess.Process, *, grace_seconds: float
    ) -> str:
        try:
            loop = asyncio.get_running_loop()
            connection, _ = await asyncio.wait_for(
                loop.sock_accept(listener), timeout=5
            )
            with connection:
                connection.setblocking(False)
                announced = bytearray()
                while b"\n" not in announced:
                    chunk = await asyncio.wait_for(
                        loop.sock_recv(connection, 64), timeout=1
                    )
                    if not chunk or len(announced) + len(chunk) > 64:
                        raise AssertionError("invalid descendant readiness message")
                    announced.extend(chunk)
            ready_children.append(
                (int(announced.partition(b"\n")[0]), time.perf_counter())
            )
        finally:
            # Even a failed readiness handshake must reap the spawned group.
            termination = await terminate(process, grace_seconds=grace_seconds)
        return termination

    monkeypatch.setattr(
        process_execution, "_terminate_async_process_tree", terminate_after_ready
    )
    return listener, ready_children


@pytest.mark.skipif(os.name != "posix", reason="POSIX process-group contract")
def test_logged_timeout_terminates_descendant_process_group(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "artifacts/media"
    root.mkdir(parents=True)
    listener, ready_children = _wait_for_descendant_before_termination(monkeypatch)
    command = (
        sys.executable,
        "-c",
        (
            "import subprocess,sys,time; "
            "subprocess.Popen([sys.executable,'-c',"
            f"{_announcing_descendant(listener.getsockname()[1])!r}]); "
            "time.sleep(60)"
        ),
    )

    with listener, pytest.raises(AtlasMediaError, match="exceeded"):
        process_execution._run_logged(
            command,
            cwd=tmp_path,
            stdout_path=root / "tree.stdout.log",
            stderr_path=root / "tree.stderr.log",
            timeout_seconds=0.2,
        )

    assert len(ready_children) == 1
    receipt = json.loads((root / "tree.execution.json").read_text(encoding="utf-8"))
    assert receipt["timed_out"] is True
    pid = ready_children[0][0]
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)


@pytest.mark.skipif(os.name != "posix", reason="POSIX process-group contract")
def test_timeout_kills_term_resistant_descendant_holding_output_pipes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "artifacts/media"
    root.mkdir(parents=True)
    listener, ready_children = _wait_for_descendant_before_termination(monkeypatch)
    command = (
        sys.executable,
        "-c",
        (
            "import subprocess,sys,time;"
            "subprocess.Popen([sys.executable,'-c',"
            f"{_announcing_descendant(listener.getsockname()[1], resist_term=True)!r}]);"
            "time.sleep(60)"
        ),
    )
    with listener, pytest.raises(AtlasMediaError, match="exceeded"):
        process_execution._run_logged(
            command,
            cwd=tmp_path,
            stdout_path=root / "resistant.stdout.log",
            stderr_path=root / "resistant.stderr.log",
            timeout_seconds=0.2,
        )

    assert len(ready_children) == 1
    assert time.perf_counter() - ready_children[0][1] < 2
    receipt = json.loads(
        (root / "resistant.execution.json").read_text(encoding="utf-8")
    )
    assert receipt["timed_out"] is True
    assert receipt["termination"] == "killed_process_group"
    pid = ready_children[0][0]
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)


@pytest.mark.skipif(os.name != "posix", reason="Actual symlinked virtualenv contract")
def test_symlinked_python_preserves_virtualenv_and_its_dependency(
    tmp_path: Path,
) -> None:
    environment = tmp_path / "isolated-venv"
    venv.EnvBuilder(with_pip=False, symlinks=True).create(environment)
    python = environment / "bin" / "python"
    assert python.is_symlink()
    inspected = process_execution.run_bounded_argv(
        (
            str(python),
            "-I",
            "-c",
            "import json,sys,sysconfig;print(json.dumps({'prefix':sys.prefix,'purelib':sysconfig.get_path('purelib')}))",
        ),
        cwd=tmp_path,
        timeout_seconds=10,
    )
    assert inspected.returncode == 0, inspected.stderr
    location = json.loads(inspected.stdout)
    assert Path(location["prefix"]) == environment
    dependency = Path(location["purelib"]) / "venv_only_dependency.py"
    dependency.write_text("VALUE = 'exclusive virtualenv dependency'\n")
    completed = process_execution.run_bounded_argv(
        (
            str(python),
            "-I",
            "-c",
            "import json,sys,venv_only_dependency as d;print(json.dumps({'prefix':sys.prefix,'dependency':d.__file__,'value':d.VALUE}))",
        ),
        cwd=tmp_path,
        timeout_seconds=10,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.command[0] == str(python)
    assert json.loads(completed.stdout) == {
        "prefix": str(environment),
        "dependency": str(dependency),
        "value": "exclusive virtualenv dependency",
    }


def test_path_lookup_preserves_executable_symlink_spelling(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    executable = tmp_path / "selected-python"
    executable.symlink_to(sys.executable)
    monkeypatch.setenv("PATH", str(tmp_path))
    completed = process_execution.run_bounded_argv(
        ("selected-python", "-c", "print('selected')"), cwd=tmp_path, timeout_seconds=5
    )
    assert completed.command[0] == str(executable)
    assert completed.returncode == 0 and completed.stdout == b"selected\n"


@pytest.mark.parametrize("kind", ["broken", "directory", "nonexecutable"])
def test_executable_link_target_must_still_be_available_regular_and_executable(
    tmp_path: Path, kind: str
) -> None:
    target = tmp_path / "target"
    if kind == "directory":
        target.mkdir()
    elif kind == "nonexecutable":
        target.write_text("not executable")
        target.chmod(0o600)
    executable = tmp_path / "selected"
    executable.symlink_to(target)
    with pytest.raises(process_execution.BoundedProcessError):
        process_execution.run_bounded_argv(
            (str(executable),), cwd=tmp_path, timeout_seconds=5
        )
