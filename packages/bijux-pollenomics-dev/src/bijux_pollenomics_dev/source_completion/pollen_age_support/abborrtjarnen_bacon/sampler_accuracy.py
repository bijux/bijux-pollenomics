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


_ORIGINAL_TARGET_PROTOCOL = (
    "0d374ce2190e5e44f70c8b28f18612809688af76",
    "f3a4ff64c2db06cb0d3d832d9b7e67159b63c439",
    "reports/science/chronology/abborrtjarnen-bacon/physical-rate-protocol.json",
    "100644",
    "1f2d4961f835da2fd5984e3f63f35ce6d13b1b9b",
    14653,
    "9853d0f6387428589f2a9ce6f81e9bd8096c161b70e9732d8dd21165cd525a1d",
)


def _original_target_protocol_bytes(
    repository: Path, execution_revision: object
) -> bytes:
    """Read one exact failed-execution target from its normal Git storage witness."""
    execution, storage, path, mode, blob, size, digest = _ORIGINAL_TARGET_PROTOCOL
    if type(execution_revision) is not str or execution_revision != execution:
        raise ValueError("Original failed execution target identity differs")
    if path != str(PROTOCOL):
        raise ValueError("Original target protocol path differs")
    command = ["git", "--no-replace-objects", "-C", str(repository)]
    ancestry = [*command, "merge-base", "--is-ancestor", storage, "HEAD"]
    subprocess.check_output(ancestry, stderr=subprocess.PIPE, timeout=10)
    tree = subprocess.check_output(
        [*command, "ls-tree", "-l", "-z", storage, "--", path],
        stderr=subprocess.PIPE,
        timeout=10,
    )
    records = tree.split(b"\0")
    if len(records) != 2 or records[1] or b"\t" not in records[0]:
        raise ValueError("Original target protocol storage population differs")
    metadata, encoded = records[0].split(b"\t", 1)
    if (
        metadata.split()
        != [
            mode.encode(),
            b"blob",
            blob.encode(),
            str(size).encode(),
        ]
        or encoded != path.encode()
    ):
        raise ValueError("Original target protocol Git identity differs")
    body = subprocess.check_output(
        [*command, "cat-file", "blob", blob], stderr=subprocess.PIPE, timeout=10
    )
    if len(body) != size or hashlib.sha256(body).hexdigest() != digest:
        raise ValueError("Original target protocol bytes differ")
    subprocess.check_output(ancestry, stderr=subprocess.PIPE, timeout=10)
    return body


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
        _original_target_protocol_bytes(
            repository, qualification["original_failed_source_commit"]
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
