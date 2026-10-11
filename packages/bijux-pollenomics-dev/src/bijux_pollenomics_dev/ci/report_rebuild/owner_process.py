"""Retain bounded producer diagnostics before accepting or refusing an owner run."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from bijux_pollenomics_dev.ci.atlas_media.process_execution import (
    BoundedProcessError,
    run_bounded_argv,
)

from .contracts import JsonObject, ReportRebuildError, atomic_write_json, sha256_bytes


def run_owner_command(
    *,
    command: tuple[str, ...],
    repo_root: Path,
    evidence_root: Path,
    owner_id: str,
    lane: str,
    binding: JsonObject,
    producer_inputs: JsonObject,
    timeout_seconds: float,
) -> None:
    """Keep execution evidence even when a producer fails or times out."""
    request: JsonObject = {
        "schema_version": "report-owner-command.v1",
        "command": list(command),
        "cwd": str(repo_root),
        "owner_id": owner_id,
        "lane": lane,
        "binding": binding,
        "producer_inputs": producer_inputs,
        "timeout_seconds": timeout_seconds,
        "max_output_bytes": 1024 * 1024,
        "started_at": datetime.now(UTC).isoformat(),
    }
    atomic_write_json(evidence_root / "producer-command.json", request)
    receipt: JsonObject = {
        "schema_version": "report-owner-execution.v1",
        "command_receipt_sha256": sha256_bytes(
            (evidence_root / "producer-command.json").read_bytes()
        ),
    }
    try:
        completed = run_bounded_argv(
            command,
            cwd=repo_root,
            timeout_seconds=timeout_seconds,
            max_output_bytes=1024 * 1024,
        )
    except BoundedProcessError as error:
        receipt.update(
            status="execution_error",
            error=str(error),
            finished_at=datetime.now(UTC).isoformat(),
            exit_code=None,
        )
        atomic_write_json(evidence_root / "producer-execution.json", receipt)
        raise ReportRebuildError(
            "owner producer could not be executed safely"
        ) from error
    for name, payload in (("stdout", completed.stdout), ("stderr", completed.stderr)):
        path = evidence_root / f"producer.{name}.log"
        path.write_bytes(payload)
        receipt[name] = {
            "path": path.name,
            "bytes": len(payload),
            "sha256": sha256_bytes(payload),
        }
    receipt.update(
        status="timed_out" if completed.timed_out else "exited",
        command=list(completed.command),
        finished_at=datetime.now(UTC).isoformat(),
        duration_seconds=completed.duration_seconds,
        exit_code=completed.returncode,
        timed_out=completed.timed_out,
        termination=completed.termination,
    )
    atomic_write_json(evidence_root / "producer-execution.json", receipt)
    if completed.timed_out or completed.returncode != 0:
        raise ReportRebuildError(
            f"owner producer failed: {owner_id}; exit={completed.returncode}; "
            f"timed_out={completed.timed_out}; receipt={evidence_root / 'producer-execution.json'}"
        )
