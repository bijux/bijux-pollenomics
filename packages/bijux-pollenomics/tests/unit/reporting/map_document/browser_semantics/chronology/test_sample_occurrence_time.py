"""Map filters and indexes preserve dated sample gaps in locality coverage."""

from __future__ import annotations

import json

import pytest

from bijux_pollenomics.adna.domain.models import AdnaChronology
from bijux_pollenomics.reporting.map_document.static_assets.indexes import build_indexes
from bijux_pollenomics.reporting.map_document.temporal_admission import (
    feature_occurrence_intervals,
    feature_temporal_admission,
)

from ..support import run_node_json, template_block
from .support import _feature


def test_browser_filter_preserves_gap_but_keeps_display_extent() -> None:
    feature = _feature()
    feature["temporal_semantics"] = AdnaChronology(
        original_text="Sample coverage hull (display only)",
        time_start_bp=100,
        time_end_bp=310,
        time_mean_bp=205,
        dating_basis="locality_sample_coverage",
        evidence_class="locality_sample_coverage_hull",
        precision_posture="display_coverage_only",
    ).as_temporal_semantics(source_family="controlled")
    source = template_block(
        "function finiteTimeValue", "function pointFeatureInTimeWindow"
    )
    observed = run_node_json(
        "const TIME_HAS_DATA=true;let timeStartBp=200;function timeWindowEndBp(){return timeStartBp;}function timeFilterUsesFullExtent(){return false;}"
        + source
        + "\nconst feature="
        + json.dumps(feature)
        + ";const layer={applies_time_filter:true};"
        + "const gap=featureInTimeWindow(layer,feature);timeStartBp=105;const young=featureInTimeWindow(layer,feature);timeStartBp=305;const old=featureInTimeWindow(layer,feature);console.log(JSON.stringify({gap,young,old,admission:featureTimeAdmission(feature)}));"
    )
    assert observed["gap"] is False
    assert observed["young"] is True
    assert observed["old"] is True
    assert observed["admission"]["window"] == {"start": 100, "end": 310}
    assert len(observed["admission"]["windows"]) == 2
    assert feature_temporal_admission(feature) == ("admitted", (100, 310))
    assert feature_occurrence_intervals(feature) == ((100, 110), (300, 310))


def test_static_selection_index_keeps_actual_sample_components() -> None:
    feature = _feature()
    feature["temporal_semantics"] = {
        "schema_version": "temporal-semantics.v1",
        "comparability_posture": "contextual_label_only",
    }
    feature["time_start_bp"], feature["time_end_bp"] = 0, 999999
    index = build_indexes([{"key": "animal", "features": [feature]}])
    assert index["time_interval_feature_indexes"] == [
        [100, 110, "animal", 0],
        [300, 310, "animal", 0],
    ]


@pytest.mark.parametrize(
    "kind", ["unknown", "duplicate", "partial", "negative", "wrong_schema"]
)
def test_malformed_sample_support_is_refused_consistently(kind: str) -> None:
    feature = _feature()
    supports = feature["sample_chronologies"]
    assert isinstance(supports, list)
    first = supports[0]
    assert isinstance(first, dict)
    if kind == "unknown":
        first["sample_id"] = "unowned"
    elif kind == "duplicate":
        supports.append(first)
    elif kind == "wrong_schema":
        first["schema_version"] = "unqualified"
    else:
        first["chronology"] = {
            "time_start_bp": -1 if kind == "negative" else 100,
            "time_end_bp": 110 if kind == "negative" else None,
        }
    observed = run_node_json(
        template_block("function finiteTimeValue", "function pointFeatureInTimeWindow")
        + "\nconsole.log(JSON.stringify(featureTimeAdmission("
        + json.dumps(feature)
        + ")));"
    )
    assert observed == {"status": "refused", "window": None}
    assert feature_temporal_admission(feature) == ("refused", None)


def test_owned_support_does_not_bypass_existing_feature_refusal() -> None:
    feature = _feature() | {
        "temporal_semantics": {
            "comparability_posture": "refused",
            "refusal_reason_code": "source_age_system_not_comparable",
        }
    }
    observed = run_node_json(
        template_block("function finiteTimeValue", "function pointFeatureInTimeWindow")
        + "\nconsole.log(JSON.stringify(featureTimeAdmission("
        + json.dumps(feature)
        + ")));"
    )
    assert observed == {"status": "refused", "window": None}
    assert feature_temporal_admission(feature) == ("refused", None)
    assert feature_occurrence_intervals(feature) == ()
