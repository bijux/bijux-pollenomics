"""Content-addressed, append-only records for LRA development-fold trials.

This records attempted work; it does not authorize a benchmark, a final-test
access, or a scientific accuracy claim.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager, suppress
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import tempfile
import time
from typing import Any
import uuid

from bijux_pollenomics.analysis.lra_validation.evaluation.api import (
    reopen_cohort_admission,
)

from .development_design import (
    DevelopmentDesignError,
    validate_attempt_against_design,
    validate_development_design,
)

_RUN_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,95}\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_START_PROFILE = "lra-development-attempt.v3"
_START_FIELDS = set(
    {
        "schema_version",
        "run_id",
        "development_design",
        "input_hashes",
        "evaluation_binding",
        "fold_id",
        "candidate_id",
        "model",
        "configuration",
        "hyperparameters",
        "seed",
        "backend",
        "budget",
        "invocation",
    }
)
_RESULT_FIELDS = {"status", "elapsed_seconds", "metrics", "reason_code"}
_INVOCATION_FIELDS = {"argv", "cwd", "environment", "result_path"}
_DEVELOPMENT_DESIGN_FIELDS = {"canonical_design_json", "design_sha256"}
_EVALUATION_BINDING_FIELDS = {
    "canonical_cohort_admission_json",
    "cohort_admission_sha256",
    "scope_sha256",
    "split_manifest_sha256",
    "split_kind",
    "experiment",
    "target",
}
_SPLIT_KINDS = {"leave_one_site_group_out", "predefined_block"}
_EXPERIMENT_TARGETS = {
    ("local_pollen_available", "vegetation_cover"),
    ("all_target_pollen_withheld", "vegetation_cover"),
    ("all_target_pollen_withheld", "pollen_composition"),
}
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
_RESERVATION_LOCK = ".development-reservation.lock"
_RESERVATION_ACTIVE_PREFIX = ".development-reservation-active-"
_RESERVATION_EVIDENCE_PREFIX = ".development-reservation-evidence-"
_RESERVATION_STALE_PREFIX = ".development-reservation-stale-"
_INCOMPLETE_ATTEMPT_PREFIX = ".development-attempt-incomplete-"
_THREAD_LIMIT_ENVIRONMENT = {
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
}


class ExperimentLedgerError(ValueError):
    """A stable refusal to write or read an invalid trial record."""

    def __init__(self, reason_code: str) -> None:
        """Preserve the stable trial-refusal code on the exception."""
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
            raise TypeError("invalid payload")
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


def _reservation_owner(content: bytes) -> tuple[int, int] | None:
    """Return a complete prior owner, or refuse malformed crash evidence."""
    if not content:
        return None
    try:
        owner = json.loads(content)
    except (UnicodeError, ValueError) as exc:
        raise ExperimentLedgerError("ledger_reservation_recovery_required") from exc
    if (
        not isinstance(owner, dict)
        or set(owner) != {"created_unix_ns", "pid"}
        or isinstance(owner["pid"], bool)
        or not isinstance(owner["pid"], int)
        or owner["pid"] < 1
        or isinstance(owner["created_unix_ns"], bool)
        or not isinstance(owner["created_unix_ns"], int)
        or owner["created_unix_ns"] < 1
    ):
        raise ExperimentLedgerError("ledger_reservation_recovery_required")
    return owner["pid"], owner["created_unix_ns"]


def _open_reservation_lock(root: Path, *, create: bool) -> int | None:
    lock = root / _RESERVATION_LOCK
    flags = os.O_RDWR | (os.O_CREAT if create else 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(lock, flags, 0o600)
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise ExperimentLedgerError("ledger_reservation_recovery_required") from exc
    if not stat.S_ISREG(os.fstat(descriptor).st_mode):
        os.close(descriptor)
        raise ExperimentLedgerError("ledger_reservation_recovery_required")
    return descriptor


def _read_descriptor(descriptor: int) -> bytes:
    os.lseek(descriptor, 0, os.SEEK_SET)
    content = bytearray()
    while block := os.read(descriptor, 4096):
        content.extend(block)
    return bytes(content)


def _publish_reservation_evidence(root: Path, path: Path, content: bytes) -> None:
    with tempfile.NamedTemporaryFile(
        dir=root, prefix=_RESERVATION_EVIDENCE_PREFIX, delete=False
    ) as stream:
        evidence = Path(stream.name)
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.link(evidence, path)
    except OSError as exc:
        raise ExperimentLedgerError("ledger_reservation_recovery_required") from exc
    finally:
        evidence.unlink(missing_ok=True)


def _dead_reservations(root: Path) -> tuple[tuple[Path, tuple[int, int]], ...]:
    evidence: list[tuple[Path, tuple[int, int]]] = []
    for path in sorted(root.iterdir()):
        if not path.name.startswith(
            (_RESERVATION_ACTIVE_PREFIX, _RESERVATION_EVIDENCE_PREFIX)
        ):
            continue
        try:
            if not stat.S_ISREG(path.lstat().st_mode):
                raise ExperimentLedgerError("ledger_reservation_recovery_required")
            owner = _reservation_owner(path.read_bytes())
        except OSError as exc:
            raise ExperimentLedgerError("ledger_reservation_recovery_required") from exc
        if owner is None:
            raise ExperimentLedgerError("ledger_reservation_recovery_required")
        evidence.append((path, owner))
    return tuple(evidence)


def _archive_dead_reservations(root: Path) -> None:
    for path, (pid, created_unix_ns) in _dead_reservations(root):
        archived = root / (
            f"{_RESERVATION_STALE_PREFIX}{pid}-{created_unix_ns}-{uuid.uuid4().hex}"
        )
        try:
            path.rename(archived)
        except OSError as exc:
            raise ExperimentLedgerError("ledger_reservation_recovery_required") from exc


@contextmanager
def _reservation(root: Path) -> Iterator[None]:
    """Serialize a crash-recoverable reservation boundary without waiting."""
    root.mkdir(parents=True, exist_ok=True)
    descriptor = _open_reservation_lock(root, create=True)
    if descriptor is None:
        raise ExperimentLedgerError("ledger_reservation_recovery_required")
    acquired = False
    published = False
    created_unix_ns = time.time_ns()
    pid = os.getpid()
    content = _bytes({"created_unix_ns": created_unix_ns, "pid": pid}) + b"\n"
    active = root / (
        f"{_RESERVATION_ACTIVE_PREFIX}{pid}-{created_unix_ns}-{uuid.uuid4().hex}"
    )
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ExperimentLedgerError("ledger_reservation_busy") from exc
        acquired = True
        if _read_descriptor(descriptor):
            raise ExperimentLedgerError("ledger_reservation_recovery_required")
        _archive_dead_reservations(root)
        _publish_reservation_evidence(root, active, content)
        published = True
        yield
    finally:
        try:
            if published:
                active.unlink(missing_ok=True)
        finally:
            try:
                if acquired:
                    fcntl.flock(descriptor, fcntl.LOCK_UN)
            finally:
                os.close(descriptor)


def _require_no_live_reservation(root: Path) -> None:
    descriptor = _open_reservation_lock(root, create=False)
    if descriptor is None:
        _dead_reservations(root)
        return
    acquired = False
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_SH | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ExperimentLedgerError("ledger_reservation_busy") from exc
        acquired = True
        if _read_descriptor(descriptor):
            raise ExperimentLedgerError("ledger_reservation_recovery_required")
        _dead_reservations(root)
    finally:
        if acquired:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


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


def _sha256(value: object, field: str) -> str:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise ExperimentLedgerError(f"invalid_{field}")
    return value


def _evaluation_binding(value: object, hashes: dict[str, object]) -> None:
    binding = _mapping(value, "evaluation_binding")
    if set(binding) != _EVALUATION_BINDING_FIELDS:
        raise ExperimentLedgerError("invalid_evaluation_binding")
    canonical = binding["canonical_cohort_admission_json"]
    if not isinstance(canonical, str):
        raise ExperimentLedgerError("invalid_cohort_admission")
    cohort_sha256 = _sha256(
        binding["cohort_admission_sha256"], "cohort_admission_sha256"
    )
    try:
        admission = reopen_cohort_admission(canonical, cohort_sha256)
    except ValueError as exc:
        raise ExperimentLedgerError("invalid_cohort_admission") from exc
    scope_sha256 = _sha256(binding["scope_sha256"], "scope_sha256")
    if admission.scope_sha256 != scope_sha256:
        raise ExperimentLedgerError("cohort_scope_mismatch")
    split_sha256 = _sha256(binding["split_manifest_sha256"], "split_manifest_sha256")
    if hashes.get("split_manifest") != split_sha256:
        raise ExperimentLedgerError("split_manifest_input_mismatch")
    split_kind = binding["split_kind"]
    if not isinstance(split_kind, str) or split_kind not in _SPLIT_KINDS:
        raise ExperimentLedgerError("invalid_split_kind")
    experiment, target = binding["experiment"], binding["target"]
    if (
        not isinstance(experiment, str)
        or not isinstance(target, str)
        or (experiment, target) not in _EXPERIMENT_TARGETS
    ):
        raise ExperimentLedgerError("invalid_experiment_target")


def start_development_attempt(
    root: Path,
    spec: dict[str, object],
    *,
    executable_descriptor: int | None = None,
) -> str:
    """Reserve a unique development trial and persist its full planned inputs."""
    if set(spec) != _START_FIELDS:
        raise ExperimentLedgerError("invalid_start_fields")
    if spec["schema_version"] != _START_PROFILE:
        raise ExperimentLedgerError("invalid_start_version")
    run_id = _identity(spec["run_id"], "run_id")
    design_binding = _mapping(spec["development_design"], "development_design")
    if set(design_binding) != _DEVELOPMENT_DESIGN_FIELDS:
        raise ExperimentLedgerError("invalid_development_design")
    try:
        design = validate_development_design(
            design_binding["canonical_design_json"], design_binding["design_sha256"]
        )
    except DevelopmentDesignError as exc:
        raise ExperimentLedgerError(exc.reason_code) from exc
    hashes = _mapping(spec["input_hashes"], "input_hashes")
    if not all(
        isinstance(value, str) and _SHA256.fullmatch(value) for value in hashes.values()
    ):
        raise ExperimentLedgerError("invalid_input_hashes")
    _evaluation_binding(spec["evaluation_binding"], hashes)
    for field in ("fold_id", "candidate_id", "model", "backend"):
        value = spec[field]
        if not isinstance(value, str) or not value.strip():
            raise ExperimentLedgerError(f"invalid_{field}")
    configuration = _mapping(spec["configuration"], "configuration")
    if set(configuration) != _CONFIG_FIELDS or not all(
        isinstance(value, str) and value.strip() for value in configuration.values()
    ):
        raise ExperimentLedgerError("invalid_configuration")
    _mapping(spec["hyperparameters"], "hyperparameters", nonempty=False)
    trial_budget = _mapping(spec["budget"], "budget")
    if (
        isinstance(spec["seed"], bool)
        or not isinstance(spec["seed"], int)
        or spec["seed"] < 0
    ):
        raise ExperimentLedgerError("invalid_seed")
    invocation = _mapping(spec["invocation"], "invocation")
    if set(invocation) != _INVOCATION_FIELDS:
        raise ExperimentLedgerError("invalid_invocation")
    argv = invocation["argv"]
    if (
        not isinstance(argv, list)
        or not argv
        or not all(
            isinstance(value, str) and value and "\0" not in value for value in argv
        )
        or not Path(argv[0]).is_absolute()
    ):
        raise ExperimentLedgerError("invalid_invocation_argv")
    for field in ("cwd", "result_path"):
        value = invocation[field]
        if not isinstance(value, str) or not Path(value).is_absolute():
            raise ExperimentLedgerError(f"invalid_invocation_{field}")
    environment = _mapping(
        invocation["environment"], "invocation_environment", nonempty=False
    )
    if not all(
        isinstance(value, str) and "\0" not in value for value in environment.values()
    ):
        raise ExperimentLedgerError("invalid_invocation_environment")
    if any(
        marker in key.lower()
        for key in environment
        for marker in (
            "token",
            "secret",
            "password",
            "credential",
            "api_key",
            "auth",
        )
    ):
        raise ExperimentLedgerError("credential_environment_not_recordable")
    declared_threads = trial_budget.get("threads")
    if any(
        environment.get(name) != str(declared_threads)
        for name in _THREAD_LIMIT_ENVIRONMENT
    ):
        raise ExperimentLedgerError("invocation_thread_budget_not_enforced")
    try:
        validate_attempt_against_design(
            design, spec, executable_descriptor=executable_descriptor
        )
    except DevelopmentDesignError as exc:
        raise ExperimentLedgerError(exc.reason_code) from exc
    record = _record(spec)
    with _reservation(root):
        existing = _read_development_attempts(root, reservation_held=True)
        maximum_trials = design.payload["resource_budget"]["maximum_trials"]
        if len(existing) >= maximum_trials:
            raise ExperimentLedgerError("development_trial_budget_exhausted")
        seconds = trial_budget["seconds"]
        threads = trial_budget["threads"]
        if not isinstance(seconds, (int, float)) or not isinstance(threads, int):
            raise ExperimentLedgerError("invalid_trial_budget")
        consumed_cpu_seconds = seconds * threads
        for row in existing:
            previous = row["start"].get("development_design")
            if previous is None:
                raise ExperimentLedgerError("legacy_records_in_active_ledger")
            if previous != design_binding:
                raise ExperimentLedgerError("mixed_development_designs")
            previous_budget = _mapping(row["start"].get("budget"), "previous_budget")
            previous_seconds = previous_budget.get("seconds")
            previous_threads = previous_budget.get("threads")
            if not isinstance(previous_seconds, (int, float)) or not isinstance(
                previous_threads, int
            ):
                raise ExperimentLedgerError("invalid_ledger_record")
            consumed_cpu_seconds += previous_seconds * previous_threads
        if (
            consumed_cpu_seconds
            > design.payload["resource_budget"]["maximum_total_declared_cpu_seconds"]
        ):
            raise ExperimentLedgerError("development_declared_cpu_budget_exhausted")
        trial = root / run_id
        if trial.exists() or trial.is_symlink():
            raise ExperimentLedgerError("run_id_already_exists")
        staging = Path(tempfile.mkdtemp(prefix=_INCOMPLETE_ATTEMPT_PREFIX, dir=root))
        published = False
        try:
            _publish_once(staging / "start.json", record)
            if trial.exists() or trial.is_symlink():
                raise ExperimentLedgerError("run_id_already_exists")
            staging.rename(trial)
            published = True
        except FileExistsError as exc:
            raise ExperimentLedgerError("run_id_already_exists") from exc
        finally:
            if not published:
                (staging / "start.json").unlink(missing_ok=True)
                with suppress(OSError):
                    staging.rmdir()
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
        isinstance(key, str)
        and key
        and not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(value)
        for key, value in metrics.items()
    ):
        raise ExperimentLedgerError("invalid_metrics")
    if status == "completed" and not metrics:
        raise ExperimentLedgerError("completed_without_metrics")
    if status != "completed" and metrics:
        raise ExperimentLedgerError("noncompleted_with_metrics")
    reason = result["reason_code"]
    if status == "completed" and reason is not None:
        raise ExperimentLedgerError("completed_with_reason")
    if status != "completed" and (not isinstance(reason, str) or not reason):
        raise ExperimentLedgerError("missing_reason_code")
    trial = root / run_id
    if not (trial / "start.json").is_file():
        raise ExperimentLedgerError("unknown_run_id")
    start = _validated_record(trial / "start.json")
    if start.get("schema_version") == _START_PROFILE:
        design_binding = start.get("development_design")
        if not isinstance(design_binding, dict):
            raise ExperimentLedgerError("invalid_development_design")
        try:
            design = validate_development_design(
                design_binding.get("canonical_design_json"),
                design_binding.get("design_sha256"),
            )
            metric_ids = validate_attempt_against_design(
                design, start, verify_executable_bytes=False
            )
        except DevelopmentDesignError as exc:
            raise ExperimentLedgerError(exc.reason_code) from exc
        if status == "completed" and set(metrics) != set(metric_ids):
            raise ExperimentLedgerError("terminal_metrics_differ_from_design")
    content = _record(result)
    _publish_once(trial / "result.json", content)


def _read_development_attempts(
    root: Path, *, reservation_held: bool
) -> tuple[dict[str, Any], ...]:
    if not root.exists():
        return ()
    if not reservation_held:
        _require_no_live_reservation(root)
    rows: list[dict[str, Any]] = []
    for trial in sorted(root.iterdir()):
        if trial.name == _RESERVATION_LOCK:
            continue
        if (
            trial.name.startswith(
                (
                    _RESERVATION_ACTIVE_PREFIX,
                    _RESERVATION_EVIDENCE_PREFIX,
                    _RESERVATION_STALE_PREFIX,
                )
            )
            and trial.is_file()
        ):
            continue
        if trial.name.startswith(_INCOMPLETE_ATTEMPT_PREFIX) and trial.is_dir():
            continue
        if not trial.is_dir():
            raise ExperimentLedgerError("unexpected_ledger_entry")
        _identity(trial.name, "run_id")
        start = _validated_record(trial / "start.json")
        if start.get("run_id") != trial.name:
            raise ExperimentLedgerError("run_id_mismatch")
        result_path = trial / "result.json"
        result = _validated_record(result_path) if result_path.exists() else None
        rows.append({"start": start, "result": result})
    if not reservation_held:
        _require_no_live_reservation(root)
    return tuple(rows)


def read_development_attempts(root: Path) -> tuple[dict[str, Any], ...]:
    """Verify all records and expose unfinished reservations explicitly."""
    return _read_development_attempts(root, reservation_held=False)
