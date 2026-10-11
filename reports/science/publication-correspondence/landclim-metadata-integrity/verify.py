"""Bind the independent metadata check to current governed outputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
REPORT = Path(__file__).with_name("result.json")
PRODUCT = ROOT / "docs/report/publication-replay/landclim-study-inputs"
MEMBERS = {
    "manifest.json",
    "primary-source-crosswalk.csv",
    "records.jsonl",
    "refusals.csv",
    "report.json",
}


def main() -> None:
    result = json.loads(REPORT.read_text(encoding="utf-8"))
    if result["verdict"] != "pass_scoped_metadata_bundle":
        raise ValueError("Independent metadata verdict changed")
    if len(result["checks"]) != 8 or not all(
        item["passed"] is True for item in result["checks"]
    ):
        raise ValueError("Independent metadata checks are incomplete")
    if len(result["mutation_results"]) != 9 or set(
        result["mutation_results"].values()
    ) != {"StudyInputProductError"}:
        raise ValueError("Adversarial refusal evidence changed")
    if set(result["product_hashes"]) != MEMBERS:
        raise ValueError("Historical product inventory changed")
    for member, expected in result["product_hashes"].items():
        path = PRODUCT / member
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Current governed product differs: {member}")
    claims = result["claim_boundary"]
    if (
        claims["essd_full_reproduction"] is not False
        or claims["publication_specific_r_executed"] is not False
    ):
        raise ValueError("Historical claim boundary changed")
    print(
        "five governed outputs match; eight historical checks and nine refusals retained"
    )


if __name__ == "__main__":
    main()
