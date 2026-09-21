"""Execute one declared development trial under the outer managed-job runner.

The ledger reservation precedes the numerical command. This module does not
admit a reference population, open final-test labels or select a model.
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
import time
from pathlib import Path
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


def run_development_trial(plan: dict[str, object]) -> int:
    """Reserve, run and terminate exactly one declared development attempt."""
    if set(plan) != {"schema_version", "ledger_root", "spec", "timeout_seconds"}:
        raise TrialPlanError("invalid_trial_plan_fields")
    if plan["schema_version"] != "lra-development-trial.v1":
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
    run_id = start_development_attempt(Path(ledger_root), spec)
    output.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    try:
        completed = subprocess.run(
            cast(list[str], invocation["argv"]),
            cwd=cwd,
            env=cast(dict[str, str], invocation["environment"]),
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        result = _failed("trial_timeout", time.monotonic() - started)
        code = 124
    except OSError:
        result = _failed("command_start_failed", time.monotonic() - started)
        code = 2
    else:
        elapsed = time.monotonic() - started
        code = completed.returncode
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
    return code


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
