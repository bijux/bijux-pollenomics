"""Execute one declared development trial under the outer managed-job runner.

The ledger reservation precedes the numerical command. This module does not
admit a reference population, open final-test labels or select a model.
"""

from __future__ import annotations

from contextlib import suppress
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from typing import Any, cast

from .experiment_ledger import (
    ExperimentLedgerError,
    finish_development_attempt,
    start_development_attempt,
)


class TrialPlanError(ValueError):
    """A trial plan is incomplete or would reuse an existing output."""


def _failed(reason_code: str, elapsed: float) -> dict[str, object]:
    return {
        "status": "failed",
        "elapsed_seconds": elapsed,
        "metrics": {},
        "reason_code": reason_code,
    }


def _declared_executable_sha256(spec: dict[str, object]) -> str:
    design_binding = cast(dict[str, object], spec["development_design"])
    payload = json.loads(cast(str, design_binding["canonical_design_json"]))
    candidates = cast(list[dict[str, object]], payload["candidates"])
    candidate_id = spec["candidate_id"]
    candidate = next(row for row in candidates if row["candidate_id"] == candidate_id)
    invocation = cast(dict[str, object], candidate["invocation"])
    return cast(str, invocation["executable_sha256"])


def _freeze_executable(
    ledger_root: Path, run_id: str, descriptor: int, expected_sha256: str
) -> Path:
    frozen = ledger_root / run_id / ".development-executable"
    destination = os.open(frozen, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o500)
    digest = hashlib.sha256()
    try:
        os.lseek(descriptor, 0, os.SEEK_SET)
        while block := os.read(descriptor, 1024 * 1024):
            digest.update(block)
            offset = 0
            while offset < len(block):
                offset += os.write(destination, block[offset:])
        os.fsync(destination)
    except BaseException:
        frozen.unlink(missing_ok=True)
        raise
    finally:
        os.close(destination)
        os.lseek(descriptor, 0, os.SEEK_SET)
    if digest.hexdigest() != expected_sha256:
        frozen.unlink(missing_ok=True)
        raise ExperimentLedgerError("executable_identity_changed_before_launch")
    return frozen


def _terminate_process_group(process: subprocess.Popen[bytes]) -> None:
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        with suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
        process.wait()
    else:
        with suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)


def run_development_trial(plan: dict[str, object]) -> int:
    """Reserve, run and terminate exactly one declared development attempt."""
    if set(plan) != {"schema_version", "ledger_root", "spec", "timeout_seconds"}:
        raise TrialPlanError("invalid_trial_plan_fields")
    if plan["schema_version"] != "lra-development-trial.v2":
        raise TrialPlanError("invalid_trial_plan_version")
    ledger_root = plan["ledger_root"]
    if not isinstance(ledger_root, str) or not Path(ledger_root).is_absolute():
        raise TrialPlanError("invalid_ledger_root")
    spec = plan["spec"]
    if not isinstance(spec, dict) or not isinstance(spec.get("invocation"), dict):
        raise TrialPlanError("missing_trial_invocation")
    timeout = plan["timeout_seconds"]
    if (
        isinstance(timeout, bool)
        or not isinstance(timeout, (int, float))
        or not math.isfinite(timeout)
        or timeout <= 0
    ):
        raise TrialPlanError("invalid_trial_timeout")
    budget = spec.get("budget")
    if not isinstance(budget, dict) or timeout != budget.get("seconds"):
        raise TrialPlanError("trial_timeout_differs_from_budget")
    invocation = cast(dict[str, Any], spec["invocation"])
    result_path = invocation.get("result_path")
    if not isinstance(result_path, str) or not Path(result_path).is_absolute():
        raise TrialPlanError("invalid_trial_result_path")
    output = Path(result_path)
    if output.resolve().is_relative_to(Path(ledger_root).resolve()):
        raise TrialPlanError("trial_result_overlaps_ledger")
    if output.exists() or output.is_symlink():
        raise TrialPlanError("trial_result_already_exists")
    cwd = invocation.get("cwd")
    if not isinstance(cwd, str) or not Path(cwd).is_dir():
        raise TrialPlanError("trial_cwd_missing")
    argv = cast(list[str], invocation["argv"])
    try:
        executable_descriptor = os.open(argv[0], os.O_RDONLY)
    except OSError as exc:
        raise ExperimentLedgerError("declared_executable_unreadable") from exc
    try:
        run_id = start_development_attempt(
            Path(ledger_root), spec, executable_descriptor=executable_descriptor
        )
    except BaseException:
        os.close(executable_descriptor)
        raise
    output.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    environment = cast(dict[str, str], invocation["environment"])
    frozen: Path | None = None
    process: subprocess.Popen[bytes] | None = None
    interrupted_signal: int | None = None

    def interrupt(signum: int, _frame: object) -> None:
        nonlocal interrupted_signal
        interrupted_signal = signum
        if process is not None:
            with suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGTERM)

    def current_interrupt() -> int | None:
        return interrupted_signal

    previous_handlers = {
        signum: signal.signal(signum, interrupt)
        for signum in (signal.SIGINT, signal.SIGTERM)
    }
    try:
        frozen = _freeze_executable(
            Path(ledger_root),
            run_id,
            executable_descriptor,
            _declared_executable_sha256(spec),
        )
        if interrupted_signal is None:
            process = subprocess.Popen(
                argv,
                cwd=cwd,
                env=environment,
                executable=str(frozen),
                start_new_session=True,
            )
    except OSError:
        result = _failed("command_start_failed", time.monotonic() - started)
        code = 2
    except ExperimentLedgerError as exc:
        result = _failed(exc.reason_code, time.monotonic() - started)
        code = 2
    else:
        if interrupted_signal is not None:
            if process is not None:
                _terminate_process_group(process)
            result = _failed("trial_runner_interrupted", time.monotonic() - started)
            code = 128 + interrupted_signal
        elif process is None:
            result = _failed("command_start_failed", time.monotonic() - started)
            code = 2
        else:
            try:
                code = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                _terminate_process_group(process)
                result = _failed("trial_timeout", time.monotonic() - started)
                code = 124
            else:
                interruption_after_wait = current_interrupt()
                if interruption_after_wait is not None:
                    _terminate_process_group(process)
                    result = _failed(
                        "trial_runner_interrupted", time.monotonic() - started
                    )
                    code = 128 + interruption_after_wait
                else:
                    _terminate_process_group(process)
            elapsed = time.monotonic() - started
            if code != 124 and interrupted_signal is None:
                if not output.is_file() or output.is_symlink():
                    result = _failed("missing_trial_result", elapsed)
                else:
                    try:
                        payload = json.loads(output.read_text(encoding="utf-8"))
                        if not isinstance(payload, dict) or set(payload) != {
                            "status",
                            "metrics",
                            "reason_code",
                        }:
                            raise ValueError("invalid terminal payload")
                        result = {**payload, "elapsed_seconds": elapsed}
                        if code != 0 and result["status"] == "completed":
                            result = _failed("nonzero_command_exit", elapsed)
                    except (OSError, UnicodeError, ValueError):
                        result = _failed("invalid_trial_result", elapsed)
                if code == 0 and result["status"] != "completed":
                    code = 2
    finally:
        try:
            if process is not None and process.poll() is None:
                _terminate_process_group(process)
            if frozen is not None:
                frozen.unlink(missing_ok=True)
        finally:
            try:
                os.close(executable_descriptor)
            finally:
                for signum, handler in previous_handlers.items():
                    signal.signal(signum, handler)
    if (
        interrupted_signal is not None
        and result["reason_code"] != "trial_runner_interrupted"
    ):
        result = _failed("trial_runner_interrupted", time.monotonic() - started)
        code = 128 + interrupted_signal
    try:
        finish_development_attempt(Path(ledger_root), run_id, result)
    except ExperimentLedgerError:
        result = _failed("invalid_trial_result", time.monotonic() - started)
        finish_development_attempt(Path(ledger_root), run_id, result)
        code = 2
    print(
        json.dumps(
            {
                "run_id": run_id,
                "status": result["status"],
                "reason_code": result["reason_code"],
                "terminal_record": str(Path(ledger_root) / run_id / "result.json"),
            },
            sort_keys=True,
        )
    )
    return code if interrupted_signal is None else 128 + interrupted_signal


def main(argv: list[str] | None = None) -> int:
    """Run a JSON trial plan; the caller must itself be a managed background job."""
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        raise SystemExit(
            "usage: python -m bijux_pollenomics_dev.lra_validation.trial_runner PLAN.json"
        )
    plan = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    if not isinstance(plan, dict):
        raise TrialPlanError("invalid_trial_plan")
    return run_development_trial(plan)


if __name__ == "__main__":
    raise SystemExit(main())
