"""Verify all retained counting draws and marginals using scalar equations."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any


def verify_counting_coverage(
    *, repository: Path, protocol_path: Path, products: Path, output: Path
) -> dict[str, Any]:
    """Recompute all quotient derivatives without importing the inverse engine."""
    repository = repository.resolve()
    if any(
        not p.resolve().is_relative_to(repository)
        for p in (protocol_path, products, output)
    ):
        raise ValueError(
            "Counting review inputs and output must be owned by the repository"
        )
    if output.exists() or not output.resolve().is_relative_to(repository / "artifacts"):
        raise ValueError("Counting review output must be an absent artifacts file")
    protocol: dict[str, Any] = json.loads(protocol_path.read_bytes())
    paths = [
        protocol_path,
        products / "report.json",
        products / "replicate-taxon-results.csv",
        products / "actual-multinomial-draws.jsonl",
    ]
    pins = {
        (
            "protocol.json" if p == protocol_path else "products/" + p.name
        ): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in paths
    }
    with (products / "replicate-taxon-results.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    index = {(r["case"], int(r["replicate"]), r["taxon"]): r for r in rows}
    assert len(index) == len(rows) == 30000
    cases = {c["name"]: c for c in protocol["cases"]}
    truths = {t["name"]: t["vector"] for t in protocol["truths"]}
    axis = protocol["taxon_axis"]
    ppe = protocol["source_ppe"]
    totals = protocol["fixed_panel_totals"]
    max_cover = max_variance = 0.0
    draw_count = 0
    for line in (products / "actual-multinomial-draws.jsonl").read_text().splitlines():
        draw = json.loads(line)
        counts = draw["site_counts"]
        assert len(counts) == len(totals)
        assert all(
            sum(row) == n and all(type(v) is int and v >= 0 for v in row)
            for row, n in zip(counts, totals, strict=True)
        )
        case = cases[draw["case"]]
        truth = truths[case["truth"]]
        factors = [
            [
                1.0
                / (
                    k
                    * p
                    * (
                        1.5
                        if case["assumed_deposition"]
                        == "multiply_only_Alnus_column_by_1.5"
                        and j == 0
                        else 1.0
                    )
                )
                for j, (k, p) in enumerate(zip(site, ppe, strict=True))
            ]
            for site in protocol["fixed_deposition"]
        ]
        weights = [
            math.fsum(counts[s][j] * factors[s][j] for s in range(len(totals)))
            for j in range(len(axis))
        ]
        weight_sum = math.fsum(weights)
        for i, taxon in enumerate(axis):
            cover = weights[i] / weight_sum
            # Independent marginal multinomial quadratic form, expanded in counts.
            variance = 0.0
            for s, n in enumerate(totals):
                derivative = [
                    factors[s][j] * ((1.0 if i == j else 0.0) - cover) / weight_sum
                    for j in range(len(axis))
                ]
                variance += (
                    math.fsum(
                        counts[s][j] * derivative[j] ** 2 for j in range(len(axis))
                    )
                    - math.fsum(counts[s][j] * derivative[j] for j in range(len(axis)))
                    ** 2
                    / n
                )
            row = index[(draw["case"], draw["replicate"], taxon)]
            max_cover = max(max_cover, abs(cover - float(row["cover"])))
            max_variance = max(
                max_variance, abs(variance - float(row["counting_variance"]))
            )
            assert math.isclose(
                cover, float(row["cover"]), rel_tol=2e-12, abs_tol=2e-14
            )
            assert math.isclose(
                variance, float(row["counting_variance"]), rel_tol=2e-12, abs_tol=2e-18
            )
            assert math.isclose(
                float(row["standard_error"]) ** 2,
                variance,
                rel_tol=2e-12,
                abs_tol=2e-18,
            )
            assert float(row["truth"]) == truth[i]
            assert (
                float(row["unclipped_wald_lower"])
                <= truth[i]
                <= float(row["unclipped_wald_upper"])
            ) == (row["truth_covered"] == "True")
            assert int(row["pooled_count"]) == sum(c[i] for c in counts)
            assert (row["zero_standard_error"] == "True") == (variance == 0.0)
        draw_count += 1
    report = json.loads((products / "report.json").read_text())
    for case in report["cases"]:
        for metric in case["metrics"]:
            selected = [
                r
                for r in rows
                if r["case"] == case["case"]["name"] and r["taxon"] == metric["taxon"]
            ]
            assert len(selected) == metric["accepted"] == 1000
            assert (
                sum(r["truth_covered"] == "True" for r in selected) == metric["covered"]
            )
            assert (
                sum(r["zero_standard_error"] == "True" for r in selected)
                == metric["zero_standard_error_replicates"]
            )
            assert (
                sum(r["zero_pooled_count"] == "True" for r in selected)
                == metric["zero_pooled_count_replicates"]
            )
    assert pins == {
        (
            "protocol.json" if p == protocol_path else "products/" + p.name
        ): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in paths
    }
    result = {
        "native_exit": 0,
        "scope": "Independent scalar review of retained synthetic counting diagnostics; no empirical truth or coverage certification.",
        "draws_reviewed": draw_count,
        "marginals_reviewed": len(rows),
        "scalar_cover_and_variance_comparisons": len(rows) * 2,
        "max_cover_absolute_difference": max_cover,
        "max_variance_absolute_difference": max_variance,
        "source_pins_unchanged": pins,
        "poor_outcomes_preserved": True,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    return result


def main() -> int:
    """Write the independent all-values review separately from numerical products."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--products", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = verify_counting_coverage(
        repository=args.repository,
        protocol_path=args.protocol,
        products=args.products,
        output=args.output,
    )
    print(json.dumps({k: v for k, v in result.items() if k != "source_pins_unchanged"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
