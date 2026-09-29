"""Pinned PANGAEA PFT positions and observed LCT arithmetic regressions."""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import cast
import zipfile

import pytest

from bijux_pollenomics_dev.essd_reproduction.pft_crosswalk import (
    ARCHIVE,
    MAPPING,
    SOURCE_GROUPS,
    _finite,
    _members,
    _source_mapping,
    _source_tbs_taxa,
    build,
    build_taxon_arithmetic,
    reconcile,
)

REPOSITORY = Path(__file__).resolve().parents[4]
GOVERNED = REPOSITORY / "docs/report/publication-replay/landclim-pft-crosswalk"


def test_parameter_table_retains_twelve_source_codes_and_three_lcts() -> None:
    codes, definitions, groups = _source_mapping((REPOSITORY / MAPPING).read_bytes())
    assert len(codes) == len(definitions) == 12
    assert len(set(definitions.values())) == 11
    assert (
        definitions["TBE1"] == definitions["TBE2"] == "Shade-tolerant evergreen trees"
    )
    assert groups == SOURCE_GROUPS
    assert "ISTS" not in codes


def test_full_published_output_supports_only_mean_arithmetic() -> None:
    columns, groups, windows, summary = reconcile(
        (REPOSITORY / MAPPING).read_bytes(), REPOSITORY / ARCHIVE
    )
    assert len(columns) == 16
    assert [(row["code"], row["output_position"]) for row in columns][-3:] == [
        ("ET", 48),
        ("ST", 49),
        ("OL", 50),
    ]
    assert columns[7]["code"] == "ISTS"
    assert columns[7]["admission"] == "unmapped_output_code_refused"
    assert len(groups) == 3
    assert groups[1]["parameter_table_pft_codes"] == "IBS;TBS;TSD"
    assert groups[1]["observed_mean_addends"] == "IBS;ISTS;TBS;TSD"
    assert len(windows) == 25
    assert sum(cast(int, row["grid_rows"]) for row in windows) == 10_500
    assert all(row["mean_se_grid_ids_equal"] == "true" for row in windows)
    assert all(
        cast(float, row["maximum_absolute_mean_residual"]) < 2e-13 for row in groups
    )
    assert summary["se_naive_sum_disagreement_rows_by_lct"] == {
        "ET": 7588,
        "ST": 7892,
        "OL": 5921,
    }
    assert summary["pft_taxon_definition_admitted_for_ists"] is False
    assert summary["source_parameter_definition_count"] == 11
    assert summary["source_parameter_duplicate_definition_groups"] == [
        {
            "definition": "Shade-tolerant evergreen trees",
            "codes": ["TBE1", "TBE2"],
        }
    ]
    assert summary["lct_standard_error_aggregation_admitted"] is False
    assert summary["paper_dataset_pft_count_reconciled"] is False


def test_parameter_group_drift_is_refused() -> None:
    source = (REPOSITORY / MAPPING).read_bytes()
    assert b",TBS," in source
    changed = source.replace(b",TBS,", b",ISTS,", 1)
    with pytest.raises(ValueError, match="source PFT/LCT grouping changed"):
        _source_mapping(changed)
    altered_taxon = source.replace(b"Castanea sativa", b"Castanea sp.", 1)
    with pytest.raises(ValueError, match="parameter TBS taxon rows changed"):
        _source_tbs_taxa(altered_taxon)


def test_incomplete_archive_and_nonfinite_output_are_refused() -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as writer:
        writer.writestr("LANDCLIMII.RV.means.JUN2021/TW1.RV.estimates.jun21.csv", "")
    buffer.seek(0)
    with (
        zipfile.ZipFile(buffer) as archive,
        pytest.raises(ValueError, match="archive incomplete"),
    ):
        _members(archive)
    with pytest.raises(ValueError, match="nonfinite ISTS"):
        _finite({"ISTS": "nan"}, "ISTS")


def test_governed_crosswalk_replays_byte_identically(tmp_path: Path) -> None:
    output = tmp_path / "crosswalk"
    report = build(REPOSITORY, output)
    assert report["schema_version"] == "landclim-pft-crosswalk.v1"
    for name in ("columns.csv", "lct_groups.csv", "windows.csv", "report.json"):
        assert (output / name).read_bytes() == (GOVERNED / name).read_bytes()
    governed = json.loads((GOVERNED / "report.json").read_text())
    assert governed["inputs"] == report["inputs"]


def test_published_ists_tbs_taxon_arithmetic_replays_from_pinned_source(
    tmp_path: Path,
) -> None:
    output = tmp_path / "taxon-arithmetic"
    report = build_taxon_arithmetic(REPOSITORY, output)
    assert report["parameter_table_tbs_taxa"] == [
        "Carpinus betulus",
        "Carpinus orientalis",
        "Castanea sativa",
        "Corylus avellana",
        "Fagus sylvatica",
        "Fraxinus",
        "Quercus deciduous t.",
        "Tilia",
        "Ulmus",
    ]
    assert report["published_mean_addends"] == {
        "ISTS": ["Corylus.avellana", "Fraxinus", "Quercus.deciduous"],
        "TBS": [
            "Carpinus.betulus",
            "Carpinus.orientalis",
            "Castanea",
            "Fagus.sylvatica",
            "Tilia",
            "Ulmus",
        ],
    }
    assert report["mean_grid_window_rows_checked"] == 10_500
    assert all(
        cast(float, residual) < 1e-12
        for residual in cast(
            dict[str, object], report["maximum_absolute_mean_residual"]
        ).values()
    )
    assert report["ists_biological_definition_admitted"] is False
    assert report["paper_dataset_pft_count_reconciled"] is False
    assert (output / "report.json").read_bytes() == (
        GOVERNED / "tbs-taxon-arithmetic/report.json"
    ).read_bytes()
