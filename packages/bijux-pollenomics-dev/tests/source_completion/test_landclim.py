from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

import pytest

from bijux_pollenomics_dev.source_completion.evidence import EvidenceReader
from bijux_pollenomics_dev.source_completion.landclim import (
    audit_landclim,
    parse_taxonomy,
)

HEADER = "Land-cover types (LCTs),PFT,PFT definition,,Plant taxa/Pollen-morphological types,FSP (m/s),PPE (SD)\n"


def test_group_heading_expansion_is_traceable_and_preserves_raw_parameters() -> None:
    rows = parse_taxonomy(
        HEADER
        + "Open land (OL),GL,Herbs,,Poaceae,0.035,1 (0)\n,,,,Rumex,0.018*,3 (0.2)\n"
    )
    assert rows[1]["source_pft"] == "GL"
    assert rows[1]["pft_heading_row"] == 2
    assert rows[1]["source_row"] == 3
    assert rows[1]["source_fall_speed"] == "0.018*"
    assert rows[1]["review_status"] == "pending_qualified_review"


def test_first_missing_group_cannot_be_guessed() -> None:
    with pytest.raises(ValueError, match="no explicit"):
        parse_taxonomy(HEADER + ",,,,Poaceae,0.035,1 (0)\n")


def test_archive_extra_pft_and_percentage_sum_remain_explicit(tmp_path: Path) -> None:
    root = tmp_path / "data/landclim/raw"
    root.mkdir(parents=True)
    (root / "landclim_ii_taxa_pft_ppe_fsp_values.csv").write_text(
        HEADER + "Open land (OL),GL,Herbs,,Poaceae,0.035,1 (0)\n"
    )
    with ZipFile(root / "landclim_ii_reveals_results.zip", "w") as archive:
        archive.writestr(
            "means/TW1.csv",
            "LCGRID_ID,Poaceae,GL,EXTRA,OL\n1,100,50,50,100\n2,NA,NA,NA,NA\n",
        )
    result = audit_landclim(EvidenceReader(tmp_path))
    member = result["archive_members"][0]
    assert member["pft_columns_without_taxonomy_definition"] == ["EXTRA"]
    assert member["rows_with_lct_sum_near_100"] == 1
    assert member["rows_with_lct_sum_near_one"] == 0
    assert member["nonnumeric_lct_row_count"] == 1
    assert (
        result["semantic_confirmation"]
        == "requires_publication_mapping_and_units_review"
    )
