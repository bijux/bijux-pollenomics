"""Check the retained R replay against its present source and vector closure."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    replay = json.loads((HERE / "source-replay.json").read_text())
    retained = json.loads((HERE / "report.json").read_text())
    if replay["schema_version"] != "native-r-source-replay.v1":
        raise ValueError("Unexpected R source replay schema")
    for field in ("current_inputs_sha256", "analysis_inputs_sha256"):
        for relative, expected in replay[field].items():
            if sha256(ROOT / relative) != expected:
                raise ValueError(f"R replay source changed: {relative}")
    if (
        sha256(ROOT / "configs/ci/lra-r-source-lock.v1.json")
        != replay["source_lock_sha256"]
        or sha256(
            ROOT
            / "docs/report/method-certification/original-r-reference/reference-bundle/certificate.json"
        )
        != replay["original_certificate_sha256"]
        or sha256(
            ROOT
            / "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/live_reference_comparison.py"
        )
        != replay["runner_sha256"]
    ):
        raise ValueError("R replay authority changed")
    vectors = {
        relative: digest
        for relative, digest in retained["raw_results_sha256"].items()
        if relative.endswith(".csv")
    }
    summary = replay["retained_numeric_csv"]
    if (
        len(vectors) != summary["file_count"]
        or hashlib.sha256(
            json.dumps(vectors, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        != summary["mapping_sha256"]
        or any(sha256(HERE / relative) != digest for relative, digest in vectors.items())
    ):
        raise ValueError("Retained R numeric vectors changed")
    cases = replay["cases"]
    if (
        (cases["core_attempted"], cases["core_passed"]) != (43, 43)
        or (cases["source_domain_attempted"], cases["source_domain_passed"])
        != (23, 23)
        or (cases["optimized_love_passed"], len(cases["optimized_love_ids"]))
        != (18, 18)
        or (
            cases["original_r_vectors_compared"],
            cases["original_r_vectors_passed"],
        )
        != (48, 48)
    ):
        raise ValueError("R replay case denominator changed")
    print("verified current R source closure and 97 retained numeric CSV files")


if __name__ == "__main__":
    main()
