"""Check the descriptive published-window uncertainty comparison."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from bijux_pollenomics_dev.essd_reproduction.published_window_correspondence import (
    ARCHIVE_SHA256,
    SOURCE_REVISION,
)
from bijux_pollenomics_dev.essd_reproduction.published_window_uncertainty import (
    compare_envelopes,
)


def _write_manifest(path: Path, report: Path) -> None:
    outputs = {}
    for product in (path, report):
        content = product.read_bytes()
        outputs[product.name] = {
            "bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
        }
    outputs["REPORT.md"] = {"bytes": 0, "sha256": "0" * 64}
    (report.parent / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "landclim-published-window-provenance-custody.v1",
                "outputs": outputs,
            }
        )
    )


def _inputs(tmp_path: Path) -> tuple[Path, Path, list[dict[str, str]]]:
    report = tmp_path / "report.json"
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
    path = tmp_path / "paper-correspondence.csv"
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
    _write_manifest(path, report)
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
    _write_manifest(path, report)
    with pytest.raises(ValueError, match="negative reported standard error"):
        compare_envelopes(path, report)
    source = json.loads(report.read_text())
    source["author_bin_bounds_bp"] = [100, 300]
    report.write_text(json.dumps(source))
    _write_manifest(path, report)
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
    _write_manifest(path, report)
    _, result = compare_envelopes(path, report)
    summaries = result["summaries"]
    assert isinstance(summaries, list)
    for summary in summaries:
        assert isinstance(summary, dict)
        assert summary["disjoint_one_se_envelopes"] == 0
        assert summary["largest_separation_taxon"] == "none"
        assert summary["largest_separation_percentage_points"] == "0"


def test_envelopes_refuse_forged_correspondence_and_report(tmp_path: Path) -> None:
    path, report, rows = _inputs(tmp_path)
    rows[0]["archive"] = "12"
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(ValueError, match="paper-correspondence.csv"):
        compare_envelopes(path, report)
    _write_manifest(path, report)
    source = json.loads(report.read_text())
    source["paired_mean_se_values"] = 123
    report.write_text(json.dumps(source))
    with pytest.raises(ValueError, match="report.json"):
        compare_envelopes(path, report)


def test_envelopes_refuse_missing_or_wrong_manifest(tmp_path: Path) -> None:
    path, report, _ = _inputs(tmp_path)
    manifest = report.parent / "manifest.json"
    manifest.unlink()
    with pytest.raises(ValueError, match="regular files"):
        compare_envelopes(path, report)
    _write_manifest(path, report)
    source = json.loads(manifest.read_text())
    source["outputs"].pop("paper-correspondence.csv")
    manifest.write_text(json.dumps(source))
    with pytest.raises(ValueError, match="population does not close"):
        compare_envelopes(path, report)


@pytest.mark.parametrize("manifest", [None, [], "provenance"])
def test_envelopes_refuse_nonobject_manifest(tmp_path: Path, manifest: object) -> None:
    path, report, _ = _inputs(tmp_path)
    (report.parent / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="Unsupported provenance custody manifest"):
        compare_envelopes(path, report)


def test_published_window_identity_has_one_unchanged_public_contract() -> None:
    from bijux_pollenomics_dev.essd_reproduction import (
        published_window_contract as contract,
    )
    from bijux_pollenomics_dev.essd_reproduction import (
        published_window_correspondence as correspondence,
    )
    from bijux_pollenomics_dev.essd_reproduction import (
        published_window_uncertainty as uncertainty,
    )

    expected = {
        "ARCHIVE_SHA256": "c585f0691ad95342b8aba083b90fe91dc398f985b6b7fbc19561299389c4fb86",
        "RECEIPT_SHA256": "eb4350724c176d0dbcb7e441f2d21489bdae1cfff7ebe3088eab27093f315677",
        "SOURCE_REVISION": "57ead2e2fcc493d099be4e5a3092fc396e1c3d3a",
        "WINDOW": "100-350 BP",
        "BIN_ID": "225",
        "GRIDS": ("512", "562"),
        "MEAN_MEMBER": "LANDCLIMII.RV.means.JUN2021/TW2.RV.estimates.jun21.csv",
        "SE_MEMBER": "LANDCLIMII.RV.standarderrors.JUN2021/TW2.RV.standarderrors.jun21.csv",
    }
    for name, value in expected.items():
        assert getattr(contract, name) == value
        assert getattr(correspondence, name) == value
    for name in ("ARCHIVE_SHA256", "SOURCE_REVISION", "GRIDS"):
        assert getattr(uncertainty, name) == expected[name]


def test_envelope_cold_import_does_not_load_host_catalog(tmp_path: Path) -> None:
    from bijux_pollenomics_dev.essd_reproduction import (
        published_window_uncertainty as uncertainty,
    )

    developer_source = Path(uncertainty.__file__).resolve().parents[2]
    command = [
        sys.executable,
        "-I",
        "-B",
        "-c",
        "import importlib,sys;sys.path.insert(0,sys.argv[1]);"
        "importlib.import_module('bijux_pollenomics_dev.source_completion.essd.published_window_uncertainty');"
        "importlib.import_module('bijux_pollenomics_dev.essd_reproduction.published_window_uncertainty');"
        "assert 'bijux_pollenomics_dev.essd_reproduction.published_window_contract' in sys.modules;"
        "assert 'bijux_pollenomics_dev.essd_reproduction.published_window_correspondence' not in sys.modules;"
        "assert not any(n == 'bijux_pollenomics' or n.startswith('bijux_pollenomics.') or "
        "n == 'bijux_pollenomics_lra' or n.startswith('bijux_pollenomics_lra.') for n in sys.modules)",
        str(developer_source),
    ]
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    result = subprocess.run(
        command,
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
