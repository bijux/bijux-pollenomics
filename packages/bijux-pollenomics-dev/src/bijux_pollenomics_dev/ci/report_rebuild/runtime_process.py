"""Validated process boundary for runtime report partition operations."""

from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
import sys

from bijux_pollenomics_dev.ci.atlas_media.process_execution import (
    BoundedProcessError,
    run_bounded_argv,
)

from .contracts import JsonObject, ReportRebuildError, require_mapping, require_string

_COMMAND_SCHEMA = "published-report-partition-command.v1"
_RESPONSE_SCHEMA = "published-report-partition-response.v1"
_TIMEOUT_SECONDS = 480
_MAX_DIAGNOSTIC_CHARS = 4_000
_MAX_OUTPUT_BYTES = 1024 * 1024
_ENV_EXECUTABLE = "/usr/bin/env"


def _unique_object(pairs: list[tuple[str, object]]) -> JsonObject:
    result: JsonObject = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON field: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> object:
    raise ValueError(f"non-finite JSON value: {value}")


def _diagnostic(stderr: bytes) -> str:
    text = stderr.decode("utf-8", errors="replace").strip()
    if len(text) <= _MAX_DIAGNOSTIC_CHARS:
        return text
    return f"...{text[-_MAX_DIAGNOSTIC_CHARS:]}"


def run_runtime_command(request: Mapping[str, object]) -> JsonObject:
    """Execute one runtime-owned command and validate its response envelope."""
    operation = require_string(request.get("operation"), "runtime operation")
    if request.get("schema_version") != _COMMAND_SCHEMA:
        raise ReportRebuildError("runtime request schema is invalid")
    try:
        payload = json.dumps(
            request, sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        completed = run_bounded_argv(
            (
                _ENV_EXECUTABLE,
                sys.executable,
                "-m",
                "bijux_pollenomics.reporting.bundles.report_partitions",
                payload,
            ),
            cwd=Path.cwd(),
            timeout_seconds=_TIMEOUT_SECONDS,
            max_output_bytes=_MAX_OUTPUT_BYTES,
        )
    except (TypeError, ValueError) as error:
        raise ReportRebuildError("runtime request is not strict JSON") from error
    except BoundedProcessError as error:
        raise ReportRebuildError(
            f"cannot execute runtime report partition command: {operation}"
        ) from error
    if completed.timed_out:
        raise ReportRebuildError(
            f"runtime report partition command timed out: {operation}"
        )
    if completed.returncode != 0:
        detail = _diagnostic(completed.stderr)
        suffix = f": {detail}" if detail else ""
        raise ReportRebuildError(
            f"runtime report partition command failed ({completed.returncode}){suffix}"
        )
    try:
        response = require_mapping(
            json.loads(
                completed.stdout.decode("utf-8"),
                object_pairs_hook=_unique_object,
                parse_constant=_reject_constant,
            ),
            "runtime response",
        )
    except (TypeError, ValueError, UnicodeError, json.JSONDecodeError) as error:
        raise ReportRebuildError("runtime response is not strict JSON") from error
    if set(response) != {"schema_version", "operation", "result"}:
        raise ReportRebuildError("runtime response fields are not exact")
    if response["schema_version"] != _RESPONSE_SCHEMA:
        raise ReportRebuildError("runtime response schema is invalid")
    if response["operation"] != operation:
        raise ReportRebuildError("runtime response operation does not match request")
    return require_mapping(response["result"], "runtime result")
