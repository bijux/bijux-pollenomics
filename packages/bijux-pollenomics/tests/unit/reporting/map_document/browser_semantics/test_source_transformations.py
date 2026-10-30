"""Supplied SEAD operations are visible without inventing a processing ledger."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, cast

import pytest

from bijux_pollenomics.collection.sources.sead.evidence.normalization import (
    normalize_sead_chronology_claims,
)
from bijux_pollenomics.reporting.map_document.evidence_projection.sead_claims import (
    _sead_claim_table,
)

from .chronology.test_age_depth_diagram import diagram_script
from .support import check_javascript_syntax
from .test_native_source_context import (
    neotoma_tabs as neotoma_tabs,
)
from .test_native_source_context import (
    observe,
    parse_html,
)
from .test_native_source_context import (
    sead_tabs as sead_tabs,
)


def decoded(tabs: dict[str, Any]) -> list[dict[str, Any]]:
    return cast(
        list[dict[str, Any]],
        observe(
            tabs,
            "tabs.chronology.records.map(row=>decodeDetailTableRow(tabs.chronology,row))",
        )["extra"],
    )


def test_actual_sead_projection_exposes_operation_source_units_and_relation_path(
    sead_tabs: dict[str, Any],
    tmp_path: Path,
) -> None:
    before = deepcopy(sead_tabs)
    html = observe(sead_tabs)["provenance"]
    assert "Supplied source transformations" in html
    assert "1 chronology claims; 1 with an explicit transformation ID" in html
    assert "sead-calendar-year-to-cal-bp-1950-v1" in html
    assert "sead-retain-all-source-chronologies-v1" in html
    assert "calendar_year" in html and "1850" in html and "100" in html
    assert "tbl_analysis_dating_ranges" in html
    assert "sead-acquisition-manifest:fixture" in html
    assert "original interval orientation" in html and "point" in html
    assert "source_classification_not_accepted" in html
    assert "No conversion is performed in this view" in html
    assert "not a complete transformation ledger" in html
    assert 'data-detail-table-page="provenance.transformations"' in html
    assert sead_tabs == before
    check_javascript_syntax(diagram_script(), tmp_path / "source-transformations.js")


def test_real_normalizer_and_compact_decoder_preserve_calendar_zero_and_nulls(
    sead_tabs: dict[str, Any],
) -> None:
    template = decoded(sead_tabs)[0]
    row = deepcopy(template["source_age_value"])
    row.update(low_value=1950, high_value=None, time_start_bp=0, time_end_bp=0)
    source: list[dict[str, object]] = [
        {
            "site_id": 2,
            "site_uuid": "site-2",
            "country_code": "DK",
            "latitude_dd": 55,
            "longitude_dd": 10,
            "country_assignment_method": "strict_boundary_containment",
            "dating_range_rows": [row],
        }
    ]
    original = deepcopy(source)
    normalized = normalize_sead_chronology_claims(
        source,
        provenance_record_id=template["provenance_record_id"],
        build_id=template["build_id"],
    )[0]
    # Reuse capture-only fixture metadata; every age/rule field is producer output.
    claim = {**template, **normalized}
    sead_tabs["chronology"] = _sead_claim_table([claim])
    native = decoded(sead_tabs)[0]
    assert native["source_age_value"] == row
    assert native["source_age_value"]["high_value"] is None
    assert native["younger_bp"] == native["older_bp"] == 0
    assert native["source_age_unit"] == "calendar_year"
    html = observe(sead_tabs)["provenance"]
    assert "1950" in html and ">0</td>" in html
    assert "&quot;high_value&quot;:null" in html
    assert "sead-calendar-year-to-cal-bp-1950-v1" in html
    assert "observation_link_not_materialized" in html
    assert source == original


@pytest.mark.parametrize("state", ["missing", "null", "empty"])
def test_missing_transformation_identity_is_not_called_no_processing(
    sead_tabs: dict[str, Any],
    state: str,
) -> None:
    rows = decoded(sead_tabs)
    rows[0]["transformation_id"] = None if state == "null" else ""
    table = cast(dict[str, Any], _sead_claim_table(rows))
    if state == "missing":
        index = table["fields"].index("transformation_id")
        table["fields"].pop(index)
        table["column_dictionaries"].pop("transformation_id")
        for row in table["records"]:
            row.pop(index)
    sead_tabs["chronology"] = table
    html = observe(sead_tabs)["provenance"]
    assert "0 with an explicit transformation ID" in html
    assert {
        "missing": "1 with no supplied field",
        "null": "1 with source-null ID",
        "empty": "1 with an empty ID",
    }[state] in html
    assert "Missing IDs do not establish that no processing occurred" in html
    assert "None supplied" in html


def test_unknown_operation_and_refusal_are_retained_without_translation(
    sead_tabs: dict[str, Any],
) -> None:
    rows = decoded(sead_tabs)
    rows[0].update(
        transformation_id='<unknown-operation onload="bad">',
        reason_codes=["native_refusal"],
        comparability_status="refused",
        chronology_eligibility="refused",
        younger_bp=None,
        older_bp=None,
    )
    sead_tabs["chronology"] = _sead_claim_table(rows)
    html = observe(sead_tabs)["provenance"]
    assert "&lt;unknown-operation" in html
    assert not parse_html(html).findall(".//unknown-operation")
    assert "native_refusal" in html and "refused" in html
    assert "null (source null)" in html
    assert "without inferring an operation from an unknown identifier" in html
    assert (
        "accepted_scientific_classification_not_available"
        in observe(sead_tabs)["accepted"]
    )


def test_transformations_reuse_original_paginated_table_by_reference(
    sead_tabs: dict[str, Any],
) -> None:
    rows = decoded(sead_tabs)
    claims = []
    for index in range(28):
        claim = deepcopy(rows[0])
        claim["chronology_claim_id"] += f":{index:02d}"
        claims.append(claim)
    sead_tabs["chronology"] = _sead_claim_table(claims)
    before = deepcopy(sead_tabs)
    output = observe(
        sead_tabs,
        "(()=>{const render=renderDetailTable;let same=false;renderDetailTable=(table,path)=>{if(path==='provenance.transformations')same=table===tabs.chronology;return render(table,path);};detailTablePages.set('provenance.transformations',1);const html=renderSourceProvenanceContext(tabs);renderDetailTable=render;return {same,html};})()",
    )
    assert output["extra"]["same"]
    assert "Showing 26–28 of 28" in output["extra"]["html"]
    assert (
        "28 chronology claims; 28 with an explicit transformation ID"
        in output["extra"]["html"]
    )
    assert sead_tabs == before and output["unchanged"]


def test_transformations_remain_available_when_dataset_citations_are_missing(
    sead_tabs: dict[str, Any],
) -> None:
    del sead_tabs["pollen_composition"]["dataset_semantics"]
    html = observe(sead_tabs)["provenance"]
    assert "Dataset citation context is unavailable" in html
    assert "1 chronology claims; 1 with an explicit transformation ID" in html


@pytest.mark.parametrize("change", ["missing", "malformed"])
def test_unavailable_chronology_does_not_generate_transformation_history(
    sead_tabs: dict[str, Any],
    change: str,
) -> None:
    if change == "missing":
        del sead_tabs["chronology"]
    else:
        sead_tabs["chronology"]["record_count"] += 1
    html = observe(sead_tabs)["provenance"]
    assert (
        "transformation context is unavailable or cannot be decoded consistently"
        in html
    )
    assert "Original chronology and provenance remain available" in html
    assert "1 with an explicit transformation ID" not in html


def test_neotoma_does_not_inherit_a_sead_operation_ledger(
    neotoma_tabs: dict[str, Any],
) -> None:
    output = observe(neotoma_tabs)
    assert (
        "per-record transformation table is not supplied for source family neotoma"
        in output["provenance"]
    )
    assert "sead-calendar-year" not in output["provenance"]
    assert output["unchanged"]
