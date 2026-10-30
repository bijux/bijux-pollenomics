"""Source model/control custody survives compact projection and the real drawer."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, cast

import pytest

from bijux_pollenomics.collection.sources.neotoma.materialization import (
    materialize_neotoma_relational_snapshot,
)
from bijux_pollenomics.collection.sources.neotoma.relational import (
    build_neotoma_relational_snapshot,
)
from bijux_pollenomics.reporting.map_document.evidence_projection import (
    neotoma as projection,
)
from tests.support.neotoma import country_decisions, download_row
from tests.support.neotoma.relational_shapes import nested, rows

from ..browser_semantics.chronology.test_age_depth_diagram import (
    diagram_script,
    render_drawer,
)
from ..browser_semantics.support import run_node_json
from .fixtures.neotoma import _neotoma_fixture


def native_source(*, age_claims: bool = True) -> dict[str, object]:
    source = download_row()
    unit = nested(source, "site", "collectionunit")
    model = nested(rows(unit["chronologies"])[0], "chronology")
    nested(model, "chronology").update(
        {"chronologyname": '<img src=x onerror="bad">', "isdefault": False}
    )
    controls = rows(model["chroncontrols"])
    controls[0].update({"chroncontrolage": 0, "ageunits": None, "depthunits": "mm"})
    controls.append(
        {"chroncontrolid": None, "chroncontrolage": None, "comment": "<control>"}
    )
    model["chroncontrols"] = controls
    if not age_claims:
        sample = rows(nested(unit, "dataset")["samples"])[0]
        sample["ages"] = []
    return source


def materialized(
    root: Path, source: dict[str, object]
) -> tuple[dict[str, Any], dict[str, Any]]:
    snapshot = build_neotoma_relational_snapshot(
        [source],
        source_snapshot_id="sha256:" + "c" * 64,
        build_id="sha256:" + "b" * 64,
        country_by_site_id=country_decisions([source]),
    )
    (root / "neotoma").mkdir()
    materialize_neotoma_relational_snapshot(
        root / "neotoma/relational", snapshot, rows_per_part=1
    )
    records, accounting, _ = projection._project_neotoma(
        root, {"features": [{"evidence_row_id": "20"}]}
    )
    return cast(dict[str, Any], records[0]["tabs"]), cast(dict[str, Any], accounting)


def decoded_models(tabs: dict[str, Any]) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        run_node_json(
            diagram_script()
            + "const tabs="
            + json.dumps(tabs)
            + ";const original=JSON.stringify(tabs);const c=tabs.chronology;"
            + "console.log(JSON.stringify({models:c.models.records.map(r=>decodeDetailTableRow(c.models,r)),controls:c.controls.records.map(r=>decodeDetailTableRow(c.controls,r)),ages:c.records.map(r=>decodeDetailTableRow(c,r)),unchanged:original===JSON.stringify(tabs)}));"
        ),
    )


def test_native_producer_to_decoder_and_drawer_preserves_models_and_controls(
    tmp_path: Path,
) -> None:
    source = native_source()
    original = deepcopy(source)
    tabs, accounting = materialized(tmp_path, source)
    assert source == original
    decoded = decoded_models(tabs)
    assert decoded["unchanged"]
    first, second = decoded["models"]
    assert first["chronology_id"] == "neotoma:chronology:301:7001"
    assert first["source_chronology_id"] == 7001
    assert first["collection_unit_id"] == "neotoma:collection-unit:301"
    assert first["selected_by_collection_unit_reference"] is True
    assert first["source_is_default_assertion"] is False
    assert second["selected_by_collection_unit_reference"] is False
    assert second["source_is_default_assertion"] is True
    for part_number, (projected, native) in enumerate(
        zip(
            decoded["models"],
            rows(nested(source, "site", "collectionunit")["chronologies"]),
            strict=True,
        ),
        start=1,
    ):
        raw = nested(native, "chronology")
        assert projected["source_payload"] == {
            key: value for key, value in raw.items() if key != "chroncontrols"
        }
        assert projected["source_part_number"] == part_number
    by_native_id = {
        row["source_chronology_control_id"]: row for row in decoded["controls"]
    }
    assert set(by_native_id) == {8001, None}
    for part_number, row in enumerate(decoded["controls"], start=1):
        assert row["chronology_id"] == first["chronology_id"]
        assert row["collection_unit_id"] == first["collection_unit_id"]
        assert row["source_part_number"] == part_number
        assert row["chronology_control_id"].startswith(
            first["chronology_id"] + ":control:"
        )
    assert by_native_id[8001]["source_payload"]["chroncontrolage"] == 0
    assert by_native_id[8001]["source_payload"]["ageunits"] is None
    assert by_native_id[8001]["source_payload"]["depthunits"] == "mm"
    assert by_native_id[None]["source_payload"] == {
        "chroncontrolid": None,
        "chroncontrolage": None,
        "comment": "<control>",
    }
    assert len(decoded["ages"]) == 2
    assert accounting["detail_row_counts"]["chronologies"] == 2
    assert accounting["detail_row_counts"]["chronology_controls"] == 2
    assert tabs["chronology"]["models"]["source_locator_contract"] == (
        "surfaces/chronologies/part-{source_part_number:05d}.json#chronology_id={chronology_id}"
    )
    output = render_drawer(tabs)
    assert output["unchanged"]
    html = str(output["html"])
    assert 'data-detail-table-page="chronology.models"' in html
    assert 'data-detail-table-page="chronology.controls"' in html
    assert "neotoma:chronology:301:7001" in html
    assert (
        "source is default assertion" in html
        and "selected by collection unit reference" in html
    )
    assert "neither selects an analysis chronology" in html
    assert "&lt;img" in html and "&lt;control&gt;" in html and "<img" not in html


def test_source_models_without_sample_age_claims_remain_visible(tmp_path: Path) -> None:
    tabs, accounting = materialized(tmp_path, native_source(age_claims=False))
    chronology = tabs["chronology"]
    assert chronology["record_count"] == 0
    assert chronology["age_assignments"] == {
        "status": "unavailable",
        "reason_code": "neotoma_site_age_claims_not_available",
    }
    assert chronology["models"]["record_count"] == 2
    assert chronology["controls"]["record_count"] == 2
    assert accounting["detail_row_counts"]["age_claims"] == 0
    output = render_drawer(tabs)
    assert cast(dict[str, object], output["data"])["groups"] == []
    assert "neotoma:chronology:301:7001" in str(output["html"])
    assert "neotoma_site_age_claims_not_available" in str(output["html"])


def test_authenticated_empty_models_are_zero_not_unavailable(tmp_path: Path) -> None:
    source = native_source(age_claims=False)
    nested(source, "site", "collectionunit").update(
        {"chronologies": [], "defaultchronology": None}
    )
    tabs, accounting = materialized(tmp_path, source)
    for name in ("models", "controls"):
        assert tabs["chronology"][name]["record_count"] == 0
        assert tabs["chronology"][name]["records"] == []
        assert "status" not in tabs["chronology"][name]
    assert accounting["detail_row_counts"]["chronologies"] == 0
    assert accounting["detail_row_counts"]["chronology_controls"] == 0


def test_legacy_missing_surfaces_leave_age_table_and_explicit_metadata_absence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _neotoma_fixture(tmp_path, monkeypatch)
    records, accounting, _ = projection._project_neotoma(
        tmp_path, {"features": [{"evidence_row_id": "10"}]}
    )
    tabs = cast(dict[str, Any], records[0]["tabs"])
    chronology = tabs["chronology"]
    assert chronology["record_count"] == 1
    assert chronology["models"] == {
        "status": "unavailable",
        "reason_code": "neotoma_chronologies_surface_not_available",
    }
    assert chronology["controls"] == {
        "status": "unavailable",
        "reason_code": "neotoma_chronology_controls_surface_not_available",
    }
    assert "chronologies" not in cast(
        dict[str, object], accounting["detail_row_counts"]
    )
    assert render_drawer(tabs)["unchanged"]


@pytest.mark.parametrize("surface", ["chronologies", "chronology_controls"])
def test_changed_model_or_control_bytes_are_refused_before_projection(
    tmp_path: Path, surface: str
) -> None:
    materialized(tmp_path, native_source())
    root = tmp_path / "neotoma/relational"
    manifest = json.loads((root / "manifest.json").read_text())
    path = root / manifest["surfaces"][surface]["parts"][0]["path"]
    body = json.loads(path.read_text())
    body["rows"][0]["source_payload"]["changed"] = True
    path.write_text(json.dumps(body))
    with pytest.raises(ValueError, match="digest|SHA-256"):
        projection._project_neotoma(tmp_path, {"features": [{"evidence_row_id": "20"}]})
