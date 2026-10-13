"""Project admitted synthetic recovery and conditional counting diagnostics."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

PACKET = Path("data/synthetic-validation/finite-count-coverage")
PACKET_SHA256 = "e26177ae94110418f011a9a3a821ed1a5735dedeb3ec524be36baa8f1d8bdbbc"
RECONSTRUCTION = Path("docs/report/synthetic-validation/reconstruction/report.json")
RECONSTRUCTION_SHA256 = (
    "5023c8d46e58680492ce3bc821d1db6ff10af1c0ad7f7bb75907aa3562e19e84"
)


def _read(path: Path, expected: str) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Synthetic evidence must be a regular file: {path.name}")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError(f"Synthetic evidence identity differs: {path.name}")
    return raw


def build_recovery_evidence(repository: Path) -> dict[str, Any]:
    """Retain every control and coverage metric from exact immutable inputs.

    This account reads completed numerical products. It performs no forward,
    inverse, sampling or uncertainty calculation, and cannot certify coverage.
    """
    manifest = json.loads(_read(repository / PACKET / "manifest.json", PACKET_SHA256))
    if manifest["schema_version"] != "synthetic-counting-source-packet.v1":
        raise ValueError("Synthetic counting packet schema differs")
    inputs = {}
    for name, identity in manifest["files"].items():
        if Path(name).name != name:
            raise ValueError("Synthetic evidence member escapes its packet")
        raw = _read(repository / PACKET / name, identity["sha256"])
        if len(raw) != identity["bytes"]:
            raise ValueError("Synthetic evidence member size differs")
        inputs[name] = raw
    coverage = json.loads(inputs["report.json"])
    protocol = json.loads(inputs["protocol.json"])
    review = json.loads(inputs["independent-review.json"])
    reconstruction = json.loads(
        _read(repository / RECONSTRUCTION, RECONSTRUCTION_SHA256)
    )
    if coverage["candidate"] != manifest["candidate"]:
        raise ValueError("Synthetic counting candidate differs")
    if coverage["uncertainty_coverage_certified"] is not False:
        raise ValueError("Conditional counting diagnostic cannot certify coverage")
    if review["native_exit"] != 0 or review["poor_outcomes_preserved"] is not True:
        raise ValueError("Independent counting review is incomplete")
    return {
        "schema_version": "synthetic-recovery-evidence.v1",
        "reconstruction_source": {
            "path": RECONSTRUCTION.as_posix(),
            "sha256": RECONSTRUCTION_SHA256,
            "prospective_contract": reconstruction["prospective_contract"],
            "denominators": reconstruction["denominators"],
        },
        "reconstruction_cases": [
            {
                key: case[key]
                for key in (
                    "case_id",
                    "source_profile",
                    "source_report_sha256",
                    "source_case_sha256",
                    "control",
                    "transport_matched",
                    "inverse_crime_control",
                    "interpretation",
                    "status",
                    "contract_status",
                    "vegetation_mae_fraction",
                    "calculation_max_abs_error_fraction",
                    "deposition_max_abs_error",
                )
            }
            for case in reconstruction["cases"]
        ],
        "counting_source": {
            "path": PACKET.as_posix(),
            "manifest_sha256": PACKET_SHA256,
            "candidate": coverage["candidate"],
            "protocol_sha256": coverage["protocol_sha256"],
            "original_plan_sha256": coverage["plan_sha256"],
            "files": manifest["files"],
            "protocol": protocol,
            "scope": coverage["scope"],
            "independent_review": review,
            "execution_custody": json.loads(inputs["execution-custody.json"]),
        },
        "counting_cases": coverage["cases"],
        "claims": {
            "independent_forward_generator": True,
            "matched_method_controls_are_inverse_crime": True,
            "different_forward_model_mismatches_preserved": True,
            "conditional_counting_coverage_diagnostics": True,
            "empirical_ecological_accuracy": False,
            "coverage_certified": False,
            "global_method_certification": False,
        },
    }


def main() -> int:
    """Write a deterministic retained account under an explicit output path."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build_recovery_evidence(args.repository)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
