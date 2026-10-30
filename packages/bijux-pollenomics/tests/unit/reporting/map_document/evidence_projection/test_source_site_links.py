"""Derived source context inherits its existing parent site page, never a new URL."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, cast

import pytest

from bijux_pollenomics.collection.exports.context_points import (
    write_context_points_geojson,
)
from bijux_pollenomics.collection.sources.neotoma.context_points import (
    normalize_neotoma_rows,
)
from bijux_pollenomics.collection.sources.neotoma.materialization import (
    materialize_neotoma_relational_snapshot,
)
from bijux_pollenomics.collection.sources.neotoma.relational import (
    build_neotoma_relational_snapshot,
)
from bijux_pollenomics.reporting.context.points.external import (
    build_external_point_layer,
)
from bijux_pollenomics.reporting.map_document.evidence_projection import (
    build_map_evidence_projection,
)
from tests.support.neotoma import (
    country_boundaries,
    country_decisions,
    download_row,
    set_row_identity,
)
from tests.support.neotoma.relational_shapes import nested, rows


@pytest.fixture
def source(tmp_path: Path) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    first, second = download_row(), download_row()
    set_row_identity(second, 21)
    downloads = [first, second]
    for row in downloads:
        sample = rows(nested(row, "site", "collectionunit", "dataset")["samples"])[0]
        rows(sample["datum"])[0]["value"] = 3
    unchanged = deepcopy(downloads)
    snapshot = build_neotoma_relational_snapshot(
        downloads,
        source_snapshot_id="sha256:" + "c" * 64,
        build_id="sha256:" + "b" * 64,
        country_by_site_id=country_decisions(downloads),
    )
    (tmp_path / "neotoma").mkdir()
    materialize_neotoma_relational_snapshot(tmp_path / "neotoma/relational", snapshot)
    points = normalize_neotoma_rows(
        [nested(row, "site") for row in downloads],
        (0, 0, 2, 2),
        country_boundaries(),
    )
    geojson_path = tmp_path / "parent-sites.geojson"
    write_context_points_geojson(geojson_path, points)
    layer = build_external_point_layer(json.loads(geojson_path.read_text()))
    assert downloads == unchanged
    assert len(cast(list[object], layer["features"])) == 2
    return tmp_path, cast(dict[str, Any], layer), cast(dict[str, Any], snapshot)


def derived(projection: Any) -> list[dict[str, Any]]:
    return [
        feature for layer in projection.point_layers for feature in layer["features"]
    ]


def test_three_native_node_levels_inherit_only_their_exact_parent_site_link(
    source: tuple[Path, dict[str, Any], dict[str, Any]],
) -> None:
    root, layer, snapshot = source
    parent_urls = {
        f"neotoma:site:{feature['evidence_row_id']}": feature["source_url"]
        for feature in layer["features"]
    }
    assert len(set(parent_urls.values())) == 2
    assert all("/explorer/#/record/site/" in url for url in parent_urls.values())
    before = deepcopy((layer, snapshot))
    projection = build_map_evidence_projection(root, [layer])
    features = derived(projection)
    assert len(features) == 6
    assert {feature["node_level"] for feature in features} == {
        "source_sample_presence",
        "source_ecological_code",
        "source_taxon",
    }
    for feature in features:
        assert feature["source_url"] == parent_urls[feature["record_id"]]
        assert feature["propagation_eligible"] is False
        assert "downloads/" not in feature["source_url"]
    for original, annotated in zip(
        before[0]["features"], layer["features"], strict=True
    ):
        assert annotated == original | {
            "record_id": f"neotoma:site:{original['evidence_row_id']}"
        }
    assert snapshot == before[1]


@pytest.mark.parametrize("missing", ["absent", None, "", "   "])
def test_missing_parent_link_stays_unavailable_without_cross_site_fallback(
    source: tuple[Path, dict[str, Any], dict[str, Any]], missing: str | None
) -> None:
    root, layer, _ = source
    parent = layer["features"][0]
    missing_id = f"neotoma:site:{parent['evidence_row_id']}"
    if missing == "absent":
        del parent["source_url"]
    else:
        parent["source_url"] = missing
    projection = build_map_evidence_projection(root, [layer])
    features = derived(projection)
    assert len([row for row in features if row["record_id"] == missing_id]) == 3
    assert all(
        "source_url" not in row for row in features if row["record_id"] == missing_id
    )
    assert all(
        row.get("source_url") for row in features if row["record_id"] != missing_id
    )


def test_existing_parent_url_bytes_are_not_normalized_or_reconstructed(
    source: tuple[Path, dict[str, Any], dict[str, Any]],
) -> None:
    root, layer, _ = source
    original = layer["features"][0]["source_url"]
    supplied = original + "?SourceCase=Native%2fValue&item=0"
    layer["features"][0]["source_url"] = supplied
    identity = f"neotoma:site:{layer['features'][0]['evidence_row_id']}"
    projection = build_map_evidence_projection(root, [layer])
    assert all(
        row["source_url"] == supplied
        for row in derived(projection)
        if row["record_id"] == identity
    )
    assert layer["features"][0]["source_url"] == supplied


def test_source_links_do_not_change_scientific_fields_details_or_accounting(
    source: tuple[Path, dict[str, Any], dict[str, Any]],
) -> None:
    root, layer, snapshot = source
    no_links = deepcopy(layer)
    for feature in no_links["features"]:
        del feature["source_url"]
    before = deepcopy(snapshot)
    linked = build_map_evidence_projection(root, [layer])
    plain = build_map_evidence_projection(root, [no_links])
    assert [
        {key: value for key, value in row.items() if key != "source_url"}
        for row in derived(linked)
    ] == derived(plain)
    assert linked.detail_records == plain.detail_records
    assert linked.reconciliation == plain.reconciliation
    assert snapshot == before
