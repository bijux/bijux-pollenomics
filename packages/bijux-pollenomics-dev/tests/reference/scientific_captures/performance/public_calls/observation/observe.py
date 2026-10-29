"""Join timings to retained scientific outputs without selecting favorable repeats."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from statistics import median

from boundary import assess
from storage import write_json
from workloads import digest


def legacy(value):
    if isinstance(value, dict) and set(value) == {"nonfinite"}:
        return None
    if isinstance(value, list):
        return [legacy(child) for child in value]
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_bytes())
    root, output = Path(plan["repository"]), Path(plan["output"])
    report = json.loads(
        (
            root
            / "docs/report/method-certification/author-site-uncertainty/report.json"
        ).read_bytes()
    )
    with (
        root
        / "docs/report/method-certification/author-site-uncertainty/cover-draws.csv"
    ).open(newline="") as stream:
        table = list(csv.reader(stream))
    assert table[0] == report["prepared_targets"]
    expected_covers = [[float(x) for x in row] for row in table[1:]]
    baseline = next(
        x
        for x in json.loads(
            (
                root / "docs/report/numerical-performance/python-baseline/report.json"
            ).read_bytes()
        )["workloads"]
        if x["name"] == "love-optimized-replay"
    )
    references = {}
    summary = []
    measured_boundaries = {}
    for workload in plan["workloads"]:
        for worker in (0, 1, 2, 100, 101, 102, 103):
            data = json.loads(
                (output / workload / f"worker-{worker}/measurement.json").read_bytes()
            )
            assert data["candidate"] == plan["candidate"] and data["worker"] == worker
            assert data["R_or_compiler_executed"] is False
            assert len(data["rows"]) == 1 and [r["workload"] for r in data["rows"]] == [
                workload
            ]
            assert data["native_thread_counters_observed"] is False
            assert data["thread_limits"] == dict.fromkeys(
                (
                    "OMP_NUM_THREADS",
                    "OPENBLAS_NUM_THREADS",
                    "MKL_NUM_THREADS",
                    "NUMEXPR_NUM_THREADS",
                    "VECLIB_MAXIMUM_THREADS",
                    "BLIS_NUM_THREADS",
                ),
                "1",
            )
            rss = data["peak_RSS_native"] * (
                1 if data["rss_units"] == "bytes" else 1024
            )
            assert rss <= plan["resources"]["declared_memory_bytes"]
            for module, path in data["source_origins"].items():
                assert path == plan["module_origins"][module]["path"]
            for row in data["rows"]:
                name = row["workload"]
                p = output / workload / f"worker-{worker}" / (name + ".json")
                assert Path(row["scientific_output_path"]) == p and not p.is_symlink()
                value = json.loads(p.read_bytes())
                assert digest(value) == row["scientific_output_sha256"]
                key = {
                    "contract": row["contract"],
                    "input_identity": row["input_identity"],
                    "output_sha256": row["scientific_output_sha256"],
                }
                if name in references:
                    assert references[name] == key
                references[name] = key
                timings = [
                    row["first_public_call_seconds"],
                    *row["warm_public_call_seconds"],
                ]
                assert len(timings) == (8 if worker < 3 else 1)
                assert all(
                    type(x) is float and math.isfinite(x) and x > 0 for x in timings
                )
                assert row["profile_is_unprofiled_hotspot_evidence"] is False
                if name == "author-conditional-joint-draws":
                    assert value["cover_draws"] == expected_covers
                    assert (
                        value["mean"] == report["joint_mean_cover"]
                        and value["standard_error"] == report["joint_standard_error"]
                    )
                else:
                    assert len(value) == 128 and all(v == value[0] for v in value)
                    mean_hash = hashlib.sha256(
                        json.dumps(
                            legacy(value[0]["cover"]), sort_keys=True, allow_nan=False
                        ).encode()
                    ).hexdigest()
                    assert mean_hash == baseline["scientific_output_sha256"]
                if worker < 3:
                    summary.append(
                        {
                            "worker": worker,
                            "workload": name,
                            "first_seconds": timings[0],
                            "warm_seconds": timings[1:],
                            "warm_median_seconds": median(timings[1:]),
                            "warm_min_seconds": min(timings[1:]),
                            "warm_max_seconds": max(timings[1:]),
                            "whole_worker_peak_RSS_bytes": rss,
                        }
                    )
                    for measured in row["measured_unprofiled_boundaries"]:
                        actual = assess(
                            **measured["timings_seconds"],
                            outputs_exact=True,
                            inputs_exact=True,
                        )
                        assert (
                            actual == measured["assessment"]
                            and actual["allows_compilation"] is False
                        )
                        measured_boundaries.setdefault(
                            measured["module"] + ":" + measured["attribute"], []
                        ).append(actual)
    scaling = json.loads((output / "scaling.json").read_bytes())
    assert [r["mode"] for r in scaling["rows"]] == [
        "sequential",
        "parallel",
        "sequential",
        "parallel",
    ]
    assert [r["workers"] for r in scaling["rows"]] == [
        [100, 101],
        [102, 103],
        [100, 101],
        [102, 103],
    ]
    assert all(
        type(r["wall_seconds"]) is float
        and math.isfinite(r["wall_seconds"])
        and r["wall_seconds"] > 0
        for r in scaling["rows"]
    )
    for row in plan["input_pins"]:
        p = Path(row["path"])
        assert p.is_file() and not p.is_symlink() and p.stat().st_size == row["bytes"]
        with p.open("rb") as stream:
            assert hashlib.file_digest(stream, "sha256").hexdigest() == row["sha256"]
    result = {
        "candidate": plan["candidate"],
        "scientific_sources_outputs_and_all_repeated_identities_pass": True,
        "observations": summary,
        "all_worker_boundary_assessments": measured_boundaries,
        "qualified_all_three_worker_hotspots": [
            k
            for k, rows in measured_boundaries.items()
            if len(rows) == 3
            and all(r["qualified_measured_hotspot"] is True for r in rows)
        ],
        "scaling": scaling,
        "new_cpp_allowed": False,
        "source_R_same_input_comparison_executed": False,
        "thread_scope": "One numerical thread is requested through six pinned vendor environment variables; immutable runtime lacks threadpoolctl, so no native thread-counter observation is claimed. Maximum two worker processes is independently bounded.",
        "remaining": "Any candidate still requires actual current identical-input sourceR/Python comparison and a separately reviewed compiled proposal under the existing2x conversion-inclusive/1.25RSS gates. No C++ adoption, optimizer convergence, field-site/vegetation/right/human or official release conclusion.",
        "scope": plan["scope"],
    }
    path = output / "independent-performance-review.json"
    assert not path.exists()
    write_json(output, path, result)
    print(
        json.dumps(
            {
                "native_exit": 0,
                "isolated_worker_processes": 14,
                "observations": len(summary),
                "new_cpp_allowed": False,
            }
        )
    )


if __name__ == "__main__":
    main()
