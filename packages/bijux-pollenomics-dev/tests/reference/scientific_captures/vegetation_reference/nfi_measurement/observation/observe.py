"""Independently decode only declared NFI metadata and compare every public schema field."""

from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contracts import (
    SOURCE,
    SOURCE_SHA,
    GUIDE_SHA,
    dump,
    exact,
    pin,
    read,
    require,
    sha,
    source_projection,
)
from runtime_custody import aliases_unchanged


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    plan = read(args.plan)
    output = Path(plan["output"])
    repository = Path(plan["repository"])
    require(
        aliases_unchanged(
            plan["runtime_aliases"], link_text=plan["runtime_alias_links"]
        ),
        "Frozen lexical aliases changed",
    )
    for row in plan["input_pins"]:
        require(pin(Path(row["path"])) == row, "Original frozen input changed")
    progress = read(output / "stage-progress.json")
    require(
        len(progress) == 1
        and progress[0]["id"] == plan["stages"][0]["id"]
        and progress[0]["argv"] == plan["stages"][0]["argv"]
        and type(progress[0]["actual_exit"]) is int
        and progress[0]["actual_exit"] == 0
        and progress[0]["timed_out"] is False,
        "Actual maintained metadata producer not zero",
    )
    origin = read(output / "producer-origin.json")
    exact(origin["maintained_producer"], plan["maintained_producer"])
    require(
        origin["maintained_main_argv"]
        == [
            plan["maintained_producer"]["path"],
            "--private-source-store",
            plan["private_source_store"],
            "--output",
            plan["metadata_output"],
        ],
        "Maintained source main args differ",
    )
    pins = {r["path"]: r for r in plan["input_pins"]}
    for row in read(output / "loaded-source-origins.json").values():
        require(
            row == pins[row["path"]],
            "Observed loaded first-party origin outside original frozen pins",
        )
    source = Path(plan["private_source_store"]) / SOURCE
    exact(pin(source), plan["private_original"])
    require(sha(source) == SOURCE_SHA, "Private workbook source identity differs")
    derived, audit = source_projection(source)
    produced = Path(plan["metadata_output"])
    exact(read(produced), derived)
    retained = (
        repository
        / "docs/report/validation/empd2-nfi-pairing/nfi-measurement-schema.json"
    )
    exact(read(retained), derived)
    encoded = (
        json.dumps(derived, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode()
    require(
        produced.read_bytes() == retained.read_bytes() == encoded,
        "Maintained/retained metadata exact bytes differ",
    )
    owner = next(
        r
        for r in read(repository / "configs/ci/report-ownership.json")["owners"]
        if r["owner_id"] == "validation/empd2-nfi-pairing/measurement-schema"
    )
    exact(owner, plan["metadata_owner"])
    require(owner["role"] == "unresolved", "Historical owner changed during run")
    guide = (
        repository
        / "docs/report/validation/empd2-nfi-pairing/inputs/slu-calibration-guide.pdf"
    )
    require(
        sha(guide) == GUIDE_SHA
        and plan["calibration_guide"]["retained_owner_admitted"] is False,
        "Historical calibration guide status changed",
    )
    dump(
        output / "independent-metadata-review.json",
        {
            "candidate": plan["candidate"],
            "plan_sha256": sha(args.plan),
            "actual_maintained_producer_native_exit": 0,
            "source_original": pin(source),
            "public_product": pin(produced),
            "retained_product": pin(retained),
            "exact_typed_and_raw_bytes": True,
            "source_projection_scope": audit,
            "plot_year_rows": derived["source_plot_support"]["plot_year_rows"],
            "metadata_cells_decoded": derived["source_plot_support"][
                "metadata_cells_decoded"
            ],
            "measurement_outcome_cells_decoded": 0,
            "source_field_dictionary_and_header_qualified": True,
            "inventory_time_scale": "Original native Excel serials; no BP/calendar collection-year substitution",
            "plot_area": "153.94m2 per undivided plot-year; not regional vegetation area",
            "land_use": "Codes only; no inferred class meaning",
            "benchmark_admission": "no_measured_pairs_admitted",
            "calibration_guide": plan["calibration_guide"],
            "raw_private_workbook_redistributed": False,
            "actual_exit": 0,
        },
    )


if __name__ == "__main__":
    main()
