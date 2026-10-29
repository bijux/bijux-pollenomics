"""Matched finite-regional-cutoff stress controls using the original Nordic packet."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_dev.ci.report_rebuild.source_paths import safe_source_file
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.nordic_static_basin.transport_sensitivity import (
    calculation,
    inputs,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.nordic_static_basin.transport_sensitivity import (
    producer as wind_producer,
)

PROTOCOL = "docs/report/pollen-reconstruction/nordic-static-basin-scenarios/assumptions/regional-extent-sensitivity.json"
PROTOCOL_SHA256 = "0df05eaefe94e96b03ae29c85559fe0656016b6ced99461a7940c6504fae9dd6"
PROTOCOL_FINGERPRINT = (
    "d6b9e6e26119f25874c4aa321e2378e26a557fc992e762ca078ad27e8bce7392"
)


def _validate_protocol(protocol: dict[str, Any]) -> None:
    if inputs.fingerprint(protocol) != PROTOCOL_FINGERPRINT:
        raise ValueError("Frozen numerical regional-cutoff protocol differs")


def calculate(
    report: dict[str, Any], protocol: dict[str, Any], baseline_protocol: dict[str, Any]
) -> dict[str, Any]:
    """Retain every matched alternative window and its separate numerical status."""
    _validate_protocol(protocol)
    cases = inputs.prepare(report, baseline_protocol)
    ledger: dict[tuple[float, float, int], dict[str, Any]] = {}
    output = []
    for case in cases:
        radius = float(case["static_geometry"]["radius_m"])
        for extent in protocol["alternative_regional_extent_m"]:
            responses = []
            for speed in case["fall_speed_m_s"]:
                key = (radius, float(speed), extent)
                if key not in ledger:
                    parameters = {
                        "receiver_radius_m": radius,
                        "inner_radius_m": radius,
                        "outer_radius_m": extent,
                        "fall_speed_m_s": float(speed),
                        "diffusion_coefficient": 0.12,
                        "turbulence_parameter": 0.25,
                        "wind_speed_m_s": 3,
                    }
                    item: dict[str, Any] = {
                        "tuple_id": f"extent-tuple:{len(ledger) + 1}",
                        "parameters": parameters,
                    }
                    try:
                        value = calculation._kernel(
                            radius, float(speed), 3, outer_radius_m=extent
                        )
                        if (
                            set(value) != {"factor", "estimated_absolute_error"}
                            or type(value["factor"]) not in (int, float)
                            or not math.isfinite(value["factor"])
                            or not 0 < value["factor"] <= 1
                            or type(value["estimated_absolute_error"])
                            not in (int, float)
                            or not math.isfinite(value["estimated_absolute_error"])
                            or value["estimated_absolute_error"] < 0
                        ):
                            raise ValueError(
                                "Maintained annulus returned an invalid result"
                            )
                        item.update(status="computed", response=value, reason=None)
                    except calculation.NumericalRefusal as error:
                        item.update(status="refused", response=None, reason=str(error))
                    ledger[key] = item
                responses.append(ledger[key])
            failures = [
                item["tuple_id"] for item in responses if item["status"] == "refused"
            ]
            windows = []
            for saved in case["results"]:
                row: dict[str, Any] = {
                    "baseline_window_sha256": inputs.fingerprint(saved),
                    "source_window": {
                        k: v
                        for k, v in saved.items()
                        if k not in inputs.VECTOR_FIELDS + inputs.MATRIX_FIELDS
                    },
                    "status": "refused",
                    "reason": None,
                    "moments": None,
                    "alternative_minus_saved_extent100km": None,
                }
                if failures:
                    row["reason"] = {
                        "kind": "annulus_numerical_refusal",
                        "tuple_ids": failures,
                    }
                else:
                    try:
                        factors = [item["response"]["factor"] for item in responses]
                        moments = calculation._moments(case, saved, factors)
                        if set(moments) != set(
                            inputs.VECTOR_FIELDS + inputs.MATRIX_FIELDS
                        ):
                            raise ValueError("Maintained moment quantity set differs")
                        difference = {
                            name: calculation._difference(moments[name], saved[name])
                            for name in moments
                        }
                        row.update(
                            status="computed",
                            moments=moments,
                            alternative_minus_saved_extent100km=difference,
                        )
                    except calculation.NumericalRefusal as error:
                        row["reason"] = {
                            "kind": "fixed_site_numerical_refusal",
                            "message": str(error),
                        }
                windows.append(row)
            output.append(
                {
                    "case_id": case["case_id"] + f".extent_{extent}m",
                    "baseline_case_id": case["case_id"],
                    "source_case_sha256": inputs.fingerprint(case),
                    "regional_extent_m": extent,
                    "original_case_context": {
                        k: v
                        for k, v in case.items()
                        if k not in {"results", "physical_response"}
                    },
                    "physical_tuple_ids": [item["tuple_id"] for item in responses],
                    "windows": windows,
                }
            )
    rows = [row for case in output for row in case["windows"]]
    return {
        "schema_version": "nordic-conditional-regional-extent-result.v1",
        "protocol": protocol,
        "baseline_source_epoch": report["candidate"],
        "source_population": report["source_population"],
        "requested_alternative_cases": len(output),
        "requested_alternative_windows": len(rows),
        "computed_windows": sum(row["status"] == "computed" for row in rows),
        "refused_windows": sum(row["status"] == "refused" for row in rows),
        "unique_physical_tuple_requests": len(ledger),
        "physical_responses": list(ledger.values()),
        "cases": output,
        "scope": "Conditional 50/200 km numerical cutoff stress settings versus saved100km on unchanged source core/window/panel support, fixed wind3 and original dispersal law. These are not source-supported regional extents or probability distributions. Quadrature error estimates are nonrigorous; count/PPE covariance conditions on fixed chronology/geometry/transport. No field accuracy, independent sites, historical reproduction, rights or wholeLCI030 acceptance.",
    }


def load(repository: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Read the fixed baseline and byte-pinned regional-cutoff protocol."""
    report, baseline_protocol = wind_producer.load(repository)
    raw = safe_source_file(
        repository, PROTOCOL, "Regional-cutoff stress protocol"
    ).read_bytes()
    if len(raw) > 16384 or hashlib.sha256(raw).hexdigest() != PROTOCOL_SHA256:
        raise ValueError("Regional-cutoff protocol bytes changed")
    protocol: dict[str, Any] = json.loads(raw)
    _validate_protocol(protocol)
    return report, protocol, baseline_protocol


def publish(repository: Path, output: Path, *, execution_epoch: str) -> dict[str, Any]:
    """Write the declared cutoff sensitivity with its actual execution identity."""
    if re.fullmatch(r"[0-9a-f]{40}", execution_epoch) is None:
        raise ValueError("Actual execution epoch must be an exact Git SHA")
    repository = repository.absolute()
    destination = require_absent_artifact_output(repository, output)
    before = load(repository)
    result = calculate(*before)
    result["baseline_report"] = {"path": inputs.REPORT, "sha256": inputs.REPORT_SHA256}
    result["protocol_sha256"] = PROTOCOL_SHA256
    result["execution_epoch"] = execution_epoch
    raw = (
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode()
    if len(raw) > 8 * 1024**2 or load(repository) != before:
        raise ValueError("Output exceeds8MiB or original source changed")
    stage = Path(tempfile.mkdtemp(prefix="regional-cutoff-", dir=destination.parent))
    try:
        (stage / "report.json").write_bytes(raw)
        require_absent_artifact_output(repository, destination)
        os.rename(stage, destination)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return result


def main(argv: list[str] | None = None) -> int:
    """Publish regional-cutoff sensitivity and report refused windows."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--execution-epoch", required=True)
    args = parser.parse_args(argv)
    result = publish(args.repository, args.output, execution_epoch=args.execution_epoch)
    return 1 if result["refused_windows"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
