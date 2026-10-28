"""Independently join native relations without interpreting or redistributing the paper."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contracts import (
    AGES,
    CONTROLS,
    REPORT,
    dump,
    exact,
    inspect_relations,
    load,
    owner_contract,
    pin,
    require,
    verify_closed_report,
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
            "Original registered input changed: " + row["path"],
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
    generated = output / "producer/report.json"
    retained = root / REPORT
    ages = load(root / AGES)["rows"]
    joins = inspect_relations(load(root / CONTROLS)["rows"], ages)
    result = load(generated)
    verify_closed_report(result, load(retained), joins, ages)
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
        "Actual native stdout/product identities differ",
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
                f"Unowned observer import: {name}: {path}",
            )
            origins.append({"module": name, "file": pin(path)})
    dump(
        output / "independent-source-review.json",
        {
            "candidate": plan["candidate"],
            "plan": pin(args.plan),
            "producer_stage": stages[0],
            "generated": pin(generated),
            "retained": pin(retained),
            "actual_exit": 0,
            "typed_report_exact_against_independent_raw_source": True,
            "historical_v1_byte_checker_exit": 0
            if generated.read_bytes() == retained.read_bytes()
            else 2,
            "tracked_byte_checker_exit": 0
            if generated.read_bytes() == retained.read_bytes()
            else 2,
            "historical_v1_preserved": exact(pin(retained), plan["historical_report"]),
            "actual_source_runtime": pin(runtime_path),
            "actual_closed_proxy_samples": result["paper_interval_proxy_samples"],
            "actual_bounded_closed_proxy_samples": result[
                "paper_interval_and_landclim_age_span_proxy_samples"
            ],
            "native_joins": joins,
            "observer_import_origins": origins,
            "runtime_profile": profile,
            "source_control_authority": "Seven inline declarations from the authenticated maintained producer; no fresh PDF table extraction.",
            "paper_scope": "Physical retained PDF SHA/size authenticated, original manual page interpretation retained. Original provider download/copy history, independent fresh document interpretation, rights and human acceptance not established.",
            "selection_scope": "92 raw native central-age records with complete original source metadata/refusals preserved. Closed and bounded totals are actual current source results, never preasserted; historical unbounded76/74 remain separate. Point selection is not uncertainty-support containment/overlap, calendar/chronology equivalence or analytical eligibility; published79 membership, dated georeferenced basin and LRA admission remain unresolved/zero.",
        },
    )


if __name__ == "__main__":
    main()
