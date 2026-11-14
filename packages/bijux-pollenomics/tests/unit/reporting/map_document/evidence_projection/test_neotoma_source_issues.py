"""Retained source issues remain distinct from observed pollen measurements."""

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
    neotoma as projection,
)
from bijux_pollenomics.reporting.map_document.evidence_projection.neotoma_chronology import (
    chronology_model_tables,
)
from bijux_pollenomics.reporting.map_document.evidence_projection.neotoma_source_issues import (
    LoadedSurfaces,
    source_issue_tables,
)
from tests.support.neotoma import country_decisions, download_row
from tests.support.neotoma.relational_shapes import nested, rows


def source_with_specimens() -> dict[str, object]:
    source = download_row()
    models = rows(nested(source, "site", "collectionunit")["chronologies"])
    first = nested(models[0], "chronology")
    control = rows(first["chroncontrols"])[0]
    control["geochron"] = {"geochronid": 101, "geochronage": 1100}
    other = deepcopy(control)
    nested(other, "geochron").update({"geochronid": 102, "geochronage": 1300})
    first["chroncontrols"] = [control, other, {"chroncontrolid": None, "depth": None}]
    return source


def decoded(table: dict[str, Any]) -> list[dict[str, Any]]:
    return [dict(zip(table["fields"], row, strict=True)) for row in table["records"]]


def test_orphan_only_control_issue_does_not_claim_retained_variants() -> None:
    control_id = "neotoma:chronology:301:7001:control:8001"
    control = {
        "chronology_control_id": control_id,
        "source_chronology_control_id": 8001,
        "chronology_id": "neotoma:chronology:301:7001",
        "collection_unit_id": "neotoma:collection-unit:301",
        "site_id": "neotoma:site:20",
        "source_payload": {"chroncontrolid": 8001, "depth": None},
    }
    orphan = {
        "orphan_id": "neotoma:orphan:control-issue",
        "entity_type": "chronology_control",
        "parent_id": control_id,
        "reason": "missing_source_identifier",
        "source_value": None,
    }
    loaded: LoadedSurfaces = {
        "chronology_controls": ([control], (1,)),
        "orphans": ([orphan], (1,)),
        "conflicts": ([], ()),
    }
    issues, _, index, coverage = source_issue_tables(
        loaded, {"neotoma:site:20"}, {"neotoma:site:20"}
    )
    tables = chronology_model_tables(
        loaded,
        {"neotoma:site:20"},
        source_issues_by_subject=index,
        control_variant_ids_by_site=coverage,
    )
    row = decoded(cast(dict[str, Any], tables["neotoma:site:20"]["controls"]))[0]
    assert row["source_issue_ids"] == [orphan["orphan_id"]]
    assert (
        cast(dict[str, Any], issues["neotoma:site:20"]["chronology_control_variants"])[
            "record_count"
        ]
        == 0
    )
    assert row["source_payload_posture"] == "retained_source_control_payload"


def test_control_owner_disagreement_is_not_classified_as_specimen_multiplicity() -> (
    None
):
    source = source_with_specimens()
    snapshot = build_neotoma_relational_snapshot(
        [source], source_snapshot_id="fixture-source", build_id="fixture-build"
    )
    conflict = rows(snapshot["conflicts"])[0]
    detail = cast(dict[str, Any], conflict["detail"])
    detail["variants"][1]["collection_unit_id"] = "neotoma:collection-unit:other"
    tables, _, _, _ = source_issue_tables(
        {"conflicts": ([conflict], (1,))}, {"neotoma:site:20"}, {"neotoma:site:20"}
    )
    table = cast(dict[str, Any], tables["neotoma:site:20"]["conflicts"])
    assert decoded(table)[0]["review_status"] == "unresolved_control_payload_conflict"


def test_unlocated_issue_remains_in_explicit_source_partition() -> None:
    orphan = {
        "orphan_id": "neotoma:orphan:unknown-owner",
        "entity_type": "site",
        "parent_id": None,
        "reason": "missing_source_identifier",
        "source_value": None,
    }
    tables, accounting, _, _ = source_issue_tables(
        {"orphans": ([orphan], (3,))}, {"neotoma:site:20"}, {"neotoma:site:20"}
    )
    assert accounting["unresolved_site_issue_ids"] == [orphan["orphan_id"]]
    retained = cast(list[dict[str, Any]], accounting["unresolved_site_records"])[0]
    assert retained["source_record"] == orphan
    assert retained["source_locator"] == (
        "surfaces/orphans/part-00003.json#orphan_id=neotoma:orphan:unknown-owner"
    )
    assert (
        cast(dict[str, Any], tables["neotoma:site:20"]["orphans"])["record_count"] == 0
    )
    assert tables["neotoma:site:20"]["conflicts"] == {
        "status": "unavailable",
        "reason_code": "neotoma_conflicts_surface_not_available",
    }


def test_issue_from_excluded_site_preserves_reason_and_source_locator() -> None:
    orphan = {
        "orphan_id": "neotoma:orphan:unassigned-site",
        "entity_type": "chronology",
        "parent_id": "neotoma:collection-unit:301",
        "reason": "missing_source_identifier",
        "source_value": None,
    }
    _, account, _, _ = source_issue_tables(
        {
            "collection_units": (
                [
                    {
                        "collection_unit_id": "neotoma:collection-unit:301",
                        "site_id": "neotoma:site:20",
                    }
                ],
                (1,),
            ),
            "orphans": ([orphan], (1,)),
        },
        {"neotoma:site:20"},
        set(),
    )
    entry = cast(list[dict[str, Any]], account["excluded_site_records"])[0]
    assert entry["source_record"] == orphan
    assert entry["site_ids"] == ["neotoma:site:20"]
    assert entry["reason_code"] == "site_without_governed_country_assignment"
    assert entry["source_locator"].endswith("#orphan_id=neotoma:orphan:unassigned-site")


def test_each_geochron_specimen_and_unknown_control_survives_current_projection(
    tmp_path: Path,
) -> None:
    source = source_with_specimens()
    original = deepcopy(source)
    snapshot = build_neotoma_relational_snapshot(
        [source],
        source_snapshot_id="sha256:" + "c" * 64,
        build_id="sha256:" + "b" * 64,
        country_by_site_id=country_decisions([source]),
    )
    (tmp_path / "neotoma").mkdir()
    materialize_neotoma_relational_snapshot(
        tmp_path / "neotoma/relational", snapshot, rows_per_part=1
    )
    records, accounting, _ = projection._project_neotoma(
        tmp_path, {"features": [{"evidence_row_id": "20"}]}
    )
    tabs = cast(dict[str, Any], records[0]["tabs"])
    issues = tabs["chronology"]["source_issues"]
    conflict = decoded(issues["conflicts"])[0]
    orphan = decoded(issues["orphans"])[0]
    variants = decoded(issues["chronology_control_variants"])
    native_conflict = rows(snapshot["conflicts"])[0]
    native_orphan = rows(snapshot["orphans"])[0]
    native_variants = cast(dict[str, Any], native_conflict["detail"])["variants"]
    assert source == original
    assert conflict["source_record"] == native_conflict
    assert orphan["source_record"] == native_orphan
    assert (
        conflict["review_status"] == "confirmed_source_geochron_specimen_multiplicity"
    )
    assert {
        v["source_record"]["source_payload"]["geochron"]["geochronid"] for v in variants
    } == {101, 102}
    assert [v["source_record"] for v in variants] == native_variants
    assert [v["source_locator"] for v in variants] == [
        f"surfaces/conflicts/part-00001.json#conflict_id={native_conflict['conflict_id']}/detail/variants/{i}"
        for i in range(2)
    ]
    assert (
        orphan["source_locator"]
        == f"surfaces/orphans/part-00001.json#orphan_id={native_orphan['orphan_id']}"
    )
    issue_account = cast(dict[str, Any], accounting["source_issues"])
    assert issue_account["source_counts"] == {
        "conflicts": 1,
        "orphans": 1,
        "chronology_control_variants": 2,
    }
    assert issue_account["unresolved_site_issue_ids"] == []
    controls = decoded(tabs["chronology"]["controls"])
    postures = {
        row["source_chronology_control_id"]: row["source_payload_posture"]
        for row in controls
    }
    assert postures == {
        8001: "retained_canonical_variant_with_all_variants_in_source_issues",
        None: "retained_source_control_payload",
    }
    assert tabs["pollen_composition"]["record_count"] == 2
