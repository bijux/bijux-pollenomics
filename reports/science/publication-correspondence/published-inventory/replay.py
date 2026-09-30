"""Reconcile current published-estimate source rows with independent checks."""

from __future__ import annotations

import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path

from bijux_pollenomics.collection.sources.landclim.published_inventory import (
    read_landclim_published_inventory,
)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ZERO = Decimal(0)
ONE = Decimal(1)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(raw_root: Path) -> dict[str, object]:
    independent = json.loads((HERE / "independent-inventory.json").read_text())
    structure = json.loads((HERE / "independent-structure.json").read_text())
    source = independent["inputs"]
    for kind in ("archive", "receipt"):
        entry = source[kind]
        if _digest(raw_root / Path(entry["path"]).name) != entry["sha256"]:
            raise ValueError(f"{kind} no longer matches independent source")
    if independent["verdict"] != "pass_scoped_published_inventory_closure":
        raise ValueError("Independent inventory verdict changed")
    if structure["verdict"] != "pass_published_row_structure":
        raise ValueError("Independent structure verdict changed")
    inventory = read_landclim_published_inventory(raw_root)
    counts = {
        "paired_records": len(inventory.records),
        "paired_values": 0,
        "variables": len(inventory.variables),
        "coordinate_available_records": 0,
        "coordinate_refused_records": 0,
        "mean_numeric_zero_values": 0,
        "mean_literal_zero_tokens": 0,
        "mean_values_above_one": 0,
        "mean_negative_values": 0,
        "mean_negative_records": 0,
        "standard_error_negative_values": 0,
        "mean_members": len(inventory.time_windows),
        "standard_error_members": len(inventory.time_windows),
    }
    refused_ids: set[str] = set()
    negative: list[dict[str, str]] = []
    for record in inventory.records:
        counts[f"coordinate_{record.coordinate_status}_records"] += 1
        if record.coordinate_status == "refused":
            refused_ids.add(record.cell_id)
        has_negative = False
        for estimate in record.estimates:
            counts["paired_values"] += 1
            if estimate.mean == ZERO:
                counts["mean_numeric_zero_values"] += 1
            if estimate.mean_token == "0":
                counts["mean_literal_zero_tokens"] += 1
            if estimate.mean > ONE:
                counts["mean_values_above_one"] += 1
            if estimate.mean < ZERO:
                counts["mean_negative_values"] += 1
                has_negative = True
                negative.append(
                    {
                        "cell_id": record.cell_id,
                        "time_window": record.time_window,
                        "variable": estimate.variable,
                        "mean_token": estimate.mean_token,
                    }
                )
            if estimate.standard_error < ZERO:
                counts["standard_error_negative_values"] += 1
        if has_negative:
            counts["mean_negative_records"] += 1
    if counts != independent["independent_counts"]:
        raise ValueError("Current source counts differ from independent check")
    if sorted(refused_ids) != independent["coordinate_refused_ids"]:
        raise ValueError("Current coordinate refusals differ from independent check")
    if (
        structure["counts"]["negative_mean_values"] != counts["mean_negative_values"]
        or structure["counts"]["negative_mean_rows"] != counts["mean_negative_records"]
    ):
        raise ValueError("Signed source values differ from independent structure")
    observed_signed = sorted(
        (
            row["cell_id"],
            inventory.time_windows.index(row["time_window"]) + 1,
            row["variable"],
            row["mean_token"],
        )
        for row in negative
    )
    independent_signed = sorted(
        (
            row["cell_id"],
            row["time_window"],
            row["variable"],
            str(row["value"]),
        )
        for row in structure["counts"]["signed_mean_facts"]
    )
    if observed_signed != independent_signed:
        raise ValueError("Signed source identities differ from independent structure")
    return {
        "schema_version": "published-estimate-source-account.v1",
        "dataset_doi": inventory.dataset_doi,
        "evidence_role": inventory.evidence_role,
        "unit": inventory.value_unit,
        "source": source,
        "inventory_sha256": inventory.sha256,
        "independent_inventory_sha256": _digest(HERE / "independent-inventory.json"),
        "independent_structure_sha256": _digest(HERE / "independent-structure.json"),
        "counts": counts,
        "coordinate_refused_ids": sorted(refused_ids),
        "negative_mean_values": negative,
        "admission": {
            "published_products_only": True,
            "historical_primary_inputs_authenticated": False,
            "measured_vegetation": False,
            "whole_paper_reproduction": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, default=ROOT / "data/landclim/raw")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    value = build(args.raw_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    print(
        f"{value['counts']['paired_records']} rows; {value['counts']['paired_values']} pairs"
    )


if __name__ == "__main__":
    main()
