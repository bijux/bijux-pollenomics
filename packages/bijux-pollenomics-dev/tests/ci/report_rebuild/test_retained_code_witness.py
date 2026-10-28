"""Historical code transport binds exact capsule names without widening source paths."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.retained_source.descriptor import decode
from bijux_pollenomics_dev.ci.report_rebuild.retained_source.objects import (
    GitSourceMember,
    environment,
    git_executable,
    read_blob,
)

PREFIX = "data/controlled-capture"


@pytest.fixture
def witness(
    tmp_path: Path, request: pytest.FixtureRequest
) -> tuple[Path, GitSourceMember, bytes]:
    executable = git_executable()

    def git(*arguments: str) -> str:
        return subprocess.run(
            [str(executable), "--no-replace-objects", "-C", str(tmp_path), *arguments],
            env=environment(),
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        ).stdout.strip()

    git("init", "--initial-branch=main")
    raw = b"# synthetic historical code witness; never executed\n"
    checksum = hashlib.sha256(raw).hexdigest()
    name = getattr(request, "param", "payloads/" + checksum)
    path = tmp_path / PREFIX / name
    path.parent.mkdir(parents=True)
    path.write_bytes(raw)
    git("add", "--", PREFIX + "/" + name)
    git(
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "commit",
        "-m",
        "retain controlled witness",
    )
    revision = git("rev-parse", "HEAD")
    blob = git("rev-parse", revision + ":" + PREFIX + "/" + name)
    path.unlink()
    return (
        tmp_path,
        GitSourceMember(
            name,
            PREFIX + "/" + name,
            revision,
            blob,
            checksum,
            len(raw),
            storage_role="historical_code_witness",
            capsule_prefix=PREFIX,
        ),
        raw,
    )


def descriptor(member: GitSourceMember) -> dict[str, Any]:
    mapping = json.dumps(
        [[member.repository_path, member.git_blob]], separators=(",", ":")
    ).encode()
    return {
        "schema_version": "git-retained-source.v1",
        "capture": {"name": "capture.json", "sha256": "a" * 64, "bytes": 2},
        "historical_native_epochs": ["b" * 40],
        "source_revision_correspondence": [
            {
                "historical_source_commit": member.source_revision,
                "source_revision": member.source_revision,
            }
        ],
        "git_groups": [
            {
                "historical_source_commit": member.source_revision,
                "source_revision": member.source_revision,
                "member_count": 1,
                "git_entries_sha256": hashlib.sha256(mapping).hexdigest(),
                "paths": [[member.member, member.repository_path]],
                "storage_role": "historical_code_witness",
            }
        ],
        "generated_members": [],
        "rewritten_source_epoch_executed": False,
    }


def test_historical_body_uses_exact_git_identity_without_physical_source(
    witness: tuple[Path, GitSourceMember, bytes],
) -> None:
    root, member, raw = witness
    members = {member.member: {"sha256": member.sha256, "bytes": member.bytes}}
    parsed = decode(
        json.dumps(descriptor(member)).encode(), members, capsule_prefix=PREFIX
    )
    assert parsed.detached == frozenset({member.member})
    resolved = parsed.resolve(root)
    assert resolved == [member]
    assert read_blob(root, resolved[0]) == raw
    assert not (root / member.repository_path).exists()
    assert descriptor(member)["historical_native_epochs"] == ["b" * 40]


def test_canonical_source_admission_remains_separate(
    witness: tuple[Path, GitSourceMember, bytes],
) -> None:
    member = replace(
        witness[1],
        member="source.py",
        repository_path="packages/example/source.py",
        storage_role="canonical_source",
        capsule_prefix=None,
    )
    member.validate()
    with pytest.raises(ReportRebuildError):
        replace(member, capsule_prefix=PREFIX).validate()


def test_git_replacement_cannot_substitute_the_original_witness(
    witness: tuple[Path, GitSourceMember, bytes],
) -> None:
    root, member, raw = witness
    executable = str(git_executable())
    replacement = (
        subprocess.run(
            [executable, "-C", str(root), "hash-object", "-w", "--stdin"],
            input=b"different body",
            env=environment(),
            capture_output=True,
            check=True,
            timeout=10,
        )
        .stdout.decode()
        .strip()
    )
    subprocess.run(
        [executable, "-C", str(root), "replace", member.git_blob, replacement],
        env=environment(),
        capture_output=True,
        check=True,
        timeout=10,
    )
    assert read_blob(root, member) == raw


@pytest.mark.parametrize(
    "change",
    [
        {"capsule_prefix": None},
        {"capsule_prefix": "data/foreign-capture"},
        {"repository_path": "data/other/payloads/" + "a" * 64},
        {"member": "source.py"},
        {"sha256": "a" * 64},
        {"storage_role": "other"},
        {"storage_role": "canonical_source", "capsule_prefix": None},
    ],
)
def test_witness_role_cannot_authorize_foreign_or_unbound_paths(
    witness: tuple[Path, GitSourceMember, bytes],
    change: dict[str, Any],
) -> None:
    with pytest.raises(ReportRebuildError):
        replace(witness[1], **change).validate()


@pytest.mark.parametrize(
    "field,value", [("bytes", 1), ("git_blob", "a" * 40), ("source_revision", "a" * 40)]
)
def test_historical_role_preserves_git_body_and_revision_guards(
    witness: tuple[Path, GitSourceMember, bytes],
    field: str,
    value: Any,
) -> None:
    root, member, _ = witness
    with pytest.raises(ReportRebuildError):
        read_blob(root, replace(member, **{field: value}))


@pytest.mark.parametrize(
    "change",
    [
        "missing_context",
        "foreign_context",
        "prefixes",
        "unknown_role",
        "missing_role",
        "extra_field",
        "changed_map",
    ],
)
def test_descriptor_requires_explicit_authenticated_capsule_scope(
    witness: tuple[Path, GitSourceMember, bytes],
    change: str,
) -> None:
    root, member, _ = witness
    packet = deepcopy(descriptor(member))
    context: str | None = PREFIX
    group = packet["git_groups"][0]
    if change == "missing_context":
        context = None
    elif change == "foreign_context":
        context = "data/foreign-capture"
    elif change == "prefixes":
        group.pop("paths")
        group["prefixes"] = {
            "member_prefix": "payloads/",
            "repository_prefix": PREFIX + "/payloads/",
        }
    elif change == "unknown_role":
        group["storage_role"] = "other"
    elif change == "missing_role":
        group.pop("storage_role")
    elif change == "extra_field":
        group["unreviewed"] = True
    else:
        group["git_entries_sha256"] = "a" * 64
    with pytest.raises(ReportRebuildError):
        parsed = decode(
            json.dumps(packet).encode(),
            {member.member: {"sha256": member.sha256, "bytes": member.bytes}},
            capsule_prefix=context,
        )
        parsed.resolve(root)


def test_original_members_namespace_preserves_exact_context_and_identity(
    witness: tuple[Path, GitSourceMember, bytes],
) -> None:
    member = witness[1]
    name = "members/" + member.sha256
    historical = replace(member, member=name, repository_path=PREFIX + "/" + name)
    historical.validate()
    for altered in (
        replace(historical, repository_path=member.repository_path),
        replace(historical, member="members/" + "0" * 64),
        replace(historical, capsule_prefix="data/foreign-capture"),
    ):
        with pytest.raises(ReportRebuildError, match="exact capsule member path"):
            altered.validate()


@pytest.mark.parametrize("witness", ["capture/oracle/oracle.R"], indirect=True)
def test_named_r_program_preserves_original_bytes_without_execution(
    witness: tuple[Path, GitSourceMember, bytes],
) -> None:
    root, member, original = witness
    parsed = decode(
        json.dumps(descriptor(member)).encode(),
        {member.member: {"sha256": member.sha256, "bytes": member.bytes}},
        capsule_prefix=PREFIX,
    )
    assert read_blob(root, parsed.resolve(root)[0]) == original
    assert not (root / member.repository_path).exists()
    for altered in (
        replace(member, repository_path="data/other/" + member.member),
        replace(member, capsule_prefix="data/other"),
        replace(member, sha256="0" * 64),
        replace(member, bytes=member.bytes + 1),
        replace(member, member="capture/oracle/oracle.txt"),
    ):
        with pytest.raises(ReportRebuildError):
            read_blob(root, altered)
