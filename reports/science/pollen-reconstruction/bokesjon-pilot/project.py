"""Project saved source-audit products into public tables without private rows."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def project(study: Path, output: Path) -> None:
    """Retain native reports and remove private lookup/workbook row witnesses."""
    if output.exists():
        raise ValueError("Absent projection directory required")
    result = json.loads((study / "result.json").read_text())
    if result["schema_version"] != "bokesjon-pilot-source-result.v1":
        raise ValueError("Bökesjön source-audit products required")
    native = json.loads((study / "native-taxa.json").read_text())
    parameters = json.loads((study / "parameters.json").read_text())
    if set(native) != {"BOKE", "KRAG"} or any(
        native[name]["dataset_id"] != value
        for name, value in (("BOKE", 54001), ("KRAG", 23013))
    ):
        raise ValueError("Declared development cores required")
    slots, taxa, targets = [], [], []
    public: dict[str, Any] = {}
    for name, core in native.items():
        for taxon in core["taxon_axis"]:
            states = {
                state: sum(c["state"] == state for c in taxon["cells"])
                for state in sorted({c["state"] for c in taxon["cells"]})
            }
            taxa.append(
                {
                    "core": name,
                    "dataset_id": core["dataset_id"],
                    "taxon_id": taxon["taxon_id"],
                    "native_label": taxon["native_label"],
                    "known_reported_nisp": taxon["known_NISP_sum"],
                    "all_selected_sample_count": taxon["aggregate_all_owner_count"],
                    "conditional_nondetection_eligible": taxon[
                        "conditional_nondetection_eligible"
                    ],
                    "states": json.dumps(states, sort_keys=True),
                }
            )
            for cell in taxon["cells"]:
                slots.append(
                    {
                        "core": name,
                        "dataset_id": core["dataset_id"],
                        "sample_id": cell["sample_id"],
                        "taxon_id": taxon["taxon_id"],
                        "native_label": taxon["native_label"],
                        "state": cell["state"],
                        "reported_count": cell["count"],
                    }
                )
        value = {
            k: v
            for k, v in parameters[name].items()
            if k not in ("native_taxa", "landclim_targets")
        }
        value["native_taxa"] = [
            {k: v for k, v in row.items() if k != "author_lookup_candidate"}
            for row in parameters[name]["native_taxa"]
        ]
        value["landclim_targets"] = [
            {k: v for k, v in row.items() if not k.startswith("workbook_")}
            for row in parameters[name]["landclim_targets"]
        ]
        value["private_author_mapping_rows_published"] = False
        public[name] = value
        for row in value["landclim_targets"]:
            targets.append(
                {
                    "core": name,
                    "landclim_target": row["target_label"],
                    "fsp_m_s_source": row["source_parameter"]["FSP (m/s)"],
                    "ppe_sd_source": row["source_parameter"]["PPE (SD)"],
                    "native_literal_matches": json.dumps(
                        row["native_exact_matches"], sort_keys=True
                    ),
                }
            )
    output.mkdir(parents=True)
    for name, rows in (
        ("native-count-slots.csv", slots),
        ("taxon-support.csv", taxa),
        ("parameter-targets.csv", targets),
    ):
        with (output / name).open("w", newline="") as handle:
            writer = csv.DictWriter(handle, list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
    (output / "parameter-coverage.json").write_text(
        json.dumps(public, indent=2, sort_keys=True) + "\n"
    )
    (output / "core-metadata.json").write_bytes((study / "metadata.json").read_bytes())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    project(args.study, args.output)


if __name__ == "__main__":
    main()
