"""Replay the retained Neotoma lake-parameter source review."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from bijux_pollenomics.analysis.lra.materialization.neotoma.lakeparameters import (
    assess_neotoma_lakeparameters,
)
from bijux_pollenomics.analysis.lra.materialization.neotoma.site_evidence import (
    NeotomaSiteEvidence,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture-root", type=Path, required=True)
    args = parser.parse_args()
    report_root = Path(__file__).resolve().parent
    expected = (report_root / "report.json").read_bytes()
    identity = json.loads(expected)
    site_bytes = (args.capture_root / "site-evidence.json").read_bytes()
    site_digest = hashlib.sha256(site_bytes).hexdigest()
    if site_digest != identity["site_evidence_sha256"]:
        raise ValueError("Retained site evidence differs from the lake review")
    site = NeotomaSiteEvidence(site_bytes, site_digest)
    result = assess_neotoma_lakeparameters(
        site, args.capture_root, identity["capture_sha256"]
    )
    if result.canonical_json != expected or identity["lra_admitted_samples"] != 0:
        raise ValueError("Lake review differs from the retained refused result")
    print(
        f"verified {identity['source_table_rows']} source rows, "
        f"{identity['candidate_sites_with_observed_parameter_rows']} "
        "candidate matches and zero LRA admissions"
    )


if __name__ == "__main__":
    main()
