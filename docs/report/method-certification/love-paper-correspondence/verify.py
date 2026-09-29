"""Compare the published LOVE parameter table with the source package example."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

PAPER = Path(
    "docs/report/method-certification/love-paper-correspondence/paper-parameter-tables.json"
)
EXAMPLE = Path(
    "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/resources/data/LOVEexampleParams.json"
)
PINNED = {
    PAPER: "9c0ce8de012ee978d158a402856fd4fcf3fbda3fcaf71d6257964b893b9a392e",
    EXAMPLE: "34e861280b7a6ee4bc2d938f2f7c891ea057c44cdc3bfd60e5c27eadca915430",
}


def _read_pinned(
    repository: Path, relative: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    path = repository / relative
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Source input missing or linked: {relative}")
    content = path.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    if digest != PINNED[relative]:
        raise ValueError(f"Source input changed: {relative}")
    payload = json.loads(content)
    if not isinstance(payload, dict):
        raise ValueError(f"Source input is not an object: {relative}")
    return payload, {
        "path": relative.as_posix(),
        "bytes": len(content),
        "sha256": digest,
    }


def build_report(repository: Path) -> dict[str, Any]:
    """Require all published values to match the pinned example by row position."""
    paper, paper_input = _read_pinned(repository, PAPER)
    example, example_input = _read_pinned(repository, EXAMPLE)
    if paper.get("schema_version") != "love-paper-parameter-tables.v1":
        raise ValueError("Published parameter table schema changed")
    published = paper.get("table_2")
    example_rows = example.get("LOVEexampleParams", {}).get("ppes", {}).get("data")
    if not isinstance(published, list) or not isinstance(example_rows, list):
        raise ValueError("Published or package parameter table missing")
    if len(published) != len(example_rows) or len(published) != 10:
        raise ValueError("Expected ten published and package parameter rows")
    comparisons = []
    for index, (left, right) in enumerate(zip(published, example_rows, strict=True)):
        if not isinstance(left, dict) or not isinstance(right, list) or len(right) != 4:
            raise ValueError(f"Parameter row {index} has an unexpected shape")
        paper_values = [
            left["fall_speed_as_published"],
            left["relative_pollen_productivity"],
            left["ppe_sd"],
        ]
        package_values = right[1:]
        if any(
            type(value) not in (int, float) or value <= 0
            for value in paper_values + package_values
        ):
            raise ValueError(f"Parameter row {index} has invalid numeric values")
        residuals = [
            abs(float(a) - float(b))
            for a, b in zip(paper_values, package_values, strict=True)
        ]
        if any(residual != 0 for residual in residuals):
            raise ValueError(
                f"Published and package parameter values differ in row {index}"
            )
        comparisons.append(
            {
                "position": index + 1,
                "paper_taxon": left["taxon"],
                "package_taxon": right[0],
                "exact_label": left["taxon"] == right[0],
                "numeric_residuals": residuals,
            }
        )
    differing = [row for row in comparisons if not row["exact_label"]]
    if [(row["paper_taxon"], row["package_taxon"]) for row in differing] != [
        ("Grasses", "Gras")
    ]:
        raise ValueError("Published and package taxon labels differ unexpectedly")
    return {
        "schema_version": "love-paper-source-parameter-correspondence.v1",
        "status": "bounded_numeric_match",
        "inputs": [paper_input, example_input],
        "compared_taxa": len(comparisons),
        "compared_numeric_cells": len(comparisons) * 3,
        "numeric_cells_equal": len(comparisons) * 3,
        "exact_label_rows": len(comparisons) - len(differing),
        "different_label_rows": differing,
        "rows": comparisons,
        "scope": "Published Table 2 versus pinned later DISQOVER example parameters; this does not establish the software version or spatial inputs used for Figure 2.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.output.is_symlink():
        parser.error("Output destination must be absent")
    result = build_report(args.repository)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
