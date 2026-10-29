"""Independently join retained measurements and source pins after metadata assembly."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from statistics import median

from contracts import (
    CAPTURE,
    REPORT_ROOT,
    WORKERS,
    WORKLOADS,
    exact,
    pin,
    require,
    write_json,
)

A = Path(__file__).absolute().parent


def independent_boundary(timings: dict) -> dict:
    baseline, passthrough, instrumented, inside, clock = [
        timings[k]
        for k in ("baseline", "passthrough", "instrumented", "inside", "clock_cost")
    ]
    require(
        all(len(v) == 3 for v in (baseline, passthrough, instrumented, inside, clock)),
        "three boundary repeats required",
    )
    require(
        all(
            type(x) in (int, float) and math.isfinite(x) and x >= 0
            for group in (baseline, passthrough, instrumented, inside, clock)
            for x in group
        )
        and min(baseline) > 0,
        "invalid boundary timing",
    )
    require(
        all(a <= b for a, b in zip(inside, instrumented, strict=True)),
        "boundary exceeds public call",
    )
    overhead = max(0.0, (median(instrumented) - median(baseline)) / median(baseline))
    share = max(
        0.0, min(inside) - max(clock) - max(0.0, max(passthrough) - min(baseline))
    ) / max(baseline)
    return {
        "instrumentation_overhead_ratio": overhead,
        "conservative_measured_boundary_share": share,
        "qualified_measured_hotspot": overhead <= 0.05 and share >= 0.5,
        "allows_compilation": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_bytes())
    output = Path(plan["output"])
    repository = output / "source-products"
    capsule = repository / CAPTURE
    packet = json.loads(capsule.read_bytes())
    require(
        exact(
            [row["original"] for row in packet["metadata_source_custody"]],
            plan["metadata_source_pins"],
        ),
        "actual metadata source custody differs from registered plan",
    )
    module_path = (
        A
        / "proposal/packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/native_backend/retained_performance.py"
    )
    spec = importlib.util.spec_from_file_location(
        "retained_performance_contract", module_path
    )
    require(
        spec is not None and spec.loader is not None, "retained consumer import failed"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = module.validated_capture(repository, capture_sha256=pin(capsule)["sha256"])
    original = Path(plan["execution_root"])
    original_plan = json.loads((original / "plan.json").read_bytes())
    copied = repository / Path(CAPTURE).parent / "execution"
    reference = copied.parent / "reference-inputs/docs/report"
    uncertainty = json.loads(
        (
            reference / "method-certification/author-site-uncertainty/report.json"
        ).read_bytes()
    )
    with (
        reference / "method-certification/author-site-uncertainty/cover-draws.csv"
    ).open(newline="") as stream:
        table = list(csv.reader(stream))
    require(
        table[0] == uncertainty["prepared_targets"] and len(table) == 1025,
        "public draw table dimensions differ",
    )
    original_covers = [[float(cell) for cell in row] for row in table[1:]]
    baseline = next(
        row
        for row in json.loads(
            (
                reference / "numerical-performance/python-baseline/report.json"
            ).read_bytes()
        )["workloads"]
        if row["name"] == "love-optimized-replay"
    )

    def legacy(value):
        if isinstance(value, dict) and set(value) == {"nonfinite"}:
            return None
        if isinstance(value, list):
            return [legacy(child) for child in value]
        return value

    require(
        {p.relative_to(original).as_posix() for p in original.rglob("*") if p.is_file()}
        == {p.relative_to(copied).as_posix() for p in copied.rglob("*") if p.is_file()},
        "original complete execution membership differs",
    )
    for path in original.rglob("*"):
        if path.is_file():
            require(
                path.read_bytes() == (copied / path.relative_to(original)).read_bytes(),
                "original execution bytes differ",
            )
    boundaries = {}
    for workload in WORKLOADS:
        for worker in WORKERS:
            source = json.loads(
                (original / workload / f"worker-{worker}/measurement.json").read_bytes()
            )
            require(
                all(
                    path == original_plan["module_origins"][name]["path"]
                    for name, path in source["source_origins"].items()
                ),
                "worker source origin differs",
            )
            row = source["rows"][0]
            scientific = json.loads(
                (copied / workload / f"worker-{worker}/{workload}.json").read_bytes()
            )
            if workload == WORKLOADS[0]:
                require(
                    exact(scientific["cover_draws"], original_covers)
                    and exact(scientific["mean"], uncertainty["joint_mean_cover"])
                    and exact(
                        scientific["standard_error"],
                        uncertainty["joint_standard_error"],
                    ),
                    "original public uncertainty scientific values differ",
                )
            else:
                cover = json.dumps(
                    legacy(scientific[0]["cover"]), sort_keys=True, allow_nan=False
                ).encode()
                require(
                    hashlib.sha256(cover).hexdigest()
                    == baseline["scientific_output_sha256"],
                    "original LOVE scientific mean differs",
                )
            if worker >= 3:
                continue
            observation = next(
                x
                for x in report["observations"]
                if x["workload"] == workload and x["worker"] == worker
            )
            require(
                exact(observation["warm_seconds"], row["warm_public_call_seconds"])
                and len(observation["warm_seconds"]) == 7,
                "warm samples were omitted",
            )
            require(
                exact(
                    observation["output_projection_seconds"],
                    row["output_projection_seconds"],
                )
                and len(observation["output_projection_seconds"]) == 8,
                "output conversion observations differ",
            )
            for entry in row["measured_unprofiled_boundaries"]:
                assessed = independent_boundary(entry["timings_seconds"])
                require(
                    exact(assessed, entry["assessment"]),
                    "independent conservative boundary calculation differs",
                )
                boundaries.setdefault(
                    entry["module"] + ":" + entry["attribute"], []
                ).append(assessed)
    require(
        exact(boundaries, report["all_worker_boundary_assessments"])
        and all(
            len(rows) == 3
            and not all(row["qualified_measured_hotspot"] for row in rows)
            for rows in boundaries.values()
        ),
        "no-hotspot decision differs",
    )
    require(
        report["new_cpp_allowed"]
        is report["source_R_same_input_comparison_executed"]
        is False,
        "compiled or R evidence invented",
    )
    replay = output / "independent-transport"
    module.build(repository, replay, capture_sha256=pin(capsule)["sha256"])
    for name in ("report.json", "README.md"):
        require(
            (replay / REPORT_ROOT / name).read_bytes()
            == (repository / REPORT_ROOT / name).read_bytes(),
            "maintained transport differs from generated public product",
        )
    write_json(
        output / "independent-publication-review.json",
        {
            "native_exit": 0,
            "source_only_metadata": True,
            "capture": pin(capsule),
            "original_input_count": len(original_plan["input_pins"]),
            "original_complete_execution_files_exact": 66,
            "all_fourteen_worker_measurements_and_scientific_outputs_exact": True,
            "all_six_first_plus_seven_warm_observations_preserved": True,
            "independent_unprofiled_boundary_assessments": boundaries,
            "qualified_all_three_worker_hotspots": [],
            "new_model_timing_profile_compiler_R_calls": 0,
            "maintained_transport_exact": True,
            "scope": "Retained execution publication only; no new timing, profiling, model, compiler, R or release admission.",
        },
    )


if __name__ == "__main__":
    main()
