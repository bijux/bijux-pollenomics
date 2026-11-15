"""Literal CHAR map observations stay exact through source readers and plots."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, cast

import pytest

from bijux_pollenomics.reporting.map_document.evidence_projection.neotoma import (
    _project_neotoma,
)
from tests.support.neotoma import download_row
from tests.support.neotoma.relational_shapes import nested, rows

from ...evidence_projection.neotoma_metadata.test_chronology_models import materialized
from ..chronology.test_age_depth_diagram import diagram_script
from ..pollen.test_focused_pollen_drawer import observe
from ..support import run_node_json


@pytest.fixture
def native_charcoal(tmp_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    source = download_row()
    sample = rows(nested(source, "site", "collectionunit", "dataset")["samples"])[0]
    values = rows(sample["datum"])
    values.extend(
        {
            **deepcopy(values[0]),
            "taxonid": 8001,
            "variablename": "Charcoal",
            "taxongroup": "Charcoal",
            "ecologicalgroup": "CHAR",
            "element": ">25 µm",
            "elementtype": ">25 µm",
            "value": value,
        }
        for value in (0, None)
    )
    sample["datum"] = values
    tabs, _ = materialized(tmp_path, source)
    _, _, layers = _project_neotoma(tmp_path, {"features": [{"evidence_row_id": "20"}]})
    layer = next(
        row for row in layers if row["key"] == "neotoma-native-charcoal-context"
    )
    return tabs, cast(list[dict[str, Any]], layer["features"])


def test_real_zero_charcoal_map_click_selects_only_its_exact_native_observation(
    native_charcoal: tuple[dict[str, Any], list[dict[str, Any]]],
) -> None:
    tabs, features = native_charcoal
    feature = next(row for row in features if row["source_value"] == 0)
    output = observe(
        tabs,
        [feature],
        """
await focusPointAtVisibleIndex(0);snapshot('plot');
callbacks.overview();snapshot('overview');
callbacks.pollen_composition();snapshot('returned');
""",
    )
    for key in ("plot", "returned"):
        html = output["snapshots"][key]
        assert 'data-pollen-focused-signal="matched"' in html
        assert "literal CHAR observation" in html
        assert "Basis: 1 exact native CHAR observation" in html
        assert "Selected anchor: Charcoal" in html
        assert 'data-selected-observation="true"' in html
        assert feature["observation_id"] in html
    overview = output["snapshots"]["overview"]
    assert 'data-native-charcoal-details="matched"' in overview
    assert "Native reported value" in overview and ">0</span>" in overview
    assert "Source observation ID" in overview and feature["observation_id"] in overview
    assert "Denominator" in overview and "null (source null)" in overview
    assert feature["source_observation_locator"] in overview
    assert "no fire, vegetation, cultivation or pollen corroboration" in overview
    assert output["sourceRetained"] and output["cached"] and output["unchanged"]


def test_null_charcoal_keeps_raw_identity_without_a_default_unrelated_plot(
    native_charcoal: tuple[dict[str, Any], list[dict[str, Any]]],
) -> None:
    tabs, features = native_charcoal
    feature = next(row for row in features if row["source_value"] is None)
    output = observe(
        tabs,
        [feature],
        """
await focusPointAtVisibleIndex(0);snapshot('initial');
callbacks.overview();snapshot('overview');callbacks.pollen_composition();
chooseNative(keys.find(key=>JSON.parse(key)[2]!==signals[0].variable_id));snapshot('manual');
callbacks.overview();snapshot('overviewAfterManual');
""",
    )
    initial = output["snapshots"]["initial"]
    assert 'data-pollen-focused-signal="unplottable"' in initial
    assert "Basis: 1 exact native CHAR observation" in initial
    assert "Choose an exact native source group" in initial
    assert "<svg" not in initial
    for key in ("overview", "overviewAfterManual"):
        html = output["snapshots"][key]
        assert 'data-native-charcoal-details="matched"' in html
        assert feature["observation_id"] in html and "null (source null)" in html
    assert "<svg" in output["snapshots"]["manual"]
    assert 'data-selected-observation="true"' not in output["snapshots"]["manual"]
    assert output["sourceRetained"] and output["unchanged"]


def test_new_charcoal_observation_resets_manual_choices_on_cached_site(
    native_charcoal: tuple[dict[str, Any], list[dict[str, Any]]],
) -> None:
    tabs, features = native_charcoal
    zero = next(row for row in features if row["source_value"] == 0)
    missing = next(row for row in features if row["source_value"] is None)
    output = observe(
        tabs,
        [zero, missing],
        """
await focusPointAtVisibleIndex(0);
chooseNative(keys.find(key=>JSON.parse(key)[2]!==signals[0].variable_id));snapshot('manual');
await focusPointAtVisibleIndex(1);snapshot('next');
""",
    )
    assert "<svg" in output["snapshots"]["manual"]
    assert "<svg" not in output["snapshots"]["next"]
    assert 'data-pollen-focused-signal="unplottable"' in output["snapshots"]["next"]
    assert output["sourceRetained"] and output["cached"] and output["unchanged"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("record_id", "foreign"),
        ("source_snapshot_id", "foreign"),
        ("site_id", "foreign"),
        ("country", "Norway"),
        ("build_id", "foreign"),
        ("source_record_id", "foreign"),
        ("sample_id", "foreign"),
        ("dataset_id", "foreign"),
        ("collection_unit_id", "foreign"),
        ("source_value", 10),
        ("source_unit", "percent"),
        ("source_denominator", "null"),
        ("detection_status", "not_reported"),
        ("source_element", "pollen"),
        ("source_element_type", "pollen"),
        ("source_ecological_group", "UPHE"),
        ("source_part_number", True),
        ("source_observation_locator", "foreign"),
        ("source_depth", 99),
        ("source_join_status", "refused"),
        ("propagation_eligible", True),
    ],
)
def test_wrong_source_or_native_assertion_never_selects_a_charcoal_plot(
    native_charcoal: tuple[dict[str, Any], list[dict[str, Any]]],
    field: str,
    value: object,
) -> None:
    tabs, features = native_charcoal
    feature = deepcopy(next(row for row in features if row["source_value"] == 0))
    feature[field] = value
    output = run_node_json(
        diagram_script()
        + "const tabs="
        + json.dumps(tabs)
        + ",signal="
        + json.dumps(feature)
        + ";console.log(JSON.stringify(pollenFocusedSignalData(tabs,signal)));"
    )
    assert output["status"] == "unavailable"
    assert output["observationIds"] == [] and output["defaultAnchorKey"] is None
