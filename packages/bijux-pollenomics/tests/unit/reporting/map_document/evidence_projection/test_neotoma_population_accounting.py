"""Published source details reconcile separately from country-excluded rows."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, cast

from bijux_pollenomics.collection.sources.neotoma.materialization import (
    materialize_neotoma_relational_snapshot,
)
from bijux_pollenomics.collection.sources.neotoma.relational import (
    build_neotoma_relational_snapshot,
)
from bijux_pollenomics.reporting.map_document.evidence_projection import (
    build_map_evidence_projection,
)
from bijux_pollenomics.reporting.map_document.evidence_projection.neotoma import (
    _project_neotoma,
)
from tests.support.neotoma import country_decisions, download_row, set_row_identity
from tests.support.neotoma.relational_shapes import nested, rows


def test_literal_charcoal_registration_preserves_native_union_and_pollen_admission(
    tmp_path: Path,
) -> None:
    admitted, excluded = download_row(), download_row()
    set_row_identity(excluded, 40)
    for source, values in ((admitted, (0, None)), (excluded, (7,))):
        sample = rows(nested(source, "site", "collectionunit", "dataset")["samples"])[0]
        observations = rows(sample["datum"])
        if source is admitted:
            observations[0]["value"] = 3
        observations.extend(
            {
                **deepcopy(observations[0]),
                "taxonid": 8001,
                "variablename": "Charcoal",
                "taxongroup": "Charcoal",
                "ecologicalgroup": "CHAR",
                "element": ">25 µm",
                "elementtype": ">25 µm",
                "value": value,
            }
            for value in values
        )
        sample["datum"] = observations
    original = deepcopy((admitted, excluded))
    snapshot = build_neotoma_relational_snapshot(
        [admitted, excluded],
        source_snapshot_id="sha256:" + "c" * 64,
        build_id="sha256:" + "b" * 64,
        country_by_site_id=country_decisions([admitted]),
    )
    (tmp_path / "neotoma").mkdir()
    materialize_neotoma_relational_snapshot(
        tmp_path / "neotoma/relational",
        snapshot,
        rows_per_part=1,
    )
    parent_url = "https://example.test/source/site/20"
    projection = build_map_evidence_projection(
        tmp_path,
        [
            {
                "key": "neotoma-pollen",
                "features": [{"evidence_row_id": "20", "source_url": parent_url}],
            }
        ],
    )
    layer = next(
        (
            row
            for row in projection.point_layers
            if row["key"] == "neotoma-native-charcoal-context"
        ),
        None,
    )
    assert layer is not None, (
        "authenticated native CHAR observations have no independent context layer"
    )
    assert layer["default_enabled"] is False and layer["count"] == 2
    features = cast(list[dict[str, Any]], layer["features"])
    assert len({row["observation_id"] for row in features}) == 2
    assert {row["source_value"] for row in features} == {0, None}
    assert all(
        row["source_unit"] == "NISP" and row["source_denominator"] is None
        for row in features
    )
    assert all(
        row["record_id"] == "neotoma:site:20" and row["source_url"] == parent_url
        for row in features
    )
    assert all(len(row["source_age_claim_ids"]) == 2 for row in features)
    assert all(
        row["observation_id"] in row["source_observation_locator"] for row in features
    )
    accounting = cast(dict[str, Any], projection.reconciliation["sources"])["neotoma"]
    charcoal = accounting["native_charcoal"]
    assert charcoal["native_charcoal_observation_count"] == 3
    assert charcoal["published_observation_count"] == 2
    assert charcoal["excluded_observation_count"] == 1
    assert charcoal["excluded_reason_counts"] == {"site_outside_projection": 1}
    assert charcoal["scientific_event_count"] == 0
    assert accounting["source_chronology"]["eligible_observation_denominator"] == 1
    assert (
        sum(
            cast(int, row["count"])
            for row in projection.point_layers
            if row["semantic_role"] == "source_chronology_context"
        )
        == 3
    )
    assert len(projection.detail_records) == 1
    assert (admitted, excluded) == original


def test_country_excluded_rows_are_denominators_not_published_details(
    tmp_path: Path,
) -> None:
    admitted = download_row()
    excluded = download_row()
    set_row_identity(excluded, 40)
    sample = rows(nested(excluded, "site", "collectionunit", "dataset")["samples"])[0]
    observations = rows(sample["datum"])
    observations.append(
        {**deepcopy(observations[0]), "taxonid": 9999, "variablename": "Excluded taxon"}
    )
    sample["datum"] = observations
    snapshot = build_neotoma_relational_snapshot(
        [admitted, excluded],
        source_snapshot_id="sha256:" + "c" * 64,
        build_id="sha256:" + "b" * 64,
        country_by_site_id=country_decisions([admitted]),
    )
    (tmp_path / "neotoma").mkdir()
    materialize_neotoma_relational_snapshot(
        tmp_path / "neotoma/relational", snapshot, rows_per_part=1
    )

    records, raw_accounting, _ = _project_neotoma(
        tmp_path, {"features": [{"evidence_row_id": "20"}]}
    )
    accounting = cast(dict[str, Any], raw_accounting)
    assert [record["record_id"] for record in records] == ["neotoma:site:20"]
    assert accounting["excluded_unassigned_site_ids"] == ["neotoma:site:40"]
    assert accounting["detail_row_counts"] == {
        "collection_units": 1,
        "datasets": 1,
        "samples": 1,
        "age_claims": 2,
        "observations": 2,
        "variables": 2,
        "chronologies": 2,
        "chronology_controls": 1,
    }
    assert accounting["detail_row_denominators"] == {
        "collection_units": 2,
        "datasets": 2,
        "samples": 2,
        "age_claims": 4,
        "observations": 5,
        "variables": 3,
        "chronologies": 4,
        "chronology_controls": 2,
    }
    assert accounting["excluded_detail_row_counts"] == {
        "collection_units": 1,
        "datasets": 1,
        "samples": 1,
        "age_claims": 2,
        "observations": 3,
        "variables": 1,
        "chronologies": 2,
        "chronology_controls": 1,
    }
    assert accounting["detail_row_exclusion_reason_code"] == (
        "site_without_governed_country_assignment"
    )
    assert accounting["variable_count_semantics"] == (
        "unique_variable_ids; excluded_counts_include_only_ids_absent_from_projected_sites"
    )
    for name, denominator in accounting["detail_row_denominators"].items():
        assert denominator == (
            accounting["detail_row_counts"][name]
            + accounting["excluded_detail_row_counts"][name]
        )
