"""Non-interactive product runner for recorded verification gates."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
import json
from pathlib import Path, PurePosixPath
import stat
import sys

from .gates import run_recorded_gate
from .release_evidence import ReleaseEvidenceError

__all__ = ["main"]


def main(argv: Sequence[str] | None = None) -> int:
    """Run one exact command and return a Make-compatible gate status."""
    args = _parser().parse_args(argv)
    try:
        command = list(args.command_argv)
        if command and command[0] == "--":
            command = command[1:]
        environment = _environment(args.environment)
        root = Path(args.repository_root)
        _remove_previous_junit(
            root,
            artifacts_directory=args.artifacts_directory,
            junit_path=args.junit_path,
        )
        record = run_recorded_gate(
            root,
            gate_id=args.gate_id,
            argv=command,
            environment=environment,
            input_paths=args.input,
            artifacts_directory=args.artifacts_directory,
            junit_path=args.junit_path,
            timeout_seconds=args.timeout_seconds,
        )
        summary = {
            "gate_id": record["gate_id"],
            "record_digest": record["record_digest"],
            "status": record["status"],
        }
        print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
        return 0 if record["status"] == "PASS" else 1
    except (OSError, ReleaseEvidenceError) as error:
        print(f"verification gate refused: {error}", file=sys.stderr)
        return 2


def _environment(values: Sequence[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in values:
        key, separator, value = item.partition("=")
        if not separator or not key or key in result:
            raise ReleaseEvidenceError(
                f"invalid or duplicate environment assignment: {item}"
            )
        result[key] = value
    return result


def _remove_previous_junit(
    repository_root: Path, *, artifacts_directory: str, junit_path: str
) -> None:
    root = repository_root.resolve(strict=True)
    directory_parts = _relative_parts(artifacts_directory)
    junit_parts = _relative_parts(junit_path)
    if not directory_parts or directory_parts[0] != "artifacts":
        raise ReleaseEvidenceError("gate artifacts directory must be under artifacts/")
    directory = root.joinpath(*directory_parts)
    junit = root.joinpath(*junit_parts)
    try:
        junit.relative_to(directory)
    except ValueError as error:
        raise ReleaseEvidenceError(
            "JUnit path must be inside the gate artifacts directory"
        ) from error
    if not junit.exists() and not junit.is_symlink():
        return
    mode = junit.lstat().st_mode
    if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
        raise ReleaseEvidenceError("existing JUnit path is not a regular file")
    junit.unlink()


def _relative_parts(relative_path: str) -> tuple[str, ...]:
    if not relative_path or "\\" in relative_path:
        raise ReleaseEvidenceError(
            f"invalid repository-relative path: {relative_path!r}"
        )
    pure = PurePosixPath(relative_path)
    if pure.is_absolute() or pure.as_posix() != relative_path:
        raise ReleaseEvidenceError(
            f"invalid repository-relative path: {relative_path!r}"
        )
    if any(part in {"", ".", ".."} for part in pure.parts):
        raise ReleaseEvidenceError(f"path escapes repository root: {relative_path!r}")
    return pure.parts


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bijux-pollenomics-verification-gate")
    parser.add_argument("--repository-root", required=True)
    parser.add_argument("--gate-id", required=True)
    parser.add_argument("--artifacts-directory", required=True)
    parser.add_argument("--junit-path", required=True)
    parser.add_argument("--input", action="append", required=True)
    parser.add_argument("--environment", action="append", default=[])
    parser.add_argument("--timeout-seconds", type=float)
    parser.add_argument("command_argv", nargs=argparse.REMAINDER)
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
