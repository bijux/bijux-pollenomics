"""Clicked source facets match native identities independently of display anchors."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, cast
from xml.etree import ElementTree as ET

import pytest

from bijux_pollenomics.analysis.propagation.source_chronology import (
    SOURCE_NODE_CONFIG_DIGEST,
    SourceNodeContext,
    derive_neotoma_source_chronology_nodes,
)
from bijux_pollenomics.reporting.map_document import template
from bijux_pollenomics.reporting.source_chronology.features import build_atlas_feature

from ....analysis.propagation.source_chronology.support import source_rows
from .chronology import test_age_depth_diagram as age
from .support import run_node_json
from .test_pollen_diagram import add_row, decoded, set_cell
from .test_pollen_small_multiples import add_variable, script


@pytest.fixture
def tabs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    result = decoded(cast(dict[str, Any], age.projected_tabs(tmp_path, monkeypatch)))
    add_variable(result)
    return result


def feature(
    tabs: dict[str, Any],
    *,
    level: str = "source_taxon",
    taxon: object = 51,
    ids: list[str] | None = None,
    code: str = "CROP",
) -> dict[str, Any]:
    """Derive real source nodes and project the real map feature fields."""
    rows = source_rows(
        taxon_id=taxon, taxon_name="Native source name", source_code=code
    )
    provenance = tabs["provenance"]
    sample_table = tabs["samples"]["samples"]
    sample_id = sample_table["records"][0][sample_table["fields"].index("sample_id")]
    for table in rows.values():
        for row in table:
            row.update(
                site_id=tabs["overview"]["site_id"],
                source_snapshot_id=provenance["source_snapshot_id"],
                build_id=provenance["build_id"],
            )
            for field in ("sample_id", "source_record_id"):
                if field in row:
                    row[field] = sample_id
    native_ids = ids if ids is not None else [f"neotoma:variable:{taxon}"]
    observation, variable = rows["observations"][0], rows["variables"][0]
    rows["observations"] = [
        {
            **observation,
            "observation_id": f"selected-source:{index}",
            "variable_id": value,
        }
        for index, value in enumerate(native_ids)
    ]
    rows["variables"] = [{**variable, "variable_id": value} for value in native_ids]
    result = derive_neotoma_source_chronology_nodes(
        **rows,
        context=SourceNodeContext(
            config_digest=SOURCE_NODE_CONFIG_DIGEST,
            source_snapshot_id=provenance["source_snapshot_id"],
            build_id=provenance["build_id"],
        ),
    )
    node = next(node for node in result.nodes if node.node_level == level)
    return cast(dict[str, Any], build_atlas_feature(node))


def observe(tabs: dict[str, Any], signal: object) -> dict[str, Any]:
    source = (
        script()
        + (
            Path(template.__file__).parent / "assets/focused-source-signal.js"
        ).read_text()
    )
    return cast(
        dict[str, Any],
        run_node_json(
            source
            + "const tabs="
            + json.dumps(tabs)
            + ",signal="
            + json.dumps(signal)
            + ";const before=JSON.stringify([tabs,signal]);console.log(JSON.stringify({data:pollenFocusedSignalData(tabs,signal),html:renderPollenFocusedSignal(tabs,signal),unchanged:before===JSON.stringify([tabs,signal])}));"
        ),
    )


def test_real_feature_producer_selects_51_instead_of_first_native_50(
    tabs: dict[str, Any],
) -> None:
    signal = feature(tabs)
    original = deepcopy([tabs, signal])
    result = observe(tabs, signal)
    data = result["data"]
    assert data["status"] == "matched" and data["anchorStatus"] == "compatible"
    assert len(data["groupKeys"]) == 1
    assert json.loads(data["defaultAnchorKey"])[2] == "neotoma:variable:51"
    assert data["observationIds"] == ["observation-51"]
    assert data["matchBasisCounts"] == {"exact_variable_taxon_unit": 1}
    assert [tabs, signal] == original and result["unchanged"] is True
    assert (
        "Selected map signal:" in result["html"]
        and "manual display anchor is separate" in result["html"]
    )
    assert "no drawable match" in result["html"]


def test_map_name_never_replaces_exact_ids_and_taxon_types_are_not_coerced(
    tabs: dict[str, Any],
) -> None:
    signal = feature(tabs)
    signal.update(title="Triticum", source_reported_name="Triticum")
    assert observe(tabs, signal)["data"]["observationIds"] == ["observation-51"]
    signal["source_taxon_id"] = "51"
    assert observe(tabs, signal)["data"]["status"] == "unmatched"
    for table in (tabs["pollen_composition"], tabs["pollen_composition"]["variables"]):
        set_cell(table, "source_taxon_id", "51", 1)
    assert observe(tabs, feature(tabs, taxon="51"))["data"]["status"] == "matched"


def test_caption_reuses_already_computed_native_matches(tabs: dict[str, Any]) -> None:
    signal = feature(tabs)
    source = (
        script()
        + (
            Path(template.__file__).parent / "assets/focused-source-signal.js"
        ).read_text()
    )
    output = run_node_json(
        source
        + "const tabs="
        + json.dumps(tabs)
        + ",signal="
        + json.dumps(signal)
        + ";const data=pollenFocusedSignalData(tabs,signal);"
        + "pollenFocusedSignalData=()=>{throw Error('unexpected second decoding')};"
        + "console.log(JSON.stringify(renderPollenFocusedSignal(tabs,signal,data)));"
    )
    assert "1 drawable source observations in 1 native measurement groups" in output


def test_sample_presence_does_not_announce_an_unselected_taxon_or_code(
    tabs: dict[str, Any],
) -> None:
    output = observe(tabs, feature(tabs, level="source_sample_presence"))
    assert output["data"]["status"] == "unavailable"
    assert output["data"]["observationIds"] == []
    assert (
        "sample presence without one selected taxon or ecological code"
        in output["html"]
    )
    assert "literal source code not supplied" not in output["html"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_family", "sead"),
        ("semantic_role", "accepted_taxonomy"),
        ("record_id", "neotoma:site:foreign"),
        ("source_record_id", None),
        ("source_record_id", ""),
        ("source_record_id", False),
        ("source_snapshot_id", "foreign"),
        ("build_id", "foreign"),
        ("source_variable_ids", []),
        ("source_variable_ids", ["neotoma:variable:51", "neotoma:variable:51"]),
        ("source_variable_ids", [True]),
        ("source_taxon_id", True),
        ("source_taxon_id", None),
        ("source_ecological_code", "CROP"),
        ("source_unit", None),
        ("node_level", "accepted_taxon"),
    ],
)
def test_foreign_or_contradictory_feature_context_is_unavailable(
    tabs: dict[str, Any],
    field: str,
    value: object,
) -> None:
    signal = feature(tabs)
    signal[field] = value
    result = observe(tabs, signal)
    assert result["data"]["status"] == "unavailable"
    assert result["data"]["groupKeys"] == [] and result["unchanged"] is True


@pytest.mark.parametrize("signal", [None, {}, False])
def test_no_signal_does_not_claim_the_default_display_anchor(
    tabs: dict[str, Any], signal: object
) -> None:
    result = observe(tabs, signal)
    assert (
        result["data"]["status"] == "unavailable"
        and result["data"]["defaultAnchorKey"] is None
    )
    assert (
        ET.fromstring(result["html"]).get("data-pollen-focused-signal") == "unavailable"
    )


def test_sample_presence_has_no_exact_native_facet(tabs: dict[str, Any]) -> None:
    signal = feature(tabs, level="source_sample_presence")
    assert signal["source_variable_ids"] == [] and signal["source_taxon_id"] is None
    result = observe(tabs, signal)["data"]
    assert result["status"] == "unavailable" and result["groupKeys"] == []
    assert "Sample presence" in result["reason"]


@pytest.mark.parametrize("field", ["record_id", "source_snapshot_id", "build_id"])
@pytest.mark.parametrize("value", [None, "", " ", "missing"])
def test_missing_identity_on_both_sides_cannot_authenticate_a_source(
    tabs: dict[str, Any], field: str, value: object
) -> None:
    signal = feature(tabs)
    owner = tabs["overview"] if field == "record_id" else tabs["provenance"]
    detail_field = "site_id" if field == "record_id" else field
    if value == "missing":
        del signal[field]
        del owner[detail_field]
    else:
        signal[field] = owner[detail_field] = value
    result = observe(tabs, signal)["data"]
    assert result["status"] == "unavailable" and result["groupKeys"] == []


@pytest.mark.parametrize(
    "field,value",
    [("source_variable_ids", ["foreign-variable"]), ("source_unit", "percent")],
)
def test_no_name_or_unit_conversion_fallback(
    tabs: dict[str, Any], field: str, value: object
) -> None:
    signal = feature(tabs)
    signal[field] = value
    result = observe(tabs, signal)["data"]
    assert result["status"] == "unmatched" and result["defaultAnchorKey"] is None
    assert result["unmatchedVariableIds"] == signal["source_variable_ids"]


@pytest.mark.parametrize("level", ["source_taxon", "source_ecological_code"])
def test_clicked_sample_limits_exact_marks_without_hiding_other_native_rows(
    tabs: dict[str, Any], level: str
) -> None:
    add_row(tabs["samples"]["samples"], sample_id="other-source-sample")
    add_row(
        tabs["pollen_composition"],
        observation_id="other-sample-observation",
        sample_id="other-source-sample",
    )
    signal = feature(tabs, level=level, taxon=50)
    result = observe(tabs, signal)
    assert result["data"]["status"] == "matched"
    assert "other-sample-observation" not in result["data"]["observationIds"]
    assert result["unchanged"] is True
    signal["source_record_id"] = "other-source-sample"
    selected = observe(tabs, signal)["data"]
    assert selected["observationIds"] == ["other-sample-observation"]
    signal["source_record_id"] = "absent-source-sample"
    assert observe(tabs, signal)["data"]["status"] == "unmatched"


@pytest.mark.parametrize("level", ["source_taxon", "source_ecological_code"])
@pytest.mark.parametrize(
    "changes",
    [
        {"source_value": 0},
        {"source_value": -1, "unit_family": "continuous"},
        {"source_element_type": "plant macrofossil"},
    ],
)
def test_only_positive_pollen_node_members_receive_selected_marks(
    tabs: dict[str, Any], level: str, changes: dict[str, Any]
) -> None:
    add_row(
        tabs["pollen_composition"],
        observation_id="not-a-source-node-member",
        **changes,
    )
    output = observe(tabs, feature(tabs, taxon=50, level=level))
    assert output["data"]["status"] == "matched"
    assert "not-a-source-node-member" not in output["data"]["observationIds"]
    assert output["unchanged"] is True


def test_multiple_source_variable_ids_keep_every_exact_match(
    tabs: dict[str, Any],
) -> None:
    table = tabs["pollen_composition"]
    opaque = "provider-owned-variable:second"
    set_cell(table, "variable_id", opaque, 1)
    set_cell(table["variables"], "variable_id", opaque, 1)
    set_cell(table, "source_taxon_id", 50, 1)
    set_cell(table["variables"], "source_taxon_id", 50, 1)
    signal = feature(tabs, taxon=50, ids=["neotoma:variable:50", opaque])
    assert signal["source_variable_ids"] == sorted(["neotoma:variable:50", opaque])
    result = observe(tabs, signal)["data"]
    assert result["status"] == "matched" and len(result["groupKeys"]) == 2
    assert set(result["observationIds"]) == {
        "neotoma:observation:40:50:1",
        "observation-51",
    }
    assert (
        result["unmatchedVariableIds"] == []
        and result["defaultAnchorKey"] in result["groupKeys"]
    )
    signal["source_variable_ids"].append("foreign-variable")
    partial = observe(tabs, signal)["data"]
    assert partial["status"] == "partial" and partial["unmatchedVariableIds"] == [
        "foreign-variable"
    ]
    assert partial["defaultAnchorKey"] is None


def test_ecological_map_code_keeps_all_native_taxa_without_claiming_one_taxon(
    tabs: dict[str, Any],
) -> None:
    signal = feature(tabs, level="source_ecological_code")
    assert signal["source_variable_ids"] == [] and signal["source_taxon_id"] is None
    result = observe(tabs, signal)
    assert (
        result["data"]["status"] == "matched" and len(result["data"]["groupKeys"]) == 2
    )
    assert result["data"]["matchBasisCounts"] == {"raw_source_code": 2}
    assert (
        "literal source code CROP" in result["html"]
        and "approve ecological taxonomy" in result["html"]
    )


def test_unique_variable_literal_code_matches_the_existing_source_enrichment(
    tabs: dict[str, Any],
) -> None:
    table = tabs["pollen_composition"]
    set_cell(table, "source_ecological_group", None)
    set_cell(
        table["variables"], "source_semantics", [{"source_ecological_group": "CROP"}]
    )
    result = observe(tabs, feature(tabs, level="source_ecological_code"))["data"]
    assert result["status"] == "matched"
    assert result["matchBasisCounts"] == {
        "unique_variable_source_code": 1,
        "raw_source_code": 1,
    }
    set_cell(table, "source_ecological_group", "TRSH")
    authoritative = observe(tabs, feature(tabs, level="source_ecological_code"))["data"]
    assert authoritative["observationIds"] == ["observation-51"]


def test_missing_code_with_multiple_variable_codes_is_ambiguous(
    tabs: dict[str, Any],
) -> None:
    table = tabs["pollen_composition"]
    set_cell(table, "source_ecological_group", None)
    set_cell(table, "source_ecological_group", "TRSH", 1)
    set_cell(
        table["variables"],
        "source_semantics",
        [{"source_ecological_group": "CROP"}, {"source_ecological_group": "TRSH"}],
    )
    result = observe(tabs, feature(tabs, level="source_ecological_code"))["data"]
    assert result["status"] == "ambiguous" and not result["groupKeys"]
    assert result["ambiguousObservationIds"] == ["neotoma:observation:40:50:1"]
    assert result["defaultAnchorKey"] is None


def test_mixed_code_group_only_marks_matching_observation_ids(
    tabs: dict[str, Any],
) -> None:
    add_row(
        tabs["pollen_composition"],
        observation_id="other-code-observation",
        source_ecological_group="TRSH",
    )
    result = observe(tabs, feature(tabs, level="source_ecological_code"))
    assert "other-code-observation" not in result["data"]["observationIds"]
    assert len(result["data"]["groupKeys"]) == 2
    assert "Matching groups can contain other source observations" in result["html"]


@pytest.mark.parametrize("which", ["observations", "variables", "samples"])
def test_ambiguous_selected_native_identity_is_not_a_match(
    tabs: dict[str, Any], which: str
) -> None:
    table = {
        "observations": tabs["pollen_composition"],
        "variables": tabs["pollen_composition"]["variables"],
        "samples": tabs["samples"]["samples"],
    }[which]
    index = 0 if which == "samples" else 1
    table["records"].append(deepcopy(table["records"][index]))
    table["record_count"] += 1
    result = observe(tabs, feature(tabs))["data"]
    assert result["status"] == "ambiguous" and not result["groupKeys"]


def test_incompatible_matching_contexts_never_choose_an_arbitrary_anchor(
    tabs: dict[str, Any],
) -> None:
    table = tabs["pollen_composition"]
    row = deepcopy(table["records"][1])
    row[table["fields"].index("observation_id")] = "other-context-observation"
    row[table["fields"].index("source_context")] = {"preparation": "other"}
    table["records"].append(row)
    table["record_count"] += 1
    result = observe(tabs, feature(tabs))
    assert (
        result["data"]["status"] == "matched" and len(result["data"]["groupKeys"]) == 2
    )
    assert result["data"]["anchorStatus"] == "ambiguous_measurement_context"
    assert result["data"]["defaultAnchorKey"] is None
    assert "choose a display anchor explicitly" in result["html"]


def test_opaque_source_ids_are_escaped_not_guessed_as_names(
    tabs: dict[str, Any],
) -> None:
    identifier = '<img src=x onerror="bad()">'
    set_cell(tabs["pollen_composition"], "variable_id", identifier, 1)
    set_cell(tabs["pollen_composition"]["variables"], "variable_id", identifier, 1)
    result = observe(tabs, feature(tabs, ids=[identifier]))
    assert result["data"]["status"] == "matched"
    assert (
        ET.fromstring(result["html"]).find(".//img") is None
        and "&lt;img" in result["html"]
    )
    assert result["unchanged"] is True


def test_invalid_encoded_tables_do_not_invent_a_source_signal(
    tabs: dict[str, Any],
) -> None:
    tabs["pollen_composition"]["records"][0].pop()
    result = observe(tabs, feature(tabs))["data"]
    assert result["status"] == "unavailable" and not result["observationIds"]
