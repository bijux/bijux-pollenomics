"""Verify repository sustainability counts use governed Git identities."""

from __future__ import annotations

from pathlib import Path
import subprocess

import pytest

from bijux_pollenomics.governance.repository_truth.release import sustainability


@pytest.mark.parametrize("data_directory_present", [True, False])
def test_tracked_data_count_excludes_ignored_files_and_tracked_symlinks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    data_directory_present: bool,
) -> None:
    repository_root = tmp_path / "repository"
    data_root = repository_root / "data"
    docs_root = repository_root / "docs"
    report_root = docs_root / "report"
    report_root.mkdir(parents=True)
    if data_directory_present:
        data_root.mkdir()
        (data_root / "tracked.json").write_text("{}\n", encoding="utf-8")
        (data_root / ".DS_Store").write_bytes(b"ignored platform metadata")
        (data_root / "tracked-link").symlink_to("tracked.json")

    index_rows = (
        b"100644 0000000000000000000000000000000000000000 0\tdata/tracked.json\0"
        b"120000 1111111111111111111111111111111111111111 0\tdata/tracked-link\0"
    )

    def fake_run(
        command: tuple[str, ...],
        *,
        check: bool,
        stdin: int,
        capture_output: bool,
        shell: bool,
    ) -> subprocess.CompletedProcess[bytes]:
        assert command == (
            "git",
            "-C",
            str(repository_root),
            "ls-files",
            "--stage",
            "-z",
            "--full-name",
            "--",
            ":(literal)data",
        )
        assert check is True
        assert stdin is subprocess.DEVNULL
        assert capture_output is True
        assert shell is False
        return subprocess.CompletedProcess(command, 0, stdout=index_rows, stderr=b"")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(
        sustainability,
        "build_repository_governance_artifact_review",
        lambda **_kwargs: {"summary": {"retire": 0}},
    )

    payload = sustainability.build_repository_output_sustainability_review(
        data_root=data_root,
        docs_root=docs_root,
        report_root=report_root,
    )

    assert payload["balance_counts"] == {
        "runtime_python_file_count": 0,
        "tracked_data_file_count": 1,
        "report_file_count": 0,
        "maintainer_root_review_file_count": 0,
    }


def test_uninspectable_index_is_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def unavailable_index(*_args: object, **_kwargs: object) -> None:
        raise OSError("Git is unavailable")

    monkeypatch.setattr(subprocess, "run", unavailable_index)
    assert (
        sustainability._count_git_tracked_regular_files(
            tmp_path / "data", repository_root=tmp_path
        )
        is None
    )


def test_external_data_root_has_no_claimed_repository_count(tmp_path: Path) -> None:
    assert (
        sustainability._count_git_tracked_regular_files(
            tmp_path / "external-data", repository_root=tmp_path / "publication"
        )
        is None
    )
