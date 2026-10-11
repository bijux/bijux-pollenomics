"""Check the descriptive published-window uncertainty comparison."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.essd_reproduction.published_window_correspondence import (
    ARCHIVE_SHA256,
    SOURCE_REVISION,
)
from bijux_pollenomics_dev.essd_reproduction.published_window_uncertainty import (
    compare_envelopes,
)


def _inputs(tmp_path: Path) -> tuple[Path, Path, list[dict[str, str]]]:
    report = tmp_path / "provenance.json"
    report.write_text(
        json.dumps(
            {
                "schema_version": "landclimii-published-window-provenance.v2",
                "source_revision": SOURCE_REVISION,
                "published_archive_sha256": ARCHIVE_SHA256,
                "author_bin_bounds_bp": [100, 350],
                "paired_mean_se_values": 124,
                "historical_raw_input_closure": "not_established",
            }
        )
    )
    path = tmp_path / "correspondence.csv"
    rows = []
    for grid in ("512", "562"):
        for index in range(31):
            for metric in ("mean", "standard_error"):
                rows.append(
                    {
                        "grid_id": grid,
                        "taxon": f"taxon-{index:02}",
                        "window": "100-350 BP",
                        "metric": metric,
                        "unit": "percentage_cover",
                        "archive": "10" if metric == "mean" else "1",
                        "author_r": ("13" if index == 0 else "11")
                        if metric == "mean"
                        else "1",
                    }
                )
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path, report, rows


def test_envelopes_keep_exact_taxon_support_and_report_separation(
    tmp_path: Path,
) -> None:
    path, report, _ = _inputs(tmp_path)
    rows, result = compare_envelopes(path, report)
    assert len(rows) == 62
    assert rows[0]["one_se_envelopes_disjoint"] == "True"
    assert rows[0]["one_se_envelope_separation_percentage_points"] == "1"
    assert rows[1]["one_se_envelopes_disjoint"] == "False"
    assert result["summaries"] == [
        {
            "grid_id": grid,
            "taxa": 31,
            "disjoint_one_se_envelopes": 1,
            "overlapping_one_se_envelopes": 30,
            "largest_separation_taxon": "taxon-00",
            "largest_separation_percentage_points": "1",
        }
        for grid in ("512", "562")
    ]


def test_envelopes_refuse_wrong_axis_and_negative_se(tmp_path: Path) -> None:
    path, report, rows = _inputs(tmp_path)
    rows[1]["author_r"] = "-1"
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(ValueError, match="negative reported standard error"):
        compare_envelopes(path, report)
    source = json.loads(report.read_text())
    source["author_bin_bounds_bp"] = [100, 300]
    report.write_text(json.dumps(source))
    with pytest.raises(ValueError, match="outside the exact published window"):
        compare_envelopes(path, report)


def test_overlapping_envelopes_have_no_separation_taxon(tmp_path: Path) -> None:
    path, report, rows = _inputs(tmp_path)
    for row in rows:
        if row["metric"] == "mean":
            row["author_r"] = "11"
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    _, result = compare_envelopes(path, report)
    summaries = result["summaries"]
    assert isinstance(summaries, list)
    for summary in summaries:
        assert isinstance(summary, dict)
        assert summary["disjoint_one_se_envelopes"] == 0
        assert summary["largest_separation_taxon"] == "none"
        assert summary["largest_separation_percentage_points"] == "0"
