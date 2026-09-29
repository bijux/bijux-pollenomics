"""Reexecute the pinned LandClim II author examples and retain bounded parity."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
from typing import Any

from bijux_pollenomics_dev.essd_reproduction.method_profile import _checked_private

SOURCE_SHA256 = "7675b6e615cddba328bad506692b3a6a31e00d9273cef5ad4641a1737fddfd87"
RUNNER = Path(
    "packages/bijux-pollenomics-lra/tests/reference/publication_oracle/run_author_replay.py"
)
R_WRAPPER = RUNNER.with_suffix(".R")
COMPARATOR = Path(
    "packages/bijux-pollenomics-lra/tests/reference/publication_oracle/compare_author_examples.py"
)
LRA_SOURCE = Path("packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra")
PROFILE = "landclimii-2016-release-source-v1"
GRID_IDS = ("512", "562")
TOLERANCES = {
    "cover": {"atol": 1e-11, "rtol": 1e-10},
    "se": {"atol": 5e-8, "rtol": 1e-9},
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_hashes(repository: Path) -> dict[str, str]:
    paths = [RUNNER, R_WRAPPER, COMPARATOR]
    paths.extend(sorted(LRA_SOURCE.glob("**/*.py")))
    if len(paths) < 40 or any((repository / path).is_symlink() for path in paths):
        raise ValueError("Local numerical source closure is incomplete or linked")
    return {path.as_posix(): _sha(repository / path) for path in paths}


def _environment(library: Path) -> dict[str, str]:
    rscript = subprocess.run(
        ["Rscript", "--version"], capture_output=True, text=True, check=True
    )
    zipfr = subprocess.run(
        [
            "Rscript",
            "--vanilla",
            "-e",
            'cat(as.character(packageVersion("zipfR", lib.loc=commandArgs(TRUE)[1])))',
            str(library),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    if zipfr.stdout.strip() != "0.6.70":
        raise ValueError("Expected exact zipfR 0.6.70 runtime")
    import numpy
    import pandas
    import scipy

    return {
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "python_executable": sys.executable,
        "R": (rscript.stdout + rscript.stderr).strip(),
        "zipfR": zipfr.stdout.strip(),
        "numpy": numpy.__version__,
        "pandas": pandas.__version__,
        "scipy": scipy.__version__,
        "thread_limit": "1",
    }


def _run(
    command: list[str], log: Path, environment: dict[str, str]
) -> dict[str, object]:
    started = time.monotonic()
    with log.open("w", encoding="utf-8") as stream:
        completed = subprocess.run(
            command,
            stdout=stream,
            stderr=subprocess.STDOUT,
            env=environment,
            check=False,
            timeout=2400,
        )
    return {
        "command": command,
        "exit_code": completed.returncode,
        "elapsed_seconds": time.monotonic() - started,
        "log_sha256": _sha(log),
    }


def _verify_comparison(comparison: dict[str, Any]) -> None:
    if comparison.get("profile") != PROFILE or comparison.get("coverage") != (
        "two_author_example_grids_only_not_full_1128_record_study"
    ):
        raise ValueError("Unexpected native comparison scope or profile")
    grids = comparison.get("grids")
    if not isinstance(grids, list) or [grid.get("grid_id") for grid in grids] != list(
        GRID_IDS
    ):
        raise ValueError("Comparison must contain the two declared author grids")
    if [grid.get("sites") for grid in grids] != [9, 8]:
        raise ValueError("Author example site denominator changed")
    for grid in grids:
        if not grid.get("passed") or grid.get("bins") != 25 or grid.get("taxa") != 31:
            raise ValueError("Native comparison grid failed or changed dimensions")
        checks = grid["checks"]
        if checks.get("site_counts_equal") is not True:
            raise ValueError("Native and author site counts disagree")
        pairs = [checks["regional_cover"], checks["regional_se"]]
        pairs.extend(item[kind] for item in checks["sites"] for kind in ("cover", "se"))
        if len(checks["sites"]) != grid["sites"]:
            raise ValueError("A site comparison is missing")
        for position, check in enumerate(pairs):
            expected = TOLERANCES["cover" if position % 2 == 0 else "se"]
            if (
                check.get("passed") is not True
                or check.get("undefined_masks_equal") is not True
                or check.get("atol") != expected["atol"]
                or check.get("rtol") != expected["rtol"]
            ):
                raise ValueError("Numerical parity or prospective tolerance failed")


def _native_output_closure(raw_output: Path) -> dict[str, dict[str, object]]:
    """Check every native output against its per-grid checksum manifest."""
    result: dict[str, dict[str, object]] = {}
    for grid in GRID_IDS:
        directory = raw_output / "comparison" / grid
        manifest = directory / "checksums.json"
        declared = json.loads(manifest.read_text())
        if not isinstance(declared, dict) or not declared:
            raise ValueError("Native output checksum manifest is empty")
        listed = set(declared)
        actual = {
            path.relative_to(directory).as_posix()
            for path in directory.rglob("*")
            if path.is_file()
        }
        if actual != listed | {"checksums.json"}:
            raise ValueError(
                "Native output inventory differs from its checksum manifest"
            )
        total = 0
        for name, identity in declared.items():
            relative = Path(name)
            path = directory / relative
            if relative.is_absolute() or ".." in relative.parts or path.is_symlink():
                raise ValueError("Native output checksum path is unsafe")
            if (
                path.stat().st_size != identity["bytes"]
                or _sha(path) != identity["sha256"]
            ):
                raise ValueError(f"Native output bytes changed: {grid}/{name}")
            total += identity["bytes"]
        result[grid] = {
            "checksum_manifest_sha256": _sha(manifest),
            "files": len(declared),
            "bytes": total,
        }
    return result


def execute(
    repository: Path,
    private: Path,
    library: Path,
    output: Path,
    report_path: Path,
) -> dict[str, object]:
    """Run the existing R and native consumers on an immutable source snapshot."""
    repository, private, library, output, report_path = (
        repository.resolve(),
        private.resolve(),
        library.resolve(),
        output.resolve(),
        report_path.resolve(),
    )
    if output.exists() or report_path.exists():
        raise ValueError("Absent run and governed report destinations required")
    private_hashes = _checked_private(private)
    if (
        private_hashes["author/run.REVEALS.files/LRA-REVEALS-release.R"]
        != SOURCE_SHA256
    ):
        raise ValueError("Private author R source changed")
    source_hashes = _source_hashes(repository)
    environment = _environment(library)
    output.mkdir(parents=True)
    process_environment = dict(os.environ)
    process_environment.update(
        {
            "PYTHONPATH": str(repository / "packages/bijux-pollenomics-lra/src"),
            "PYTHONDONTWRITEBYTECODE": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "OMP_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
        }
    )
    original = _run(
        [
            sys.executable,
            str(repository / RUNNER),
            "--source",
            str(private / "author"),
            "--library",
            str(library),
            "--output",
            str(output / "reference"),
        ],
        output / "original-r.log",
        process_environment,
    )
    native: dict[str, object] | None = None
    if original["exit_code"] == 0:
        native = _run(
            [
                sys.executable,
                str(repository / COMPARATOR),
                "--source",
                str(private / "author"),
                "--reference",
                str(output / "reference"),
                "--output",
                str(output / "comparison"),
            ],
            output / "native-comparison.log",
            process_environment,
        )
    if (
        _source_hashes(repository) != source_hashes
        or _checked_private(private) != private_hashes
    ):
        raise ValueError("Governed source or private snapshot changed during execution")
    reference_path = output / "reference/receipt.json"
    comparison_path = output / "comparison/report.json"
    reference = (
        json.loads(reference_path.read_text()) if reference_path.is_file() else None
    )
    comparison = (
        json.loads(comparison_path.read_text()) if comparison_path.is_file() else None
    )
    if comparison is not None:
        _verify_comparison(comparison)
    native_outputs = _native_output_closure(output) if comparison is not None else None
    passed = bool(
        original["exit_code"] == 0
        and native is not None
        and native["exit_code"] == 0
        and reference is not None
        and reference.get("exit_code") == 0
        and reference.get("input_files_unchanged") is True
        and reference.get("source_sha256") == SOURCE_SHA256
        and comparison is not None
    )
    report: dict[str, object] = {
        "schema_version": "landclim-example-reexecution.v1",
        "scope": "two_author_example_grids_only",
        "passed": passed,
        "repository_head_at_execution": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repository, text=True
        ).strip(),
        "private_snapshot_manifest_sha256": _sha(private / "snapshot-manifest.json"),
        "private_snapshot_members_verified": len(private_hashes),
        "author_r_source_sha256": SOURCE_SHA256,
        "native_source_files": source_hashes,
        "environment": environment,
        "tolerances": TOLERANCES,
        "runs": {"original_r": original, "native_comparison": native},
        "original_r_receipt_sha256": _sha(reference_path)
        if reference is not None
        else None,
        "original_r_receipt": reference,
        "native_comparison_report_sha256": _sha(comparison_path)
        if comparison is not None
        else None,
        "native_comparison": comparison,
        "native_output_checksums": native_outputs,
        "admission": {
            "two_grid_numerical_parity": passed,
            "full_study_reproduction": False,
            "independent_vegetation_accuracy": False,
            "private_input_redistribution_rights_cleared": False,
        },
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    return report


def verify_report(
    report_path: Path, raw_output: Path | None = None
) -> dict[str, object]:
    """Check retained claims and, when available, original raw output hashes."""
    report = json.loads(report_path.read_text())
    if report.get("schema_version") != "landclim-example-reexecution.v1":
        raise ValueError("Unexpected example reexecution report schema")
    if (
        report.get("passed") is not True
        or report.get("author_r_source_sha256") != SOURCE_SHA256
    ):
        raise ValueError("Example execution or source identity was not established")
    if report.get("tolerances") != TOLERANCES:
        raise ValueError("Prospective numerical tolerances changed")
    if report.get("private_snapshot_members_verified") != 193:
        raise ValueError("Private snapshot verification denominator changed")
    sources = report.get("native_source_files")
    if (
        not isinstance(sources, dict)
        or len(sources) < 40
        or any(
            not isinstance(value, str) or len(value) != 64 for value in sources.values()
        )
    ):
        raise ValueError("Native source closure is missing")
    receipt = report.get("original_r_receipt")
    if not isinstance(receipt, dict) or (
        receipt.get("exit_code") != 0
        or receipt.get("source_sha256") != SOURCE_SHA256
        or receipt.get("input_files_unchanged") is not True
        or len(receipt.get("output_files", {})) != 77
    ):
        raise ValueError("Original R receipt failed")
    if report["runs"]["original_r"]["exit_code"] != 0 or (
        report["runs"]["native_comparison"]["exit_code"] != 0
    ):
        raise ValueError("Original or native process failed")
    comparison = report.get("native_comparison")
    if not isinstance(comparison, dict):
        raise ValueError("Native comparison is missing")
    _verify_comparison(comparison)
    if comparison.get("reference_receipt_sha256") != report.get(
        "original_r_receipt_sha256"
    ):
        raise ValueError("Native comparison used a different R receipt")
    native_outputs = report.get("native_output_checksums")
    if not isinstance(native_outputs, dict) or set(native_outputs) != set(GRID_IDS):
        raise ValueError("Native output checksum closure is missing")
    if raw_output is not None:
        reference = raw_output / "reference"
        observed = {
            str(path.relative_to(reference)) for path in reference.rglob("*.csv")
        }
        if observed != set(receipt["output_files"]):
            raise ValueError("Original R output inventory changed")
        for name, expected in receipt["output_files"].items():
            if _sha(reference / name) != expected:
                raise ValueError(f"Original R output bytes changed: {name}")
        if _sha(reference / "receipt.json") != report["original_r_receipt_sha256"]:
            raise ValueError("Original R receipt bytes changed")
        if (
            _sha(raw_output / "comparison/report.json")
            != report["native_comparison_report_sha256"]
        ):
            raise ValueError("Native comparison report bytes changed")
        if _native_output_closure(raw_output) != native_outputs:
            raise ValueError("Native output checksum closure changed")
        for kind, name in (
            ("original_r", "original-r.log"),
            ("native_comparison", "native-comparison.log"),
        ):
            if _sha(raw_output / name) != report["runs"][kind]["log_sha256"]:
                raise ValueError(f"Execution log bytes changed: {name}")
    return {
        "passed": True,
        "grids": list(GRID_IDS),
        "raw_bytes_verified": raw_output is not None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path)
    parser.add_argument("--private", type=Path)
    parser.add_argument("--r-library", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--verify-report", type=Path)
    args = parser.parse_args()
    if args.verify_report is not None:
        print(
            json.dumps(verify_report(args.verify_report, args.output), sort_keys=True)
        )
        return
    if any(
        value is None
        for value in (
            args.repository,
            args.private,
            args.r_library,
            args.output,
            args.report,
        )
    ):
        parser.error(
            "Execution requires --repository, --private, --r-library, --output and --report"
        )
    result = execute(
        args.repository, args.private, args.r_library, args.output, args.report
    )
    if not result["passed"]:
        raise SystemExit("Two-grid original-R/native comparison did not pass")


if __name__ == "__main__":
    main()
