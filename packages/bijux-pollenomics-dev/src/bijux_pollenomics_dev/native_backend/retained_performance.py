"""Custody and exact public projections for completed performance observations."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path, PurePosixPath
from statistics import median
from typing import Any

from ..ci.report_rebuild.retained_source import SourceCapsule, validated_descriptor

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
    """Refuse retained performance evidence that violates its declared contract."""
    if not condition:
        raise ValueError(reason)


def sha(path: Path) -> str:
    """Return the byte digest of a declared retained file."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def pin(path: Path) -> dict[str, Any]:
    """Describe one regular confined file with its byte identity."""
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
    """Decode the declared retained JSON file."""
    return json.loads(path.read_bytes())


def exact(left: Any, right: Any) -> bool:
    """Compare ordered native values without collapsing types or signed zero."""
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
    """Require a confined canonical relative member name."""
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
    """Digest canonical finite scientific metadata."""
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def _execution_namespace(root: Path, expected: set[str], stage_files: set[str]) -> None:
    """Retain complete original execution files and reject undeclared/aliased entries."""
    require(
        stage_files <= expected,
        "native stage files absent from original output catalog",
    )
    require(
        root.is_absolute()
        and root.is_dir()
        and not any(p.is_symlink() for p in (root, *root.parents)),
        "original execution root is absent or aliased",
    )
    directories = {
        parent.as_posix()
        for name in expected
        for parent in PurePosixPath(relative_name(name)).parents
        if parent.as_posix() != "."
    }
    files: set[str] = set()
    actual_directories: set[str] = set()
    for path in root.rglob("*"):
        require(
            not path.is_symlink() and (path.is_file() or path.is_dir()),
            "original execution namespace contains alias/special entry",
        )
        name = path.relative_to(root).as_posix()
        if path.is_dir():
            actual_directories.add(name)
        else:
            files.add(name)
    require(
        files == expected and actual_directories == directories,
        "complete actual output namespace differs",
    )


def _validate_source_transport(
    repository: Path, packet: Path, members: list[dict[str, Any]]
) -> SourceCapsule:
    """Bind exact original source and named controls without restoring any copies."""
    source_buffer = validated_descriptor(
        repository, packet.relative_to(repository).as_posix(), members
    )
    controls = {
        "controls/boundary.py",
        "controls/check_contracts.py",
        "controls/measure.py",
        "controls/observe.py",
        "controls/prepare.py",
        "controls/run.py",
        "controls/scaling.py",
        "controls/storage.py",
        "controls/workloads.py",
        "controls/shared/run_account_qualification.py",
        "publication-controls/assemble.py",
        "publication-controls/contracts.py",
        "publication-controls/check_contracts.py",
        "publication-controls/observe.py",
        "publication-controls/prepare.py",
        "publication-controls/run.py",
        "publication-controls/proposal/packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/native_backend/retained_performance.py",
    }
    expected = {
        row["path"]
        for row in members
        if row["path"].startswith("source-code/packages/")
    }
    expected |= controls | {
        "reference-inputs/docs/report/method-certification/author-site-uncertainty/replay.py"
    }
    require(
        source_buffer.detached == expected,
        "performance detached source-role membership differs",
    )
    return source_buffer


def qualified_execution(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate the retained execution and its declared source and output identities."""
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
    _execution_namespace(
        root,
        expected,
        {
            Path(stage[field]).name
            for stage in common["stages"]
            for field in ("stdout", "stderr")
        },
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
    """Project retained measurements within their declared workload and resource scope."""
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
    """Write one absent JSON output with finite native values."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def validated_capture(repository: Path, *, capture_sha256: str) -> dict[str, Any]:
    """Admit exact retained measurements, never reproduce historical timings."""
    capture_path = repository / CAPTURE
    require(
        sha(capture_path) == capture_sha256,
        "retained performance capture identity differs",
    )
    capture = json_value(capture_path)
    require(
        capture["schema_version"] == "representative-performance-source-capture.v1"
        and capture["execution_candidate"] == EXECUTION_CANDIDATE,
        "retained performance epoch differs",
    )
    packet = capture_path.parent
    members = capture["members"]
    names = [relative_name(row["path"]) for row in members]
    require(names == sorted(set(names)), "capture members must be unique and sorted")
    source_buffer = _validate_source_transport(repository, packet, members)
    member_map = {row["path"]: row for row in members}
    plan, review = qualified_execution(packet / "execution")
    custody = capture["original_input_custody"]
    require(
        capture["input_count"] == len(custody) == len(plan["input_pins"])
        and exact([row["original"] for row in custody], plan["input_pins"]),
        "original input custody differs",
    )
    original_repository = Path(plan["repository"])
    original_controls = Path(plan["stages"][0]["argv"][2]).parent
    packages = (
        "bijux-pollenomics",
        "bijux-pollenomics-dev",
        "bijux-pollenomics-lra",
        "pollenomics",
    )
    retained = set()
    for row in custody:
        origin = row["original"]
        path = Path(origin["path"])
        source = any(
            path.is_relative_to(original_repository / "packages" / name / "src")
            for name in packages
        )
        control = path.is_relative_to(original_controls) or path == Path(
            plan["common_runner"]
        )
        public_reference = path.is_relative_to(original_repository / "docs/report")
        if source or control or public_reference:
            if source:
                expected = (
                    "source-code/" + path.relative_to(original_repository).as_posix()
                )
            elif public_reference:
                expected = (
                    "reference-inputs/"
                    + path.relative_to(original_repository).as_posix()
                )
            elif path.is_relative_to(original_controls):
                expected = "controls/" + path.relative_to(original_controls).as_posix()
            else:
                expected = "controls/shared/" + path.name
            require(
                row["disposition"] == "retained_first_party"
                and row["member"] == expected,
                "first-party source/control was omitted",
            )
            member = member_map[expected]
            require(
                member["original"] == origin
                and member["sha256"] == origin["sha256"]
                and member["bytes"] == origin["bytes"],
                "first-party source differs from actual input pin",
            )
            retained.add(expected)
        else:
            require(
                row["disposition"] == "hash_reference_only_not_redistributed"
                and "member" not in row,
                "private/runtime source bytes cannot be redistributed",
            )
    metadata = capture["metadata_source_custody"]
    require(
        len(metadata) == 8 and len({row["member"] for row in metadata}) == 8,
        "metadata publication source membership differs",
    )
    for row in metadata:
        name = relative_name(row["member"])
        require(
            name.startswith("publication-controls/"),
            "publication control outside declared prefix",
        )
        member = member_map[name]
        origin = row["original"]
        require(
            member["original"] == origin
            and member["sha256"] == origin["sha256"]
            and member["bytes"] == origin["bytes"],
            "metadata publication source pin differs",
        )
        retained.add(name)
    expected_names = (
        retained
        | {
            "execution/" + p.relative_to(packet / "execution").as_posix()
            for p in (packet / "execution").rglob("*")
            if p.is_file()
        }
        | {"publication/report.json", "publication/README.md"}
    )
    require(
        set(names) == expected_names,
        "undeclared source or private/runtime member in capture",
    )
    report = measurement_projection(packet / "execution", plan, review)
    require(
        exact(report, json_value(packet / "publication/report.json")),
        "retained performance publication differs",
    )
    source_buffer.fresh()
    return report


def _require_confined_target(output: Path, path: Path) -> None:
    require(
        path.is_relative_to(output)
        and path.resolve() == path
        and not any(parent.is_symlink() for parent in (path, *path.parents)),
        "transport target or ancestor is linked or unconfined",
    )
    require(not path.exists(), "transport output already exists")


def _output_targets(output: Path) -> tuple[Path, Path]:
    """Refuse linked descendants before creating either publication output."""
    require(
        output.is_absolute()
        and output.resolve() == output
        and not any(p.is_symlink() for p in (output, *output.parents)),
        "transport output is linked or unconfined",
    )
    targets = tuple(
        output / REPORT_ROOT / name for name in ("report.json", "README.md")
    )
    for path in targets:
        _require_confined_target(output, path)
    return targets[0], targets[1]


def build(repository: Path, output: Path, *, capture_sha256: str) -> tuple[Path, Path]:
    """Transport the original report/reader after full capsule admission."""
    validated_capture(repository, capture_sha256=capture_sha256)
    targets = _output_targets(output)
    packet = repository / Path(CAPTURE).parent
    for target in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        _require_confined_target(output, target)
        with target.open("xb") as stream:
            stream.write((packet / "publication" / target.name).read_bytes())
    return targets[0], targets[1]
