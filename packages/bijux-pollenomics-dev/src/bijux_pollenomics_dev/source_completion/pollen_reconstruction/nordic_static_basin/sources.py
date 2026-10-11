"""Require fixed retained aggregate identities and their separate native authority."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from bijux_pollenomics_dev.ci.report_rebuild.source_paths import safe_source_file

from .authority import CAPTURE_PINS, DESCRIPTOR, DESCRIPTOR_SHA256, FAMILY
from .publications import publication_inventory


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate Nordic captured JSON key")
        result[key] = value
    return result


def _finite(value: object) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("nonfinite Nordic captured JSON value")
    if isinstance(value, dict):
        for child in value.values():
            _finite(child)
    if isinstance(value, list):
        for child in value:
            _finite(child)


def _record(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise ValueError("Nordic captured record must be a string-keyed object")
    return dict(value)


def _cell(value: object, *keys: str) -> object:
    for key in keys:
        value = _record(value)[key]
    return value


def load_inputs(repository: Path) -> dict[str, object]:
    """Authenticate exact original source/capture/review bytes before use."""
    inputs: dict[str, object] = {}
    for relative, expected in {DESCRIPTOR: DESCRIPTOR_SHA256, **CAPTURE_PINS}.items():
        path = safe_source_file(repository, relative, "Nordic retained source")
        body = path.read_bytes()
        if hashlib.sha256(body).hexdigest() != expected:
            raise ValueError("Nordic retained source bytes changed")
        value: object = json.loads(body, object_pairs_hook=_pairs)
        if (
            not isinstance(value, dict)
            and relative != FAMILY + "/verification/physical-response-tuples.json"
        ):
            raise ValueError("Nordic retained source must be an object")
        _finite(value)
        inputs[relative.removeprefix(FAMILY + "/")] = value
    descriptor = _record(inputs["inputs/retained-source-identities.json"])
    if descriptor["files_sha256"] != CAPTURE_PINS:
        raise ValueError("Nordic source descriptor membership changed")
    report = _record(inputs["report.json"])
    if report["protocol"] != inputs["assumptions/protocol.json"]:
        raise ValueError("Nordic source protocol differs")
    terminal = _record(inputs["verification/native-terminal.json"])
    if terminal["native_exit_code"] != 0 or not terminal["custody_after_unchanged"]:
        raise ValueError("Nordic native numerical receipt does not admit output")
    if (
        _cell(terminal, "comparison_files", "report.json", "sha256")
        != CAPTURE_PINS[FAMILY + "/report.json"]
    ):
        raise ValueError("Nordic numerical output authority differs")
    if (
        report["source_census_sha256"]
        != CAPTURE_PINS[FAMILY + "/verification/source-census.json"]
    ):
        raise ValueError("Nordic original census authority differs")
    census_terminal = _record(inputs["verification/source-census-terminal.json"])
    if (
        census_terminal["native_exit_code"] != 0
        or _cell(census_terminal, "comparison_files", "report.json", "sha256")
        != report["source_census_sha256"]
    ):
        raise ValueError("Nordic source census terminal differs")
    for kind in ("scalar", "physical"):
        review = _record(inputs[f"verification/independent-{kind}-review.json"])
        receipt = _record(inputs[f"verification/independent-{kind}-terminal.json"])
        if (
            receipt["native_exit"] != 0
            or receipt["supervisor_exit"] != 0
            or receipt["frozen_input_custody_before_after"] != "unchanged"
        ):
            raise ValueError("Nordic independent review terminal differs")
        if (
            _cell(receipt, "outputs", "review.json", "sha256")
            != CAPTURE_PINS[FAMILY + f"/verification/independent-{kind}-review.json"]
            or receipt["plan_sha256"] != review["plan_sha256"]
        ):
            raise ValueError("Nordic independent review output authority differs")
        if (
            review["source_report_sha256"] != CAPTURE_PINS[FAMILY + "/report.json"]
            or review["source_native_terminal_sha256"]
            != CAPTURE_PINS[FAMILY + "/verification/native-terminal.json"]
        ):
            raise ValueError("Nordic independent review source scope differs")
    scalar = _record(inputs["verification/independent-scalar-review.json"])
    physical = _record(inputs["verification/independent-physical-review.json"])
    if (
        scalar["cases"] != 9
        or scalar["case_window_results"] != 182
        or scalar["scalar_values_compared"] != 6840
    ):
        raise ValueError("Nordic scalar review population differs")
    if (
        physical["actual_new_tuple_count"] != 23
        or physical["actual_case_target_uses"] != 29
        or physical["source_tuple_ledger_sha256"]
        != report["physical_response_tuples_sha256"]
    ):
        raise ValueError("Nordic physical review population differs")
    publication_inventory(inputs)
    return inputs
