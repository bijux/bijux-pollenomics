"""Authenticate committed-source native custody beside the finite covariance domain."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.retained_source import validated_descriptor
from bijux_pollenomics_dev.ci.report_rebuild.retained_source.capsule import (
    native_reference_members,
)
from bijux_pollenomics_dev.ci.report_rebuild.retained_source.descriptor import (
    json_object,
    object_fields,
    pinned_bytes,
)
from bijux_pollenomics_dev.ci.report_rebuild.retained_source.generated import (
    reconstruct,
)
from bijux_pollenomics_dev.ci.report_rebuild.retained_source.objects import (
    GitSourceMember,
    physical,
    query,
    validate_blobs,
)
from bijux_pollenomics_dev.lra_validation.native_reference.annulus_capture import (
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

GENERATED_SOURCE = (
    "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/_build_version.py"
)
GENERATED_CONFIG = (
    "configs/ci/report-capture-projections/native-finite-generated-source.json"
)
GENERATED_CONFIG_SHA256 = (
    "34ea05d479fbf99d7c24485f6df5bca44d8c0eb984ba992033810bf2bb3825e8"
)
GENERATED_CONFIG_BYTES = 677

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
    read_input: Callable[[str], bytes] = field(compare=False, repr=False)


def _generated_source(repository: Path, context: dict[str, Any]) -> bytes:
    """Recover exact metadata content without claiming its original generation."""
    row = object_fields(
        json_object(
            pinned_bytes(
                repository / GENERATED_CONFIG,
                GENERATED_CONFIG_SHA256,
                GENERATED_CONFIG_BYTES,
                8192,
            )
        ),
        {"schema_version", "source_path", "identity", "correspondence"},
    )
    identity = object_fields(row["identity"], {"sha256", "bytes"})
    correspondence = object_fields(
        row["correspondence"],
        {
            "member",
            "generator",
            "scalars",
            "original_generator_execution_claimed",
            "original_version_derivation_claimed",
        },
    )
    expected = context["protected_science_sha256"][GENERATED_SOURCE]
    if (
        row["schema_version"] != "native-finite-generated-source.v1"
        or row["source_path"] != GENERATED_SOURCE
        or correspondence["member"] != GENERATED_SOURCE
        or identity["sha256"] != expected
        or context["generated_source_sha256"] != {GENERATED_SOURCE: expected}
    ):
        raise ValueError("Finite covariance generated source correspondence differs")
    return reconstruct(correspondence, identity)


def _require_current_sources(repository: Path, context: dict[str, Any]) -> None:
    """Keep every tracked scientific identity and exact historical metadata content."""
    from bijux_pollenomics_dev.lra_validation.native_reference.source_layout_adoption import (
        validate_current_native_source,
    )

    for name, digest in context["protected_science_sha256"].items():
        try:
            if name != GENERATED_SOURCE:
                validate_current_native_source(repository, name, digest)
                continue
            body = _generated_source(repository, context)
        except (OSError, ValueError, ReportRebuildError) as error:
            raise ValueError(
                "Current protected source differs from finite covariance capture"
            ) from error
        if hashlib.sha256(body).hexdigest() != digest:
            raise ValueError(
                "Current protected source differs from finite covariance capture"
            )


def validated_finite_covariance_capture(repository: Path) -> FiniteCovarianceCapture:
    """Preserve native identities while reading detached control source through Git."""
    try:
        capture = _validated_finite_covariance_capture(repository)
        require_current_finite_covariance_sources(repository, capture)
        return capture
    except ReportRebuildError as error:
        raise ValueError(str(error)) from error


def _validated_finite_covariance_capture(repository: Path) -> FiniteCovarianceCapture:
    """Require retained bytes, every tracked science input and exact generated metadata."""
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
    resolver = validated_descriptor(
        repository, CAPTURE_ROOT, native_reference_members(record)
    )
    inputs = {manifest_path: CAPTURE_MANIFEST_SHA256}

    def read_input(path: str) -> bytes:
        if path not in inputs:
            raise ValueError("Unlisted native input read")
        try:
            pinned_bytes(
                repository / GENERATED_CONFIG,
                GENERATED_CONFIG_SHA256,
                GENERATED_CONFIG_BYTES,
                8192,
            )
            if path == manifest_path:
                body = _file(repository, path)
            else:
                prefix = CAPTURE_ROOT + "/"
                if not path.startswith(prefix):
                    raise ValueError("Native input escaped its capture")
                body = resolver.read_source(path.removeprefix(prefix))
        except ReportRebuildError as error:
            raise ValueError(str(error)) from error
        if hashlib.sha256(body).hexdigest() != inputs[path]:
            raise ValueError("Native admission changed during validation")
        return body

    def member(name: str, identity: dict[str, Any]) -> bytes:
        path = f"{CAPTURE_ROOT}/{_relative(name, 'finite covariance native member')}"
        if (
            set(identity) != {"sha256", "size"}
            or type(identity["size"]) is not int
            or identity["size"] < 0
        ):
            raise ValueError("native R capture member identity is invalid")
        body = resolver.read_source(path.removeprefix(CAPTURE_ROOT + "/"))
        if (
            len(body) != identity["size"]
            or hashlib.sha256(body).hexdigest() != identity["sha256"]
        ):
            raise ValueError("native R capture member bytes changed")
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
    resolver.fresh()
    _historical_scientific_sources(repository, context)
    certificate = "docs/report/method-certification/original-r-reference/reference-bundle/certificate.json"
    if hashlib.sha256(_file(repository, certificate)).hexdigest() != CERTIFICATE_SHA256:
        raise ValueError("Original R certificate changed")
    if any(
        hashlib.sha256(read_input(name)).hexdigest() != digest
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
        dict(inputs),
        context,
        read_input,
    )


def _historical_scientific_sources(repository: Path, context: dict[str, Any]) -> None:
    """Read the sealed source epoch in place; never reconstruct a package tree."""
    science = context["protected_science_sha256"]
    generated = GENERATED_SOURCE
    raw = _generated_source(repository, context)
    if hashlib.sha256(raw).hexdigest() != science[generated]:
        raise ValueError("Historical generated scientific source bytes differ")
    names = set(science) - {generated}
    physical(repository)
    physical(repository / ".git")
    tree = query(
        repository,
        ["ls-tree", "-r", "-l", "-z", CAPTURE_SOURCE_REVISION, "--", *sorted(names)],
        128 * 1024,
        time.monotonic() + 180,
    )
    members = []
    for row in tree.split(b"\0"):
        if not row:
            continue
        identity, path = row.split(b"\t", 1)
        mode, kind, blob, size = identity.decode("ascii").split()
        name = path.decode("utf-8")
        if mode not in {"100644", "100755"} or kind != "blob" or name not in names:
            raise ValueError("Historical scientific source tree identity differs")
        members.append(
            GitSourceMember(
                name, name, CAPTURE_SOURCE_REVISION, blob, science[name], int(size)
            )
        )
    if len(members) != 67 or {row.member for row in members} != names:
        raise ValueError("Historical scientific source population differs")
    validate_blobs(repository, members)


def historical_finite_covariance_capture(repository: Path) -> FiniteCovarianceCapture:
    """Authenticate sealed historical evidence without admitting current-code reuse."""
    try:
        return _validated_finite_covariance_capture(repository)
    except ReportRebuildError as error:
        raise ValueError(str(error)) from error


def require_current_finite_covariance_sources(
    repository: Path, capture: FiniteCovarianceCapture
) -> None:
    """Check current reuse separately from the authenticated historical source epoch."""
    record = json.loads(capture.read_input(CAPTURE_ROOT + "/capture/capture.json"))
    _require_current_sources(repository, record["source_context"])
    if any(
        hashlib.sha256(capture.read_input(name)).hexdigest() != digest
        for name, digest in capture.input_sha256.items()
    ):
        raise ValueError("Native admission changed during validation")
