"""Check the root research library and its selected governed source identities."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import runpy
from statistics import median

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.retained_source import read_source_path
from bijux_pollenomics_dev.reader_reports.source import (
    MAINTAINED_PRESENTATION_INPUTS,
    MAINTAINED_READER_BOOKKEEPING,
    MAINTAINED_REPORT_ENTRYPOINTS,
)

ROOT = Path(__file__).resolve().parent.parent
REPORTS = ROOT / "reports"
LOCK = REPORTS / "source-lock.json"
LINK = re.compile(r"(?<!!)\[[^]]+\]\(([^)]+)\)")
LOCAL_RUN_PATH = re.compile(r"(?:/Users|/home)/[^/\s]+/|artifacts/v\d+/")
HUMAN_SURFACES = (
    REPORTS,
    ROOT / "docs/report",
    ROOT / "docs/public",
    ROOT / "presentation",
)
RUNTIME_MEASUREMENT = ROOT / "docs/report/numerical-performance/runtime-metadata"
PYTHON_BASELINE = ROOT / "docs/report/numerical-performance/python-baseline"
PYTHON_ISOLATED = ROOT / "docs/report/numerical-performance/python-isolated"
NATIVE_FORWARD = ROOT / "docs/report/numerical-performance/native-forward"
NATIVE_MEMORY = ROOT / "docs/report/numerical-performance/native-memory"
EMPD2_NFI = ROOT / "docs/report/validation/empd2-nfi-pairing"


def verify_reader_paths() -> None:
    """Keep disposable run directories and personal checkouts out of reader text."""
    for surface in HUMAN_SURFACES:
        for suffix in ("*.md", "*.tex"):
            for page in sorted(surface.rglob(suffix)):
                for number, line in enumerate(
                    page.read_text(encoding="utf-8").splitlines(), start=1
                ):
                    if LOCAL_RUN_PATH.search(line):
                        relative = page.relative_to(ROOT)
                        raise ValueError(
                            f"Local run path in reader text: {relative}:{number}"
                        )


def verify_runtime_measurement() -> None:
    """Check the compact timing comparison without its disposable raw profiler."""
    reference_path = RUNTIME_MEASUREMENT / "reference-baseline.json"
    reference = json.loads(reference_path.read_text())
    measured = json.loads((RUNTIME_MEASUREMENT / "report.json").read_text())
    comparison = json.loads((RUNTIME_MEASUREMENT / "comparison.json").read_text())
    producer = (
        ROOT
        / "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/native_backend/profile_summary.py"
    )
    if (
        measured.get("schema_version") != "lra-runtime-metadata-measurement.v1"
        or measured.get("summary_producer_sha256")
        != hashlib.sha256(producer.read_bytes()).hexdigest()
        or measured.get("environment") != reference.get("environment")
        or comparison.get("reference_baseline_sha256")
        != hashlib.sha256(reference_path.read_bytes()).hexdigest()
        or comparison.get("reference_baseline_source_sha256")
        != reference.get("source_report_sha256")
        or comparison.get("same_dependency_versions") is not True
    ):
        raise ValueError("Runtime measurement source or environment changed")
    rows = measured["workloads"]
    baseline = reference["workloads"]
    comparisons = comparison["comparisons"]
    if len(rows) != 7 or len(baseline) != 7 or len(comparisons) != 7:
        raise ValueError("Runtime measurement workload denominator changed")
    for row, original, paired in zip(rows, baseline, comparisons, strict=True):
        if (
            row["name"] != original["name"]
            or row["name"] != paired["workload"]
            or row["contract_sha256"] != original["contract_sha256"]
            or row["scientific_output_sha256"] != original["scientific_output_sha256"]
            or row["nonfinite_semantics_sha256"]
            != original["nonfinite_semantics_sha256"]
            or hashlib.sha256(
                json.dumps(row["contract"], sort_keys=True).encode()
            ).hexdigest()
            != row["contract_sha256"]
            or paired["baseline_median_seconds"] != original["warm_median_seconds"]
            or paired["optimized_median_seconds"] != row["warm_median_seconds"]
            or not math.isclose(
                paired["latency_ratio"],
                original["warm_median_seconds"] / row["warm_median_seconds"],
                rel_tol=0,
                abs_tol=1e-15,
            )
            or any(
                paired[field] is not True
                for field in (
                    "same_config",
                    "same_scientific_outputs",
                    "same_native_missingness",
                )
            )
        ):
            raise ValueError(f"Runtime measurement comparison changed: {row['name']}")


def verify_python_baseline() -> None:
    """Bind the compact measured baseline to its actual isolated consumer."""
    baseline_path = PYTHON_BASELINE / "report.json"
    baseline_bytes = baseline_path.read_bytes()
    baseline = json.loads(baseline_bytes)
    isolated = json.loads((PYTHON_ISOLATED / "report.json").read_bytes())
    producer = (
        ROOT
        / "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/native_backend/baseline_summary.py"
    )
    if (
        baseline.get("schema_version") != "lra-python-performance-measurement.v1"
        or baseline.get("summary_producer_sha256")
        != hashlib.sha256(producer.read_bytes()).hexdigest()
        or baseline.get("repetitions") != 7
        or set(baseline["environment"]["threads"].values()) != {"1"}
        or isolated.get("baseline_sha256") != hashlib.sha256(baseline_bytes).hexdigest()
        or isolated.get("repetitions_per_workload") != 5
        or len(baseline["workloads"]) != 7
        or len(isolated["cases"]) != 7
    ):
        raise ValueError("Python baseline source or isolated measurement changed")
    for measured, worker in zip(baseline["workloads"], isolated["cases"], strict=True):
        contract_sha = hashlib.sha256(
            json.dumps(measured["contract"], sort_keys=True).encode()
        ).hexdigest()
        if (
            measured["name"] != worker["name"]
            or measured["contract"] != worker["contract"]
            or measured["contract_sha256"] != contract_sha
            or measured["scientific_output_sha256"]
            != worker["retained_scientific_output_sha256"]
            or measured["nonfinite_single_call_sha256"]
            != worker["retained_nonfinite_semantics_sha256"]
            or len(measured["warm_seconds"]) != 7
            or measured["warm_median_seconds"] != median(measured["warm_seconds"])
            or len(worker["observations"]) != 5
            or any(
                observation["contract_sha256"] != contract_sha
                or observation["scientific_output_sha256"]
                != measured["scientific_output_sha256"]
                or observation["nonfinite_semantics_sha256"]
                != measured["nonfinite_single_call_sha256"]
                for observation in worker["observations"]
            )
        ):
            raise ValueError(
                f"Python baseline scientific support changed: {measured['name']}"
            )


def verify_native_forward() -> None:
    """Bind the compact negative adoption result to retained R outputs."""
    payload = (NATIVE_FORWARD / "report.json").read_bytes()
    measured = json.loads(payload)
    producer = (
        ROOT
        / "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/native_backend/forward_summary.py"
    )
    gate = measured["prospective_gate"]
    shapes = ((1, 8, 3), (32, 128, 32), (512, 256, 64))
    if (
        measured.get("schema_version") != "lra-forward-native-measurement.v1"
        or measured.get("summary_producer_sha256")
        != hashlib.sha256(producer.read_bytes()).hexdigest()
        or b"/Users/" in payload
        or b"/home/" in payload
        or set(measured["thread_settings"].values()) != {"1"}
        or gate["minimum_validated_facade_speedup"] != 2.0
        or [(row["rows"], row["rings"], row["taxa"]) for row in measured["cases"]]
        != list(shapes)
    ):
        raise ValueError("Native forward measurement source or scope changed")
    for row in measured["cases"]:
        shape = (row["rows"], row["rings"], row["taxa"])
        reference = (
            f"reference/rows-{shape[0]}-rings-{shape[1]}-taxa-{shape[2]}/R-output.csv"
        )
        timings = row["measurements"]
        numerator = timings["numpy_validated_facade"]["median_seconds_per_call"]
        denominator = timings["native_validated_facade"]["median_seconds_per_call"]
        if (
            row["reference_R_output"] != reference
            or hashlib.sha256((NATIVE_FORWARD / reference).read_bytes()).hexdigest()
            != row["reference_R_output_sha256"]
            or any(
                value["passed"] is not True
                or value["maximum_absolute_error"] > gate["atol"]
                for value in row["comparisons"].values()
            )
            or row["inputs_unchanged"] is not True
            or any(
                len(value["seconds_per_call"]) != 9
                or value["median_seconds_per_call"] != median(value["seconds_per_call"])
                for value in timings.values()
            )
            or not math.isclose(
                row["validated_facade_speedup"],
                numerator / denominator,
                rel_tol=0,
                abs_tol=1e-15,
            )
            or row["validated_facade_speedup"] >= 2.0
        ):
            raise ValueError(f"Native forward decision changed: {shape}")


def verify_native_memory() -> None:
    """Check the measured worker distributions behind the bounded RSS claim."""
    payload = (NATIVE_MEMORY / "report.json").read_bytes()
    measured = json.loads(payload)
    shapes = ((1, 8, 3), (32, 128, 32), (512, 256, 64), (8192, 256, 512))
    if (
        measured.get("schema_version") != "native-forward-isolated-worker-memory.1"
        or measured.get("status") != "passed"
        or b"/Users/" in payload
        or b"/home/" in payload
        or measured.get("repetitions_per_method_shape") != 5
        or set(measured["thread_settings"].values()) != {"1"}
        or measured["build"]["flags"][:3] != ["-std=c++17", "-O3", "-fPIC"]
        or measured["build"]["flags"][3] not in ("-dynamiclib", "-shared")
        or [tuple(row["shape"]) for row in measured["cases"]] != list(shapes)
        or any(
            hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != digest
            for path, digest in measured["source_sha256"].items()
        )
    ):
        raise ValueError("Native worker source or measurement scope changed")
    for row in measured["cases"]:
        observations = row["observations"]
        metrics = row["metrics"]
        if (
            set(observations) != {"numpy", "native"}
            or row["numerical_parity"] is not True
        ):
            raise ValueError(f"Native worker methods or parity changed: {row['shape']}")
        if (
            len(
                {
                    item["input_sha256"]
                    for group in observations.values()
                    for item in group
                }
            )
            != 1
        ):
            raise ValueError(f"Native worker inputs differ: {row['shape']}")
        for method in ("numpy", "native"):
            items = observations[method]
            if (
                len(items) != 5
                or len({item["output_sha256"] for item in items}) != 1
                or any(
                    item["method"] != method
                    or item["shape"] != row["shape"]
                    or item["output_shape"] != [row["shape"][0], row["shape"][2]]
                    or item["post_call_process_peak_rss_bytes"]
                    < item["pre_call_process_peak_rss_bytes"]
                    or item["observed_peak_increment_bytes"]
                    != item["post_call_process_peak_rss_bytes"]
                    - item["pre_call_process_peak_rss_bytes"]
                    for item in items
                )
                or metrics[method]["median_process_peak_rss_bytes"]
                != median(item["post_call_process_peak_rss_bytes"] for item in items)
                or metrics[method]["median_single_call_seconds"]
                != median(item["single_call_seconds"] for item in items)
                or metrics[method][
                    "median_whole_worker_seconds_including_import_and_export"
                ]
                != median(
                    item["whole_worker_seconds_including_import_and_export"]
                    for item in items
                )
            ):
                raise ValueError(
                    f"Native worker observations changed: {row['shape']}/{method}"
                )
        numpy, native = metrics["numpy"], metrics["native"]
        if not math.isclose(
            row["native_to_numpy_peak_rss_ratio"],
            native["median_process_peak_rss_bytes"]
            / numpy["median_process_peak_rss_bytes"],
            rel_tol=0,
            abs_tol=1e-15,
        ) or not math.isclose(
            row["numpy_to_native_whole_worker_latency_ratio"],
            numpy["median_whole_worker_seconds_including_import_and_export"]
            / native["median_whole_worker_seconds_including_import_and_export"],
            rel_tol=0,
            abs_tol=1e-15,
        ):
            raise ValueError(f"Native worker comparison changed: {row['shape']}")


def verify_empd2_nfi_pairing() -> None:
    """Keep the public measured-vegetation refusal tied to its producer and ledger."""
    report = json.loads((EMPD2_NFI / "report.json").read_bytes())
    schema = json.loads((EMPD2_NFI / "nfi-measurement-schema.json").read_bytes())
    ledger = (EMPD2_NFI / "pairs.csv").read_bytes()
    producer = (
        ROOT
        / "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/empd2_nfi_pairing.py"
    )
    with (EMPD2_NFI / "pairs.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if (
        report.get("schema_version") != "empd2-nfi-pair-decision.v1"
        or report.get("status") != "zero_measured_pairs_refused_for_current_benchmark"
        or report["input_sha256"]["producer"]
        != hashlib.sha256(producer.read_bytes()).hexdigest()
        or report["pairs_csv"]
        != {"bytes": len(ledger), "sha256": hashlib.sha256(ledger).hexdigest()}
        or report["denominators"]["current_benchmark_refusals"] != len(rows)
        or len(rows) != 16
        or report["denominators"]["measured_pairs_admitted"] != 0
        or report["decision"]["evaluation_performed"] is not False
        or schema["measurement_outcome_cells_decoded"] != 0
        or any(
            row["current_benchmark_decision"] != "refused_missing_pair_evidence"
            or row["scientific_admission"] != "false"
            for row in rows
        )
    ):
        raise ValueError("EMPD2–NFI pairing refusal or source identity changed")


REPORT_SOURCE_FAMILIES = (
    "method-certification/love-paper-correspondence",
    "numerical-performance",
    "synthetic-validation",
    "validation/empd2-nfi-pairing",
)


HISTORICAL_SOURCE_PARTS = {
    "reference-bundle",
    "reference",
    "retained",
    "historical",
    "source-snapshot",
    "source-capture",
    "original-source",
}


def _source_file(root: Path, relative: object) -> Path:
    if not isinstance(relative, str):
        raise ValueError("Research source path must be text")
    native = PurePosixPath(relative)
    path = root / relative
    if (
        not native.parts
        or native.is_absolute()
        or ".." in native.parts
        or "\\" in relative
        or native.as_posix() != relative
        or not path.is_file()
        or not path.resolve().is_relative_to(root.resolve())
    ):
        raise ValueError(f"Research source is unavailable or unsafe: {relative}")
    return path


def _source_bytes(root: Path, relative: str) -> bytes:
    """Read named finite native controls from their authenticated Git custody."""
    native = PurePosixPath(relative)
    if relative.startswith(
        "data/method-certification/native-r-finite-covariance/"
    ) and native.suffix in {".py", ".R"}:
        if ".." in native.parts or "\\" in relative or native.as_posix() != relative:
            raise ValueError(f"Research source is unavailable or unsafe: {relative}")
        try:
            return read_source_path(root, relative)
        except ReportRebuildError as error:
            raise ValueError(
                f"Research source is unavailable or unsafe: {relative}"
            ) from error
    return _source_file(root, relative).read_bytes()


def verify_source_lock(root: Path, lock: dict[str, object]) -> tuple[int, int]:
    """Inventory maintained source paths and authenticate byte-bound evidence."""
    if set(lock) != {"schema_version", "reports", "sources", "maintained_paths"} or (
        lock.get("schema_version") != "research-report-source-lock.v2"
    ):
        raise ValueError("Unexpected research report source lock")
    sources = lock["sources"]
    maintained = lock["maintained_paths"]
    reports = lock["reports"]
    if not isinstance(sources, dict) or not all(
        isinstance(path, str)
        and isinstance(digest, str)
        and re.fullmatch(r"[0-9a-f]{64}", digest)
        for path, digest in sources.items()
    ):
        raise ValueError("Research evidence identities are invalid")
    if not isinstance(maintained, list) or not isinstance(reports, list):
        raise ValueError("Research source inventories must be lists")
    for inventory in (maintained, reports):
        if not all(isinstance(path, str) for path in inventory) or inventory != sorted(
            set(inventory)
        ):
            raise ValueError("Research source inventory is invalid or duplicated")
    if set(sources) & set(maintained):
        raise ValueError("Research source roles overlap")
    for relative in maintained:
        path = _source_file(root, relative)
        native = PurePosixPath(relative)
        if relative not in (
            MAINTAINED_REPORT_ENTRYPOINTS
            | MAINTAINED_PRESENTATION_INPUTS
            | MAINTAINED_READER_BOOKKEEPING
        ) and (
            native.parts[0] not in {"docs", "packages", "reports", "configs"}
            or (
                path.suffix not in {".md", ".py"}
                and relative not in MAINTAINED_READER_BOOKKEEPING
            )
            or set(native.parts) & HISTORICAL_SOURCE_PARTS
        ):
            raise ValueError(
                f"Research source is not maintained prose or code: {relative}"
            )
    for relative, expected in sources.items():
        if hashlib.sha256(_source_bytes(root, relative)).hexdigest() != expected:
            raise ValueError(
                f"Review changed research evidence before publishing: {relative}"
            )
    all_sources = set(sources) | set(maintained)
    for family in REPORT_SOURCE_FAMILIES:
        family_files = {
            path.relative_to(root).as_posix()
            for path in (root / "docs/report" / family).rglob("*")
            if path.is_file()
        }
        family_locked = {
            path for path in all_sources if path.startswith(f"docs/report/{family}/")
        }
        if family_files != family_locked:
            raise ValueError(f"{family} report ownership changed")
    actual_reports = sorted(
        path.relative_to(root).as_posix() for path in (root / "reports").rglob("*.md")
    )
    if reports != actual_reports:
        raise ValueError("Research report inventory changed; review its source lock")
    for relative in reports:
        _source_file(root, relative)
    return len(sources), len(maintained)


def main() -> None:
    if (REPORTS / "needed").exists():
        raise ValueError(
            "Human request and review registers must remain outside the research library"
        )
    runpy.run_path(str(REPORTS / "exports/papers/verify.py"), run_name="__main__")
    portal_module = runpy.run_path(
        str(
            ROOT
            / "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/docs/report_portal_check.py"
        )
    )
    portal = portal_module["check_report_portal"](ROOT)
    print(
        f"verified {portal.registered_surface_count} report portal surfaces, "
        f"{portal.markdown_page_count} Markdown identities and "
        f"{portal.excluded_metadata_count} explicit metadata exclusions"
    )
    ownership_module = runpy.run_path(
        str(
            ROOT
            / "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/report_rebuild/ownership.py"
        )
    )
    ownership = ownership_module["check_report_ownership"](ROOT)
    print(
        f"verified {ownership.path_count} output ownership declarations; "
        f"{ownership.unresolved_path_count} paths still require custody resolution"
    )
    verify_reader_paths()
    verify_runtime_measurement()
    verify_python_baseline()
    verify_native_forward()
    verify_native_memory()
    verify_empd2_nfi_pairing()
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    locked_count, maintained_count = verify_source_lock(ROOT, lock)
    reports = lock["reports"]
    checked = 0
    for relative in reports:
        page = ROOT / relative
        for target in LINK.findall(page.read_text(encoding="utf-8")):
            if target.startswith(("https://", "http://", "mailto:", "#")):
                continue
            local = target.split("#", 1)[0]
            if not (page.parent / local).exists():
                raise ValueError(f"Broken research link: {relative} -> {target}")
            checked += 1
    print(
        f"verified {len(reports)} research pages, {locked_count} byte-locked "
        f"sources, {maintained_count} maintained paths and {checked} local links"
    )


if __name__ == "__main__":
    main()
