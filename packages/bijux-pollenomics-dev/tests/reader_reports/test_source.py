import csv
from pathlib import Path

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
    assert portable_link(root, report, "#question", "a" * 40).endswith(
        "paper.md#question"
    )
    assert portable_link(root, report, "paper.md", "a" * 40).startswith(
        "https://github.com/"
    )
    for destination in (
        "file:///etc/passwd",
        "../../../outside.md",
        "paper.md?download=1",
    ):
        with pytest.raises(SourceError):
            portable_link(root, report, destination, "a" * 40)


def test_report_symlink_is_refused(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    target = root / "reports" / "science" / "paper.md"
    target.unlink()
    target.symlink_to(root / "artifacts")
    inventory = _inventory(root, "reports/science/paper.md")
    with pytest.raises(SourceError):
        load_inventory(root, inventory)
