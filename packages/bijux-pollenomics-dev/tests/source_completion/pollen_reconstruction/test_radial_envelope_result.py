"""Independently verify a closed finite radial-mass result; no producer imports."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import time
from typing import Any

from .spatial_field_forward.radial_envelope.certificates import (
    quadrature_rules,
    verify_geometry,
)
from .spatial_field_forward.radial_envelope.exact_arithmetic import require
from .spatial_field_forward.radial_envelope.result_checks import (
    same,
    verify_contexts,
    verify_scores,
    verify_summaries,
)
from .spatial_field_forward.radial_envelope.sources import (
    CORES,
    bound,
    decode,
    prediction_inputs,
)


def verify(repository: Path, result_path: Path) -> dict[str, Any]:
    started = time.monotonic()
    repository = repository.resolve()
    protocol, prior, original = prediction_inputs(repository)
    prediction_path = result_path.parent / "prediction-ranges.json"
    prediction_body = prediction_path.read_bytes()
    packet = decode(prediction_body)
    require(
        packet["schema_version"] == "spatial-field-radial-envelope-predictions.v1"
        and packet["prior_source_commit"] == prior["source_commit"],
        "new prediction authority differs",
    )
    pins = {name: pin["sha256"] for name, pin in protocol["repository_inputs"].items()}
    same(packet["input_sha256"], pins)
    same(packet["finite_target"], protocol["finite_target"])
    same(packet["scope"], protocol["scope"])
    require(
        len(packet["geometry"]) == 3
        and [row["core"] for row in packet["geometry"]] == list(CORES),
        "complete geometry population required",
    )
    rules = quadrature_rules()
    geometries = {
        row["core"]: verify_geometry(row, old, protocol, original, rules)
        for row, old in zip(packet["geometry"], prior["geometry"], strict=True)
    }
    contexts = verify_contexts(packet, prior, geometries)
    require(packet["actual_ring_calls"] == 768, "fixed ring-call population differs")
    # Native scored observations enter only after every prediction certificate
    # and held-place boundary above has been checked against the closed packet.
    native = decode(
        bound(
            repository,
            protocol["source_result"],
            protocol["repository_inputs"][protocol["source_result"]],
        )
    )
    require(
        native["source_commit"] == prior["source_commit"]
        and native["prediction_file"]["sha256"] == pins[protocol["source_prediction"]],
        "native result belongs to another prediction packet",
    )
    result_body = result_path.read_bytes()
    result = decode(result_body)
    require(
        result["schema_version"] == "spatial-field-radial-envelope-result.v1"
        and result["status"] == "conditional_finite_mass_radial_envelope",
        "new result schema/status differs",
    )
    head = subprocess.check_output(
        ["git", "-C", str(repository), "rev-parse", "HEAD"], text=True, timeout=10
    ).strip()
    require(
        result["source_commit"] == packet["source_commit"] == head,
        "producer source no longer matches frozen HEAD",
    )
    same(result["input_sha256"], pins)
    same(
        result["prediction_file"],
        {
            "path": prediction_path.name,
            "bytes": len(prediction_body),
            "sha256": sha256(prediction_body).hexdigest(),
        },
    )
    same(
        result["native_population"],
        {
            "source_rows": 147,
            "selected_samples": 59,
            "contexts": 18,
            "family_outcomes": 54,
        },
    )
    require(
        result["actual_ring_calls"] == 768
        and result["model_fits"] == result["new_point_predictions"] == 0,
        "new calls or model fits were introduced",
    )
    require(
        all(
            result[flag] is False
            for flag in (
                "raw_count_or_age_inputs_read",
                "prior_point_values_changed",
                "true_integral_or_field_accuracy_claim",
            )
        ),
        "scientific scope was promoted",
    )
    for key in ("finite_target", "scope", "rights_and_use"):
        same(result[key], protocol[key])
    rows = verify_scores(result, native, prior, contexts)
    verify_summaries(result["summaries"], rows, native["summaries"])
    refused = sum(row["refused_ring_calls"] for row in geometries.values())
    references = sum(
        row["reference_point_status"] == "refused_reference_point_correspondence"
        for row in rows
    )
    require(
        result["refused_ring_calls"] == refused
        and result["reference_point_refusals"] == references,
        "failed ring/reference population differs",
    )
    require(
        prediction_path.read_bytes() == prediction_body
        and result_path.read_bytes() == result_body,
        "closed outputs changed during verification",
    )
    for relative, pin in protocol["repository_inputs"].items():
        bound(repository, relative, pin)
    return {
        "status": "independent_finite_radial_envelope_pass",
        "source_commit": head,
        "result_sha256": sha256(result_body).hexdigest(),
        "prediction_sha256": sha256(prediction_body).hexdigest(),
        "source_rows": 147,
        "selected_samples": 59,
        "contexts": 18,
        "family_outcomes": 54,
        "ring_outcomes_checked": 768,
        "refused_ring_calls": refused,
        "reference_point_refusals": references,
        "maximum_projection_correspondence_gap_m": max(
            row["projection_gap"] for row in geometries.values()
        ),
        "maximum_angular_correspondence_gap": max(
            row["angular_gap"] for row in geometries.values()
        ),
        "maximum_angular_resolution_gap": max(
            row["angular_resolution_gap"] for row in geometries.values()
        ),
        "repeated_ring_quadratures": 0,
        "true_integral_or_field_accuracy_claim": False,
        "elapsed_seconds": time.monotonic() - started,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repository = args.repository.resolve()
    output = args.output.absolute()
    require(
        ".." not in args.output.parts
        and output.resolve().is_relative_to(repository / "artifacts")
        and not output.exists()
        and not any(parent.is_symlink() for parent in output.parents),
        "absent artifacts output with regular ancestry required",
    )
    result = verify(repository, args.result.resolve())
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result, allow_nan=False))


if __name__ == "__main__":
    main()
