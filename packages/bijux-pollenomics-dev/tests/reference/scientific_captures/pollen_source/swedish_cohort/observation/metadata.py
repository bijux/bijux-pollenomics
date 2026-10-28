"""Independently rejoin every Swedish metadata claim without importing its producer."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

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
    ROOT,
    SOURCE,
    dump,
    exact,
    load,
    pin,
    require,
    source_namespace,
    validate_scope,
    verify_frozen_pins,
)
from metadata import (  # noqa: E402
    report as independently_joined_report,
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
    expected = independently_joined_report(ROOT, Path(declared["private_root"]))
    generated = output / "producer/report.json"
    actual = load(generated)
    validate_scope(actual)
    require(
        exact(actual, expected), "Complete independently source-joined report differs"
    )
    original = Path(plan["historical_report"]["path"])
    require(exact(actual, load(original)), "Complete current tracked report differs")
    require(
        generated.read_bytes() == original.read_bytes(),
        "Tracked full report bytes differ",
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
            "private_metadata_members": 26,
            "public_relational_surfaces": ["sites", "collection_units", "datasets"],
            "metadata_dataset_count": 102,
            "metadata_site_count": 99,
            "all_country_core_handles": 206,
            "metadata_title_population": 66,
            "retained_handle_hits": 62,
            "unmatched_named": 3,
            "generic_unbound": 1,
            "checked_final_age_events": 37,
            "fresh_distinct_cohort_admitted": False,
            "selected_sample_age_sequence_admitted": False,
            "acquisition_rights_human_ecological_or_LRA_admitted": False,
            "raw_private_bytes_redistributed": False,
            "source_runtime": pin(output / "source-runtime-observation.json"),
            "observer_before": before,
            "observer_after": after,
            "scope": "Current metadata-only exact source epoch and whole report replay. All-country includes UNASSIGNED; collisions/unmatched aliases/selected-age/rights limits remain literal. No pollen/count table reads, new source acquisition, untouched physical site proof, chronology normalization, LRA or ecological/human acceptance.",
        },
    )


if __name__ == "__main__":
    main()
