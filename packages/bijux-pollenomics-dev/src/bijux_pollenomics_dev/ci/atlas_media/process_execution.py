"""Bounded argv-only process execution and durable command receipts."""

from __future__ import annotations

import asyncio
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime
import os
from pathlib import Path
import shutil
import signal
import tempfile
import time
from typing import BinaryIO

from .contracts import AtlasMediaError
from .gallery import canonical_json_bytes, sha256_file

_DEFAULT_MAX_OUTPUT_BYTES = 64 * 1024 * 1024
_TERMINATION_GRACE_SECONDS = 2.0


class BoundedProcessError(RuntimeError):
    """Report an invalid or unavailable bounded process invocation."""


@dataclass(frozen=True, slots=True)
class CompletedCommand:
    """Captured result of one bounded argv-only process invocation."""

    command: tuple[str, ...]
    returncode: int
    stdout: bytes
    stderr: bytes
    duration_seconds: float
    timed_out: bool
    termination: str


def run_bounded_argv(
    command: tuple[str, ...],
    *,
    cwd: Path,
    timeout_seconds: float,
    max_output_bytes: int = _DEFAULT_MAX_OUTPUT_BYTES,
) -> CompletedCommand:
    """Execute validated argv without a shell and enforce one wall-clock deadline."""
    validated_command = _validated_command(command)
    working_directory = _validated_working_directory(cwd)
    if timeout_seconds <= 0:
        raise BoundedProcessError("timeout_seconds must be positive")
    if max_output_bytes <= 0:
        raise BoundedProcessError("max_output_bytes must be positive")
    return asyncio.run(
        _run_bounded_argv(
            validated_command,
            cwd=working_directory,
            timeout_seconds=timeout_seconds,
            max_output_bytes=max_output_bytes,
        )
    )


async def _run_bounded_argv(
    command: tuple[str, ...],
    *,
    cwd: Path,
    timeout_seconds: float,
    max_output_bytes: int,
) -> CompletedCommand:
    started = time.perf_counter()
    with (
        tempfile.TemporaryFile() as stdout_file,
        tempfile.TemporaryFile() as stderr_file,
    ):
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                cwd=str(cwd),
                stdout=stdout_file,
                stderr=stderr_file,
                start_new_session=(os.name == "posix"),
            )
        except OSError as error:
            raise BoundedProcessError(
                f"process executable could not be started: {command[0]}"
            ) from error
        timed_out = False
        termination = "not_required"
        try:
            await asyncio.wait_for(process.wait(), timeout=timeout_seconds)
        except TimeoutError:
            timed_out = True
            termination = await _terminate_async_process_tree(
                process,
                grace_seconds=min(
                    _TERMINATION_GRACE_SECONDS,
                    max(0.2, timeout_seconds),
                ),
            )
        duration_seconds = time.perf_counter() - started
        stdout = _read_bounded_output(
            stdout_file, max_output_bytes=max_output_bytes, label="stdout"
        )
        stderr = _read_bounded_output(
            stderr_file, max_output_bytes=max_output_bytes, label="stderr"
        )
    return CompletedCommand(
        command=command,
        returncode=process.returncode if process.returncode is not None else -1,
        stdout=stdout,
        stderr=stderr,
        duration_seconds=duration_seconds,
        timed_out=timed_out,
        termination=termination,
    )


def _validated_command(command: tuple[str, ...]) -> tuple[str, ...]:
    if not command or any(not argument or "\0" in argument for argument in command):
        raise BoundedProcessError("command must contain non-empty NUL-free argv")
    requested = Path(command[0])
    discovered = str(requested) if requested.is_absolute() else shutil.which(command[0])
    if discovered is None:
        raise BoundedProcessError(f"process executable is unavailable: {command[0]}")
    try:
        executable = Path(discovered).resolve(strict=True)
    except OSError as error:
        raise BoundedProcessError(
            f"process executable is unavailable: {command[0]}"
        ) from error
    if not executable.is_file() or not os.access(executable, os.X_OK):
        raise BoundedProcessError(
            f"process executable must be an executable file: {executable}"
        )
    return (str(executable), *command[1:])


def _validated_working_directory(cwd: Path) -> Path:
    try:
        resolved = cwd.resolve(strict=True)
    except OSError as error:
        raise BoundedProcessError("process working directory is unavailable") from error
    if not resolved.is_dir():
        raise BoundedProcessError("process working directory must be a directory")
    return resolved


def _read_bounded_output(
    stream: BinaryIO, *, max_output_bytes: int, label: str
) -> bytes:
    stream.seek(0)
    payload = stream.read(max_output_bytes + 1)
    if len(payload) > max_output_bytes:
        raise BoundedProcessError(f"process {label} exceeded {max_output_bytes} bytes")
    return payload


async def _terminate_async_process_tree(
    process: asyncio.subprocess.Process, *, grace_seconds: float
) -> str:
    if os.name == "posix":
        _signal_process_group(process.pid, signal.SIGTERM)
    else:
        process.terminate()
    with suppress(TimeoutError):
        await asyncio.wait_for(process.wait(), timeout=grace_seconds)
    group_survived_term = os.name == "posix" and _process_group_exists(process.pid)
    if process.returncode is None or group_survived_term:
        if os.name == "posix":
            _signal_process_group(process.pid, signal.SIGKILL)
        else:
            process.kill()
        termination = "killed_process_group"
    else:
        termination = "terminated_process_group"
    try:
        await asyncio.wait_for(process.wait(), timeout=grace_seconds)
    except TimeoutError as error:
        raise BoundedProcessError("timed-out process could not be reaped") from error
    if os.name == "posix":
        await _require_process_group_exit(process.pid, timeout_seconds=grace_seconds)
    return termination


async def _require_process_group_exit(
    process_group: int, *, timeout_seconds: float
) -> None:
    deadline = asyncio.get_running_loop().time() + timeout_seconds
    while _process_group_exists(process_group):
        if asyncio.get_running_loop().time() >= deadline:
            raise BoundedProcessError("timed-out process group could not be terminated")
        await asyncio.sleep(0.02)


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
    try:
        completed = run_bounded_argv(
            command,
            cwd=cwd,
            timeout_seconds=timeout_seconds,
        )
    except BoundedProcessError as error:
        raise AtlasMediaError("media command could not be executed safely") from error
    stdout_path.write_bytes(completed.stdout)
    stderr_path.write_bytes(completed.stderr)
    receipt_path = stdout_path.with_name(
        stdout_path.name.replace(".stdout.log", ".execution.json")
    )
    _write_json(
        receipt_path,
        {
            "schema_version": "atlas-media-command-execution.v1",
            "command": list(completed.command),
            "cwd": str(cwd.resolve()),
            "started_at": started_at,
            "duration_seconds": completed.duration_seconds,
            "timeout_seconds": timeout_seconds,
            "timed_out": completed.timed_out,
            "process_group_policy": (
                "new-session-terminate-then-kill.v1"
                if os.name == "posix"
                else "process-terminate-then-kill.v1"
            ),
            "termination": completed.termination,
            "exit_status": None if completed.timed_out else completed.returncode,
            "stdout_log": stdout_path.name,
            "stdout_byte_count": stdout_path.stat().st_size,
            "stdout_sha256": sha256_file(stdout_path),
            "stderr_log": stderr_path.name,
            "stderr_byte_count": stderr_path.stat().st_size,
            "stderr_sha256": sha256_file(stderr_path),
        },
    )
    if completed.timed_out:
        raise AtlasMediaError(
            f"media command exceeded {timeout_seconds:g} seconds: {command[0]}"
        )
    if completed.returncode != 0:
        raise AtlasMediaError(
            f"media command failed with exit {completed.returncode}: {command[0]}"
        )


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
