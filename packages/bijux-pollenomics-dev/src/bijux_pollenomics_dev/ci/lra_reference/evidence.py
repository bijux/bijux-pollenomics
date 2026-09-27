"""Strict shared validation for local and retrieved actual-R evidence bundles."""

from __future__ import annotations

import csv
import hashlib
import io
import math
from pathlib import Path, PurePosixPath
import re
from typing import Any

from .contracts import ReferenceRefusal, load_lock, read_json

APIS = frozenset(
    {
        "DispersalFactorK",
        "REVEALS",
        "REVEALSinR",
        "LOVEr",
        "LOVEoptim",
        "lov",
        "calK",
        "tf",
        "logeuclidean",
    }
)
MODES = frozenset(
    {
        "unmodified_function",
        "sampler_instrumented_wrapper",
        "supplied_random_draws",
        "sampler_and_optimizer_replay",
    }
)
CORE_CASE_IDS = frozenset(f"C{index:04d}" for index in range(25))
EXTENDED_CASE_IDS = frozenset(f"C{index:04d}" for index in range(43))
PROSPECTIVE_CASE_HASHES = {
    "mixed-canopy-compact": "d84c9d9c6631c208f25b6ef8b5fdd8cc6a5e509eaa371795d1a2c19fee0b12c0",
    "open-land-extended": "d376065884b1668f6ad89cd14c827bf40c52b53fc16171be8561c71706dd137d",
    "conifer-rich-broad": "7ef8956c4b031c3b12f497e56ed14dee9bbc3064b59780a6b66de9920348fa03",
}
PROSPECTIVE_DECLARATION_SHA256 = (
    "7bd61e0c7feefadf81428261443674612c6767e957fd25ea65591aeab9602ded"
)
PROSPECTIVE_KINDS = {
    "intermediates": ("LOVEoptim", "prospective_fixed_input", 1e-10, 1e-10, None),
    "taxon_axis": ("LOVEoptim", "prospective_fixed_input", 0, 0, 10),
    "ring_axis": ("LOVEoptim", "prospective_fixed_input", 0, 0, 36),
    "wrapper_replay": (
        "LOVEoptim",
        "prospective_sampler_and_optimizer_replay",
        1e-10,
        1e-10,
        None,
    ),
    "nonfinite_objective": ("tf", "prospective_nonfinite", 1e-10, 1e-10, 1),
    "all_nonfinite_refusal": ("LOVEoptim", "prospective_refusal", 0, 0, 1),
}
SCHEMA = "lra-live-r-certification.v2"


def file_inventory(root: Path) -> dict[str, dict[str, Any]]:
    """Hash regular evidence files and refuse links or special entries."""
    result = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ReferenceRefusal("Evidence trees may not contain symlinks")
        if path.is_file():
            data = path.read_bytes()
            result[path.relative_to(root).as_posix()] = {
                "sha256": hashlib.sha256(data).hexdigest(),
                "byte_count": len(data),
            }
        elif not path.is_dir():
            raise ReferenceRefusal("Evidence trees may contain only regular files")
    return result


def validate_oracle(
    report: Any,
    manifest: Any,
    reference_hash: str,
    *,
    expected_core_cases: int | None = None,
) -> int:
    """Require the complete, source-bound actual-R oracle case profile."""
    if not isinstance(report, dict) or not isinstance(manifest, list):
        raise ReferenceRefusal("Oracle report/manifest shape differs")
    count = report.get("prepared_cases")
    if (
        type(count) is not int
        or count not in {25, 43}
        or (expected_core_cases is not None and count != expected_core_cases)
    ):
        raise ReferenceRefusal("Exact oracle profile denominator differs")
    ids = CORE_CASE_IDS if count == 25 else EXTENDED_CASE_IDS
    exact = {
        "status": "passed",
        "oracle": "disqover",
        "source_version": "0.9.14",
        "source_archive_sha256": reference_hash,
        "live_R_executed": True,
        "prepared_cases": count,
        "passed_cases": count,
        "failed_cases": 0,
        "R_exit_code": 0,
    }
    if any(
        type(report.get(key)) is not type(expected) or report[key] != expected
        for key, expected in exact.items()
    ):
        raise ReferenceRefusal("Actual R execution and all cases are required")
    cases = report.get("cases")
    if not isinstance(cases, list) or len(cases) != count or len(manifest) != count:
        raise ReferenceRefusal("Exact oracle case denominator is missing")
    if any(not isinstance(row, dict) for row in [*cases, *manifest]):
        raise ReferenceRefusal("Malformed oracle case row")
    if (
        frozenset(row.get("id") for row in cases) != ids
        or frozenset(row.get("id") for row in manifest) != ids
    ):
        raise ReferenceRefusal("Oracle case IDs are missing or duplicated")
    if (
        frozenset(row.get("api") for row in cases) != APIS
        or frozenset(row.get("mode") for row in cases[:25]) != MODES
    ):
        raise ReferenceRefusal("Required numerical API/replay coverage is missing")
    if (
        frozenset(report.get("source_compatible_api", [])) != APIS
        or frozenset(report.get("api_covered_by_prepared_cases", [])) != APIS
    ):
        raise ReferenceRefusal("Source-compatible API declaration differs")
    indexed = {row["id"]: row for row in manifest}
    for row in cases:
        expected = indexed[row["id"]]
        if row.get("status") != "passed" or any(
            row.get(key) != expected.get(key) for key in ("name", "api", "mode")
        ):
            raise ReferenceRefusal(
                "Oracle case result disagrees with the supplied-input manifest"
            )
        if not isinstance(expected.get("name"), str) or not expected["name"]:
            raise ReferenceRefusal("Unnamed oracle case")
        for key in ("rtol", "atol"):
            number = expected.get(key)
            if (
                type(number) not in (int, float)
                or not math.isfinite(number)
                or number < 0
            ):
                raise ReferenceRefusal("Invalid numerical comparison tolerance")
        if type(expected.get("values")) is not int or expected["values"] < 1:
            raise ReferenceRefusal("Oracle value denominator is missing")
    if count == 43:
        _validate_prospective_oracle(report, manifest)
    return count


def _validate_prospective_oracle(
    report: dict[str, Any], manifest: list[dict[str, Any]]
) -> None:
    prospective = report.get("prospective_optimized_love")
    if not isinstance(prospective, dict) or prospective != {
        "declaration_id": "disqover-0.9.14-optimized-love-prospective-20260924",
        "declaration_sha256": PROSPECTIVE_DECLARATION_SHA256,
        "case_input_sha256": PROSPECTIVE_CASE_HASHES,
        "rtol": 1e-10,
        "atol": 1e-10,
        "stochastic_optimizer_trajectory": "excluded",
    }:
        raise ReferenceRefusal("Frozen prospective LOVE input declaration differs")
    ordered = manifest[25:]
    for index, case_id in enumerate(PROSPECTIVE_CASE_HASHES):
        for offset, (kind, (api, mode, rtol, atol, values)) in enumerate(
            PROSPECTIVE_KINDS.items()
        ):
            row = ordered[index * 6 + offset]
            if (
                row.get("id") != f"C{25 + index * 6 + offset:04d}"
                or row.get("name") != f"{case_id}_{kind}"
                or row.get("api") != api
                or row.get("mode") != mode
                or row.get("rtol") != rtol
                or row.get("atol") != atol
                or (values is not None and row.get("values") != values)
            ):
                raise ReferenceRefusal("Prospective LOVE case/profile differs")
            exact_indices = row.get("exact_indices", [])
            if (
                not isinstance(exact_indices, list)
                or any(
                    type(item) is not int or item < 0 or item >= row["values"]
                    for item in exact_indices
                )
                or (kind == "wrapper_replay" and not exact_indices)
            ):
                raise ReferenceRefusal("Prospective exact-coordinate contract differs")


def validate_bundle(
    root: Path,
    *,
    target_sha: str,
    expected_lock_sha256: str,
    expected_run: tuple[str, int, int] | None = None,
) -> dict[str, Any]:
    """Check source/runtime/case/member closure; transport authenticity is external."""
    try:
        certificate = read_json((root / "certificate.json").read_bytes())
        if (
            not isinstance(certificate, dict)
            or certificate.get("schema_version") != SCHEMA
            or certificate.get("status") != "passed"
        ):
            raise ReferenceRefusal("An actual passed certification bundle is required")
        if (
            re.fullmatch(r"[0-9a-f]{40}", target_sha) is None
            or certificate.get("source_commit") != target_sha
        ):
            raise ReferenceRefusal(
                "Certification source commit differs from the release target"
            )
        if certificate.get("source_unchanged") is not True:
            raise ReferenceRefusal("Source changed during reference execution")
        if (
            not isinstance(certificate.get("source_files"), dict)
            or not certificate["source_files"]
        ):
            raise ReferenceRefusal("Executed source inventory is missing")
        if certificate.get("lock_sha256") != expected_lock_sha256:
            raise ReferenceRefusal("Certification source lock differs")
        inventory = file_inventory(root)
        inventory.pop("certificate.json", None)
        if inventory != certificate.get("files"):
            raise ReferenceRefusal("Certification bundle file inventory differs")
        from .source_identity import validate_generated_evidence

        validate_generated_evidence(root, certificate)
        lock_path = root / "source-lock.json"
        if hashlib.sha256(lock_path.read_bytes()).hexdigest() != expected_lock_sha256:
            raise ReferenceRefusal("Bundled source-lock bytes differ")
        lock = load_lock(lock_path)
        if certificate.get("profile_id") != lock.payload["profile_id"]:
            raise ReferenceRefusal("Certification profile differs")
        provision = read_json((root / "provision.json").read_bytes())
        if (
            provision.get("schema_version") != "lra-r-provision.v1"
            or provision.get("status") != "passed"
            or provision.get("lock_sha256") != expected_lock_sha256
        ):
            raise ReferenceRefusal("Successful source-locked provisioning is missing")
        runtime = provision.get("r_runtime", {})
        if runtime.get("version") != lock.payload["runtime_policy"][
            "r_version"
        ] or not runtime.get("Rscript_sha256"):
            raise ReferenceRefusal("Actual pinned R interpreter identity is missing")
        if (
            certificate.get("r_runtime") != runtime
            or certificate.get("library_files") != provision.get("library_files")
            or not certificate["library_files"]
        ):
            raise ReferenceRefusal("Runtime/library byte closure differs")
        expected_versions = {
            row.package: row.version for row in lock.sources if row.package != "R"
        }
        expected_versions["disqover"] = lock.payload["reference"]["version"]
        packages = provision.get("installed_packages", [])
        if (
            len(packages) != len(expected_versions)
            or {row["package"]: row["version"] for row in packages} != expected_versions
        ):
            raise ReferenceRefusal("Installed dependency version closure differs")
        if any(
            PurePosixPath(row["library"])
            != PurePosixPath(provision["library"]) / row["package"]
            for row in packages
        ):
            raise ReferenceRefusal("Dependency loaded outside the private library")
        report = read_json((root / "oracle/report.json").read_bytes())
        manifest = read_json((root / "oracle/case_manifest.json").read_bytes())
        count = validate_oracle(
            report,
            manifest,
            lock.payload["reference"]["sha256"],
            expected_core_cases=43 if expected_run is not None else None,
        )
        required = {
            "oracle/R_case_status.csv",
            "oracle/R_session_info.txt",
            "oracle/oracle.R",
            *(
                f"oracle/{name}.csv"
                for name in (CORE_CASE_IDS if count == 25 else EXTENDED_CASE_IDS)
            ),
        }
        if (
            not required <= inventory.keys()
            or certificate.get("shared_input_representation")
            != "executed-oracle.R-inline-literals-v1"
        ):
            raise ReferenceRefusal("Raw R outputs/shared inputs are missing")
        statuses = list(
            csv.DictReader(io.StringIO((root / "oracle/R_case_status.csv").read_text()))
        )
        if (
            len(statuses) != count
            or frozenset(row.get("id") for row in statuses)
            != (CORE_CASE_IDS if count == 25 else EXTENDED_CASE_IDS)
            or any(row.get("status") != "completed" for row in statuses)
        ):
            raise ReferenceRefusal(
                "Raw R completion status differs from the reported pass"
            )
        for item in manifest:
            with (root / "oracle" / f"{item['id']}.csv").open() as handle:
                raw = list(csv.DictReader(handle))
            if len(raw) != item["values"] or any(
                set(row) != {"kind", "value"}
                or row["kind"] not in {"numeric", "character"}
                for row in raw
            ):
                raise ReferenceRefusal("Raw R value denominator/schema differs")
            for value in raw:
                if value["kind"] == "numeric":
                    try:
                        float(value["value"])
                    except (TypeError, ValueError) as error:
                        raise ReferenceRefusal(
                            "Malformed raw R numeric value"
                        ) from error
        required_profiles = {
            "core_source_compatibility": 25,
            "source_domains_corrected_forward": 23,
        }
        if count == 43:
            required_profiles["prospective_optimized_love"] = 18
        if certificate.get("required_profiles") != required_profiles:
            raise ReferenceRefusal("Required reference profile denominators differ")
        from .profiles import validate_source_domains

        validate_source_domains(
            root / "source-domains", lock.payload["reference"]["sha256"]
        )
        python_runtime = certificate.get("python_runtime")
        if (
            not isinstance(python_runtime, dict)
            or not isinstance(python_runtime.get("version"), str)
            or re.match(r"^3\.11\.[0-9]+", python_runtime["version"]) is None
            or not isinstance(python_runtime.get("executable_sha256"), str)
            or re.fullmatch(r"[0-9a-f]{64}", python_runtime["executable_sha256"])
            is None
        ):
            raise ReferenceRefusal(
                "Actual supported Python interpreter identity is missing"
            )
        distributions = python_runtime.get("distributions")
        if (
            not isinstance(distributions, list)
            or not distributions
            or any(
                not isinstance(row, dict)
                or not isinstance(row.get("name"), str)
                or not isinstance(row.get("version"), str)
                or not row["version"]
                for row in distributions
            )
        ):
            raise ReferenceRefusal(
                "Actual Python dependency version inventory is missing"
            )
        names = [row["name"].casefold() for row in distributions]
        if len(names) != len(set(names)) or not {"numpy", "pandas", "scipy"} <= set(
            names
        ):
            raise ReferenceRefusal(
                "Numerical Python dependency inventory is incomplete or ambiguous"
            )
        if expected_run is not None:
            build = provision.get("runtime_build")
            if (
                not isinstance(build, dict)
                or build.get("schema_version") != "lra-r-runtime.v1"
                or build.get("status") != "passed"
                or build.get("lock_sha256") != expected_lock_sha256
                or build.get("source_archive_sha256") != lock.payload["r"]["sha256"]
                or build.get("Rscript_sha256") != runtime["Rscript_sha256"]
                or not build.get("runtime_files")
                or runtime.get("origin") != "source-built-verified"
            ):
                raise ReferenceRefusal(
                    "Release requires verified source-built R runtime evidence"
                )
            owner, run_id, attempt = expected_run
            expected = {"repository": owner, "run_id": run_id, "run_attempt": attempt}
            if (
                certificate.get("github") != expected
                or certificate.get("committed_source") is not True
            ):
                raise ReferenceRefusal(
                    "Release requires same-attempt committed CI evidence"
                )
        return certificate
    except ReferenceRefusal:
        raise
    except (OSError, KeyError, TypeError, ValueError, AttributeError) as error:
        raise ReferenceRefusal(
            "Malformed or incomplete certification bundle"
        ) from error
