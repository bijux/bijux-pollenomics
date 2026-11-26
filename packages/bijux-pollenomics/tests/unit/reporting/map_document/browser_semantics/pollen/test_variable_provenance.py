"""Generated native qualifiers survive compact transport, display and export."""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
import json
from pathlib import Path
import re
from types import SimpleNamespace
from typing import Any, cast

import pytest

from bijux_pollenomics.reporting.map_document import template
from bijux_pollenomics.reporting.map_document.evidence_projection.neotoma import (
    _project_neotoma,
)
from bijux_pollenomics.reporting.map_document.static_assets import (
    write_static_atlas_assets,
)
from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
    normalize_asset_inventory,
)
from bijux_pollenomics.reporting.map_document.static_assets.serialization import (
    decode_chunk_script,
)

from ...source_resources.test_service import (
    atlas_catalogue as atlas_catalogue,
)
from ...source_resources.test_service import (
    catalogue_sources as catalogue_sources,
)
from ..source_context.test_source_record_export import source_export_script
from ..support import run_node_json
from .test_pollen_diagram import decoded, diagram_script, observe
from .test_pollen_small_multiples import script as multiples_script
from .variable_sources import generated_pair


def projected(
    root: Path,
    dimension: str,
    *,
    native_provenance: tuple[dict[str, Any], dict[str, Any]] | None = None,
    charcoal: bool = False,
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    """Use the actual raw, relational, materialization and Atlas producers."""
    snapshot, _, _, datums = generated_pair(
        root, dimension, native_provenance=native_provenance, charcoal=charcoal
    )
    records, _, layers = _project_neotoma(
        root, {"features": [{"evidence_row_id": "20"}]}
    )
    return (
        snapshot,
        cast(dict[str, Any], records[0]["tabs"]),
        cast(list[dict[str, Any]], layers),
        datums,
    )


def exported(tabs: dict[str, Any]) -> dict[str, Any]:
    """Exercise the maintained export admission, decoder and factory together."""
    return cast(
        dict[str, Any],
        run_node_json(
            diagram_script()
            + source_export_script()
            + "const tabs="
            + json.dumps(tabs)
            + ";console.log(JSON.stringify(buildSourcePollenRecordExport({kind:'point',"
            + "recordId:'neotoma:site:20',detailTabs:tabs},{},decodeDetailTableRow)));"
        ),
    )


def test_conflicting_literal_names_survive_source_projection_diagram_and_download(
    tmp_path: Path,
) -> None:
    snapshot, tabs, _, datums = projected(tmp_path, "name")
    assert len(snapshot["variables"]) == 1
    assert len({row["variable_id"] for row in snapshot["observations"]}) == 1
    assert len({row["variablename"] for row in datums}) == 2
    exported_rows = exported(tabs)["pollen_observations"]["records"]
    expected = {row["value"]: row["variablename"] for row in datums}
    assert {
        row["source_value"]: row["source_variable_provenance"]["variablename"]
        for row in exported_rows
    } == expected
    output = observe(tabs)
    assert len(output["data"]["groups"]) == 2
    assert all(len(group["rows"]) == 1 for group in output["data"]["groups"])
    assert all(name in output["html"] for name in expected.values())


@pytest.mark.parametrize("first", [{}, {"variablename": None}, {"variablename": ""}])
def test_source_name_absent_null_and_empty_survive_actual_source_pipeline(
    tmp_path: Path, first: dict[str, Any]
) -> None:
    _, _, _, datums = generated_pair(
        tmp_path,
        "name",
        source_names=(first, {"variablename": "Poaceae (Cerealia-type)"}),
    )
    records, _, _ = _project_neotoma(
        tmp_path, {"features": [{"evidence_row_id": "20"}]}
    )
    tabs = cast(dict[str, Any], records[0]["tabs"])
    rows = exported(tabs)["pollen_observations"]["records"]
    actual = next(
        row["source_variable_provenance"]
        for row in rows
        if row["source_value"] == datums[0]["value"]
    )
    assert ("variablename" in actual) == ("variablename" in first)
    assert actual.get("variablename") == first.get("variablename")
    assert actual["source_reported_name_status"] == (
        "reported" if first else "not_provided_by_source"
    )
    output = observe(tabs)
    assert len(output["data"]["groups"]) == 2


def test_invalid_taxon_status_and_mixed_prefix_survive_name_dictionary(
    tmp_path: Path,
) -> None:
    snapshot, _, _, _ = generated_pair(tmp_path, "name", taxon_ids=(1947, {"id": 1947}))
    records, _, _ = _project_neotoma(
        tmp_path, {"features": [{"evidence_row_id": "20"}]}
    )
    tabs = cast(dict[str, Any], records[0]["tabs"])
    table = tabs["pollen_composition"]
    assert "source_taxon_identifier_status" in table["fields"]
    assert table["identifier_prefixes"]["variable_id"] == "neotoma:"
    rows = exported(tabs)["pollen_observations"]["records"]
    assert {row["variable_id"] for row in rows} == {
        row["variable_id"] for row in snapshot["observations"]
    }
    assert {row["source_taxon_identifier_status"] for row in rows} == {
        "not_recorded",
        "invalid_source_identifier",
    }
    assert {row["source_variable_provenance"]["variablename"] for row in rows} == {
        row["source_payload"]["variablename"] for row in snapshot["observations"]
    }
    output_dir = tmp_path / "static"
    output_dir.mkdir()
    assets = write_static_atlas_assets(
        output_dir,
        slug="taxon-source",
        version="fixture",
        point_layers=[],
        polygon_layers=[],
        detail_records=records,
    )
    detail_rows = [
        record
        for entry, path in zip(
            normalize_asset_inventory(assets.manifest["assets"]),
            assets.asset_paths,
            strict=True,
        )
        if entry["domain"] == "details"
        for record in cast(
            list[dict[str, Any]],
            decode_chunk_script(
                path.read_bytes(),
                expected_asset_key=str(entry["asset_key"]),
                expected_payload_sha256=str(entry["payload_sha256"]),
                expected_payload_encoding=str(entry["payload_encoding"]),
                expected_decoded_byte_count=cast(int, entry["decoded_byte_count"]),
            )["records"],
        )
    ]
    assert len(detail_rows) == 1
    assert exported(detail_rows[0]["tabs"])["pollen_observations"]["records"] == rows


def test_literal_names_do_not_create_measurement_context_ambiguity(
    tmp_path: Path,
) -> None:
    from . import test_focused_pollen_drawer as drawer
    from .test_focused_source_signal import feature
    from .test_focused_source_signal import observe as observe_signal

    _, tabs, _, _ = projected(tmp_path, "name")
    tabs = decoded(tabs)
    signal = feature(tabs, taxon=1947)
    result = observe_signal(tabs, signal)["data"]
    assert result["status"] == "matched"
    assert len(result["groupKeys"]) == 2
    assert result["anchorStatus"] == "compatible"
    assert result["defaultAnchorKey"] in result["groupKeys"]
    assert len(result["observationIds"]) == 2
    drawer_result = drawer.observe(
        tabs,
        [signal],
        """
await focusPointAtVisibleIndex(0);snapshot('default');
chooseNative(keys.find(key=>key!==pollenDisplaySelection(tabs).key));snapshot('alternate');
""",
    )
    for html in drawer_result["snapshots"].values():
        assert "2 drawable observations; 2 matching native groups" in html
        marks = re.findall(
            r'<g[^>]*data-selected-observation="true"[^>]*aria-label="([^"]+)"', html
        )
        assert len(marks) == 2
        assert all(
            sum(observation_id in mark for mark in marks) == 1
            for observation_id in result["observationIds"]
        )
        assert html.count("data-native-panel=") == 2
    assert (
        drawer_result["snapshots"]["default"] != drawer_result["snapshots"]["alternate"]
    )


@pytest.mark.parametrize(
    "dimension", ["units", "context", "element", "symmetry", "taphonomics", "native_id"]
)
def test_same_taxon_qualifiers_survive_producer_decoder_display_and_export(
    tmp_path: Path, dimension: str
) -> None:
    provenance_cases: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {
        "symmetry": ({"symmetry": "radial"}, {"symmetry": "bilateral"}),
        "taphonomics": ({"taphonomics": None}, {"taphonomics": "corroded"}),
        "units": ({}, {}),
        "context": ({}, {}),
        "element": ({}, {}),
    }
    provenance = provenance_cases.get(dimension)
    snapshot, tabs, _, datums = projected(
        tmp_path, dimension, native_provenance=provenance
    )
    original = deepcopy(tabs)
    output = observe(tabs)
    records = exported(tabs)["pollen_observations"]["records"]
    assert output["unchanged"] is True and tabs == original
    assert len(snapshot["variables"]) == 1
    assert {row["variable_id"] for row in records} == {"neotoma:variable:1947"}
    assert {row["observation_id"] for row in records} == {
        row["observation_id"] for row in snapshot["observations"]
    }
    expected = {
        row["value"]: {
            **{
                key: row[key]
                for key in ("variableid", "symmetry", "taphonomics", "variablename")
                if key in row
            },
            "source_reported_name_status": "reported"
            if "variablename" in row
            else "not_provided_by_source",
        }
        for row in datums
    }
    assert {
        row["source_value"]: row["source_variable_provenance"] for row in records
    } == expected
    assert output["data"]["total"] == 2 and len(output["data"]["groups"]) == 2
    assert "taxon-derived variable key" in output["html"]
    assert "complete native variable identity" in output["html"]
    assert "Exact native source group" not in output["html"]


def test_older_compact_document_renders_without_inventing_native_identity(
    tmp_path: Path,
) -> None:
    _, tabs, _, _ = projected(tmp_path, "native_id")
    table = tabs["pollen_composition"]
    index = table["fields"].index("source_variable_provenance")
    table["fields"].pop(index)
    for row in table["records"]:
        row.pop(index)
    original = deepcopy(tabs)
    output = observe(tabs)
    records = exported(tabs)["pollen_observations"]["records"]
    assert output["data"]["status"] == "available"
    assert output["data"]["total"] == 2 and len(output["data"]["groups"]) == 1
    group = output["data"]["groups"][0]
    assert len(group["identity"]) == 11
    assert group["key"] == json.dumps(group["identity"], separators=(",", ":"))
    assert observe(tabs, group["key"])["data"]["status"] == "available"
    assert {row["source_value"] for row in records} == {2, 3}
    assert all("source_variable_provenance" not in row for row in records)
    assert "not available in this document" in output["html"]
    assert "Exact native source group" not in output["html"]
    assert output["unchanged"] is True and tabs == original


@pytest.mark.parametrize(
    "native_provenance",
    [
        ({}, {}),
        ({}, {"variableid": None}),
        ({"variableid": None}, {"variableid": "null"}),
        ({"variableid": True}, {"variableid": 1}),
        ({"symmetry": ["unknown", None]}, {"symmetry": {"reported": "unknown"}}),
        (
            {"variableid": "<img src=x onerror=alert(1)>"},
            {"taphonomics": {"source": "<script>literal</script>"}},
        ),
    ],
)
def test_missing_null_and_unknown_native_values_roundtrip_without_coercion(
    tmp_path: Path, native_provenance: tuple[dict[str, Any], dict[str, Any]]
) -> None:
    _, tabs, _, datums = projected(
        tmp_path, "native_id", native_provenance=native_provenance
    )
    records = exported(tabs)["pollen_observations"]["records"]
    expected = {
        row["value"]: {
            **{
                key: row[key]
                for key in ("variableid", "symmetry", "taphonomics", "variablename")
                if key in row
            },
            "source_reported_name_status": "reported"
            if "variablename" in row
            else "not_provided_by_source",
        }
        for row in datums
    }
    assert {
        row["source_value"]: row["source_variable_provenance"] for row in records
    } == expected
    assert json.dumps(
        {row["source_value"]: row["source_variable_provenance"] for row in records},
        sort_keys=True,
    ) == json.dumps(expected, sort_keys=True)
    output = observe(tabs)
    expected_groups = len(
        {json.dumps(row, sort_keys=True) for row in native_provenance}
    )
    assert len(output["data"]["groups"]) == expected_groups
    assert "<img" not in output["html"] and "<script>" not in output["html"]
    assert output["unchanged"] is True


@pytest.mark.parametrize(
    "dimension,panels", [("native_id", 2), ("symmetry", 1), ("taphonomics", 1)]
)
def test_compatible_panels_allow_native_ids_to_differ_and_keep_modifiers_separate(
    tmp_path: Path, dimension: str, panels: int
) -> None:
    _, tabs, _, _ = projected(tmp_path, dimension)
    output = run_node_json(
        multiples_script()
        + "const tabs="
        + json.dumps(tabs)
        + ";const source=pollenObservationDiagramData(tabs);"
        + "console.log(JSON.stringify(pollenSmallMultiplesData(tabs,source.groups[0].key)));"
    )
    assert len(output["panels"]) == panels
    assert output["nativeTotal"] == 2


def test_charcoal_drawer_labels_derived_key_and_literal_native_provenance(
    tmp_path: Path,
) -> None:
    _, tabs, layers, _ = projected(tmp_path, "symmetry", charcoal=True)
    layer = next(
        row for row in layers if row["key"] == "neotoma-native-charcoal-context"
    )
    assert len(layer["features"]) == 2
    feature = layer["features"][0]
    native_details = (
        Path(template.__file__).parent / "assets/source-record-details.js"
    ).read_text()
    output = run_node_json(
        diagram_script()
        + native_details
        + "const tabs="
        + json.dumps(tabs)
        + ";const feature="
        + json.dumps(feature)
        + ";const result=nativeCharcoalSourceSignal(tabs,feature);console.log(JSON.stringify("
        + "{result,html:renderNativeCharcoalObservation(tabs,feature,result)}));"
    )
    assert output["result"]["status"] == "matched"
    assert "Taxon-derived variable key" in output["html"]
    assert "Native variable ID" not in output["html"]
    assert "Source-reported variable provenance" in output["html"]
    assert output["result"]["observation"]["source_variable_provenance"][
        "variableid"
    ] in (501, 502)


def test_generated_four_country_service_preserves_existing_runtime_byte_limit(
    atlas_catalogue: Callable[..., tuple[Path, str, dict[str, Any]]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The real publisher keeps new provenance display within its existing cap."""
    from bijux_pollenomics.reporting import service
    from bijux_pollenomics.reporting.bundles import atlas_bundle
    from bijux_pollenomics.reporting.map_document import render
    from bijux_pollenomics.reporting.map_document.source_resources import (
        AtlasResourceCatalogueInput,
    )
    from bijux_pollenomics.reporting.map_document.static_assets import (
        ATLAS_DOCUMENT_MAX_BYTES,
    )

    root, digest, _ = atlas_catalogue()
    countries = ("Denmark", "Finland", "Norway", "Sweden")
    monkeypatch.setattr(
        service, "build_homo_sapiens_runtime_manifest_for_version_dir", lambda _: None
    )
    monkeypatch.setattr(
        service,
        "load_multi_country_map_inputs",
        lambda **_: SimpleNamespace(
            country_sample_counts=dict.fromkeys(countries, 0), all_samples=()
        ),
    )
    monkeypatch.setattr(service, "build_context_layers", lambda **_: ([], [], []))
    monkeypatch.setattr(atlas_bundle, "build_sweden_lake_atlas_layers", lambda **_: [])
    measured: list[int] = []
    bounded = render._runtime_resources

    def observe(*args: Any, **kwargs: Any) -> None:
        measured.append(args[1])
        bounded(*args, **kwargs)

    monkeypatch.setattr(render, "_runtime_resources", observe)
    output = tmp_path / "published"
    report = service.generate_multi_country_map(
        tmp_path / "v66",
        countries,
        output,
        "Metadata context",
        "nordic",
        source_resource_catalogue=AtlasResourceCatalogueInput(root, digest),
    )
    assert report.total_unique_samples == 0
    assert len(measured) == 1 and 0 < measured[0] <= ATLAS_DOCUMENT_MAX_BYTES
    assert (output / "nordic_map.html").is_file()
    contract = json.loads(
        next(output.glob("*map_publication_contract.json")).read_bytes()
    )
    assert contract["source_resources"]["record_count"] == 4
    assert contract["source_resources"]["numerical_atlas_denominator_changed"] is False
