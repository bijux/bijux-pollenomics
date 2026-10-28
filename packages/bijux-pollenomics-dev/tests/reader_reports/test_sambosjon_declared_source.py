"""Keep declared code identities within the exact historical docstring boundary."""

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
    read_historical_python_correspondence,
)

ROOT = Path(__file__).resolve().parents[4]
SOURCE = "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/pollen_age_support/sambosjon.py"


@pytest.fixture
def source(tmp_path: Path) -> SimpleNamespace:
    def git(*args: str) -> str:
        return (
            subprocess.check_output(["git", "-C", str(tmp_path), *args])
            .decode()
            .strip()
        )

    git("init", "-q")
    git("config", "user.name", "Bijux source fixture")
    git("config", "user.email", "source-fixture@example.invalid")
    path = tmp_path / SOURCE
    path.parent.mkdir(parents=True)
    old = b'"""Module detail."""\n\ndef main():\n    """Old main description."""\n    return 12\n'
    current = old.replace(b"Old main description", b"Current main description")
    path.write_bytes(old)
    git("add", "--", SOURCE)
    git("commit", "-qm", "test(source): retain synthetic source identity")
    member = GitSourceMember(
        member=SOURCE,
        repository_path=SOURCE,
        source_revision=git("rev-parse", "HEAD"),
        git_blob=git("rev-parse", "HEAD:" + SOURCE),
        sha256=hashlib.sha256(old).hexdigest(),
        bytes=len(old),
    )
    path.write_bytes(current)
    return SimpleNamespace(
        repository=tmp_path, path=path, old=old, current=current, member=member
    )


def helper(sample: SimpleNamespace) -> dict[str, Any]:
    path = ROOT / "docs/report/pollen-reconstruction/verify_report.py"
    tree = ast.parse(path.read_text())
    tree.body = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_sambosjon_declared_source"
    ]
    calls = []

    def historical(
        repository: Path, member: GitSourceMember, *, function_docstring: str
    ) -> bytes:
        assert member.source_revision == "1a3f44530170d81b38317760d86d766ec418a03f"
        assert member.git_blob == "3cff8d67f68b6ea630e167159887e9f3d3fd4e25"
        assert (
            member.sha256
            == "02bfa94a1fe33a526b0089d52c525b1c743b9badf192fcef5027601977a9fdd5"
        )
        assert member.bytes == 17278 and function_docstring == "main"
        calls.append(member)
        return read_historical_python_correspondence(
            repository,
            replace(sample.member, member=member.member),
            function_docstring=function_docstring,
        )

    namespace: dict[str, Any] = {
        "Path": Path,
        "GitSourceMember": GitSourceMember,
        "hashlib": hashlib,
        "read_historical_python_correspondence": historical,
        "calls": calls,
    }
    exec(compile(tree, str(path), "exec"), namespace)
    return namespace


@pytest.mark.parametrize("identity", ["historical", "current"])
def test_declared_identity_always_authenticates_fixed_historical_source(
    source: SimpleNamespace, identity: str
) -> None:
    expected = source.old if identity == "historical" else source.current
    api = helper(source)
    assert (
        api["_sambosjon_declared_source"](
            source.repository, SOURCE, hashlib.sha256(expected).hexdigest()
        )
        == expected
    )
    assert len(api["calls"]) == 1


@pytest.mark.parametrize(
    "damage", ["third_identity", "executable", "import", "other_doc", "path"]
)
def test_matching_current_hash_never_exempts_runtime_or_other_documentation_drift(
    source: SimpleNamespace, damage: str
) -> None:
    raw = source.current
    relative = SOURCE
    if damage == "executable":
        raw = raw.replace(b"return 12", b"return 13")
    elif damage == "import":
        raw += b"\nimport math\n"
    elif damage == "other_doc":
        raw = raw.replace(b"Module detail", b"Changed module detail")
    elif damage == "path":
        relative = "packages/example/other.py"
    source.path.write_bytes(raw)
    expected = (
        "0" * 64 if damage == "third_identity" else hashlib.sha256(raw).hexdigest()
    )
    with pytest.raises((ValueError, ReportRebuildError)):
        helper(source)["_sambosjon_declared_source"](
            source.repository, relative, expected
        )
