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
POLLEN = Path(
    "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/resources/data/LOVEexamplePollen.json"
)
RINGS = Path(
    "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/resources/data/LOVEexampleRings.json"
)
PINNED = {
    PAPER: "9c0ce8de012ee978d158a402856fd4fcf3fbda3fcaf71d6257964b893b9a392e",
    EXAMPLE: "34e861280b7a6ee4bc2d938f2f7c891ea057c44cdc3bfd60e5c27eadca915430",
    POLLEN: "40e94bd1b261097ba6417054975f60a6d525b239cf3604079030e0929f0e0fcc",
    RINGS: "bd574247e704e446dd2d3d70895aeefeae6d6d9f067436e289692cf3a5048445",
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
    pollen, pollen_input = _read_pinned(repository, POLLEN)
    rings, rings_input = _read_pinned(repository, RINGS)
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
    pollen_table = pollen.get("LOVEexamplePollen")
    ring_table = rings.get("LOVEexampleRings")
    if not isinstance(pollen_table, dict) or not isinstance(ring_table, dict):
        raise ValueError("Package LOVE example pollen or ring table missing")
    pollen_rows = pollen_table.get("data")
    ring_rows = ring_table.get("data")
    if not isinstance(pollen_rows, list) or not isinstance(ring_rows, list):
        raise ValueError("Package LOVE example rows missing")
    if pollen_table.get("index") != ["local", "regional"] or len(pollen_rows) != 2:
        raise ValueError("Package LOVE example pollen scope changed")
    if len(ring_rows) != 36 or ring_rows[-1][5] != 100000.0:
        raise ValueError("Package LOVE example ring scope changed")
    return {
        "schema_version": "love-paper-source-parameter-correspondence.v1",
        "status": "bounded_numeric_match",
        "inputs": [paper_input, example_input, pollen_input, rings_input],
        "compared_taxa": len(comparisons),
        "compared_numeric_cells": len(comparisons) * 3,
        "numeric_cells_equal": len(comparisons) * 3,
        "exact_label_rows": len(comparisons) - len(differing),
        "different_label_rows": differing,
        "rows": comparisons,
        "package_example_scope": {
            "pollen_row_labels": pollen_table["index"],
            "pollen_row_count": len(pollen_rows),
            "ring_row_count": len(ring_rows),
            "last_ring_outer_as_published": ring_rows[-1][5],
        },
        "scope": "Published Table 2 versus pinned later DISQOVER example parameters. The packaged two-row pollen/one-ring-layout example is not the article's eight-pond Figure 2 simulation; the software version and spatial/draw inputs remain unestablished.",
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
