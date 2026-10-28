"""Historical reader custody cannot authorize numerical or escaping source roles."""

import ast
from dataclasses import replace
import hashlib
from pathlib import Path
import subprocess
from types import SimpleNamespace
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.retained_source.objects import (
    GitSourceMember,
    read_blob,
)

ROOT = Path(__file__).resolve().parents[4]
READER = "packages/example/scientific_accounts.py"


def api(member: GitSourceMember) -> dict[str, Any]:
    path = ROOT / "docs/report/pollen-reconstruction/verify_report.py"
    tree = ast.parse(path.read_text())
    tree.body = [
        n
        for n in tree.body
        if isinstance(n, ast.FunctionDef)
        and n.name == "_buffered_historical_reader_source"
    ]
    namespace: dict[str, Any] = {
        "Path": Path,
        "read_blob": read_blob,
        "BUFFERED_READER_WITNESSES": {READER: member},
    }
    exec(compile(tree, str(path), "exec"), namespace)
    return namespace


@pytest.fixture
def witness(tmp_path: Path) -> SimpleNamespace:
    def git(*args: str) -> str:
        return (
            subprocess.check_output(["git", "-C", str(tmp_path), *args])
            .decode()
            .strip()
        )

    git("init", "-q")
    git("config", "user.name", "Bijux source fixture")
    git("config", "user.email", "source-fixture@example.invalid")
    path = tmp_path / READER
    path.parent.mkdir(parents=True)
    raw = b"def render():\n    return 12\n"
    path.write_bytes(raw)
    git("add", "--", READER)
    git("commit", "-qm", "test(source): retain synthetic reader")
    member = GitSourceMember(
        member=READER,
        repository_path=READER,
        source_revision=git("rev-parse", "HEAD"),
        git_blob=git("rev-parse", "HEAD:" + READER),
        sha256=hashlib.sha256(raw).hexdigest(),
        bytes=len(raw),
    )
    return SimpleNamespace(repository=tmp_path, member=member, raw=raw)


def test_historical_reader_has_exact_bytes_without_a_current_execution_claim(
    witness: SimpleNamespace,
) -> None:
    method = api(witness.member)["_buffered_historical_reader_source"]
    assert method(witness.repository, READER, witness.member.sha256) == witness.raw
    (witness.repository / READER).write_text(
        "# Current reader implementation differs.\n"
    )
    assert method(witness.repository, READER, witness.member.sha256) == witness.raw


@pytest.mark.parametrize(
    "damage",
    ["role", "escape", "expected_hash", "path", "blob", "sha", "size", "ancestor"],
)
def test_historical_reader_refuses_wrong_roles_and_source_custody(
    witness: SimpleNamespace, damage: str
) -> None:
    member = witness.member
    relative, expected = READER, member.sha256
    if damage == "role":
        relative = "packages/example/prediction.py"
    elif damage == "escape":
        relative = "../scientific_accounts.py"
    elif damage == "expected_hash":
        expected = "0" * 64
    elif damage == "path":
        member = replace(member, repository_path="packages/example/other.py")
    elif damage == "blob":
        member = replace(member, git_blob="0" * 40)
    elif damage == "sha":
        member = replace(member, sha256="0" * 64)
        expected = member.sha256
    elif damage == "size":
        member = replace(member, bytes=member.bytes + 1)
    elif damage == "ancestor":
        member = replace(member, source_revision="0" * 40)
    with pytest.raises((ReportRebuildError, ValueError)):
        api(member)["_buffered_historical_reader_source"](
            witness.repository, relative, expected
        )
