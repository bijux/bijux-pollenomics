"""Content-addressed, append-only records for LRA development-fold trials.

This records attempted work; it does not authorize a benchmark, a final-test
access, or a scientific accuracy claim.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import re
import tempfile
from typing import Any

_RUN_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,95}\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_START_FIELDS = set(
    {
        "run_id",
        "policy_sha256",
        "input_hashes",
        "target",
        "fold_id",
        "model",
        "configuration",
        "hyperparameters",
        "seed",
        "backend",
        "budget",
    }
)
_RESULT_FIELDS = {"status", "elapsed_seconds", "metrics", "reason_code"}
_CONFIG_FIELDS = {
    "method",
    "transport",
    "taxon_profile",
    "ppe_profile",
    "basin_scenario",
    "spatial_support",
    "temporal_support",
    "uncertainty",
}


class ExperimentLedgerError(ValueError):
    """A stable refusal to write or read an invalid trial record."""

    def __init__(self, reason_code: str) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code


def _bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ExperimentLedgerError("non_json_or_nonfinite_value") from exc


def _record(value: dict[str, object]) -> bytes:
    return (
        _bytes({"payload": value, "sha256": hashlib.sha256(_bytes(value)).hexdigest()})
        + b"\n"
    )


def _validated_record(path: Path) -> dict[str, object]:
    try:
        envelope = json.loads(path.read_bytes())
        if not isinstance(envelope, dict) or set(envelope) != {"payload", "sha256"}:
            raise ValueError("invalid envelope")
        payload = envelope["payload"]
        if not isinstance(payload, dict):
            raise ValueError("invalid payload")
        digest = hashlib.sha256(_bytes(payload)).hexdigest()
        if envelope["sha256"] != digest:
            raise ValueError("digest mismatch")
        return payload
    except (OSError, ValueError, TypeError) as exc:
        raise ExperimentLedgerError("invalid_ledger_record") from exc


def _publish_once(path: Path, content: bytes) -> None:
    """Link a complete temporary file into place without replacing a prior record."""
    with tempfile.NamedTemporaryFile(
        dir=path.parent, prefix=".record-", delete=False
    ) as tmp:
        temporary = Path(tmp.name)
        tmp.write(content)
        tmp.flush()
        os.fsync(tmp.fileno())
    try:
        os.link(temporary, path)
    except FileExistsError as exc:
        raise ExperimentLedgerError("record_already_exists") from exc
    finally:
        temporary.unlink(missing_ok=True)


def _identity(value: object, field: str) -> str:
    if not isinstance(value, str) or not value or not _RUN_ID.fullmatch(value):
        raise ExperimentLedgerError(f"invalid_{field}")
    return value


def _mapping(value: object, field: str, *, nonempty: bool = True) -> dict[str, object]:
    if (
        not isinstance(value, dict)
        or (nonempty and not value)
        or not all(isinstance(key, str) and key for key in value)
    ):
        raise ExperimentLedgerError(f"invalid_{field}")
    return value


def start_development_attempt(root: Path, spec: dict[str, object]) -> str:
    """Reserve a unique development trial and persist its full planned inputs."""
    if set(spec) != _START_FIELDS:
        raise ExperimentLedgerError("invalid_start_fields")
    run_id = _identity(spec["run_id"], "run_id")
    digest = spec["policy_sha256"]
    if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
        raise ExperimentLedgerError("invalid_policy_sha256")
    hashes = _mapping(spec["input_hashes"], "input_hashes")
    if not all(
        isinstance(value, str) and _SHA256.fullmatch(value) for value in hashes.values()
    ):
        raise ExperimentLedgerError("invalid_input_hashes")
    if spec["target"] not in {"local_pollen_available", "withheld_pollen_prediction"}:
        raise ExperimentLedgerError("invalid_target")
    for field in ("fold_id", "model", "backend"):
        value = spec[field]
        if not isinstance(value, str) or not value.strip():
            raise ExperimentLedgerError(f"invalid_{field}")
    configuration = _mapping(spec["configuration"], "configuration")
    if set(configuration) != _CONFIG_FIELDS or not all(
        isinstance(value, str) and value.strip() for value in configuration.values()
    ):
        raise ExperimentLedgerError("invalid_configuration")
    _mapping(spec["hyperparameters"], "hyperparameters", nonempty=False)
    _mapping(spec["budget"], "budget")
    if (
        isinstance(spec["seed"], bool)
        or not isinstance(spec["seed"], int)
        or spec["seed"] < 0
    ):
        raise ExperimentLedgerError("invalid_seed")
    record = _record(spec)
    root.mkdir(parents=True, exist_ok=True)
    trial = root / run_id
    try:
        trial.mkdir()
    except FileExistsError as exc:
        raise ExperimentLedgerError("run_id_already_exists") from exc
    _publish_once(trial / "start.json", record)
    return run_id


def finish_development_attempt(
    root: Path, run_id: str, result: dict[str, object]
) -> None:
    """Publish one terminal result, retaining refusals and failures."""
    _identity(run_id, "run_id")
    if set(result) != _RESULT_FIELDS:
        raise ExperimentLedgerError("invalid_result_fields")
    status = result["status"]
    if status not in {"completed", "refused", "failed"}:
        raise ExperimentLedgerError("invalid_status")
    elapsed = result["elapsed_seconds"]
    if (
        isinstance(elapsed, bool)
        or not isinstance(elapsed, (int, float))
        or (not math.isfinite(elapsed) or elapsed < 0)
    ):
        raise ExperimentLedgerError("invalid_elapsed_seconds")
    metrics = result["metrics"]
    if not isinstance(metrics, dict) or not all(
        isinstance(key, str) and key for key in metrics
    ):
        raise ExperimentLedgerError("invalid_metrics")
    if status == "completed" and not metrics:
        raise ExperimentLedgerError("completed_without_metrics")
    reason = result["reason_code"]
    if status == "completed" and reason is not None:
        raise ExperimentLedgerError("completed_with_reason")
    if status != "completed" and (not isinstance(reason, str) or not reason):
        raise ExperimentLedgerError("missing_reason_code")
    content = _record(result)
    trial = root / run_id
    if not (trial / "start.json").is_file():
        raise ExperimentLedgerError("unknown_run_id")
    _validated_record(trial / "start.json")
    _publish_once(trial / "result.json", content)


def read_development_attempts(root: Path) -> tuple[dict[str, Any], ...]:
    """Verify all records and expose unfinished reservations explicitly."""
    if not root.exists():
        return ()
    rows: list[dict[str, Any]] = []
    for trial in sorted(root.iterdir()):
        if not trial.is_dir():
            raise ExperimentLedgerError("unexpected_ledger_entry")
        _identity(trial.name, "run_id")
        start = _validated_record(trial / "start.json")
        if start.get("run_id") != trial.name:
            raise ExperimentLedgerError("run_id_mismatch")
        result_path = trial / "result.json"
        result = _validated_record(result_path) if result_path.exists() else None
        rows.append({"start": start, "result": result})
    return tuple(rows)
