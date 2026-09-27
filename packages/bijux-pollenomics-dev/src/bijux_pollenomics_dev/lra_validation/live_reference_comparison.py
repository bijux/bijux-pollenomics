"""Preserve and compare current native R output with the original R certificate."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any

import numpy as np
import pandas as pd

from bijux_pollenomics_dev.ci.lra_reference.evidence import validate_bundle
from bijux_pollenomics_dev.lra_validation.reference_replay import (
    CERTIFICATE_SHA256,
    compare_vectors,
)


_SAFE_ENVIRONMENT = frozenset(
    {
        "R_LIBS_USER",
        "R_LIBS_SITE",
        "R_ENVIRON_USER",
        "R_PROFILE_USER",
        "PYTHONDONTWRITEBYTECODE",
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
        "TZ",
        "LANG",
        "LC_ALL",
        "PATH",
        "R_MAKEVARS_USER",
    }
)


def _read_vector(path: Path) -> np.ndarray:
    data = pd.read_csv(path, keep_default_na=False, dtype=str)
    if "value" not in data:
        raise ValueError("R vector has no value column")
    if "kind" in data and set(data["kind"]) == {"character"}:
        return data["value"].to_numpy()
    return pd.to_numeric(
        data["value"].replace({"NaN": np.nan, "NA": np.nan}), errors="raise"
    ).to_numpy(float)


def summarize(
    repository: Path, run: Path, original: Path, output: Path, private_sources: Path
) -> dict[str, Any]:
    """Validate exact inputs and all output denominators before retaining raw R."""
    repository, run, original, output = (
        p.resolve() for p in (repository, run, original, output)
    )
    if output.exists():
        raise ValueError("Durable output must be absent")
    original_certificate = original / "certificate.json"
    if (
        hashlib.sha256(original_certificate.read_bytes()).hexdigest()
        != CERTIFICATE_SHA256
    ):
        raise ValueError("Original certificate changed")
    certificate = json.loads(original_certificate.read_text())
    validate_bundle(
        original,
        target_sha=certificate["source_commit"],
        expected_lock_sha256=certificate["lock_sha256"],
    )
    receipt = json.loads((run / "receipt.json").read_text())
    lock_path = repository / "configs/ci/lra-r-source-lock.v1.json"
    lock = json.loads(lock_path.read_text())
    if (
        receipt.get("status") != "passed"
        or receipt.get("fresh_R_executed") is not True
        or receipt.get("release_certificate") is not False
    ):
        raise ValueError("Actual current R pass and nonrelease scope required")
    if (
        receipt.get("lock_sha256") != hashlib.sha256(lock_path.read_bytes()).hexdigest()
        or receipt.get("r_version") != lock["runtime_policy"]["r_version"]
    ):
        raise ValueError("Native R runtime/lock differs")
    if any(
        hashlib.sha256((repository / p).read_bytes()).hexdigest() != h
        for p, h in receipt["current_inputs_sha256"].items()
    ):
        raise ValueError("Current R/Python input changed")
    for command in receipt["commands"]:
        if command["exit_code"] != 0 or command["timed_out"]:
            raise ValueError("R command failed")
        environment = [
            part.split("=", 1)[0]
            for part in command["argv"][1:]
            if "=" in part and part.split("=", 1)[0].isidentifier()
        ]
        if set(environment) - _SAFE_ENVIRONMENT:
            raise ValueError("Receipt contains unrelated process environment")
    if {item["package"] for item in receipt["sources"]} != {
        "GenSA",
        "RcppArmadillo",
        "RcppDE",
        "Rmalschains",
        "plyr",
    }:
        raise ValueError("Missing exact private-source custody")
    sources = {item["package"]: item for item in receipt["sources"]}
    for row in lock["packages"]:
        name = row["package"]
        if receipt["final_locked_versions"].get(name) != row["version"]:
            raise ValueError("Locked dependency differs: " + name)
        if name in sources:
            item = sources[name]
            p = private_sources / row["archive_filename"]
            if (
                item["origin"] != "exact_private_source_cache"
                or item["sha256"] != row["sha256"]
                or hashlib.sha256(p.read_bytes()).hexdigest() != row["sha256"]
            ):
                raise ValueError("Private source archive changed: " + name)
    original_core = json.loads((original / "oracle/case_manifest.json").read_text())
    current_core = json.loads((run / "oracle/case_manifest.json").read_text())
    original_domain = json.loads(
        (original / "source-domains/case_manifest.json").read_text()
    )
    current_domain = json.loads((run / "source-domains/case_manifest.json").read_text())
    outcomes = []
    current_by_name = {row["name"]: row for row in current_core}
    for row in original_core:
        current = current_by_name[row["name"]]
        if any(current[k] != row[k] for k in ("api", "mode", "rtol", "atol", "values")):
            raise ValueError(
                "Original core comparison contract changed: " + row["name"]
            )
        o = _read_vector(original / "oracle" / (row["id"] + ".csv"))
        n = _read_vector(run / "oracle" / (current["id"] + ".csv"))
        outcomes.append(
            {
                "profile": "core",
                "original_id": row["id"],
                "current_id": current["id"],
                "name": row["name"],
                **compare_vectors(
                    n,
                    o,
                    rtol=row["rtol"],
                    atol=row["atol"],
                    exact_indices=tuple(row.get("exact_indices", ())),
                ),
            }
        )
    if current_domain != original_domain:
        raise ValueError("Source-domain input declaration changed")
    for row in original_domain:
        id_ = row["id"]
        o = _read_vector(original / "source-domains" / (id_ + "-R.csv"))
        n = _read_vector(run / "source-domains" / (id_ + "-R.csv"))
        outcomes.append(
            {
                "profile": "source-domains",
                "original_id": id_,
                "current_id": id_,
                "semantics": row["semantics"],
                **compare_vectors(n, o, rtol=1e-10, atol=3e-10),
            }
        )
    oracle = json.loads((run / "oracle/report.json").read_text())
    domains = json.loads((run / "source-domains/report.json").read_text())
    if (
        any(
            (x.get("status") != "passed" or x.get("failed_cases") != 0)
            for x in (oracle, domains)
        )
        or oracle.get("passed_cases") != 43
        or domains.get("passed_cases") != 23
    ):
        raise ValueError("Full fresh R case denominators differ")
    new = [
        row
        for row in current_core
        if row["name"] not in {old["name"] for old in original_core}
    ]
    if len(new) != 18 or len(outcomes) != 48:
        raise ValueError("Current/new and original case denominators differ")
    output.mkdir(parents=True)
    for name in ("oracle", "source-domains"):
        shutil.copytree(run / name, output / name)
    report = {
        "schema_version": "current-native-r-reference.1",
        "status": "passed",
        "fresh_R_executed": True,
        "release_certificate": False,
        "original_certificate_sha256": CERTIFICATE_SHA256,
        "original_source_commit": certificate["source_commit"],
        "current_inputs_sha256": receipt["current_inputs_sha256"],
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "r_version": receipt["r_version"],
        "rscript_sha256": receipt["rscript_sha256"],
        "source_lock_sha256": receipt["lock_sha256"],
        "current_core_attempted": 43,
        "current_core_passed": 43,
        "current_domains_attempted": 23,
        "current_domains_passed": 23,
        "new_core_cases": [
            {"id": r["id"], "name": r["name"], "api": r["api"], "mode": r["mode"]}
            for r in new
        ],
        "original_R_to_current_R_compared": len(outcomes),
        "original_R_to_current_R_cases": outcomes,
        "private_source_custody": [
            {
                "package": x["package"],
                "version": x["version"],
                "sha256": x["sha256"],
                "byte_count": x["byte_count"],
            }
            for x in receipt["sources"]
        ],
        "raw_results_sha256": {
            p.relative_to(output).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in output.rglob("*")
            if p.is_file()
        },
        "scientific_limitations": [
            "native macOS reference execution is not the locked Linux release certificate",
            "optimizer trajectory excluded",
            "no ecological accuracy or measured vegetation truth",
        ],
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--private-sources", type=Path, required=True)
    args = parser.parse_args()
    summarize(
        args.repository, args.run, args.original, args.output, args.private_sources
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
