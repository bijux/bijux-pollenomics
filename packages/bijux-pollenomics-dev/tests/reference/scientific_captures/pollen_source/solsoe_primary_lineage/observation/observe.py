"""Independently verify the complete primary pollen depth/count/name lineage."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contracts import (
    MANIFEST,
    REPORT,
    SAMPLES,
    dump,
    exact,
    load,
    owner_contract,
    part_rows,
    pin,
    reconcile,
    require,
    verify_products,
)
from runtime import check_aliases, profile_guard, qualify_process_snapshot


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    plan = load(args.plan)
    root = Path(plan["repository"])
    output = Path(plan["output"])
    profile = profile_guard()
    require(
        exact(
            owner_contract(load(root / "configs/ci/report-ownership.json")),
            plan["declared_owner"],
        )
        and exact(
            pin(root / "configs/ci/report-ownership.json"), plan["ownership_policy"]
        ),
        "Registered named owner/policy differs",
    )
    require(
        check_aliases(
            plan["runtime_profile"]["tree_aliases"]
            + plan["runtime_profile"]["native_aliases"]
        ),
        "Runtime aliases changed",
    )
    for row in plan["input_pins"]:
        require(
            exact(pin(Path(row["path"])), row),
            "Registered input changed: " + row["path"],
        )
    stages = load(output / "stage-progress.json")
    require(
        len(stages) == 1
        and stages[0]["id"] == plan["stages"][0]["id"]
        and exact(stages[0]["argv"], plan["stages"][0]["argv"])
        and type(stages[0]["actual_exit"]) is int
        and stages[0]["actual_exit"] == 0
        and stages[0]["timed_out"] is False,
        "Genuine maintained producer stage zero required",
    )
    manifest = load(root / MANIFEST)
    samples = list(part_rows(root, manifest, "samples"))
    derived, ledger = reconcile(
        Path(plan["private_primary"]["path"]).read_bytes(),
        samples,
        part_rows(root, manifest, "observations"),
    )
    generated = output / "producer/report.json"
    generated_csv = output / "producer/samples.csv"
    retained, retained_csv = root / REPORT, root / SAMPLES
    result = load(generated)
    verify_products(result, load(retained), ledger, generated_csv.read_bytes(), derived)
    require(
        generated.read_bytes() == retained.read_bytes()
        and generated_csv.read_bytes() == retained_csv.read_bytes(),
        "Complete current JSON/CSV byte identities differ",
    )
    require(
        exact(pin(retained), plan["historical_report"])
        and exact(pin(retained_csv), plan["historical_samples"]),
        "Canonical product inputs changed",
    )
    runtime_path = output / "source-runtime-observation.json"
    runtime = load(runtime_path)
    stdout = Path(stages[0]["stdout"])
    require(
        pin(stdout)["sha256"] == stages[0]["stdout_sha256"],
        "Producer stdout binding differs",
    )
    native_output = json.loads(stdout.read_text().splitlines()[-1])
    require(
        exact(native_output["source_runtime"], pin(runtime_path))
        and exact(native_output["generated_report"], pin(generated)),
        "Native stdout/product identities differ",
    )
    require(
        runtime["candidate"] == plan["candidate"]
        and exact(runtime["plan"], pin(args.plan))
        and exact(runtime["source"], plan["maintained_source"])
        and exact(runtime["executed_source_argv"], plan["maintained_source_argv"])
        and exact(runtime["interpreter_flags"], ["-I", "-S", "-B"]),
        "Actual maintained source/runtime binding differs",
    )
    require(
        exact(
            runtime["actual_launcher_argv"],
            [plan["stages"][0]["argv"][0], *plan["stages"][0]["argv"][4:]],
        )
        and type(runtime["source_exit"]) is int
        and runtime["source_exit"] == 0
        and type(runtime["metadata_exit"]) is int
        and runtime["metadata_exit"] == 0,
        "Actual source/metadata exit or argv differs",
    )
    for side in ("before", "after"):
        qualify_process_snapshot(
            runtime[side], plan["input_pins"], Path(__file__).resolve().parent
        )
    require(
        type(runtime["before"]["pid"]) is int
        and runtime["before"]["pid"] > 0
        and exact(runtime["before"]["pid"], runtime["after"]["pid"]),
        "Native before/after process identity differs",
    )
    origins = []
    for name, module in sorted(sys.modules.items()):
        value = getattr(module, "__file__", None)
        if value:
            path = Path(value).resolve()
            require(
                path.is_relative_to(Path(profile["prefix"]))
                or path.is_relative_to(Path(__file__).resolve().parent),
                "Unowned observer import: " + name + ": " + str(path),
            )
            origins.append({"module": name, "file": pin(path)})
    dump(
        output / "independent-source-review.json",
        {
            "candidate": plan["candidate"],
            "plan": pin(args.plan),
            "producer_stage": stages[0],
            "generated": [pin(generated), pin(generated_csv)],
            "canonical": [pin(retained), pin(retained_csv)],
            "actual_exit": 0,
            "tracked_byte_checker_exit": 0,
            "complete_typed_report_and_ordered_CSV_exact": True,
            "independently_derived_source_counts": derived,
            "independent_sample_rows": ledger,
            "actual_source_runtime": pin(runtime_path),
            "observer_import_origins": origins,
            "runtime_profile": profile,
            "raw_primary_redistributed": False,
            "scope": "New current source-count lineage only. All66 native depth/sample IDs,147 count axes, explicit zero/sparse absence and18 unique count-vector candidates are independently joined. Numeric names are not ecological-taxonomy approvals. Primary CCBYNC source stays external; no prior acquisition/copy proof, author79 selection, chronology, basin, LRA, rights, human or release acceptance is inferred.",
        },
    )


if __name__ == "__main__":
    main()
