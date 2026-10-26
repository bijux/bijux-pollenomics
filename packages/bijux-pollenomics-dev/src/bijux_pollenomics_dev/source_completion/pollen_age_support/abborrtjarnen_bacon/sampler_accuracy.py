"""Fixed-length prefix replay qualification of the original two ABBO chains."""

from __future__ import annotations

import copy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from typing import Any

from .inputs import PROTOCOL, CoreInputs

ACCURACY_PROTOCOL = Path(
    "reports/science/chronology/abborrtjarnen-bacon/sampler-accuracy-protocol.json"
)


def _identity(path: Path, size: int, digest: str) -> None:
    with path.open("rb") as stream:
        actual = hashlib.file_digest(stream, "sha256").hexdigest()
    if path.stat().st_size != size or actual != digest:
        raise ValueError(f"Sampler accuracy source identity differs: {path}")


def prepare_case(
    repository: Path, library: Path, case: CoreInputs
) -> tuple[CoreInputs, dict[str, Any]]:
    """Bind the unaltered original target before changing only retained length."""
    qualification = json.loads((repository / ACCURACY_PROTOCOL).read_text())
    expected_execution = {
        "seeds": [314159, 271828],
        "chains": 2,
        "retained_rows_per_seed": 16000,
        "native_ssize_argument": 16500,
        "raw_rows_per_seed": 19501,
        "first_retained_native_row": 3502,
        "last_retained_native_row": 19501,
        "initial_burn_rows": 500,
        "additional_source_equivalent_removals": 3001,
        "saved_proposal_interval": 1325,
        "proposal_ticks_per_seed": 25837500,
        "further_length_escalation_permitted": False,
        "extra_chain_or_new_seed_permitted": False,
    }
    if qualification["execution"] != expected_execution:
        raise ValueError("The single fixed sampler-accuracy length/clock differs")
    original = json.loads(
        subprocess.check_output(
            [
                "git",
                "-C",
                str(repository),
                "show",
                f"{qualification['original_failed_source_commit']}:{PROTOCOL}",
            ]
        )
    )
    if case.protocol != original:
        raise ValueError("The original target-law protocol has changed")
    if [row["seed"] for row in qualification["prefixes"]] != [314159, 271828]:
        raise ValueError("Original seeded prefix identities differ")
    for row in qualification["prefixes"]:
        _identity(repository / row["native_output_path"], row["bytes"], row["sha256"])
        _identity(
            repository / row["native_input_path"],
            row["native_input_bytes"],
            row["native_input_sha256"],
        )
    for row in qualification["runtime_files"]:
        path = library / row["path"] if row["root"] == "library" else Path(row["path"])
        _identity(path, row["bytes"], row["sha256"])
        if row["root"] == "absolute":
            executable = shutil.which("Rscript")
            if executable is None or Path(executable).resolve() != path.resolve():
                raise ValueError("The native Rscript executable differs")
    resources = qualification["resources"]
    if (
        resources["max_total_seconds"],
        resources["peak_rss_budget_bytes"],
        resources["max_output_bytes"],
    ) != (600, 1500000000, 100000000):
        raise ValueError("Sampler accuracy resource ceiling differs")
    protocol = copy.deepcopy(case.protocol)
    protocol["execution"]["requested_ssize_per_chain"] = 16000
    protocol["execution"]["retention"] = (
        "Preserve 19501 raw rows; retain original one-based rows 3502..19501, including each original 4000-row retained prefix exactly once. No additional thinning or burnin."
    )
    protocol["execution"]["resources"]["max_output_bytes"] = 100000000
    return replace(case, protocol=protocol), qualification


def compare_prefix(baseline: Path, extended: Path) -> dict[str, Any]:
    """Compare literal bytes, including the original incomplete final line."""
    compared = 0
    mismatch = None
    prefix_hash = hashlib.sha256()
    with baseline.open("rb") as old, extended.open("rb") as new:
        while expected := old.read(65536):
            actual = new.read(len(expected))
            prefix_hash.update(actual)
            if mismatch is None and actual != expected:
                offset = next(
                    (
                        i
                        for i, (a, b) in enumerate(zip(expected, actual, strict=False))
                        if a != b
                    ),
                    min(len(expected), len(actual)),
                )
                mismatch = compared + offset
            compared += len(expected)
        next_byte_is_newline = new.read(1) == b"\n"
    return {
        "baseline_path": str(baseline),
        "bytes_compared": compared,
        "matched": mismatch is None and next_byte_is_newline,
        "first_mismatch_byte": mismatch,
        "native_prefix_sha256": prefix_hash.hexdigest(),
        "next_byte_starts_new_native_row": next_byte_is_newline,
    }


def prefix_checks(
    repository: Path, destination: Path, qualification: dict[str, Any]
) -> list[dict[str, Any]]:
    """Keep both original chain identities and every failed prefix outcome."""
    rows = []
    for source in qualification["prefixes"]:
        baseline = repository / source["native_output_path"]
        _identity(baseline, source["bytes"], source["sha256"])
        extended = destination / f"seed-{source['seed']}/ABBO/ABBO_51.out"
        check = compare_prefix(baseline, extended)
        rows.append(
            {"seed": source["seed"], "baseline_sha256": source["sha256"], **check}
        )
    return rows


def account(qualification: dict[str, Any]) -> dict[str, Any]:
    """Identify this separate qualification without changing the old refusal."""
    return {
        "protocol": str(ACCURACY_PROTOCOL),
        "original_failed_source_commit": qualification["original_failed_source_commit"],
        "original_failed_status": qualification["original_failed_status"],
        "retained_rows_per_seed": 16000,
        "raw_rows_per_seed": 19501,
        "prefix_checks": [],
        "prefixes_passed": False,
        "diagnostics_passed": False,
        "qualified": False,
        "score_interpretation_permitted": False,
    }
