import csv
import os
from pathlib import Path
import subprocess
from typing import IO, Any

import pytest

from bijux_pollenomics_dev.reader_reports.source import (
    SourceError,
    load_inventory,
    output_directory,
    portable_link,
    repository_root,
)


def _repository(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / ".git").mkdir(parents=True)
    (root / "artifacts").mkdir()
    (root / "reports" / "science").mkdir(parents=True)
    (root / "reports" / "science" / "paper.md").write_text(
        "# Paper\n", encoding="utf-8"
    )
    return repository_root(root)


def _inventory(root: Path, report: str) -> Path:
    path = root / "reports" / "science" / "paper-accounts.csv"
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file, fieldnames=["paper_id", "canonical_report", "citation"]
        )
        writer.writeheader()
        writer.writerow(
            {"paper_id": "paper", "canonical_report": report, "citation": "Paper"}
        )
    return path


def _commit_paths(root: Path, paths: list[str]) -> str:
    """Bind generated reference paths to an ordinary Git commit."""
    subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
    subprocess.run(["git", "add", "--", *paths], cwd=root, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Bijux",
            "-c",
            "user.email=checks@bijux.io",
            "-c",
            "commit.gpgsign=false",
            "-c",
            "core.hooksPath=/dev/null",
            "commit",
            "--quiet",
            "-m",
            "test(science): bind generated citation paths",
        ],
        cwd=root,
        check=True,
    )
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()


def test_inventory_pins_only_canonical_reports(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    inventory = _inventory(root, "reports/science/paper.md")
    _, digest, papers = load_inventory(root, inventory)
    assert len(digest) == 64
    assert papers[0].relative_path.as_posix() == "reports/science/paper.md"
    assert len(papers[0].source_sha256) == 64
    _inventory(root, "reports/science/../../../outside.md")
    with pytest.raises(SourceError):
        load_inventory(root, inventory)


def test_output_and_local_links_stay_within_repository(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    report = root / "reports" / "science" / "paper.md"
    revision = _commit_paths(root, ["reports/science/paper.md"])
    assert (
        output_directory(root, "artifacts/jobs/export")
        == root / "artifacts" / "jobs" / "export"
    )
    for candidate in (
        "reports/export",
        "artifacts/jobs/../../reports/export",
        "artifacts",
    ):
        with pytest.raises(SourceError):
            output_directory(root, candidate)
    assert portable_link(root, report, "#question", revision).endswith(
        "paper.md#question"
    )
    assert portable_link(root, report, "paper.md", revision).startswith(
        "https://github.com/"
    )
    for destination in (
        "file:///etc/passwd",
        "../../../outside.md",
        "paper.md?download=1",
    ):
        with pytest.raises(SourceError):
            portable_link(root, report, destination, revision)


@pytest.mark.parametrize("mode", [0o644, 0o755])
def test_committed_citations_need_no_physical_payload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: int
) -> None:
    """A committed reference is URL metadata, not a source-body intake."""
    root = _repository(tmp_path)
    target = root / "data/reference.body"
    target.parent.mkdir()
    target.write_bytes(b"generated reference, not a scientific input")
    target.chmod(mode)
    revision = _commit_paths(root, ["reports/science/paper.md", "data/reference.body"])
    target.unlink()
    target.parent.rmdir()
    opened: list[str] = []
    original_path_open = Path.open
    original_os_open = os.open

    def path_open(
        path: Path,
        mode: str = "r",
        buffering: int = -1,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> IO[Any]:
        if path == target:
            opened.append("Path.open")
            raise AssertionError("Citation opened a payload")
        return original_path_open(path, mode, buffering, encoding, errors, newline)

    def descriptor_open(
        path: str | bytes | os.PathLike[str] | os.PathLike[bytes],
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ) -> int:
        if os.fsdecode(path).endswith("reference.body"):
            opened.append("os.open")
            raise AssertionError("Citation opened a payload descriptor")
        return original_os_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(Path, "open", path_open)
    monkeypatch.setattr(os, "open", descriptor_open)
    source = root / "reports/science/paper.md"
    assert portable_link(root, source, "../../data/reference.body", revision) == (
        "https://github.com/bijux/bijux-pollenomics/blob/"
        + revision
        + "/data/reference.body"
    )
    assert portable_link(root, source, "../../data", revision) == (
        "https://github.com/bijux/bijux-pollenomics/tree/" + revision + "/data"
    )
    assert opened == []


@pytest.mark.parametrize("revision", ["main", "a" * 40, "../HEAD", "0" * 39])
def test_citation_requires_an_exact_existing_commit(
    tmp_path: Path, revision: str
) -> None:
    """A present physical target cannot authenticate a different revision."""
    root = _repository(tmp_path)
    _commit_paths(root, ["reports/science/paper.md"])
    with pytest.raises(SourceError):
        portable_link(root, root / "reports/science/paper.md", "paper.md", revision)


def test_untracked_citation_is_not_published_at_a_commit(tmp_path: Path) -> None:
    """An untracked file cannot supply a commit-pinned reference."""
    root = _repository(tmp_path)
    revision = _commit_paths(root, ["reports/science/paper.md"])
    (root / "reports/science/uncaptured.md").write_text("Untracked\n")
    with pytest.raises(SourceError):
        portable_link(
            root, root / "reports/science/paper.md", "uncaptured.md", revision
        )


@pytest.mark.parametrize("kind", ["working_alias", "git_alias", "submodule"])
def test_citation_refuses_aliases_and_submodules(tmp_path: Path, kind: str) -> None:
    """Only ordinary committed file/tree paths can supply a citation URL."""
    root = _repository(tmp_path)
    target = root / "data/reference.body"
    target.parent.mkdir()
    target.write_bytes(b"generated reference")
    revision = _commit_paths(root, ["reports/science/paper.md", "data/reference.body"])
    if kind == "working_alias":
        target.unlink()
        target.symlink_to(root / "foreign.body")
        destination = "../../data/reference.body"
    elif kind == "git_alias":
        alias = root / "data/alias.body"
        alias.symlink_to("reference.body")
        revision = _commit_paths(root, ["data/alias.body"])
        alias.unlink()
        destination = "../../data/alias.body"
    else:
        subprocess.run(
            [
                "git",
                "update-index",
                "--add",
                "--cacheinfo",
                f"160000,{revision},data/module",
            ],
            cwd=root,
            check=True,
        )
        revision = _commit_paths(root, ["reports/science/paper.md"])
        (root / "data/module").mkdir()
        destination = "../../data/module"
    with pytest.raises(SourceError):
        portable_link(root, root / "reports/science/paper.md", destination, revision)


def test_sparse_git_alias_cannot_be_hidden_by_parent_navigation(
    tmp_path: Path,
) -> None:
    """Parent navigation cannot erase an aliased intermediate Git component."""
    root = _repository(tmp_path)
    target = root / "data/reference.body"
    target.parent.mkdir()
    target.write_bytes(b"generated reference")
    alias = root / "data/alias"
    alias.symlink_to(".")
    revision = _commit_paths(
        root, ["reports/science/paper.md", "data/reference.body", "data/alias"]
    )
    alias.unlink()
    with pytest.raises(SourceError):
        portable_link(
            root,
            root / "reports/science/paper.md",
            "../../data/alias/../reference.body",
            revision,
        )


def test_report_symlink_is_refused(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    target = root / "reports" / "science" / "paper.md"
    target.unlink()
    target.symlink_to(root / "artifacts")
    inventory = _inventory(root, "reports/science/paper.md")
    with pytest.raises(SourceError):
        load_inventory(root, inventory)
