"""Keep radius retained-input witnesses separate from current scientific publication."""

from __future__ import annotations

import ast
from dataclasses import replace
import hashlib
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.retained_source.objects import (
    PUBLICATION_INPUT_SOURCES,
    GitSourceMember,
)

ROOT = Path(__file__).resolve().parents[4]
PREFIX = "docs/report/pollen-reconstruction/author-lra-constrained/direct-pollen/"
WITNESSES = {
    "direct_mae": (
        PREFIX + "matched-scores.csv",
        "a1299c24ad4ac875b0cf9d0ec10251719a63ed46",
        "623b0eb20e46e86fccbd48e840fa20e1882b89bf17ef3ef81c89e63c3a2c6f50",
        12440,
    ),
    "direct_hellinger": (
        PREFIX + "paired-hellinger.json",
        "0f552f401fc02e27e8745abdfce44e9c4a181b2c",
        "91255eda5f958f7072ea489dfc36201360b7aaa5f019e5f0c91f3e2a59830950",
        26709,
    ),
}


def helper(repository: Path, callback: Any) -> Any:
    """Exercise the actual reader helper without importing unrelated producers."""
    path = ROOT / "docs/report/pollen-reconstruction/verify_report.py"
    tree = ast.parse(path.read_text())
    tree.body = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_radius_paired_retained_sha256"
    ]
    assert len(tree.body) == 1
    namespace: dict[str, Any] = {
        "Path": Path,
        "REPOSITORY_ROOT": repository,
        "GitSourceMember": GitSourceMember,
        "hashlib": hashlib,
        "read_blob": callback,
    }
    exec(compile(tree, str(path), "exec"), namespace)
    return namespace["_radius_paired_retained_sha256"]


@pytest.mark.parametrize("name", list(WITNESSES))
def test_exact_witness_is_used_even_with_different_current_publication(
    tmp_path: Path, name: str
) -> None:
    relative, blob, checksum, size = WITNESSES[name]
    current = tmp_path / relative
    current.parent.mkdir(parents=True)
    current.write_bytes(b"different current synthetic publication")
    calls = []
    body = b"explicit synthetic historical bytes"

    def read(repository: Path, member: GitSourceMember) -> bytes:
        assert repository == tmp_path
        assert member.member == member.repository_path == relative
        assert member.source_revision == "a734ef042e20ae18042583caa2bd9894cb018b1e"
        assert (member.git_blob, member.sha256, member.bytes) == (blob, checksum, size)
        assert (
            member.storage_role == "canonical_source" and member.capsule_prefix is None
        )
        calls.append(member)
        return body

    assert helper(tmp_path, read)(name, current) == hashlib.sha256(body).hexdigest()
    assert len(calls) == 1 and current.read_bytes() != body


@pytest.mark.parametrize("name", list(WITNESSES))
def test_changed_callback_bytes_change_the_join_hash(tmp_path: Path, name: str) -> None:
    relative = WITNESSES[name][0]
    body = [b"synthetic numeric value 0.1"]

    def read(repository: Path, member: GitSourceMember) -> bytes:
        assert repository == tmp_path and member.repository_path == relative
        return body[0]

    read_hash = helper(tmp_path, read)
    before = read_hash(name, tmp_path / relative)
    body[0] = b"synthetic numeric value 0.2"
    assert read_hash(name, tmp_path / relative) != before


@pytest.mark.parametrize("name", list(WITNESSES))
def test_authentication_failure_never_falls_back_to_current_file(
    tmp_path: Path, name: str
) -> None:
    relative = WITNESSES[name][0]
    current = tmp_path / relative
    current.parent.mkdir(parents=True)
    current.write_bytes(b"current file cannot rescue a refused Git witness")

    def refuse(repository: Path, member: GitSourceMember) -> bytes:
        raise ReportRebuildError("synthetic Git witness refused")

    with pytest.raises(ReportRebuildError, match="synthetic Git witness refused"):
        helper(tmp_path, refuse)(name, current)


@pytest.mark.parametrize("name", ["radius_report", "radius_scores", "unknown"])
def test_private_helper_rejects_other_source_roles(tmp_path: Path, name: str) -> None:
    def refuse_call(repository: Path, member: GitSourceMember) -> bytes:
        pytest.fail("Unknown roles must fail before Git authentication")

    with pytest.raises(ValueError, match="Unknown retained radius"):
        helper(tmp_path, refuse_call)(name, tmp_path / "source.json")


@pytest.mark.parametrize("name", list(WITNESSES))
def test_private_helper_rejects_swapped_or_moved_path(
    tmp_path: Path, name: str
) -> None:
    def refuse_call(repository: Path, member: GitSourceMember) -> bytes:
        pytest.fail("Wrong paths must fail before Git authentication")

    with pytest.raises(ValueError, match="input path differs"):
        helper(tmp_path, refuse_call)(
            name, tmp_path / "elsewhere" / Path(WITNESSES[name][0]).name
        )


def test_publication_namespace_contains_only_two_declared_inputs() -> None:
    assert (
        frozenset(value[0] for value in WITNESSES.values()) == PUBLICATION_INPUT_SOURCES
    )
    member = GitSourceMember(
        member=WITNESSES["direct_mae"][0],
        repository_path=WITNESSES["direct_mae"][0],
        source_revision="1" * 40,
        git_blob="2" * 40,
        sha256=hashlib.sha256(b"synthetic").hexdigest(),
        bytes=9,
    )
    member.validate()
    replace(
        member,
        member=WITNESSES["direct_hellinger"][0],
        repository_path=WITNESSES["direct_hellinger"][0],
    ).validate()
    for relative in [PREFIX + "other.json", "docs/report/unrelated/matched-scores.csv"]:
        with pytest.raises(ReportRebuildError, match="Git storage must be canonical"):
            replace(member, member=relative, repository_path=relative).validate()
