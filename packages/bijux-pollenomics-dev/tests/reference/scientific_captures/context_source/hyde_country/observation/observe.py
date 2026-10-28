"""Independently rejoin every HYDE country arithmetic claim without importing its producer."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

_entry_path = Path(__file__).absolute()
if _entry_path != _entry_path.resolve() or any(
    p.is_symlink() for p in (_entry_path, *_entry_path.parents)
):
    raise ValueError("Controller entrypoint alias refused before helper imports")
_entry_directory = Path(__file__).resolve().parent
_expected_python = {
    "execute_source.py",
    "observe.py",
    "metadata.py",
    "common_runner.py",
    "runtime.py",
    "prepare.py",
    "contracts.py",
    "run.py",
    "check_contracts.py",
}
for _entry in _entry_directory.iterdir():
    if _entry.is_symlink() or (not _entry.is_file() and not _entry.is_dir()):
        raise ValueError("Controller namespace contains an alias or special entry")
    if _entry.is_dir() and _entry.name != "preflight":
        raise ValueError("Unexpected controller import directory")
    if _entry.suffix in {".py", ".pyc", ".so"} and _entry.name not in _expected_python:
        raise ValueError("Unexpected controller module before helper import")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contracts import (  # noqa: E402 - closed namespace must precede owned imports.
    SOURCE,
    dump,
    exact,
    load,
    pin,
    require,
    source_namespace,
    validate_products,
    validate_scope,
    verify_frozen_pins,
)
from metadata import (  # noqa: E402
    report_and_csv as independently_joined_report,
)
from runtime import (  # noqa: E402
    profile_guard,
    qualify_process_snapshot,
    raw_process_snapshot,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    source_namespace()
    profile_guard()
    plan = load(args.plan)
    output = Path(plan["output"])
    before = raw_process_snapshot()
    qualify_process_snapshot(before, plan["input_pins"], SOURCE)
    verify_frozen_pins(plan["input_pins"])
    declared = load(SOURCE / "declared-inputs.json")
    historical = {
        Path(row["path"]).name: Path(row["path"]) for row in plan["historical_reports"]
    }
    validate_scope(load(historical["report.json"]))
    expected, expected_csv = independently_joined_report(
        Path(declared["private_root"]), load(historical["report.json"])
    )
    generated = output / "producer/report.json"
    actual = load(generated)
    validate_scope(actual)
    original = historical["report.json"]
    require(
        generated.read_bytes() == original.read_bytes(),
        "Tracked complete report bytes differ",
    )
    generated_csv = output / "producer/country-years.csv"
    validate_products(
        actual,
        generated_csv.read_bytes(),
        load(original),
        historical["country-years.csv"].read_bytes(),
        expected,
        expected_csv,
    )
    runtime = load(output / "source-runtime-observation.json")
    require(
        type(runtime["source_exit"]) is int
        and runtime["source_exit"] == 0
        and type(runtime["metadata_exit"]) is int
        and runtime["metadata_exit"] == 0,
        "Producer/runtime scope failed",
    )
    require(
        runtime["candidate"] == plan["candidate"]
        and exact(runtime["plan"], pin(args.plan))
        and exact(runtime["source"], plan["maintained_source"])
        and exact(runtime["executed_source_argv"], plan["maintained_source_argv"]),
        "Actual source execution binding differs",
    )
    for position in ("before", "after"):
        qualify_process_snapshot(runtime[position], plan["input_pins"], SOURCE)
    verify_frozen_pins(plan["input_pins"])
    after = raw_process_snapshot()
    qualify_process_snapshot(after, plan["input_pins"], SOURCE)
    dump(
        output / "independent-source-review.json",
        {
            "actual_exit": 0,
            "candidate": plan["candidate"],
            "plan": pin(args.plan),
            "generated": pin(generated),
            "canonical": pin(original),
            "tracked_byte_checker_exit": 0,
            "complete_independent_metadata_join_typed_and_bytes_exact": True,
            "generated_csv": pin(generated_csv),
            "canonical_csv": pin(historical["country-years.csv"]),
            "source_country_count": 4,
            "source_year_ce_labels": [500, 1000, 1500, 1700, 1900, 2000, 2025],
            "scenario_count": 3,
            "source_reported_modeled_rows": 84,
            "country_years": 28,
            "source_grid_reads": 0,
            "scenario_uncertainty_interval_admitted": False,
            "calendar_rights_version_human_ecological_or_LRA_admitted": False,
            "raw_private_bytes_redistributed": False,
            "source_runtime": pin(output / "source-runtime-observation.json"),
            "observer_before": before,
            "observer_after": after,
            "scope": "Current source-reported HYDE country arithmetic and whole two-product byte replay only. No grid source/overlay, scenario uncertainty interval, independent vegetation truth, pollen covariate, CE/BP/calendar conversion, release/rights reconciliation, human/ecological or LRA acceptance.",
        },
    )


if __name__ == "__main__":
    main()
