"""Source and publication boundaries for ABBO conditional membership."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path
import runpy
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError

PACKAGE = Path(__file__).resolve().parents[3]
REPOSITORY = Path(__file__).resolve().parents[5]
SOURCE = (
    PACKAGE
    / "src/bijux_pollenomics_dev/source_completion/pollen_age_support/abborrtjarne_membership.py"
)
PRODUCER = runpy.run_path(str(SOURCE))


def repository() -> Path:
    return next(
        ancestor
        for ancestor in Path(__file__).resolve().parents
        if (ancestor / "pyproject.toml").is_file()
        and (
            ancestor / "docs/report/pollen-reconstruction/age-interval-sensitivity"
        ).is_dir()
    )


def _rewritten_support(field: str, value: str) -> bytes:
    rows = list(
        csv.DictReader(
            io.StringIO(
                (
                    repository()
                    / "docs/report/pollen-reconstruction/age-interval-sensitivity/age-bin-support.csv"
                ).read_text(encoding="utf-8")
            )
        )
    )
    if field == "closed_nisp_count":
        row = next(row for row in rows if row["contained_common_bin"] == "3")
    else:
        row = rows[0]
    row[field] = value
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def test_actual_source_reproduces_all_memberships_and_exact_bounds() -> None:
    membership, report = PRODUCER["build"](repository())
    governed = (
        REPOSITORY
        / "docs/report/pollen-reconstruction/age-interval-sensitivity/conditional-membership"
    )
    assert membership == (governed / "membership.csv").read_bytes()
    assert report == json.loads((governed / "report.json").read_bytes())
    assert report["membership_status_counts"] == {
        "mandatory": 8,
        "optional": 49,
        "outside": 371,
    }
    assert [
        (
            row["bin_id"],
            row["closed16_fraction_lower_outer_bound"],
            row["closed16_fraction_upper_outer_bound"],
        )
        for row in report["bounds"]
    ] == [
        (
            3,
            {"numerator": 483, "denominator": 2203},
            {"numerator": 14, "denominator": 41},
        ),
        (
            4,
            {"numerator": 2283, "denominator": 6823},
            {"numerator": 3847, "denominator": 8958},
        ),
        (
            5,
            {"numerator": 1895, "denominator": 4979},
            {"numerator": 5103, "denominator": 11483},
        ),
        (
            9,
            {"numerator": 167, "denominator": 409},
            {"numerator": 3963, "denominator": 7111},
        ),
    ]


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("possible_common_bins", "3", "source admission differs"),
        ("all_nisp_count", "-1", "nonnegative integer"),
        ("closed_nisp_count", "1", "reviewed fraction bounds differ"),
    ],
)
def test_changed_source_ledger_refuses(field: str, value: str, reason: str) -> None:
    config: dict[str, Any] = json.loads(
        (
            repository()
            / "docs/report/pollen-reconstruction/age-interval-sensitivity/config.json"
        ).read_bytes()
    )
    with pytest.raises(ValueError, match=reason):
        PRODUCER["derive"](_rewritten_support(field, value), config)


def test_output_refuses_parent_traversal_without_writing() -> None:
    root = repository()
    escaped = root / "artifacts/../docs/report/pollen-reconstruction/escaped"
    with pytest.raises(ReportRebuildError):
        PRODUCER["run"](root, escaped)
    assert not (root / "docs/report/pollen-reconstruction/escaped").exists()


def test_imported_helper_must_have_reviewed_bytes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    replacement = tmp_path / "interval_fraction.py"
    replacement.write_text("# changed helper\n", encoding="utf-8")
    monkeypatch.setattr(PRODUCER["interval_fraction"], "__file__", str(replacement))
    with pytest.raises(ValueError, match="Imported ABBO interval helper bytes differ"):
        PRODUCER["_checked_inputs"](repository())


def test_source_change_before_publication_removes_staging(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    original = PRODUCER["_checked_inputs"]
    calls = 0

    def checked(root: Path) -> Any:
        nonlocal calls
        calls += 1
        if calls == 3:
            raise ValueError("ABBO source byte identity differs")
        return original(root)

    monkeypatch.setitem(PRODUCER["run"].__globals__, "_checked_inputs", checked)
    destination = tmp_path / "products"
    with pytest.raises(ValueError, match="source byte identity differs"):
        PRODUCER["run"](repository(), destination)
    assert calls == 3
    assert list(tmp_path.iterdir()) == []


def test_existing_output_is_preserved(tmp_path: Path) -> None:
    destination = tmp_path / "products"
    destination.mkdir()
    marker = destination / "source.txt"
    marker.write_bytes(b"existing source")
    with pytest.raises(ReportRebuildError):
        PRODUCER["run"](repository(), destination)
    assert marker.read_bytes() == b"existing source"
    assert list(tmp_path.iterdir()) == [destination]
