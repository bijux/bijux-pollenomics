"""Preserve historical bytes and refuse executable or undeclared document drift."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import os
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.retained_source.objects import (
    GitSourceMember,
    read_historical_python_correspondence,
)

SOURCE = (
    b'"""Module source documentation."""\n'
    b"def main():\n"
    b'    """Command source documentation."""\n'
    b"    return 1\n"
    b"def score():\n"
    b'    """Scientific source documentation."""\n'
    b'    return "retained"\n'
)


def git(repository: Path, *arguments: str) -> str:
    return (
        subprocess.check_output(
            ["git", "-C", str(repository), *arguments], stderr=subprocess.PIPE
        )
        .decode()
        .strip()
    )


@pytest.fixture
def source(tmp_path: Path) -> SimpleNamespace:
    relative = "packages/source_identity/worker.py"
    path = tmp_path / relative
    path.parent.mkdir(parents=True)
    path.write_bytes(SOURCE)
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.name", "Bijux source fixtures")
    git(tmp_path, "config", "user.email", "source-fixtures@example.invalid")
    git(tmp_path, "add", "--", relative)
    git(
        tmp_path, "commit", "-q", "-m", "test(source): retain controlled python witness"
    )
    member = GitSourceMember(
        member=relative,
        repository_path=relative,
        source_revision=git(tmp_path, "rev-parse", "HEAD"),
        git_blob=git(tmp_path, "rev-parse", "HEAD:" + relative),
        sha256=hashlib.sha256(SOURCE).hexdigest(),
        bytes=len(SOURCE),
    )
    return SimpleNamespace(repository=tmp_path, path=path, member=member)


@pytest.mark.parametrize("comments", [False, True])
def test_exact_source_or_comment_edits_keep_original_returned_bytes(
    source: SimpleNamespace, comments: bool
) -> None:
    if comments:
        source.path.write_bytes(b"# Editorial comment only.\n" + SOURCE)
    result = read_historical_python_correspondence(source.repository, source.member)
    assert result == SOURCE
    assert hashlib.sha256(result).hexdigest() == source.member.sha256
    assert (
        source.path.read_bytes() != result
        if comments
        else source.path.read_bytes() == result
    )


def test_only_explicit_main_docstring_edit_can_correspond(
    source: SimpleNamespace,
) -> None:
    source.path.write_bytes(
        SOURCE.replace(
            b"Command source documentation.", b"Current command explanation."
        )
    )
    with pytest.raises(ReportRebuildError, match="executable source differs"):
        read_historical_python_correspondence(source.repository, source.member)
    assert (
        read_historical_python_correspondence(
            source.repository, source.member, function_docstring="main"
        )
        == SOURCE
    )


@pytest.mark.parametrize(
    "old,new",
    [
        (b"Module source documentation.", b"Other module documentation."),
        (b"Scientific source documentation.", b"Other scientific documentation."),
        (b"return 1", b"return 2"),
        (b'"retained"', b'"different"'),
        (b"def main():", b"import math\ndef main():"),
        (b"def score():", b"def score(other=1):"),
        (b"return 1", b"raise ValueError('changed')"),
    ],
)
def test_all_other_syntax_changes_refuse(
    source: SimpleNamespace, old: bytes, new: bytes
) -> None:
    source.path.write_bytes(SOURCE.replace(old, new))
    with pytest.raises(ReportRebuildError, match="executable source differs"):
        read_historical_python_correspondence(
            source.repository, source.member, function_docstring="main"
        )


@pytest.mark.parametrize(
    "defect", ["witness", "path", "logical_path", "hash", "blob", "size", "ancestry"]
)
def test_exact_historical_identity_is_required(
    source: SimpleNamespace, defect: str
) -> None:
    variants: dict[str, dict[str, str | int]] = {
        "witness": {"source_revision": "0" * 40},
        "path": {"repository_path": "packages/source_identity/missing.py"},
        "logical_path": {"member": "packages/source_identity/other.py"},
        "hash": {"sha256": "0" * 64},
        "blob": {"git_blob": "0" * 40},
        "size": {"bytes": len(SOURCE) + 1},
    }
    changes = variants.get(defect, {})
    if defect == "ancestry":
        changes = {
            "source_revision": git(
                source.repository,
                "commit-tree",
                git(source.repository, "rev-parse", "HEAD^{tree}"),
                "-m",
                "test(source): retain unrelated controlled witness",
            )
        }
    member = replace(source.member, **changes)
    with pytest.raises(ReportRebuildError):
        read_historical_python_correspondence(source.repository, member)


@pytest.mark.parametrize(
    "defect",
    [
        "missing",
        "symlink",
        "hardlink",
        "oversized",
        "syntax",
        "missing_doc",
        "other_function",
    ],
)
def test_current_source_must_remain_physical_bounded_and_well_formed(
    source: SimpleNamespace, defect: str
) -> None:
    document = "main"
    if defect == "missing":
        source.path.unlink()
    elif defect == "symlink":
        target = source.repository / "source.txt"
        target.write_bytes(SOURCE)
        source.path.unlink()
        source.path.symlink_to(target)
    elif defect == "hardlink":
        os.link(source.path, source.repository / "source.txt")
    elif defect == "oversized":
        source.path.write_bytes(b"#" * (128 * 1024 + 1))
    elif defect == "syntax":
        source.path.write_bytes(b"def invalid(\n")
    elif defect == "missing_doc":
        source.path.write_bytes(
            SOURCE.replace(b'    """Command source documentation."""\n', b"")
        )
    else:
        document = "score"
    with pytest.raises(ReportRebuildError):
        read_historical_python_correspondence(
            source.repository, source.member, function_docstring=document
        )
