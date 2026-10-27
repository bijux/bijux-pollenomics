"""Reconcile native owners and exact source/window sums independently."""

from __future__ import annotations

from typing import Any

from .native_rows import (
    AGE_NAME,
    AGE_TYPE,
    TAXA,
    WINDOWS,
    require,
    rows,
    sample_row,
    source_integer,
)

IDENTITY = {
    "site_id": 3204,
    "dataset_id": 23013,
    "collection_unit_id": 16622,
    "handle": "KRAGMJNY",
    "source_sample_count": 96,
}


def frequencies(values: list[str]) -> dict[str, int]:
    return {value: values.count(value) for value in dict.fromkeys(values)}


def group_mass(members: list[dict[str, Any]], unassigned: list[int]) -> dict[str, Any]:
    panel_available = (
        bool(members)
        and not unassigned
        and all(member["panel_complete"] for member in members)
    )
    full_available = (
        bool(members)
        and not unassigned
        and all(member["pollen_N"] is not None for member in members)
    )
    panel = (
        [sum(member["panel_counts"][i] for member in members) for i in (0, 1)]
        if panel_available
        else None
    )
    total_panel = sum(panel) if panel is not None else None
    total_source = (
        sum(member["pollen_N"] for member in members) if full_available else None
    )
    if unassigned:
        status = "suppressed_unassignable_age"
    elif not members:
        status = "empty_window"
    elif panel is None:
        status = "suppressed_incomplete_panel"
    elif total_panel == 0:
        status = "suppressed_zero_panel"
    elif total_source is None:
        status = "suppressed_full_mass"
    else:
        status = "supported"
    return {
        "sample_ids": [member["sample_id"] for member in members],
        "member_count": len(members),
        "unassignable_source_sample_ids": unassigned,
        "status": status,
        "panel_counts": panel,
        "panel_N": total_panel,
        "pollen_N": total_source,
        "excluded_pollen_N": None
        if total_panel is None or total_source is None
        else total_source - total_panel,
    }


def native_owner(source: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    candidates: list[dict[str, Any]] = []
    for row in rows(source["rows"]):
        site = row.get("site")
        require(type(site) is dict, "native site object required")
        assert isinstance(site, dict)
        outer = site.get("dataset")
        unit = site.get("collectionunit")
        require(type(outer) is dict, "native dataset ownership object required")
        assert isinstance(outer, dict)
        inner = unit.get("dataset") if type(unit) is dict else None
        if outer.get("datasetid") == 23013 or (
            type(inner) is dict and inner.get("datasetid") == 23013
        ):
            candidates.append(site)
    require(len(candidates) == 1, "one unambiguous native dataset owner required")
    site = candidates[0]
    require(
        type(site.get("collectionunit")) is dict
        and type(site["collectionunit"].get("dataset")) is dict,
        "selected native collection-unit dataset required",
    )
    unit, dataset = site["collectionunit"], site["collectionunit"]["dataset"]
    actual = [
        site.get("siteid"),
        site["dataset"].get("datasetid"),
        unit.get("collectionunitid"),
        dataset.get("datasetid"),
    ]
    require(
        all(type(value) is int for value in actual)
        and actual == [3204, 23013, 16622, 23013]
        and unit.get("handle") == "KRAGMJNY"
        and dataset.get("datasettype") == "pollen",
        "native site/unit/dataset identity differs",
    )
    require(
        type(unit.get("defaultchronology")) is int
        and unit["defaultchronology"] == 13365,
        "native collection reference must remain 13365",
    )
    declarations: list[dict[str, Any]] = []
    for row in rows(unit["chronologies"]):
        declaration = row.get("chronology")
        require(
            type(declaration) is dict
            and type(declaration.get("chronologyid")) is int
            and type(declaration.get("chronology")) is dict,
            "native chronology declaration required",
        )
        assert isinstance(declaration, dict)
        declarations.append(declaration)
    ids = [row["chronologyid"] for row in declarations]
    require(len(set(ids)) == len(ids), "duplicate chronology declaration")
    by_id = {row["chronologyid"]: row["chronology"] for row in declarations}
    require(
        13366 in by_id
        and 13365 in by_id
        and by_id[13365].get("isdefault") is True
        and by_id[13366].get("isdefault") is True,
        "both source default flags must remain true",
    )
    selected = by_id[13366]
    require(
        selected.get("chronologyname") == AGE_NAME
        and selected.get("modelagetype") == AGE_TYPE,
        "selected calibrated MADCAP metadata differs",
    )
    chronology = {
        "selected_chronology_id": 13366,
        "selected_native_metadata": selected,
        "native_collection_default_reference": 13365,
        "source_chronology_declarations": [
            {"chronology_id": row["chronologyid"], "native_metadata": row["chronology"]}
            for row in declarations
        ],
        "reference_epoch_ad": 1950,
        "selection_policy": "explicit_selected_chronology_not_generic_default",
    }
    samples = rows(dataset["samples"])
    ids = [sample.get("sampleid") for sample in samples]
    require(
        len(samples) == 96
        and all(source_integer(value) for value in ids)
        and len(set(ids)) == 96,
        "all 96 unique integer native sample owners required",
    )
    return chronology, samples


def expected_result(source: dict[str, Any], protocol: dict[str, Any]) -> dict[str, Any]:
    require(
        protocol["schema_version"] == "krageholm-regional-literal-panel-protocol.v1"
        and protocol["identity"] == IDENTITY
        and protocol["taxa"]
        == [{"label": label, "taxon_id": identity} for label, identity in TAXA]
        and protocol["windows"] == [list(window) for window in WINDOWS],
        "prospective identity/panel/window contract differs",
    )
    require(
        protocol["chronology"]
        == {
            "selected_id": 13366,
            "selected_name": AGE_NAME,
            "selected_native_type": AGE_TYPE,
            "reference_epoch_ad": 1950,
            "native_collection_default_reference": 13365,
            "source_default_flags": {"13365": True, "13366": True},
        },
        "prospective chronology contract differs",
    )
    chronology, owners = native_owner(source)
    samples = [sample_row(sample, index) for index, sample in enumerate(owners)]
    unassigned = [
        sample["sample_id"]
        for sample in samples
        if sample["age_disposition"] == "unassignable_selected_age"
    ]
    windows = [
        {
            "window": list(window),
            **group_mass(
                [sample for sample in samples if sample["window"] == list(window)],
                unassigned,
            ),
        }
        for window in WINDOWS
    ]
    totals = group_mass(samples, [])
    totals["known_valid_pollen_cell_sum"] = sum(
        sample["known_valid_pollen_cell_sum"] for sample in samples
    )
    datum_states: dict[str, int] = {}
    for sample in samples:
        for state, count in sample["datum_status_counts"].items():
            if count:
                datum_states[state] = datum_states.get(state, 0) + count
    return {
        "schema_version": "krageholm-regional-source-support.v1",
        "status": "literal_source_support_accounted",
        "source": protocol["source"],
        "identity": dict(IDENTITY),
        "chronology": chronology,
        "samples": samples,
        "windows": windows,
        "population": {
            "samples": 96,
            "age_disposition_counts": frequencies(
                [row["age_disposition"] for row in samples]
            ),
            "selected_age_status_counts": frequencies(
                [row["selected_age_status"] for row in samples]
            ),
            "panel_complete_samples": sum(row["panel_complete"] for row in samples),
            "full_mass_complete_samples": sum(
                row["pollen_N"] is not None for row in samples
            ),
        },
        "source_totals": totals,
        "support_summary": {
            "supported_windows": sum(row["status"] == "supported" for row in windows),
            "window_status_counts": frequencies([row["status"] for row in windows]),
            "literal_taxon_state_counts": frequencies(
                [axis["status"] for row in samples for axis in row["taxa"]]
            ),
            "datum_status_counts": datum_states,
        },
        "engine_calls": 0,
        "model_fits": 0,
        "source_acquisition": False,
        "scientific_or_field_admission": False,
        **{
            key: protocol[key]
            for key in ("scope", "suppression_semantics", "rights_and_attribution")
        },
    }
