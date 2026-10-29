"""Custody and exact public projections for completed performance observations."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path, PurePosixPath
from statistics import median
from typing import Any

EXECUTION_CANDIDATE = "19642380cc6051ed9d6cfc3fbddfdb56b4feeba7"
PLAN_SHA256 = "654d6c451994c277768d5aa82a5e559817df7801d93dbee33ef0b931bf8bfac9"
OUTER_SHA256 = "010d63133dd64afdb93949b4802fa307f1b084eeebbfe06cebe92e49f5948d1b"
COMMON_SHA256 = "4f0195a2a3ee730f26bb08f22c6369af93bf67578ae4f9efdf10e55f64f64030"
REVIEW_SHA256 = "67b127de47dd23385677a94902f42f3faa4fe9989a2b8265e76cd3a2c0670854"
WORKLOADS = ("author-conditional-joint-draws", "love-larger-fixed-candidate-batch")
WORKERS = (0, 1, 2, 100, 101, 102, 103)
CAPTURE = "data/numerical-performance/representative-public-call-capture/capture.json"
REPORT_ROOT = "docs/report/numerical-performance/representative-public-calls"
THREADS = dict.fromkeys(
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


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def pin(path: Path) -> dict[str, Any]:
    require(
        path.is_absolute() and path.resolve() == path and path.is_file(),
        "file is absent, linked or unconfined",
    )
    require(
        not any(p.is_symlink() for p in (path, *path.parents)),
        "file ancestor is linked",
    )
    return {"path": str(path), "sha256": sha(path), "bytes": path.stat().st_size}


def json_value(path: Path) -> Any:
    return json.loads(path.read_bytes())


def exact(left: Any, right: Any) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return list(left) == list(right) and all(exact(left[k], right[k]) for k in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(
            exact(a, b) for a, b in zip(left, right, strict=True)
        )
    if isinstance(left, float) and left == right == 0:
        return math.copysign(1, left) == math.copysign(1, right)
    return bool(left == right)


def relative_name(value: str) -> str:
    path = PurePosixPath(value)
    require(
        bool(value)
        and not path.is_absolute()
        and ".." not in path.parts
        and path.as_posix() == value,
        "member name is unconfined",
    )
    return value


def scientific_digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def qualified_execution(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    for name, digest in (
        ("plan.json", PLAN_SHA256),
        ("terminal.json", COMMON_SHA256),
        ("performance-terminal.json", OUTER_SHA256),
        ("independent-performance-review.json", REVIEW_SHA256),
    ):
        require(
            sha(root / name) == digest, "original execution authority differs: " + name
        )
    plan, common, outer, review = [
        json_value(root / name)
        for name in (
            "plan.json",
            "terminal.json",
            "performance-terminal.json",
            "independent-performance-review.json",
        )
    ]
    require(
        all(
            x["candidate"] == EXECUTION_CANDIDATE for x in (plan, common, outer, review)
        ),
        "execution candidate differs",
    )
    require(
        common["plan_sha256"] == outer["plan_sha256"] == PLAN_SHA256,
        "plan binding differs",
    )
    require(
        all(
            type(x) is int and x == 0
            for x in (
                common["actual_exit"],
                outer["actual_exit"],
                outer["common_actual_exit"],
            )
        ),
        "actual native execution failed",
    )
    require(
        outer["common_terminal"]["sha256"] == COMMON_SHA256
        and common["status"] == "passed",
        "common terminal binding differs",
    )
    require(
        common["canonical_before"]
        == common["canonical_after"]
        == plan["canonical_identity"],
        "original source identity changed",
    )
    require(
        common["before_pin_mismatches"] == common["after_pin_mismatches"] == []
        and common["absent_input_paths_unchanged"] is True,
        "original protected inputs changed",
    )
    require(
        outer["memory_bound_pass"] is outer["storage_bound_pass"] is True,
        "completed resource bound failed",
    )
    require(
        len(common["stages"]) == len(plan["stages"]) == 8,
        "eight actual stages required",
    )
    for actual, intended in zip(common["stages"], plan["stages"], strict=True):
        require(
            actual["id"] == intended["id"] and actual["argv"] == intended["argv"],
            "stage membership or invocation differs",
        )
        require(
            type(actual["actual_exit"]) is int
            and actual["actual_exit"] == 0
            and actual["timed_out"] is False,
            "native stage failed",
        )
        for field in ("stdout", "stderr"):
            require(
                sha(root / Path(actual[field]).name) == actual[field + "_sha256"],
                "native stage log differs",
            )
    original_root = Path(plan["output"])
    require(
        len(common["products"]) == len({row["path"] for row in common["products"]}),
        "duplicate original output",
    )
    for row in common["products"]:
        relative = Path(row["path"]).relative_to(original_root)
        actual = pin(root / relative)
        require(
            actual["sha256"] == row["sha256"] and actual["bytes"] == row["bytes"],
            "original actual output differs",
        )
    expected = {
        str(Path(row["path"]).relative_to(original_root)) for row in common["products"]
    } | {"terminal.json", "performance-terminal.json"}
    require(
        {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()} == expected,
        "complete actual output membership differs",
    )
    require(
        review["scientific_sources_outputs_and_all_repeated_identities_pass"] is True
        and review["new_cpp_allowed"]
        is review["source_R_same_input_comparison_executed"]
        is False,
        "scope or scientific admission differs",
    )
    return plan, review


def measurement_projection(
    root: Path, plan: dict[str, Any], review: dict[str, Any]
) -> dict[str, Any]:
    observations: list[dict[str, Any]] = []
    boundaries: dict[str, list[dict[str, Any]]] = {}
    identities: dict[str, Any] = {}
    for workload in WORKLOADS:
        for worker in WORKERS:
            data = json_value(root / workload / f"worker-{worker}/measurement.json")
            require(
                data["candidate"] == EXECUTION_CANDIDATE
                and data["worker"] == worker
                and len(data["rows"]) == 1,
                "worker identity differs",
            )
            require(
                data["R_or_compiler_executed"]
                is data["native_thread_counters_observed"]
                is False
                and data["thread_limits"] == THREADS,
                "backend or thread scope differs",
            )
            row = data["rows"][0]
            require(row["workload"] == workload, "workload identity differs")
            output = json_value(root / workload / f"worker-{worker}/{workload}.json")
            require(
                scientific_digest(output) == row["scientific_output_sha256"],
                "scientific output digest differs",
            )
            identity = (
                row["contract"],
                row["input_identity"],
                row["scientific_output_sha256"],
            )
            require(
                workload not in identities
                or exact(identities[workload], list(identity)),
                "repeated scientific identity differs",
            )
            identities[workload] = list(identity)
            times = [row["first_public_call_seconds"], *row["warm_public_call_seconds"]]
            require(
                len(times) == (8 if worker < 3 else 1)
                and all(type(x) is float and math.isfinite(x) and x > 0 for x in times),
                "first/warm timing membership differs",
            )
            require(
                row["profile_is_unprofiled_hotspot_evidence"] is False,
                "diagnostic profile promoted to hotspot evidence",
            )
            if workload == WORKLOADS[0]:
                require(
                    len(row["contract"]["sites"]) == 6
                    and len(row["contract"]["taxa"]) == 10
                    and row["contract"]["draws"] == 1024,
                    "author workload population differs",
                )
            else:
                require(
                    row["contract"]["logical_calls"] == 128
                    and row["contract"]["physical_fixture"] == 1
                    and row["contract"]["optimizer_search_convergence"] is False,
                    "computational repetitions became field sites or convergence",
                )
                require(
                    len(output) == 128 and all(exact(v, output[0]) for v in output),
                    "LOVE repeated output differs",
                )
            if worker >= 3:
                continue
            rss = data["peak_RSS_native"] * (
                1 if data["rss_units"] == "bytes" else 1024
            )
            observed = {
                "worker": worker,
                "workload": workload,
                "first_seconds": times[0],
                "warm_seconds": times[1:],
                "warm_median_seconds": median(times[1:]),
                "warm_min_seconds": min(times[1:]),
                "warm_max_seconds": max(times[1:]),
                "whole_worker_peak_RSS_bytes": rss,
            }
            require(
                exact(observed, review["observations"][len(observations)]),
                "independent six-observation summary differs",
            )
            observations.append(
                observed
                | {
                    "construction_loading_conversion_seconds": row[
                        "construction_loading_conversion_seconds"
                    ],
                    "worker_body_seconds": data["worker_body_seconds"],
                    "output_projection_seconds": row["output_projection_seconds"],
                    "diagnostic_profile_total_seconds": row[
                        "diagnostic_profile_total_seconds"
                    ],
                    "measured_unprofiled_boundaries": row[
                        "measured_unprofiled_boundaries"
                    ],
                    "warnings": row["warnings"],
                    "contract": row["contract"],
                    "input_identity": row["input_identity"],
                    "scientific_output_sha256": row["scientific_output_sha256"],
                }
            )
            for boundary in row["measured_unprofiled_boundaries"]:
                key = boundary["module"] + ":" + boundary["attribute"]
                boundaries.setdefault(key, []).append(boundary["assessment"])
    require(
        exact(boundaries, review["all_worker_boundary_assessments"]),
        "all boundary assessments differ",
    )
    require(
        review["qualified_all_three_worker_hotspots"] == [],
        "original no-hotspot conclusion changed",
    )
    scaling = json_value(root / "scaling.json")
    require(exact(scaling, review["scaling"]), "scaling differs")
    require(
        [x["mode"] for x in scaling["rows"]] == ["sequential", "parallel"] * 2
        and [x["workers"] for x in scaling["rows"]] == [[100, 101], [102, 103]] * 2,
        "equal-total process membership differs",
    )
    return {
        "schema_version": "representative-public-call-performance.v1",
        "execution_candidate": EXECUTION_CANDIDATE,
        "original_plan_sha256": PLAN_SHA256,
        "original_common_terminal_sha256": COMMON_SHA256,
        "original_resource_terminal_sha256": OUTER_SHA256,
        "original_independent_review_sha256": REVIEW_SHA256,
        "observations": observations,
        "all_worker_boundary_assessments": boundaries,
        "qualified_all_three_worker_hotspots": [],
        "scaling": scaling,
        "new_cpp_allowed": False,
        "source_R_same_input_comparison_executed": False,
        "thread_scope": review["thread_scope"],
        "scope": review["scope"],
        "remaining": review["remaining"],
        "retained_capture": CAPTURE,
        "resource_scope": "Completed-child peak RSS and complete regular logical output were checked, not OS quotas or full descendant RSS. First-call means a fresh process, not a proven cold OS cache. Full process stage wall time includes startup; input loading/construction/conversion and output projection are separate from the public call.",
    }


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")
