"""Check the root research library and its selected governed source identities."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
from statistics import median


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


def main() -> None:
    verify_reader_paths()
    verify_runtime_measurement()
    verify_python_baseline()
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    if lock.get("schema_version") != "research-report-source-lock.v1":
        raise ValueError("Unexpected research report source lock")
    reports = sorted(
        path.relative_to(ROOT).as_posix() for path in REPORTS.rglob("*.md")
    )
    if reports != lock["reports"]:
        raise ValueError("Research report inventory changed; review its source lock")
    for relative, expected in lock["sources"].items():
        path = ROOT / relative
        if (
            not path.is_file()
            or not path.resolve().is_relative_to(ROOT)
            or hashlib.sha256(path.read_bytes()).hexdigest() != expected
        ):
            raise ValueError(
                f"Review changed research source before publishing: {relative}"
            )
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
        f"verified {len(reports)} research pages, {len(lock['sources'])} "
        f"locked sources and {checked} local links"
    )


if __name__ == "__main__":
    main()
