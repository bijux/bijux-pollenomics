"""Authenticate the independently admitted native count-domain source packet."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
import hashlib
import json
import math
from pathlib import Path
import stat
from typing import Any, TypedDict

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.retained_source import validated_descriptor
from bijux_pollenomics_dev.ci.report_rebuild.retained_source.capsule import (
    native_oracle_members,
)
from bijux_pollenomics_dev.lra_validation.native_reference.annulus_capture import (
    _checked,
    _file,
    _relative,
)
from bijux_pollenomics_dev.lra_validation.reference_replay import CERTIFICATE_SHA256


class _PublicArchive(TypedDict):
    """Exact mixed-value identity of one independently acquired source archive."""

    path: str
    sha256: str
    size: int
    version: str


CAPTURE_ROOT = "data/method-certification/native-r-count-domain"
CAPTURE_MANIFEST_SHA256 = (
    "3df20fa6eee85e55438ea782bde2a5cc5c126c8a5d9587f9af2787c5e08bddaf"
)
CAPTURE_SOURCE_REVISION = "60061f9d60c519673e479fc7bf8e478cd653c4e1"
SOURCE_CONTEXT_SHA256 = (
    "2b0fb1762cf8bf5fc0b12bacebbd1d1dfdb1bc0ab7f7d8a503bc49c99b6e364a"
)
COUNT_DOMAIN_OVERLAYS = {
    "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/fixed_site_covariance.py": {
        "after_sha256": "4dde1a078ae7d57f3c93e93fa8cc4e73756f551e774d78aadb606fa47c483448",
        "before_sha256": "27111502bc7d0d7e61d234bd40d7d5ef2edffc98b652ed0571c4d1aed2000c7c",
    },
    "packages/bijux-pollenomics-lra/tests/unit/reconstruction/test_fixed_site_covariance.py": {
        "after_sha256": "c1b1fb2b033c2124068e620dcd5d1eb5ec3f758ce163229ec8bc0661874cf5ae",
        "before_sha256": "e14d449a03eeace4588ee20c8aad0b56b32e7ad82e46ff6cc0d464cb5917ab4e",
    },
}
RAW_MEMBERS = frozenset(
    [
        "oracle/C0000.csv",
        "oracle/C0001.csv",
        "oracle/C0002.csv",
        "oracle/C0003.csv",
        "oracle/C0004.csv",
        "oracle/C0005.csv",
        "oracle/C0006.csv",
        "oracle/C0007.csv",
        "oracle/C0008.csv",
        "oracle/C0009.csv",
        "oracle/C0010.csv",
        "oracle/C0011.csv",
        "oracle/C0012.csv",
        "oracle/C0013.csv",
        "oracle/C0014.csv",
        "oracle/C0015.csv",
        "oracle/C0016.csv",
        "oracle/C0017.csv",
        "oracle/C0018.csv",
        "oracle/C0019.csv",
        "oracle/C0020.csv",
        "oracle/C0021.csv",
        "oracle/C0022.csv",
        "oracle/C0023.csv",
        "oracle/C0024.csv",
        "oracle/C0025.csv",
        "oracle/C0026.csv",
        "oracle/C0027.csv",
        "oracle/C0028.csv",
        "oracle/C0029.csv",
        "oracle/C0030.csv",
        "oracle/C0031.csv",
        "oracle/C0032.csv",
        "oracle/C0033.csv",
        "oracle/C0034.csv",
        "oracle/C0035.csv",
        "oracle/C0036.csv",
        "oracle/C0037.csv",
        "oracle/C0038.csv",
        "oracle/C0039.csv",
        "oracle/C0040.csv",
        "oracle/C0041.csv",
        "oracle/C0042.csv",
        "oracle/R_case_status.csv",
        "oracle/R_session_info.txt",
        "oracle/R_stderr.log",
        "oracle/R_stdout.log",
        "oracle/case_manifest.json",
        "oracle/oracle.R",
        "oracle/python_expected_not_R_goldens.npz",
        "oracle/report.json",
        "source-domains/F001-R.csv",
        "source-domains/F001-rings.csv",
        "source-domains/F002-R.csv",
        "source-domains/F002-rings.csv",
        "source-domains/F003-R.csv",
        "source-domains/F003-rings.csv",
        "source-domains/F004-R.csv",
        "source-domains/F004-rings.csv",
        "source-domains/F005-R.csv",
        "source-domains/F005-rings.csv",
        "source-domains/F006-R.csv",
        "source-domains/F006-rings.csv",
        "source-domains/F007-R.csv",
        "source-domains/F007-rings.csv",
        "source-domains/F008-R.csv",
        "source-domains/F008-rings.csv",
        "source-domains/F009-R.csv",
        "source-domains/F009-rings.csv",
        "source-domains/F010-R.csv",
        "source-domains/F010-rings.csv",
        "source-domains/F011-R.csv",
        "source-domains/F011-rings.csv",
        "source-domains/F012-R.csv",
        "source-domains/F012-rings.csv",
        "source-domains/F013-R.csv",
        "source-domains/F013-rings.csv",
        "source-domains/R_case_status.csv",
        "source-domains/R_session_info.txt",
        "source-domains/R_stderr.log",
        "source-domains/R_stdout.log",
        "source-domains/S001-R.csv",
        "source-domains/S001-rings.csv",
        "source-domains/S001-source-error.txt",
        "source-domains/S002-R.csv",
        "source-domains/S002-rings.csv",
        "source-domains/S002-source-error.txt",
        "source-domains/S003-R.csv",
        "source-domains/S003-corrected-output.csv",
        "source-domains/S003-legacy-output.csv",
        "source-domains/S003-rings.csv",
        "source-domains/S004-R.csv",
        "source-domains/S004-corrected-output.csv",
        "source-domains/S004-legacy-output.csv",
        "source-domains/S004-rings.csv",
        "source-domains/S005-R.csv",
        "source-domains/S005-rings.csv",
        "source-domains/S006-R.csv",
        "source-domains/S006-rings.csv",
        "source-domains/S007-R.csv",
        "source-domains/S007-rings.csv",
        "source-domains/S008-R.csv",
        "source-domains/S008-rings.csv",
        "source-domains/S009-R.csv",
        "source-domains/S009-rings.csv",
        "source-domains/S010-R.csv",
        "source-domains/S010-rings.csv",
        "source-domains/case_manifest.csv",
        "source-domains/case_manifest.json",
        "source-domains/command.json",
        "source-domains/parameters.csv",
        "source-domains/python_expected_not_R_goldens/F001.npy",
        "source-domains/python_expected_not_R_goldens/F002.npy",
        "source-domains/python_expected_not_R_goldens/F003.npy",
        "source-domains/python_expected_not_R_goldens/F004.npy",
        "source-domains/python_expected_not_R_goldens/F005.npy",
        "source-domains/python_expected_not_R_goldens/F006.npy",
        "source-domains/python_expected_not_R_goldens/F007.npy",
        "source-domains/python_expected_not_R_goldens/F008.npy",
        "source-domains/python_expected_not_R_goldens/F009.npy",
        "source-domains/python_expected_not_R_goldens/F010.npy",
        "source-domains/python_expected_not_R_goldens/F011.npy",
        "source-domains/python_expected_not_R_goldens/F012.npy",
        "source-domains/python_expected_not_R_goldens/F013.npy",
        "source-domains/python_expected_not_R_goldens/S001.npy",
        "source-domains/python_expected_not_R_goldens/S002.npy",
        "source-domains/python_expected_not_R_goldens/S003.npy",
        "source-domains/python_expected_not_R_goldens/S004.npy",
        "source-domains/python_expected_not_R_goldens/S005.npy",
        "source-domains/python_expected_not_R_goldens/S006.npy",
        "source-domains/python_expected_not_R_goldens/S007.npy",
        "source-domains/python_expected_not_R_goldens/S008.npy",
        "source-domains/python_expected_not_R_goldens/S009.npy",
        "source-domains/python_expected_not_R_goldens/S010.npy",
        "source-domains/r_support.R",
        "source-domains/report.json",
        "source-domains/run_source_domains.py",
        "source-domains/source_domains.R",
    ]
)
REPORT_SOURCE_MEMBERS: tuple[str, ...] = (
    "oracle/C0000.csv",
    "oracle/C0001.csv",
    "oracle/C0002.csv",
    "oracle/C0003.csv",
    "oracle/C0004.csv",
    "oracle/C0005.csv",
    "oracle/C0006.csv",
    "oracle/C0007.csv",
    "oracle/C0008.csv",
    "oracle/C0009.csv",
    "oracle/C0010.csv",
    "oracle/C0011.csv",
    "oracle/C0012.csv",
    "oracle/C0013.csv",
    "oracle/C0014.csv",
    "oracle/C0015.csv",
    "oracle/C0016.csv",
    "oracle/C0017.csv",
    "oracle/C0018.csv",
    "oracle/C0019.csv",
    "oracle/C0020.csv",
    "oracle/C0021.csv",
    "oracle/C0022.csv",
    "oracle/C0023.csv",
    "oracle/C0024.csv",
    "oracle/C0025.csv",
    "oracle/C0026.csv",
    "oracle/C0027.csv",
    "oracle/C0028.csv",
    "oracle/C0029.csv",
    "oracle/C0030.csv",
    "oracle/C0031.csv",
    "oracle/C0032.csv",
    "oracle/C0033.csv",
    "oracle/C0034.csv",
    "oracle/C0035.csv",
    "oracle/C0036.csv",
    "oracle/C0037.csv",
    "oracle/C0038.csv",
    "oracle/C0039.csv",
    "oracle/C0040.csv",
    "oracle/C0041.csv",
    "oracle/C0042.csv",
    "oracle/R_case_status.csv",
    "oracle/R_session_info.txt",
    "oracle/case_manifest.json",
    "oracle/python_expected_not_R_goldens.npz",
    "oracle/report.json",
    "source-domains/F001-R.csv",
    "source-domains/F001-rings.csv",
    "source-domains/F002-R.csv",
    "source-domains/F002-rings.csv",
    "source-domains/F003-R.csv",
    "source-domains/F003-rings.csv",
    "source-domains/F004-R.csv",
    "source-domains/F004-rings.csv",
    "source-domains/F005-R.csv",
    "source-domains/F005-rings.csv",
    "source-domains/F006-R.csv",
    "source-domains/F006-rings.csv",
    "source-domains/F007-R.csv",
    "source-domains/F007-rings.csv",
    "source-domains/F008-R.csv",
    "source-domains/F008-rings.csv",
    "source-domains/F009-R.csv",
    "source-domains/F009-rings.csv",
    "source-domains/F010-R.csv",
    "source-domains/F010-rings.csv",
    "source-domains/F011-R.csv",
    "source-domains/F011-rings.csv",
    "source-domains/F012-R.csv",
    "source-domains/F012-rings.csv",
    "source-domains/F013-R.csv",
    "source-domains/F013-rings.csv",
    "source-domains/R_case_status.csv",
    "source-domains/R_session_info.txt",
    "source-domains/S001-R.csv",
    "source-domains/S001-rings.csv",
    "source-domains/S001-source-error.txt",
    "source-domains/S002-R.csv",
    "source-domains/S002-rings.csv",
    "source-domains/S002-source-error.txt",
    "source-domains/S003-R.csv",
    "source-domains/S003-corrected-output.csv",
    "source-domains/S003-legacy-output.csv",
    "source-domains/S003-rings.csv",
    "source-domains/S004-R.csv",
    "source-domains/S004-corrected-output.csv",
    "source-domains/S004-legacy-output.csv",
    "source-domains/S004-rings.csv",
    "source-domains/S005-R.csv",
    "source-domains/S005-rings.csv",
    "source-domains/S006-R.csv",
    "source-domains/S006-rings.csv",
    "source-domains/S007-R.csv",
    "source-domains/S007-rings.csv",
    "source-domains/S008-R.csv",
    "source-domains/S008-rings.csv",
    "source-domains/S009-R.csv",
    "source-domains/S009-rings.csv",
    "source-domains/S010-R.csv",
    "source-domains/S010-rings.csv",
    "source-domains/case_manifest.csv",
    "source-domains/case_manifest.json",
    "source-domains/parameters.csv",
    "source-domains/python_expected_not_R_goldens/F001.npy",
    "source-domains/python_expected_not_R_goldens/F002.npy",
    "source-domains/python_expected_not_R_goldens/F003.npy",
    "source-domains/python_expected_not_R_goldens/F004.npy",
    "source-domains/python_expected_not_R_goldens/F005.npy",
    "source-domains/python_expected_not_R_goldens/F006.npy",
    "source-domains/python_expected_not_R_goldens/F007.npy",
    "source-domains/python_expected_not_R_goldens/F008.npy",
    "source-domains/python_expected_not_R_goldens/F009.npy",
    "source-domains/python_expected_not_R_goldens/F010.npy",
    "source-domains/python_expected_not_R_goldens/F011.npy",
    "source-domains/python_expected_not_R_goldens/F012.npy",
    "source-domains/python_expected_not_R_goldens/F013.npy",
    "source-domains/python_expected_not_R_goldens/S001.npy",
    "source-domains/python_expected_not_R_goldens/S002.npy",
    "source-domains/python_expected_not_R_goldens/S003.npy",
    "source-domains/python_expected_not_R_goldens/S004.npy",
    "source-domains/python_expected_not_R_goldens/S005.npy",
    "source-domains/python_expected_not_R_goldens/S006.npy",
    "source-domains/python_expected_not_R_goldens/S007.npy",
    "source-domains/python_expected_not_R_goldens/S008.npy",
    "source-domains/python_expected_not_R_goldens/S009.npy",
    "source-domains/python_expected_not_R_goldens/S010.npy",
    "source-domains/report.json",
)
COMMAND_NAMES = (
    "initial-installed",
    "runtime",
    "install-GenSA",
    "install-RcppArmadillo",
    "install-Rmalschains",
    "install-plyr",
    "install-RcppDE",
    "install-disqover",
    "final-installed",
    "oracle",
    "source-domains",
)
PUBLIC_ARCHIVES: dict[str, _PublicArchive] = {
    "GenSA": {
        "path": "source-archives/GenSA_1.1.15.tar.gz",
        "sha256": "68970dc3b463986b5b7130acbd42a5ae5a85835d004fb54f81b3ef5c2fccf925",
        "size": 51065,
        "version": "1.1.15",
    },
    "RcppArmadillo": {
        "path": "source-archives/RcppArmadillo_15.4.2-1.tar.gz",
        "sha256": "141c8da25f1e8ff1771b0a1b68d65fbdd821b6061cdd9504ff446ee65f70b801",
        "size": 1093518,
        "version": "15.4.2-1",
    },
    "RcppDE": {
        "path": "source-archives/RcppDE_0.1.9.tar.gz",
        "sha256": "f48aeea87e379beb1a408aef11d65c3f2b8ce09e97c2add6f42f9446ea92fe3b",
        "size": 291113,
        "version": "0.1.9",
    },
    "Rmalschains": {
        "path": "source-archives/Rmalschains_0.2-11.tar.gz",
        "sha256": "cc240727129edd1aa9a1d666dc3ddcc220d5f0e66498e982f72cfef8910ce3f3",
        "size": 265014,
        "version": "0.2-11",
    },
    "plyr": {
        "path": "source-archives/plyr_1.8.9.tar.gz",
        "sha256": "15b5e7f711d53bf41b8687923983b8ef424563aa2f74c5195feb5b1df1aee103",
        "size": 401488,
        "version": "1.8.9",
    },
}
RSCRIPT_SHA256 = "d918ce5022d859e20c38094bb0b6199186cefd8bb96ffeb58618471c9a65a22d"
FORTRAN_RUNTIME_SHA256 = (
    "624e083bf9ebdcd8c6713ef8adaf1aa49ec2a1756cd0dbaed553fd48fc3e6950"
)
_GENERATED_VERSION = (
    "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/_build_version.py"
)


@dataclass(frozen=True)
class CountDomainCapture:
    """Actual retained native bytes; validation runs neither R nor a compiler."""

    directory: Path
    source_archives: Path
    source_revision: str
    manifest_sha256: str
    report_source_members: tuple[str, ...]
    raw_sha256: dict[str, str]
    input_sha256: dict[str, str]
    source_context: dict[str, Any]
    read_input: Callable[[str], bytes] | None = field(
        default=None, compare=False, repr=False
    )


def _canonical_digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def _require_context(context: object) -> dict[str, Any]:
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
        raise ValueError("Count-domain capture requires complete source custody")
    science = context["protected_science_sha256"]
    generated = context["generated_source_sha256"]
    evidence = context["actual_evidence_sha256"]
    if (
        context["schema_version"] != "native-r-count-domain-execution-context.v1"
        or context["base_revision"] != CAPTURE_SOURCE_REVISION
        or context["clean_execution"] is not False
        or context["staged_changes"] is not False
        or context["overlays"] != COUNT_DOMAIN_OVERLAYS
        or not isinstance(science, dict)
        or len(science) != 67
        or not isinstance(generated, dict)
        or set(generated) != {_GENERATED_VERSION}
        or science.get(_GENERATED_VERSION) != generated[_GENERATED_VERSION]
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
            "Count-domain source, overlays or protected input population differs"
        )
    for name in science:
        _relative(name, "protected native count-domain input")
    digests = [
        *science.values(),
        *generated.values(),
        *evidence.values(),
        context["raw_git_inventory_sha256"],
        context["native_input_inventory_sha256"],
    ]
    if any(
        not isinstance(v, str)
        or len(v) != 64
        or any(c not in "0123456789abcdef" for c in v)
        for v in digests
    ):
        raise ValueError("Exact SHA256 custody required")
    if (
        _canonical_digest(context) != SOURCE_CONTEXT_SHA256
        or _canonical_digest(science) != context["native_input_inventory_sha256"]
    ):
        raise ValueError("Count-domain dirty source context differs")
    if any(
        science.get(name) != v["after_sha256"]
        for name, v in COUNT_DOMAIN_OVERLAYS.items()
        if name in science
    ):
        raise ValueError("Count-domain protected overlay differs")
    return context


def validated_count_domain_capture(repository: Path) -> CountDomainCapture:
    """Require the exact current source admission and every retained native member."""
    repository = repository.resolve(strict=True)
    manifest_path = f"{CAPTURE_ROOT}/capture/capture.json"
    payload = _file(repository, manifest_path)
    if hashlib.sha256(payload).hexdigest() != CAPTURE_MANIFEST_SHA256:
        raise ValueError("Count-domain native admission pin differs")
    record = json.loads(payload)
    if (
        record["schema_version"] != "qualified-native-r-count-domain-capture.v1"
        or record["source_revision"] != CAPTURE_SOURCE_REVISION
        or record["r_version"] != "4.6.0"
        or record["release_certificate"] is not False
        or record["original_certificate_sha256"] != CERTIFICATE_SHA256
        or any(
            type(record[k]) is not int or record[k] != n
            for k, n in (
                ("core_passed", 43),
                ("domains_passed", 23),
                ("original_vectors_compared", 48),
                ("cached_public_archive_count", 5),
            )
        )
    ):
        raise ValueError("Actual native execution scope differs")
    context = _require_context(record["source_context"])
    raw_payload: object = record["raw_members"]
    report_payload: object = record["report_source_members"]
    if not isinstance(raw_payload, dict) or any(
        not isinstance(name, str) for name in raw_payload
    ):
        raise ValueError("Exact numeric/raw membership differs")
    raw: dict[str, object] = dict(raw_payload)
    if not isinstance(report_payload, list) or any(
        not isinstance(name, str) for name in report_payload
    ):
        raise ValueError("Exact numeric/raw membership differs")
    reports: list[str] = report_payload
    if (
        frozenset(raw) != RAW_MEMBERS
        or tuple(reports) != REPORT_SOURCE_MEMBERS
        or len(raw) != 138
        or len(reports) != 129
        or sum(name.endswith(".csv") for name in raw) != 97
    ):
        raise ValueError("Exact numeric/raw membership differs")
    try:
        resolver = validated_descriptor(
            repository, CAPTURE_ROOT, native_oracle_members(record)
        )
    except ReportRebuildError as error:
        raise ValueError("Native R source transport differs: " + str(error)) from error

    def source_member(path: str) -> bytes:
        prefix = CAPTURE_ROOT + "/"
        if not path.startswith(prefix):
            raise ValueError("Native input escaped its capture")
        try:
            return resolver.read_source(path.removeprefix(prefix))
        except ReportRebuildError as error:
            raise ValueError(
                "Native R retained input changed: " + str(error)
            ) from error

    inputs = {manifest_path: CAPTURE_MANIFEST_SHA256}

    def read_input(path: str) -> bytes:
        if path not in inputs:
            raise ValueError("Unlisted native input read")
        body = _file(repository, path) if path == manifest_path else source_member(path)
        if hashlib.sha256(body).hexdigest() != inputs[path]:
            raise ValueError("Native admission changed during validation")
        return body

    raw_digests: dict[str, str] = {}
    for name, raw_spec in raw.items():
        if not isinstance(raw_spec, dict) or any(
            not isinstance(key, str) for key in raw_spec
        ):
            raise ValueError("native R capture member identity is invalid")
        spec: dict[str, object] = dict(raw_spec)
        digest = spec.get("sha256")
        if not isinstance(digest, str):
            raise ValueError("native R capture member identity is invalid")
        path = f"{CAPTURE_ROOT}/capture/{_relative(name, 'count-domain raw member')}"
        _checked(repository, path, spec, read_source=source_member)
        inputs[path] = digest
        raw_digests[name] = digest
    receipt_path = f"{CAPTURE_ROOT}/capture/receipt.json"
    receipt = json.loads(
        _checked(
            repository,
            receipt_path,
            record["execution_receipt"],
            read_source=source_member,
        )
    )
    inputs[receipt_path] = record["execution_receipt"]["sha256"]
    if (
        receipt["schema_version"] != "native-r-oracle-execution.1"
        or receipt["status"] != "passed"
        or receipt["fresh_R_executed"] is not True
        or receipt["release_certificate"] is not False
        or receipt["r_version"] != "4.6.0"
        or receipt["rscript_sha256"] != RSCRIPT_SHA256
        or receipt["fortran_runtime_sha256"] != FORTRAN_RUNTIME_SHA256
        or receipt["current_inputs_sha256"] != context["protected_science_sha256"]
        or receipt["lock_sha256"] != record["source_lock_sha256"]
        or tuple(c["name"] for c in receipt["commands"]) != COMMAND_NAMES
        or any(
            type(c["exit_code"]) is not int
            or c["exit_code"] != 0
            or c["timed_out"] is not False
            or not isinstance(c["duration_seconds"], (int, float))
            or not math.isfinite(c["duration_seconds"])
            or c["duration_seconds"] < 0
            for c in receipt["commands"]
        )
    ):
        raise ValueError("Actual native command receipt differs")
    sources = {v["package"]: v for v in receipt["sources"]}
    if (
        len(receipt["sources"]) != 5
        or set(sources) != set(PUBLIC_ARCHIVES)
        or record["public_archives"] != PUBLIC_ARCHIVES
    ):
        raise ValueError("Exact cached public archive population differs")
    for name, row in PUBLIC_ARCHIVES.items():
        source = sources[name]
        if (
            source["origin"] != "exact_private_source_cache"
            or source["version"] != row["version"]
            or source["sha256"] != row["sha256"]
            or source["byte_count"] != row["size"]
        ):
            raise ValueError("Cached source provenance differs")
        path = f"{CAPTURE_ROOT}/{_relative(row['path'], 'cached native archive')}"
        _checked(
            repository,
            path,
            {"size": row["size"], "sha256": row["sha256"]},
            read_source=source_member,
        )
        inputs[path] = row["sha256"]
    public = record["public_acquisition"]
    public_path = (
        f"{CAPTURE_ROOT}/{_relative(public['path'], 'historical native acquisition')}"
    )
    _checked(
        repository,
        public_path,
        {"size": public["size"], "sha256": public["sha256"]},
        read_source=source_member,
    )
    inputs[public_path] = public["sha256"]
    physical = set()
    for member in (repository / CAPTURE_ROOT).rglob("*"):
        mode = member.lstat().st_mode
        if stat.S_ISDIR(mode):
            continue
        if not stat.S_ISREG(mode):
            raise ValueError("Native source packet has aliases or irregular members")
        physical.add(member.relative_to(repository).as_posix())
    if physical != (
        set(inputs) - {CAPTURE_ROOT + "/" + name for name in resolver.detached}
    ) | {CAPTURE_ROOT + "/source-transport.json"}:
        raise ValueError("Native source packet has extra/missing members")
    science = context["protected_science_sha256"]
    for name, digest in science.items():
        if hashlib.sha256(_file(repository, name)).hexdigest() != digest:
            raise ValueError(
                "Current protected source differs from count-domain capture"
            )
    if (
        hashlib.sha256(
            _file(
                repository,
                "docs/report/method-certification/original-r-reference/reference-bundle/certificate.json",
            )
        ).hexdigest()
        != CERTIFICATE_SHA256
    ):
        raise ValueError("Original R certificate changed")
    if (
        hashlib.sha256(
            _file(repository, "configs/ci/lra-r-source-lock.v1.json")
        ).hexdigest()
        != record["source_lock_sha256"]
    ):
        raise ValueError("Current locked source differs")
    if (
        any(
            hashlib.sha256(read_input(name)).hexdigest() != digest
            for name, digest in inputs.items()
        )
        or _file(repository, manifest_path) != payload
    ):
        raise ValueError("Native admission changed during validation")
    return CountDomainCapture(
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
