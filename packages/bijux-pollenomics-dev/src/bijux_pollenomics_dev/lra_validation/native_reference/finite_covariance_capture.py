"""Authenticate committed-source native custody beside the finite covariance domain."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import stat
from typing import Any

from bijux_pollenomics_dev.lra_validation.native_reference.annulus_capture import (
    _checked,
    _file,
    _relative,
)
from bijux_pollenomics_dev.lra_validation.native_reference.count_domain_capture import (
    COMMAND_NAMES,
    PUBLIC_ARCHIVES,
    RAW_MEMBERS,
    REPORT_SOURCE_MEMBERS,
)
from bijux_pollenomics_dev.lra_validation.reference_replay import CERTIFICATE_SHA256

CAPTURE_ROOT = "data/method-certification/native-r-finite-covariance"
CAPTURE_MANIFEST_SHA256 = (
    "008cb45fa66f8b7c96915678ee3f1ec3026924ba3fe81050ca773515e030199b"
)
CAPTURE_SOURCE_REVISION = "92a0adc1f00245c1a51b4e096e1eaac4c23325e5"


@dataclass(frozen=True)
class FiniteCovarianceCapture:
    """Retained actual native bytes; this witness does not establish covariance R parity."""

    directory: Path
    source_archives: Path
    source_revision: str
    manifest_sha256: str
    report_source_members: tuple[str, ...]
    raw_sha256: dict[str, str]
    input_sha256: dict[str, str]
    source_context: dict[str, Any]


def validated_finite_covariance_capture(repository: Path) -> FiniteCovarianceCapture:
    """Require reviewed physical bytes and the exact current scientific source closure."""
    repository = repository.resolve(strict=True)
    manifest_path = f"{CAPTURE_ROOT}/capture/capture.json"
    payload = _file(repository, manifest_path)
    if hashlib.sha256(payload).hexdigest() != CAPTURE_MANIFEST_SHA256:
        raise ValueError("Finite covariance native admission pin differs")
    record = json.loads(payload)
    if (
        record["schema_version"] != "native-r-finite-covariance-capture.v1"
        or record["source_revision"] != CAPTURE_SOURCE_REVISION
        or record["r_version"] != "4.6.0"
        or record["release_certificate"] is not False
        or record["original_certificate_sha256"] != CERTIFICATE_SHA256
        or any(
            type(record[key]) is not int or record[key] != value
            for key, value in (
                ("core_passed", 43),
                ("domains_passed", 23),
                ("original_vectors_compared", 48),
                ("cached_public_archive_count", 5),
            )
        )
    ):
        raise ValueError("Actual finite covariance native execution scope differs")
    context = record["source_context"]
    science = context["protected_science_sha256"]
    if (
        context["schema_version"] != "native-r-committed-source-context.v1"
        or context["base_revision"] != CAPTURE_SOURCE_REVISION
        or context["committed_export"] is not True
        or context["execution_overlays"] != {}
        or not isinstance(science, dict)
        or len(science) != 68
        or record["independent_terminal_review"] is None
    ):
        raise ValueError("Reviewed committed scientific source custody required")
    inputs = {manifest_path: CAPTURE_MANIFEST_SHA256}

    def member(name: str, identity: dict[str, Any]) -> bytes:
        path = f"{CAPTURE_ROOT}/{_relative(name, 'finite covariance native member')}"
        body = _checked(repository, path, identity)
        inputs[path] = identity["sha256"]
        return body

    raw = record["raw_members"]
    reports = record["report_source_members"]
    if frozenset(raw) != RAW_MEMBERS or tuple(reports) != REPORT_SOURCE_MEMBERS:
        raise ValueError("Exact native numeric/raw membership differs")
    raw_digests = {}
    for name, identity in raw.items():
        member(f"capture/{name}", identity)
        raw_digests[name] = identity["sha256"]
    receipt = json.loads(member("capture/receipt.json", record["execution_receipt"]))
    review = record["independent_terminal_review"]
    member(review["path"], {key: review[key] for key in ("sha256", "size")})
    evidence = context["evidence_members"]
    if set(evidence) != {
        f"execution-evidence/{name}"
        for name in (
            "plan.json",
            "terminal.json",
            "candidate-custody.json",
            "runner.py",
            "host-before.json",
            "host-after.json",
        )
    }:
        raise ValueError("Exact execution custody evidence required")
    retained_evidence = {
        name: member(name, identity) for name, identity in evidence.items()
    }
    terminal = json.loads(retained_evidence["execution-evidence/terminal.json"])
    plan = json.loads(retained_evidence["execution-evidence/plan.json"])
    if (
        terminal["status"] != "passed"
        or type(terminal["exit_code"]) is not int
        or terminal["exit_code"] != 0
        or terminal["candidate"] != CAPTURE_SOURCE_REVISION
        or plan["candidate"] != CAPTURE_SOURCE_REVISION
        or terminal["plan_sha256"] != evidence["execution-evidence/plan.json"]["sha256"]
        or terminal["source_unchanged"] is not True
        or terminal["host_unchanged"] is not True
        or terminal["host_before_sha256"]
        != evidence["execution-evidence/host-before.json"]["sha256"]
        or terminal["host_after_sha256"]
        != evidence["execution-evidence/host-after.json"]["sha256"]
        or terminal["host_before_sha256"] != terminal["host_after_sha256"]
        or terminal["outputs_sha256"]["native/receipt.json"]
        != record["execution_receipt"]["sha256"]
    ):
        raise ValueError("Actual terminal or before/after custody differs")
    if (
        receipt["schema_version"] != "native-r-oracle-execution.1"
        or receipt["status"] != "passed"
        or receipt["fresh_R_executed"] is not True
        or receipt["release_certificate"] is not False
        or receipt["r_version"] != "4.6.0"
        or receipt["current_inputs_sha256"] != science
        or receipt["lock_sha256"] != record["source_lock_sha256"]
        or tuple(command["name"] for command in receipt["commands"]) != COMMAND_NAMES
        or any(
            type(command["exit_code"]) is not int
            or command["exit_code"] != 0
            or command["timed_out"] is not False
            or not isinstance(command["duration_seconds"], (int, float))
            or not math.isfinite(command["duration_seconds"])
            or command["duration_seconds"] < 0
            for command in receipt["commands"]
        )
    ):
        raise ValueError("Actual native command receipt differs")
    sources = {source["package"]: source for source in receipt["sources"]}
    if (
        len(receipt["sources"]) != 5
        or set(sources) != set(PUBLIC_ARCHIVES)
        or record["public_archives"] != PUBLIC_ARCHIVES
    ):
        raise ValueError("Exact locked native archive population differs")
    for name, identity in PUBLIC_ARCHIVES.items():
        source = sources[name]
        if (
            source["origin"] != "exact_private_source_cache"
            or source["version"] != identity["version"]
            or source["sha256"] != identity["sha256"]
            or source["byte_count"] != identity["size"]
        ):
            raise ValueError("Cached source provenance differs")
        member(
            identity["path"], {"sha256": identity["sha256"], "size": identity["size"]}
        )
    public = record["public_acquisition"]
    member(public["path"], {key: public[key] for key in ("sha256", "size")})
    physical = set()
    for path in (repository / CAPTURE_ROOT).rglob("*"):
        mode = path.lstat().st_mode
        if stat.S_ISDIR(mode):
            continue
        if not stat.S_ISREG(mode):
            raise ValueError("Native source packet has aliases or irregular members")
        physical.add(path.relative_to(repository).as_posix())
    if physical != set(inputs):
        raise ValueError("Native source packet has extra/missing members")
    for name, digest in science.items():
        if hashlib.sha256(_file(repository, name)).hexdigest() != digest:
            raise ValueError(
                "Current protected source differs from finite covariance capture"
            )
    certificate = "docs/report/method-certification/original-r-reference/reference-bundle/certificate.json"
    if hashlib.sha256(_file(repository, certificate)).hexdigest() != CERTIFICATE_SHA256:
        raise ValueError("Original R certificate changed")
    if any(
        hashlib.sha256(_file(repository, name)).hexdigest() != digest
        for name, digest in inputs.items()
    ):
        raise ValueError("Native admission changed during validation")
    return FiniteCovarianceCapture(
        repository / CAPTURE_ROOT / "capture",
        repository / CAPTURE_ROOT / "source-archives",
        CAPTURE_SOURCE_REVISION,
        CAPTURE_MANIFEST_SHA256,
        tuple(reports),
        raw_digests,
        inputs,
        context,
    )
