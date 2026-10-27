"""Freeze conditional coupled-pollen predictions before outcome diagnostics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import time
from typing import Any

import numpy as np

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)

from .draws import generate_draw_bank, nominal_draw_bank
from .inputs import METHODS, InputPacket, load_inputs
from .predictions import predict_case
from .products import (
    StudyError,
    _git_state,
    _loaded_code,
    _pin,
    _plain,
    _read_product,
    _resource_check,
    _source_check,
    _write,
)
from .scoring import joint_predictions, score_diagnostics


def _nominal(packet: InputPacket, bank: Any, tolerance: float) -> list[dict[str, Any]]:
    references = {(r["case_id"], r["method"]): r for r in packet.nominal_predictions}
    result = []
    for case in sorted(packet.cases, key=lambda item: item.case_id):
        row = predict_case(case, bank)
        for method in METHODS:
            values = row["methods"][method]
            reference = references[(case.case_id, method)]
            if values["valid_mask"] != [True]:
                raise StudyError(
                    "Original nominal domain-eligible prediction now refuses"
                )
            pollen = values["pollen"][0]
            cover = values["cover"][0]
            for observed, expected in (
                (pollen, reference["pollen_fraction"]),
                (cover, reference["vegetation_fraction"]),
            ):
                if not np.allclose(observed, expected, rtol=0, atol=tolerance):
                    raise StudyError(
                        "Nominal source correspondence exceeds its original bound"
                    )
            result.append(
                {
                    "case_id": case.case_id,
                    "target_id": case.target_id,
                    "method": method,
                    "pollen_fraction": pollen,
                    "vegetation_fraction": cover,
                    "reference_prediction_manifest_sha256": reference[
                        "prediction_manifest_sha256"
                    ],
                }
            )
    if len(result) != 9:
        raise StudyError("Exactly nine nominal comparisons required")
    return result


def produce(repository: Path, protocol_path: Path, output: Path) -> dict[str, Any]:
    """Freeze all numerical draws/predictions before new outcome diagnostics."""
    started = time.monotonic()
    repository = repository.resolve(strict=True)
    protocol_path = protocol_path.resolve(strict=True)
    output = require_absent_artifact_output(repository, output)
    protocol_raw = protocol_path.read_bytes()
    protocol = json.loads(protocol_raw)
    packet = load_inputs(repository, protocol)
    inputs = {"protocol": protocol, **_plain(packet)}
    _source_check(repository, inputs)
    code = _loaded_code(repository)
    head, index = _git_state(repository)
    owner_ids = {case.regional_owner_id for case in packet.cases} | {
        local.owner_id for case in packet.cases for local in case.local_owners
    }
    owners = tuple(owner for owner in packet.owners if owner.owner_id in owner_ids)
    if len(owners) != 4:
        raise StudyError("Exactly four active owner/windows may be resampled")
    sampling = protocol["sampling"]
    means = (float(sampling["ppe_means"][0]), float(sampling["ppe_means"][1]))
    nominal = _nominal(
        packet,
        nominal_draw_bank(owners, ppe_means=means),
        protocol["numerical_checks"]["nominal_prediction_absolute_tolerance"],
    )
    bank = generate_draw_bank(
        owners,
        replicates=sampling["replicates"],
        seed=sampling["seed"],
        ppe_means=means,
        ppe_sds=(float(sampling["ppe_sds"][0]), float(sampling["ppe_sds"][1])),
    )
    predicted = {
        "schema_version": "krageholm-predictive-ensemble.v1",
        "cases": [
            predict_case(case, bank)
            for case in sorted(packet.cases, key=lambda item: item.case_id)
        ],
        "original_dispositions": _plain(packet.dispositions),
        "nominal_predictions": nominal,
    }
    limits = protocol["limits"]
    output.mkdir()
    pins = {
        "inputs": _write(output / "inputs.json", inputs, limits["max_output_bytes"]),
        "draws": _write(output / "draws.json", bank, limits["max_output_bytes"]),
        "predictions": _write(
            output / "predictions.json", predicted, limits["max_output_bytes"]
        ),
    }
    manifest = {
        "schema_version": "coupled-pollen-bootstrap-freeze.v1",
        "files": pins,
        "role": "Whole-run accounting only; fold scientific ancestry is each case allowed_inputs plus its allowed source references.",
    }
    manifest_pin = _write(
        output / "prediction-manifest.json", manifest, limits["max_output_bytes"]
    )
    closed_manifest = _read_product(output, manifest_pin)
    if closed_manifest["files"] != pins:
        raise StudyError(
            "Prediction freeze member bindings differ before outcome access"
        )
    # Outcome diagnostics consume the closed serialized prediction, not a mutable array.
    reopened = {key: _read_product(output, pin) for key, pin in pins.items()}
    summary = {
        "schema_version": "coupled-pollen-bootstrap-summary.v1",
        "joint_predictions": joint_predictions(reopened["predictions"]["cases"]),
        "score_diagnostics": score_diagnostics(
            reopened["inputs"], reopened["predictions"]
        ),
        "outcome_access": {
            "prediction_manifest_sha256": manifest_pin["sha256"],
            "readback_verified": True,
            "scope": "Previously exposed; postfreeze diagnostic only",
        },
    }
    pins["summary"] = _write(
        output / "summary.json", summary, limits["max_output_bytes"]
    )
    _source_check(repository, inputs)
    if (
        protocol_path.read_bytes() != protocol_raw
        or any(path.read_bytes() != raw for path, raw in code.items())
        or _git_state(repository) != (head, index)
    ):
        raise StudyError(
            "Consumed source, protocol, HEAD or index changed during study"
        )
    resources = _resource_check(started, output, limits)
    result = {
        "schema_version": "coupled-pollen-bootstrap-result.v1",
        "status": "produced_awaiting_independent_verification",
        "source_commit": head,
        "source_guards_passed": True,
        "input_files_checked": len(packet.source_files),
        "loaded_code_files_checked": len(code),
        "protocol": _pin(protocol_path, repository),
        "products": pins,
        "prediction_manifest": manifest_pin,
        "resources": resources,
    }
    _write(output / "result.json", result, limits["max_output_bytes"])
    _resource_check(started, output, limits)
    return result


def main() -> None:
    """Run one explicitly declared source-bootstrap producer."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = produce(args.repository, args.protocol, args.output)
    print(json.dumps({"status": result["status"], "resources": result["resources"]}))


if __name__ == "__main__":
    main()
