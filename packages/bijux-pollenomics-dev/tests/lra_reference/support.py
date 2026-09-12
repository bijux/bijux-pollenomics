"""Synthetic contract fixtures; these are never empirical or actual-R evidence."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

LOCK = (
    Path(os.environ["LRA_REFERENCE_TEST_LOCK"])
    if "LRA_REFERENCE_TEST_LOCK" in os.environ
    else Path(__file__).resolve().parents[4] / "configs/ci/lra-r-source-lock.v1.json"
)
APIS = [
    "DispersalFactorK",
    "REVEALS",
    "REVEALSinR",
    "LOVEr",
    "LOVEoptim",
    "lov",
    "calK",
    "tf",
    "logeuclidean",
]
MODES = [
    "unmodified_function",
    "sampler_instrumented_wrapper",
    "supplied_random_draws",
    "sampler_and_optimizer_replay",
]
SHA = "1" * 40
REPOSITORY = "example/pollenomics"


def oracle_fixture() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    manifest = [
        {
            "id": f"C{index:04d}",
            "name": f"synthetic-contract-{index}",
            "api": APIS[index % 9],
            "mode": MODES[index % 4],
            "rtol": 1e-9,
            "atol": 1e-12,
            "values": 1,
        }
        for index in range(25)
    ]
    report: dict[str, Any] = {
        "schema_version": "1.0.0",
        "oracle": "disqover",
        "status": "passed",
        "source_version": "0.9.14",
        "source_archive_sha256": json.loads(LOCK.read_text())["reference"]["sha256"],
        "live_R_executed": True,
        "prepared_cases": 25,
        "passed_cases": 25,
        "failed_cases": 0,
        "R_exit_code": 0,
        "source_compatible_api": list(APIS),
        "api_covered_by_prepared_cases": list(APIS),
        "cases": [
            {
                "id": row["id"],
                "name": row["name"],
                "api": row["api"],
                "mode": row["mode"],
                "status": "passed",
            }
            for row in manifest
        ],
    }
    return report, manifest


def bundle_fixture(root: Path) -> dict[str, Any]:
    from bijux_pollenomics_dev.ci.lra_reference.evidence import file_inventory

    root.mkdir()
    (root / "oracle").mkdir()
    lock_bytes = LOCK.read_bytes()
    lock = json.loads(lock_bytes)
    lock_sha = hashlib.sha256(lock_bytes).hexdigest()
    (root / "source-lock.json").write_bytes(lock_bytes)
    report, manifest = oracle_fixture()
    (root / "oracle/report.json").write_text(json.dumps(report))
    (root / "oracle/case_manifest.json").write_text(json.dumps(manifest))
    (root / "oracle/R_case_status.csv").write_text(
        "id,status,message\n"
        + "".join(f"C{index:04d},completed,\n" for index in range(25))
    )
    (root / "oracle/R_session_info.txt").write_text(
        "Synthetic validator fixture. Not an executed runtime."
    )
    (root / "oracle/oracle.R").write_text(
        "# Synthetic contract fixture. This code was not run.\n"
    )
    for index in range(25):
        (root / f"oracle/C{index:04d}.csv").write_text("kind,value\nnumeric,0\n")
    runtime = {
        "version": "4.6.0",
        "Rscript_sha256": "2" * 64,
        "origin": "source-built-verified",
    }
    library_files = {"synthetic": "3" * 64}
    packages = [
        {
            "package": row["package"],
            "version": row["version"],
            "library": "/synthetic/library/" + row["package"],
        }
        for row in lock["packages"]
    ]
    packages.append(
        {
            "package": "disqover",
            "version": "0.9.14",
            "library": "/synthetic/library/disqover",
        }
    )
    provision = {
        "schema_version": "lra-r-provision.v1",
        "status": "passed",
        "lock_sha256": lock_sha,
        "library": "/synthetic/library",
        "r_runtime": runtime,
        "library_files": library_files,
        "installed_packages": packages,
        "runtime_build": {
            "schema_version": "lra-r-runtime.v1",
            "status": "passed",
            "lock_sha256": lock_sha,
            "source_archive_sha256": lock["r"]["sha256"],
            "Rscript_sha256": runtime["Rscript_sha256"],
            "runtime_files": {"synthetic": {"sha256": "4" * 64, "byte_count": 1}},
        },
    }
    (root / "provision.json").write_text(json.dumps(provision))
    domain_fixture(root / "source-domains", lock["reference"]["sha256"])
    certificate = {
        "required_profiles": {
            "core_source_compatibility": 25,
            "source_domains_corrected_forward": 23,
        },
        "schema_version": "lra-live-r-certification.v2",
        "status": "passed",
        "fixture_only": True,
        "python_runtime": {
            "version": "3.11.13",
            "executable_sha256": "7" * 64,
            "distributions": [
                {"name": name, "version": "synthetic"}
                for name in ("numpy", "pandas", "scipy")
            ],
        },
        "source_commit": SHA,
        "source_tree": "5" * 40,
        "source_unchanged": True,
        "source_files": {"synthetic.py": "6" * 64},
        "tracked_git_blobs": {"synthetic.py": "7" * 40},
        "generated_source_files": {},
        "engine_version_identity": {
            "origin": "source-only-unknown-fallback",
            "version": "0+unknown",
        },
        "committed_source": True,
        "lock_sha256": lock_sha,
        "profile_id": lock["profile_id"],
        "r_runtime": runtime,
        "library_files": library_files,
        "shared_input_representation": "executed-oracle.R-inline-literals-v1",
        "github": {"repository": REPOSITORY, "run_id": 7, "run_attempt": 1},
        "files": file_inventory(root),
    }
    (root / "certificate.json").write_text(json.dumps(certificate))
    return certificate


def domain_fixture(root: Path, reference_hash: str) -> None:
    root.mkdir()
    semantics = {
        "S001": "source-wrapper-refusal",
        "S002": "source-wrapper-refusal",
        "S003": "legacy-source-refusal",
        "S004": "legacy-source-refusal",
        "S005": "source-supported-zero-local",
        "S006": "source-supported-zero-regional",
        **{
            f"S{index:03d}": "source-supported-supplied-regional"
            for index in range(7, 11)
        },
        **{f"F{index:03d}": "corrected-matrix-forward" for index in range(1, 11)},
        "F011": "corrected-matrix-single-local",
        "F012": "corrected-matrix-single-regional",
        "F013": "corrected-matrix-rounded-cover",
    }
    rows = [
        {"id": key, "semantics": meaning, "values": 1, "passed": True}
        for key, meaning in semantics.items()
    ]
    report: dict[str, Any] = {
        "schema_version": "1.0.0",
        "profile": "disqover-source-domains-and-corrected-forward-v1",
        "source_version": "0.9.14",
        "source_archive_sha256": reference_hash,
        "prepared_cases": 23,
        "live_R_executed": True,
        "passed_cases": 23,
        "failed_cases": 0,
        "status": "passed",
        "r_exit_code": 0,
        "cases": rows,
        "retained_source_sha256": {},
    }
    for name in ("run_source_domains.py", "source_domains.R", "r_support.R"):
        data = b"# Synthetic unexecuted contract fixture\n"
        (root / name).write_bytes(data)
        report["retained_source_sha256"][name] = hashlib.sha256(data).hexdigest()
    (root / "report.json").write_text(json.dumps(report))
    (root / "case_manifest.json").write_text(json.dumps(rows))
    (root / "R_case_status.csv").write_text(
        "id,status,message\n" + "".join(key + ",completed,\n" for key in semantics)
    )
    for key in semantics:
        (root / (key + "-R.csv")).write_text("value\n0\n")
        (root / (key + "-rings.csv")).write_text("synthetic\n")
