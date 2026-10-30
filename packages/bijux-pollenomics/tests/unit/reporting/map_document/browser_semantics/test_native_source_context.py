"""Literal native classification and dataset metadata remain separate from review."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
from typing import Any, cast
from xml.etree import ElementTree as ET

import pytest

from bijux_pollenomics.reporting.map_document.evidence_projection import (
    neotoma,
    sead,
)
from bijux_pollenomics.reporting.map_document.evidence_projection.constants import (
    PROJECTION_SCHEMA_VERSION,
)
from tests.support.neotoma.relational_shapes import nested
from tests.support.sead_evidence import (
    install_sead_projection_fixture,
    sead_projection_layers,
)

from ..evidence_projection.fixtures.neotoma import _neotoma_fixture
from ..evidence_projection.test_neotoma_chronology_models import (
    materialized,
    native_source,
)
from .chronology.test_age_depth_diagram import diagram_script
from .support import check_javascript_syntax, run_node_json


@pytest.fixture
def neotoma_tabs(tmp_path: Path) -> dict[str, Any]:
    native = native_source()
    dataset = nested(native, "site", "collectionunit", "dataset")
    dataset.update(
        doi=["10.1234/Native.ONE", "10.1234/native.two"],
        datasetpi=[{"contactname": "Native investigator", "contactid": 0}],
        datasetnotes=None,
    )
    tabs, _ = materialized(tmp_path, native)
    return tabs


@pytest.fixture
def sead_tabs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    install_sead_projection_fixture(tmp_path, monkeypatch)
    records, _ = sead._project_sead(tmp_path, sead_projection_layers()[1:])
    return cast(
        dict[str, Any],
        next(
            record["tabs"] for record in records if record["record_id"] == "sead:site:2"
        ),
    )


def parse_html(html: str) -> ET.Element:
    # The canonical table uses valid HTML boolean attributes on paging buttons.
    return ET.fromstring(
        re.sub(r"(<button\b[^>]*?)\sdisabled(?=\s|>)", r'\1 disabled="disabled"', html)
    )


def observe(tabs: dict[str, Any], expression: str = "null") -> dict[str, Any]:
    return cast(
        dict[str, Any],
        run_node_json(
            diagram_script()
            + "const tabs="
            + json.dumps(tabs)
            + ";const original=JSON.stringify(tabs);const detailTablePages=new Map(),DETAIL_TABLE_PAGE_SIZE=25;const extra="
            + expression
            + ";console.log(JSON.stringify({native:renderNativeClassificationContext(tabs),provenance:renderSourceProvenanceContext(tabs),accepted:renderDetailValue(tabs.classification,'classification'),identity:renderDetailValue(tabs.provenance,'provenance'),extra,unchanged:original===JSON.stringify(tabs)}));"
        ),
    )


def test_actual_drawer_keeps_review_status_and_provenance_with_native_context(
    neotoma_tabs: dict[str, Any],
) -> None:
    output = run_node_json(
        diagram_script()
        + "const tabs="
        + json.dumps(neotoma_tabs)
        + r""";
const original=JSON.stringify(tabs),callbacks={},detailTablePages=new Map(),DETAIL_TABLE_PAGE_SIZE=25;
const focusTabs={innerHTML:'',contains(){return false;},querySelectorAll(){return ['classification','provenance'].map(key=>({dataset:{focusTab:key},addEventListener(event,cb){callbacks[key]=cb;}}));}};
const focusDetail={innerHTML:'',dataset:{},contains(){return false;},setAttribute(){},querySelectorAll(){return [];}};
const focusExportButton={},focusCopyLinkButton={},focusExportStatus={},document={activeElement:null};
function sourcePollenExportAvailable(){return false;}
function syncHashState(){}
const focusState={kind:'point',detailTabs:tabs};let activeFocusTab='classification';
renderFocusDetail();const classification=focusDetail.innerHTML;
callbacks.provenance();const provenance=focusDetail.innerHTML;
callbacks.classification();
console.log(JSON.stringify({classification,provenance,returned:focusDetail.innerHTML,unchanged:original===JSON.stringify(tabs)}));
"""
    )
    assert (
        "accepted_scientific_classification_not_available" in output["classification"]
    )
    assert "Poaceae (Cerealia-type)" in output["classification"]
    assert "UPHE" in output["classification"] and "LABO" in output["classification"]
    assert output["classification"] == output["returned"]
    assert "projection schema version" in output["provenance"]
    assert PROJECTION_SCHEMA_VERSION in output["provenance"]
    assert "record locator" in output["provenance"]
    assert "10.1234/Native.ONE" in output["provenance"]
    assert "Native investigator" in output["provenance"]
    assert 'data-detail-table-page="provenance.datasets"' in output["provenance"]
    assert "not a full primary publication citation" in output["provenance"]
    assert output["unchanged"]


def test_native_neotoma_context_does_not_turn_source_codes_into_accepted_mapping(
    neotoma_tabs: dict[str, Any],
) -> None:
    original = deepcopy(neotoma_tabs)
    output = observe(neotoma_tabs)
    assert "Poaceae (Cerealia-type)" in output["native"]
    assert "UPHE" in output["native"] and "LABO" in output["native"]
    assert "Vascular plants" in output["native"] and "pollen" in output["native"]
    assert 'data-detail-table-page="classification.native_context"' in output["native"]
    assert "do not establish accepted normalized names" in output["native"]
    assert "accepted_scientific_classification_not_available" in output["accepted"]
    assert neotoma_tabs["classification"] == {
        "status": "unavailable",
        "reason_code": "accepted_scientific_classification_not_available",
    }
    assert neotoma_tabs == original and output["unchanged"]


def test_native_sead_taxon_relations_and_status_stay_literal(
    sead_tabs: dict[str, Any],
) -> None:
    output = observe(sead_tabs)
    table = sead_tabs["pollen_composition"]["taxa"]
    assert table["record_count"] > 0
    assert "source ecocodes" in output["native"]
    assert "derived classification status" in output["native"]
    assert "accepted_scientific_classification_not_available" in output["accepted"]
    assert "primary publication citations are not exposed" in output["provenance"]
    assert 'data-detail-table-page="provenance.datasets"' in output["provenance"]
    assert output["unchanged"]


def test_provenance_keeps_doi_alternatives_investigators_and_raw_payload(
    neotoma_tabs: dict[str, Any],
) -> None:
    output = observe(neotoma_tabs)
    assert "10.1234/Native.ONE" in output["provenance"]
    assert "10.1234/native.two" in output["provenance"]
    assert "Native investigator" in output["provenance"]
    assert "European Pollen Database" in output["provenance"]
    assert "null (source null)" in output["provenance"]
    assert "source payload" in output["provenance"]
    assert (
        "not a full primary publication citation or a rights decision"
        in output["provenance"]
    )
    assert "separate qualified join" in output["provenance"]
    links = parse_html(output["provenance"]).findall(".//a")
    assert len(links) == 1 and links[0].text == "Current provider dataset JSON"
    assert "observation locator contract" in output["identity"]
    assert output["unchanged"]


def test_authenticated_schema_tags_are_passed_through_not_invented(
    tmp_path: Path, neotoma_tabs: dict[str, Any]
) -> None:
    manifest = json.loads((tmp_path / "neotoma/relational/manifest.json").read_text())
    provenance = neotoma_tabs["provenance"]
    assert provenance["materialization_schema_version"] == manifest["schema_version"]
    assert (
        provenance["relational_snapshot_schema_version"]
        == manifest["relational_snapshot_schema_version"]
    )
    assert provenance["projection_schema_version"] == PROJECTION_SCHEMA_VERSION
    assert "transformations" not in provenance
    output = observe(neotoma_tabs)
    assert manifest["schema_version"] in output["identity"]
    assert manifest["relational_snapshot_schema_version"] in output["identity"]
    assert "No transformation history is invented" in output["provenance"]


def test_legacy_missing_source_schema_is_not_labelled_current(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _neotoma_fixture(tmp_path, monkeypatch)
    records, _, _ = neotoma._project_neotoma(
        tmp_path, {"features": [{"evidence_row_id": "10"}]}
    )
    tabs = cast(dict[str, Any], records[0]["tabs"])
    assert tabs["provenance"]["projection_schema_version"] == PROJECTION_SCHEMA_VERSION
    assert "materialization_schema_version" not in tabs["provenance"]
    assert "relational_snapshot_schema_version" not in tabs["provenance"]


@pytest.mark.parametrize("state", ["absent", "null", "empty"])
def test_citation_absence_is_not_fabricated_or_called_external_unavailability(
    neotoma_tabs: dict[str, Any], state: str
) -> None:
    table = neotoma_tabs["samples"]["datasets"]
    payload = table["records"][0][table["fields"].index("source_payload")]
    if state == "absent":
        payload.pop("doi")
    else:
        payload["doi"] = None if state == "null" else []
    output = observe(neotoma_tabs)
    assert "Dataset DOI values as reported" in output["provenance"]
    expected = {"absent": "Unavailable", "null": "null (source null)", "empty": "[]"}[
        state
    ]
    document = parse_html(output["provenance"])
    first = document.find("article/div")
    assert first is not None and list(first)[1].text == expected
    assert "not a full primary publication citation" in output["provenance"]
    assert "source is externally unavailable" not in output["provenance"]
    assert output["unchanged"]


def test_native_context_and_dataset_tables_are_rendered_by_original_reference(
    neotoma_tabs: dict[str, Any],
) -> None:
    output = observe(
        neotoma_tabs,
        "(()=>{const renderer=renderDetailTable,calls=[];renderDetailTable=(table,path)=>{calls.push({path,native:table===tabs.pollen_composition.variables,datasets:table===tabs.samples.datasets});return renderer(table,path);};renderNativeClassificationContext(tabs);renderSourceProvenanceContext(tabs);renderDetailTable=renderer;return calls;})()",
    )
    assert output["extra"] == [
        {"path": "classification.native_context", "native": True, "datasets": False},
        {"path": "provenance.datasets", "native": False, "datasets": True},
    ]
    assert output["unchanged"]


def test_native_codes_keep_zero_null_multiple_contexts_and_pagination(
    neotoma_tabs: dict[str, Any],
) -> None:
    table = neotoma_tabs["pollen_composition"]["variables"]
    for index in range(28):
        row = deepcopy(table["records"][0])
        row[table["fields"].index("variable_id")] = f"native-{index}"
        row[table["fields"].index("source_taxon_id")] = 0 if index == 27 else None
        row[table["fields"].index("source_semantics")] = [
            {"source_ecological_group": "CROP"},
            {"source_ecological_group": "TRSH"},
        ]
        table["records"].append(row)
    table["record_count"] = len(table["records"])
    output = observe(
        neotoma_tabs,
        "(()=>{detailTablePages.set('classification.native_context',1);return renderNativeClassificationContext(tabs);})()",
    )
    assert "Showing 26–30 of 30" in output["extra"]
    assert "null (source null)" in output["extra"] and ">0</td>" in output["extra"]
    assert "CROP" in output["extra"] and "TRSH" in output["extra"]
    assert (
        "not_accepted" in output["identity"]
        or "accepted_scientific_classification_not_available" in output["accepted"]
    )
    assert output["unchanged"]


@pytest.mark.parametrize("family", ["unknown", None])
def test_unsupported_source_context_is_named_without_hiding_existing_provenance(
    neotoma_tabs: dict[str, Any], family: str | None
) -> None:
    neotoma_tabs["overview"]["source_family"] = family
    output = observe(neotoma_tabs)
    assert "Native classification context is unavailable" in output["native"]
    assert "Dataset citation context is unavailable" in output["provenance"]
    assert "missing citation metadata is not a claim" in output["provenance"]
    assert "materialization schema version" in output["identity"]
    assert output["unchanged"]


def test_missing_tables_remain_named_unavailable(neotoma_tabs: dict[str, Any]) -> None:
    del neotoma_tabs["pollen_composition"]["variables"]
    del neotoma_tabs["samples"]["datasets"]
    output = observe(neotoma_tabs)
    assert "native taxon table is not available" in output["native"]
    assert "Dataset citation context is unavailable" in output["provenance"]
    assert output["unchanged"]


def test_source_metadata_is_escaped_and_cannot_create_a_citation_link(
    neotoma_tabs: dict[str, Any], tmp_path: Path
) -> None:
    table = neotoma_tabs["samples"]["datasets"]
    payload = table["records"][0][table["fields"].index("source_payload")]
    payload["doi"] = ["javascript:alert(1)", '<img src=x onerror="bad">']
    variable = neotoma_tabs["pollen_composition"]["variables"]
    variable["records"][0][variable["fields"].index("source_reported_name")] = (
        "<native taxon>"
    )
    output = observe(neotoma_tabs)
    assert not parse_html(output["provenance"]).findall(".//img")
    links = parse_html(output["provenance"]).findall(".//a")
    assert len(links) == 1
    assert (
        links[0]
        .attrib["href"]
        .startswith("https://api.neotomadb.org/v2.0/data/downloads/")
    )
    assert "&lt;native taxon&gt;" in output["native"]
    assert "&lt;img" in output["provenance"] and output["unchanged"]
    check_javascript_syntax(diagram_script(), tmp_path / "native-source-context.js")


def test_native_dataset_navigation_uses_decoded_identity_and_preserves_snapshot(
    neotoma_tabs: dict[str, Any], tmp_path: Path
) -> None:
    output = observe(neotoma_tabs)
    document = parse_html(output["provenance"])
    links = document.findall(".//a")
    assert len(links) == 1
    assert links[0].attrib == {
        "href": "https://api.neotomadb.org/v2.0/data/downloads/201",
        "target": "_blank",
        "rel": "noopener noreferrer",
    }
    assert links[0].text == "Current provider dataset JSON"
    assert "for neotoma:dataset:201" in "".join(document.itertext())
    assert "may differ from the retained source snapshot" in output["provenance"]
    assert "not the original HTTP response bytes" in output["provenance"]
    assert output["unchanged"]
    check_javascript_syntax(diagram_script(), tmp_path / "provider-navigation.js")


@pytest.mark.parametrize(
    "value", [None, True, False, 0, -1, 1.5, 2**53, "201", '<a href="bad">']
)
def test_invalid_native_ids_do_not_create_a_provider_link(
    neotoma_tabs: dict[str, Any], value: object
) -> None:
    table = neotoma_tabs["samples"]["datasets"]
    row = table["records"][0]
    row[table["fields"].index("source_dataset_id")] = value
    row[table["fields"].index("source_payload")]["datasetid"] = value
    output = observe(neotoma_tabs)
    assert not parse_html(output["provenance"]).findall(".//a")
    assert "Current provider dataset JSON link is unavailable" in output["provenance"]
    assert 'data-detail-table-page="provenance.datasets"' in output["provenance"]
    assert output["unchanged"]


@pytest.mark.parametrize(
    "state",
    [
        "missing_source_id",
        "missing_payload_id",
        "source_null",
        "payload_mismatch",
        "namespace_mismatch",
    ],
)
def test_missing_or_inconsistent_dataset_identity_is_not_inferred(
    neotoma_tabs: dict[str, Any], state: str
) -> None:
    table = neotoma_tabs["samples"]["datasets"]
    row = table["records"][0]
    if state == "missing_source_id":
        index = table["fields"].index("source_dataset_id")
        table["fields"].pop(index)
        for record in table["records"]:
            record.pop(index)
    elif state == "missing_payload_id":
        row[table["fields"].index("source_payload")].pop("datasetid")
    elif state == "source_null":
        row[table["fields"].index("source_payload")] = None
    elif state == "payload_mismatch":
        row[table["fields"].index("source_payload")]["datasetid"] = 202
    else:
        row[table["fields"].index("dataset_id")] = "neotoma:dataset:202"
    output = observe(neotoma_tabs)
    assert not parse_html(output["provenance"]).findall(".//a")
    assert "link is unavailable" in output["provenance"]
    assert output["unchanged"]


@pytest.mark.parametrize("duplicate", ["both", "native_only", "namespace_only"])
def test_duplicate_dataset_identities_cannot_select_a_navigation_target(
    neotoma_tabs: dict[str, Any], duplicate: str
) -> None:
    table = neotoma_tabs["samples"]["datasets"]
    second = deepcopy(table["records"][0])
    if duplicate == "native_only":
        second[table["fields"].index("dataset_id")] = "neotoma:dataset:202"
    elif duplicate == "namespace_only":
        second[table["fields"].index("source_dataset_id")] = 202
        second[table["fields"].index("source_payload")]["datasetid"] = 202
    table["records"].append(second)
    table["record_count"] += 1
    output = observe(neotoma_tabs)
    assert not parse_html(output["provenance"]).findall(".//a")
    assert output["provenance"].count("link is unavailable") == 2
    assert "Showing 1–2 of 2" in output["provenance"]
    assert output["unchanged"]


def test_multiple_valid_datasets_have_separate_contextual_provider_links(
    neotoma_tabs: dict[str, Any],
) -> None:
    table = neotoma_tabs["samples"]["datasets"]
    second = deepcopy(table["records"][0])
    second[table["fields"].index("dataset_id")] = "neotoma:dataset:202"
    second[table["fields"].index("source_dataset_id")] = 202
    second[table["fields"].index("source_payload")]["datasetid"] = 202
    table["records"].append(second)
    table["record_count"] += 1
    output = observe(neotoma_tabs)
    document = parse_html(output["provenance"])
    assert [link.attrib["href"] for link in document.findall(".//a")] == [
        f"https://api.neotomadb.org/v2.0/data/downloads/{identifier}"
        for identifier in (201, 202)
    ]
    assert "for neotoma:dataset:201" in "".join(document.itertext())
    assert "for neotoma:dataset:202" in "".join(document.itertext())
    assert output["unchanged"]
