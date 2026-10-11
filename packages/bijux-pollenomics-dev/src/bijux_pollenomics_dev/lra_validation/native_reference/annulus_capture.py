"""Authenticate the separately retained annulus native R capture and dirty source context."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import stat
from typing import Any

CAPTURE_ROOT = "data/method-certification/native-r-annulus"
CAPTURE_MANIFEST_SHA256 = (
    "2c80e50e8fc2a68e784139052ccd31a49a4e4d05413a7eb2b997cfa89f2b9f61"
)
CAPTURE_SOURCE_REVISION = "ed7005d0845f4755a906d7f2642c68100f7ea3d7"
SOURCE_CONTEXT_SHA256 = (
    "feefc8594bf9ad00ba959fa25c4ebb3d8692e76703736f79881a3488b4915ff8"
)
ANNULUS_OVERLAYS = {
    "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/dispersal/receiver_annulus.py": {
        "before_sha256": "f3ae57b79a159824d37a17204a9cb957d97d287b8300ae590c39f54de114bb75",
        "after_sha256": "9aeae845a11540abcddf77dd9f09a418aed8838e52ba516a7eb058efbeff5563",
    },
    "packages/bijux-pollenomics-lra/tests/unit/dispersal/test_receiver_annulus.py": {
        "before_sha256": "349c25fb7381df5972fd084a1658a29064105b00462de39d436ca6896c1dd01b",
        "after_sha256": "9f413a4376365caa976534aa6bbc22496fe6704f23841dda70ddff2ea62fe140",
    },
}
_GENERATED_VERSION = (
    "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/_build_version.py"
)

EXTRA_RAW_MEMBERS = frozenset(
    {
        "oracle/R_stderr.log",
        "oracle/R_stdout.log",
        "oracle/oracle.R",
        "source-domains/R_stderr.log",
        "source-domains/R_stdout.log",
        "source-domains/command.json",
        "source-domains/r_support.R",
        "source-domains/run_source_domains.py",
        "source-domains/source_domains.R",
    }
)


@dataclass(frozen=True)
class AnnulusCapture:
    """Retained actual native bytes; validation never executes R or a compiler."""

    directory: Path
    source_archives: Path
    source_revision: str
    manifest_sha256: str
    report_source_members: tuple[str, ...]
    raw_sha256: dict[str, str]
    input_sha256: dict[str, str]
    source_context: dict[str, Any]


def _relative(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or "\\" in value
        or value.startswith("/")
        or any(part in {"", ".", ".."} for part in value.split("/"))
    ):
        raise ValueError(f"{label} must be a confined canonical repository path")
    return value


def _file(repository: Path, relative: str) -> bytes:
    parts = _relative(relative, "native R source capture").split("/")
    path = repository
    for part in parts[:-1]:
        path /= part
        if not stat.S_ISDIR(path.lstat().st_mode):
            raise ValueError("native R source has a non-real directory")
    path /= parts[-1]
    if not stat.S_ISREG(path.lstat().st_mode) or not path.resolve().is_relative_to(
        repository
    ):
        raise ValueError("native R source must be a confined real regular file")
    if path.stat().st_nlink != 1:
        raise ValueError("native R capture cannot share a file inode")
    return path.read_bytes()


def _checked(repository: Path, name: str, spec: dict[str, Any]) -> bytes:
    _relative(name, "native R capture member")
    if (
        set(spec) != {"sha256", "size"}
        or type(spec["size"]) is not int
        or spec["size"] < 0
    ):
        raise ValueError("native R capture member identity is invalid")
    payload = _file(repository, name)
    if (
        len(payload) != spec["size"]
        or hashlib.sha256(payload).hexdigest() != spec["sha256"]
    ):
        raise ValueError("native R capture member bytes changed")
    return payload


def _require_source_context(context: object) -> None:
    """Keep base Git identity separate from the two physical execution overlays."""
    if not isinstance(context, dict) or set(context) != {
        "schema_version",
        "base_revision",
        "clean_execution",
        "staged_changes",
        "overlays",
        "raw_git_inventory_sha256",
        "native_input_inventory_sha256",
        "protected_science_sha256",
        "generated_source_sha256",
        "actual_evidence_sha256",
    }:
        raise ValueError("annulus capture requires the complete dirty source context")
    science = context["protected_science_sha256"]
    generated = context["generated_source_sha256"]
    evidence = context["actual_evidence_sha256"]
    if (
        context["schema_version"] != "native-r-annulus-execution-context.v1"
        or context["base_revision"] != CAPTURE_SOURCE_REVISION
        or context["clean_execution"] is not False
        or context["staged_changes"] is not False
        or context["overlays"] != ANNULUS_OVERLAYS
        or not isinstance(science, dict)
        or len(science) != 67
        or not isinstance(generated, dict)
        or set(generated) != {_GENERATED_VERSION}
        or science.get(_GENERATED_VERSION) != generated[_GENERATED_VERSION]
        or science.get(next(iter(ANNULUS_OVERLAYS)))
        != ANNULUS_OVERLAYS[next(iter(ANNULUS_OVERLAYS))]["after_sha256"]
        or not isinstance(evidence, dict)
        or set(evidence)
        != {
            "plan",
            "terminal_receipt",
            "output_observation",
            "root_terminal_review",
            "root_retention_approval",
        }
    ):
        raise ValueError(
            "annulus capture base, overlays, or protected source population differs"
        )
    for name in science:
        _relative(name, "protected annulus input")
    digests = [
        *science.values(),
        *generated.values(),
        *evidence.values(),
        context["raw_git_inventory_sha256"],
        context["native_input_inventory_sha256"],
    ]
    if any(
        not isinstance(value, str)
        or len(value) != 64
        or any(char not in "0123456789abcdef" for char in value)
        for value in digests
    ):
        raise ValueError("annulus context requires exact SHA256 identities")


def validated_annulus_capture(repository: Path) -> AnnulusCapture:
    """Require the exact reviewed source packet and complete 139 raw/receipt files."""
    repository = repository.resolve(strict=True)
    manifest_path = f"{CAPTURE_ROOT}/capture/capture.json"
    payload = _file(repository, manifest_path)
    if hashlib.sha256(payload).hexdigest() != CAPTURE_MANIFEST_SHA256:
        raise ValueError("native R capture differs from independent admission pin")
    record = json.loads(payload)
    if (
        record["schema_version"] != "qualified-native-r-annulus-capture.v1"
        or record["source_revision"] != CAPTURE_SOURCE_REVISION
        or record["r_version"] != "4.6.0"
        or record["release_certificate"] is not False
        or any(
            type(record[k]) is not int or record[k] != n
            for k, n in (
                ("core_passed", 43),
                ("domains_passed", 23),
                ("original_vectors_compared", 48),
                ("fresh_public_archive_count", 5),
            )
        )
    ):
        raise ValueError("native R captured execution scope is invalid")
    context = record["source_context"]
    _require_source_context(context)
    if (
        hashlib.sha256(
            json.dumps(
                context, sort_keys=True, separators=(",", ":"), allow_nan=False
            ).encode()
        ).hexdigest()
        != SOURCE_CONTEXT_SHA256
    ):
        raise ValueError("annulus native capture dirty source context differs")
    raw = record["raw_members"]
    reports = record["report_source_members"]
    if (
        len(raw) != 138
        or len(reports) != 129
        or reports != sorted(set(reports))
        or set(raw) != set(reports) | EXTRA_RAW_MEMBERS
    ):
        raise ValueError("native R raw/retained report membership differs")
    if sum(name.endswith(".csv") for name in raw) != 97:
        raise ValueError("annulus capture requires 97 retained numeric CSV files")
    inputs = {manifest_path: CAPTURE_MANIFEST_SHA256}
    for name, spec in raw.items():
        path = f"{CAPTURE_ROOT}/capture/{_relative(name, 'native raw member')}"
        _checked(repository, path, spec)
        inputs[path] = spec["sha256"]
    receipt_path = f"{CAPTURE_ROOT}/capture/receipt.json"
    receipt = json.loads(
        _checked(repository, receipt_path, record["execution_receipt"])
    )
    inputs[receipt_path] = record["execution_receipt"]["sha256"]
    if (
        receipt["status"] != "passed"
        or receipt["fresh_R_executed"] is not True
        or receipt["release_certificate"] is not False
        or receipt["r_version"] != record["r_version"]
        or receipt["schema_version"] != "native-r-oracle-execution.1"
        or receipt["current_inputs_sha256"] != context["protected_science_sha256"]
        or receipt["lock_sha256"] != record["source_lock_sha256"]
        or any(
            type(command["exit_code"]) is not int
            or command["exit_code"] != 0
            or command["timed_out"] is not False
            for command in receipt["commands"]
        )
    ):
        raise ValueError("actual native execution receipt scope differs")
    archive_paths = set()
    for row in record["public_archives"].values():
        path = f"{CAPTURE_ROOT}/{_relative(row['path'], 'public native archive')}"
        _checked(repository, path, {"size": row["size"], "sha256": row["sha256"]})
        inputs[path] = row["sha256"]
        archive_paths.add(path)
    if len(archive_paths) != 5:
        raise ValueError("exact five public native archives required")
    public = record["public_acquisition"]
    public_path = (
        f"{CAPTURE_ROOT}/{_relative(public['path'], 'public native acquisition')}"
    )
    _checked(
        repository, public_path, {"sha256": public["sha256"], "size": public["size"]}
    )
    inputs[public_path] = public["sha256"]
    physical = set()
    for member in (repository / CAPTURE_ROOT).rglob("*"):
        mode = member.lstat().st_mode
        if stat.S_ISDIR(mode):
            continue
        if not stat.S_ISREG(mode):
            raise ValueError("native R source packet has an alias or irregular member")
        physical.add(member.relative_to(repository).as_posix())
    if physical != set(inputs):
        raise ValueError("native R source packet has missing or extra members")
    if any(
        hashlib.sha256(_file(repository, name)).hexdigest() != digest
        for name, digest in inputs.items()
    ):
        raise ValueError("native R source bytes changed during validation")
    if _file(repository, manifest_path) != payload:
        raise ValueError("native R source admission changed during validation")
    return AnnulusCapture(
        repository / CAPTURE_ROOT / "capture",
        repository / CAPTURE_ROOT / "source-archives",
        CAPTURE_SOURCE_REVISION,
        CAPTURE_MANIFEST_SHA256,
        tuple(reports),
        {name: spec["sha256"] for name, spec in raw.items()},
        inputs,
        context,
    )
