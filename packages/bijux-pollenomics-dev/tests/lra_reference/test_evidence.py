"""Passing counts cannot substitute for actual R, exact identities or replay coverage."""

import copy
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.lra_reference.contracts import ReferenceRefusal, read_json
from bijux_pollenomics_dev.ci.lra_reference.evidence import validate_oracle

from .support import oracle_fixture


def payloads() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    return oracle_fixture()


def test_complete_contract_fixture() -> None:
    report, manifest = payloads()
    assert validate_oracle(report, manifest, report["source_archive_sha256"]) == 25


def test_prospective_contract_requires_all_declared_cases() -> None:
    report, manifest = oracle_fixture(extended=True)
    digest = report["source_archive_sha256"]
    assert validate_oracle(report, manifest, digest, expected_core_cases=43) == 43
    with pytest.raises(ReferenceRefusal, match="denominator"):
        old, old_manifest = oracle_fixture()
        validate_oracle(old, old_manifest, digest, expected_core_cases=43)
    report["prospective_optimized_love"]["case_input_sha256"]["open-land-extended"] = (
        "0" * 64
    )
    with pytest.raises(ReferenceRefusal, match="prospective"):
        validate_oracle(report, manifest, digest)


def test_prospective_case_contract_rejects_missing_exact_replay_coordinate() -> None:
    report, manifest = oracle_fixture(extended=True)
    manifest[28]["exact_indices"] = []
    with pytest.raises(ReferenceRefusal, match="exact-coordinate"):
        validate_oracle(report, manifest, report["source_archive_sha256"])


@pytest.mark.parametrize(
    "mutation",
    [
        "no_r",
        "skip",
        "fake_total",
        "boolean_exit",
        "missing_case",
        "duplicate_case",
        "missing_api",
        "missing_replay",
        "different_manifest",
        "wrong_source",
    ],
)
def test_forged_or_incomplete_pass_refuses(mutation: str) -> None:
    report, manifest = payloads()
    digest = report["source_archive_sha256"]
    if mutation == "no_r":
        report["live_R_executed"] = False
    elif mutation == "skip":
        report["status"] = "skipped"
    elif mutation == "fake_total":
        report["passed_cases"] = 24
    elif mutation == "boolean_exit":
        report["R_exit_code"] = False
    elif mutation == "missing_case":
        report["cases"].pop()
    elif mutation == "duplicate_case":
        report["cases"][0] = copy.deepcopy(report["cases"][1])
    elif mutation == "missing_api":
        report["source_compatible_api"].pop()
    elif mutation == "missing_replay":
        for case in report["cases"]:
            case["mode"] = "unmodified_function"
    elif mutation == "different_manifest":
        manifest[0]["name"] = "unrelated-case"
    elif mutation == "wrong_source":
        report["source_archive_sha256"] = "a" * 64
    with pytest.raises(ReferenceRefusal):
        validate_oracle(report, manifest, digest)


@pytest.mark.parametrize(
    "value", [b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":Infinity}', b"{broken"]
)
def test_strict_evidence_json(value: bytes) -> None:
    with pytest.raises(ReferenceRefusal):
        read_json(value)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_member",
        "changed_member",
        "missing_profile",
        "mixed_semantics",
        "raw_denominator",
        "wrong_ci",
        "wrong_runtime",
        "wrong_lock",
        "uncommitted",
    ],
)
def test_bundle_closure_refuses(tmp_path: Path, mutation: str) -> None:

    from bijux_pollenomics_dev.ci.lra_reference.evidence import (
        file_inventory,
        validate_bundle,
    )

    from .support import REPOSITORY, SHA, bundle_fixture

    root = tmp_path / "bundle"
    certificate = bundle_fixture(root)
    lock_hash = certificate["lock_sha256"]
    if mutation == "missing_member":
        (root / "oracle/C0000.csv").unlink()
    elif mutation == "changed_member":
        (root / "oracle/C0000.csv").write_text("changed")
    elif mutation == "missing_profile":
        certificate["required_profiles"].pop("source_domains_corrected_forward")
    elif mutation == "mixed_semantics":
        path = root / "source-domains/report.json"
        report = json.loads(path.read_text())
        report["cases"][0]["semantics"] = "corrected-matrix-forward"
        path.write_text(json.dumps(report))
        certificate["files"] = file_inventory(root)
        certificate["files"].pop("certificate.json")
    elif mutation == "raw_denominator":
        (root / "oracle/C0000.csv").write_text("kind,value\n")
        certificate["files"] = file_inventory(root)
        certificate["files"].pop("certificate.json")
    elif mutation == "wrong_ci":
        certificate["github"]["run_attempt"] = 2
    elif mutation == "wrong_runtime":
        certificate["r_runtime"]["version"] = "4.6.1"
    elif mutation == "wrong_lock":
        lock_hash = "a" * 64
    elif mutation == "uncommitted":
        certificate["committed_source"] = False
    (root / "certificate.json").write_text(json.dumps(certificate))
    with pytest.raises(ReferenceRefusal):
        validate_bundle(
            root,
            target_sha=SHA,
            expected_lock_sha256=lock_hash,
            expected_run=(REPOSITORY, 7, 1),
        )


@pytest.mark.parametrize(
    "defect",
    [
        None,
        "changed",
        "missing",
        "symlink",
        "hardlink",
        "missing_pin",
        "wrong_pin",
        "partial_retention",
        "raw_rows",
    ],
)
def test_current_bundle_authenticates_canonical_scripts_without_source_copies(
    tmp_path: Path, defect: str | None
) -> None:
    from bijux_pollenomics_dev.ci.lra_reference.evidence import (
        file_inventory,
        validate_bundle,
    )

    from .support import SHA, bundle_fixture

    root = tmp_path / "bundle"
    repository = tmp_path / "repository"
    certificate = bundle_fixture(root)
    owner = "packages/bijux-pollenomics-lra/tests/reference/lra_oracle"
    for name in ("run_source_domains.py", "source_domains.R", "r_support.R"):
        source = root / "source-domains" / name
        target = repository / owner / name
        target.parent.mkdir(parents=True, exist_ok=True)
        source.rename(target)
        raw = target.read_bytes()
        certificate["source_files"][f"{owner}/{name}"] = hashlib.sha256(raw).hexdigest()
        certificate["tracked_git_blobs"][f"{owner}/{name}"] = hashlib.sha1(
            b"blob " + str(len(raw)).encode() + b"\0" + raw
        ).hexdigest()
    relative = f"{owner}/r_support.R"
    target = repository / relative
    if defect == "changed":
        target.write_bytes(target.read_bytes() + b"Changed scientific source\n")
    elif defect == "missing":
        target.unlink()
    elif defect in {"symlink", "hardlink"}:
        outside = tmp_path / "aliased-source.R"
        target.rename(outside)
        if defect == "symlink":
            target.symlink_to(outside)
        else:
            os.link(outside, target)
    elif defect == "missing_pin":
        del (
            certificate["source_files"][relative],
            certificate["tracked_git_blobs"][relative],
        )
    elif defect == "wrong_pin":
        certificate["source_files"][relative] = "0" * 64
    elif defect == "partial_retention":
        target.rename(root / "source-domains/r_support.R")
    elif defect == "raw_rows":
        (root / "source-domains/S001-R.csv").write_text("value\n0\n0\n")
    certificate["files"] = file_inventory(root)
    del certificate["files"]["certificate.json"]
    (root / "certificate.json").write_text(json.dumps(certificate))
    if defect is None:
        validate_bundle(
            root,
            target_sha=SHA,
            expected_lock_sha256=certificate["lock_sha256"],
            current_repository=repository,
        )
        assert not list((root / "source-domains").glob("*.py"))
        assert not list((root / "source-domains").glob("*.R"))
        with pytest.raises(ReferenceRefusal):
            validate_bundle(
                root, target_sha=SHA, expected_lock_sha256=certificate["lock_sha256"]
            )
    else:
        with pytest.raises(ReferenceRefusal):
            validate_bundle(
                root,
                target_sha=SHA,
                expected_lock_sha256=certificate["lock_sha256"],
                current_repository=repository,
            )


@pytest.mark.parametrize(
    "name", ["r_support.R", "source-domains/../r_support.R", "source-domains/sibling.R"]
)
def test_canonical_domain_reader_refuses_every_undeclared_route(
    tmp_path: Path, name: str
) -> None:
    from bijux_pollenomics_dev.ci.lra_reference.profiles import (
        canonical_domain_source_reader,
    )

    with pytest.raises(ReferenceRefusal, match="Unlisted canonical"):
        canonical_domain_source_reader(tmp_path, {})(name)
