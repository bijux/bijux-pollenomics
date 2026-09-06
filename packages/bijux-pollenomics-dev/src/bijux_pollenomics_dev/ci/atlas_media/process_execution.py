"""Bounded subprocess execution and durable command receipts."""

from __future__ import annotations

import os
import signal
import subprocess  # nosec B404
import time
from datetime import UTC, datetime
from pathlib import Path

from .contracts import AtlasMediaError
from .gallery import canonical_json_bytes, sha256_file


def _write_json(path: Path, value: object) -> None:
    pending = path.with_suffix(path.suffix + ".pending")
    pending.write_bytes(canonical_json_bytes(value))
    pending.replace(path)


def _run_logged(
    command: tuple[str, ...],
    *,
    cwd: Path,
    stdout_path: Path,
    stderr_path: Path,
    timeout_seconds: float = 300,
) -> None:
    started_at = datetime.now(UTC).isoformat()
    started = time.perf_counter()
    timed_out = False
    process = subprocess.Popen(  # nosec B603
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=(os.name == "posix"),
    )
    termination = "not_required"
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
        returncode: int | None = process.returncode
    except subprocess.TimeoutExpired:
        timed_out = True
        stdout, stderr, termination = _terminate_process_tree(
            process,
            grace_seconds=min(2.0, max(0.2, timeout_seconds)),
        )
        returncode = None
    duration_seconds = time.perf_counter() - started
    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")
    receipt_path = stdout_path.with_name(
        stdout_path.name.replace(".stdout.log", ".execution.json")
    )
    _write_json(
        receipt_path,
        {
            "schema_version": "atlas-media-command-execution.v1",
            "command": list(command),
            "cwd": str(cwd.resolve()),
            "started_at": started_at,
            "duration_seconds": duration_seconds,
            "timeout_seconds": timeout_seconds,
            "timed_out": timed_out,
            "process_group_policy": (
                "new-session-terminate-then-kill.v1"
                if os.name == "posix"
                else "process-terminate-then-kill.v1"
            ),
            "termination": termination,
            "exit_status": returncode,
            "stdout_log": stdout_path.name,
            "stdout_byte_count": stdout_path.stat().st_size,
            "stdout_sha256": sha256_file(stdout_path),
            "stderr_log": stderr_path.name,
            "stderr_byte_count": stderr_path.stat().st_size,
            "stderr_sha256": sha256_file(stderr_path),
        },
    )
    if timed_out:
        raise AtlasMediaError(
            f"media command exceeded {timeout_seconds:g} seconds: {command[0]}"
        )
    if returncode != 0:
        raise AtlasMediaError(
            f"media command failed with exit {returncode}: {command[0]}"
        )


def _terminate_process_tree(
    process: subprocess.Popen[str], *, grace_seconds: float
) -> tuple[str, str, str]:
    """Bound TERM/KILL escalation and pipe cleanup for a timed-out process group."""
    if os.name == "posix":
        _signal_process_group(process.pid, signal.SIGTERM)
    else:
        process.terminate()
    try:
        process.wait(timeout=grace_seconds)
    except subprocess.TimeoutExpired:
        pass
    group_survived_term = os.name == "posix" and _process_group_exists(process.pid)
    if process.poll() is None or group_survived_term:
        if os.name == "posix":
            _signal_process_group(process.pid, signal.SIGKILL)
        else:
            process.kill()
        termination = "killed_process_group"
    else:
        termination = "terminated_process_group"
    try:
        stdout, stderr = process.communicate(timeout=grace_seconds)
    except subprocess.TimeoutExpired:
        for stream in (process.stdout, process.stderr):
            if stream is not None:
                stream.close()
        if process.poll() is None:
            process.kill()
            try:
                process.wait(timeout=grace_seconds)
            except subprocess.TimeoutExpired as error:
                raise AtlasMediaError(
                    "timed-out media command could not be reaped"
                ) from error
        stdout = ""
        stderr = "pipe drain abandoned after bounded process-group kill"
        termination += "_pipe_drain_abandoned"
    return stdout, stderr, termination


def _signal_process_group(process_group: int, requested_signal: signal.Signals) -> None:
    try:
        os.killpg(process_group, requested_signal)
    except ProcessLookupError:
        return


def _process_group_exists(process_group: int) -> bool:
    try:
        os.killpg(process_group, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True
