"""Project native ownership and chronology independently of a target-name policy."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from copy import deepcopy
from typing import Any

from ...physical_forward.inputs import require
from ..regional_source_support import (
    WINDOWS,
    aggregate,
    finite,
    integer,
    mapping,
    objects,
    pollen_mass,
)


def selected_age(
    sample: dict[str, Any], chronology: dict[str, Any]
) -> tuple[str, dict[str, Any] | None]:
    """Select the named point without requiring or inventing uncertainty bounds."""
    matches = [
        row
        for row in objects(sample["ages"])
        if type(row.get("chronologyid")) is int
        and row["chronologyid"] == chronology["selected_id"]
    ]
    if not matches:
        return "missing_selected_age", None
    if len(matches) != 1:
        return "duplicate_selected_age", None
    selected = deepcopy(matches[0])
    if (
        selected.get("chronologyname") != chronology["selected_name"]
        or selected.get("agetype") != chronology["selected_native_type"]
    ):
        return "incompatible_selected_age_type_or_name", selected
    if not finite(selected.get("age")) or any(
        selected.get(key) is not None and not finite(selected[key])
        for key in ("ageyounger", "ageolder")
    ):
        return "invalid_selected_age_value", selected
    if (
        selected.get("ageyounger") is not None
        and selected["ageyounger"] > selected["age"]
    ) or (
        selected.get("ageolder") is not None and selected["ageolder"] < selected["age"]
    ):
        return "conflicting_selected_age_bounds", selected
    return "selected_typed_point", selected


def sample_account(
    sample: dict[str, Any],
    index: int,
    chronology: dict[str, Any],
    panel_projector: Callable[[list[dict[str, Any]]], dict[str, Any]],
) -> dict[str, Any]:
    datum = objects(sample["datum"])
    status, selected = selected_age(sample, chronology)
    window = None
    if status != "selected_typed_point":
        disposition = "unassignable_selected_age"
    else:
        assert selected is not None
        matches = [
            list(edge) for edge in WINDOWS if edge[0] <= selected["age"] < edge[1]
        ]
        require(len(matches) <= 1, "Overlapping declared source windows")
        window = matches[0] if matches else None
        disposition = (
            "negative_native_age_retained"
            if selected["age"] < 0
            else "in_requested_window"
            if window
            else "outside_requested_windows"
        )
    panel, mass = panel_projector(datum), pollen_mass(datum)
    panel_n, pollen_n = panel["panel_N"], mass["pollen_N"]
    require(
        panel_n is None or pollen_n is None or 0 <= panel_n <= pollen_n,
        "Literal panel exceeds complete pollen denominator",
    )
    return {
        "native_sample_index": index,
        "sample_id": sample["sampleid"],
        "analysisunit_id": sample.get("analysisunitid"),
        "native_depth": sample.get("depth"),
        "native_thickness": sample.get("thickness"),
        "native_ages": deepcopy(sample["ages"]),
        "selected_age": selected,
        "selected_age_status": status,
        "age_disposition": disposition,
        "window": window,
        **panel,
        **mass,
        "excluded_pollen_N": pollen_n - panel_n
        if pollen_n is not None and panel_n is not None
        else None,
    }


def project(
    source: dict[str, Any],
    core: dict[str, Any],
    protocol: dict[str, Any],
    *,
    panel_projector: Callable[[list[dict[str, Any]]], dict[str, Any]],
    schema_version: str,
    status: str,
    require_alternative_reference: bool = False,
    exact_default_flags: bool = False,
    panel_state_key: str = "literal_taxon_state_counts",
) -> dict[str, Any]:
    """Project every owner under an explicit core-specific chronology contract."""
    identity, chronology = mapping(core["identity"]), mapping(core["chronology"])
    require(
        all(
            integer(identity.get(key)) and identity[key] > 0
            for key in (
                "site_id",
                "dataset_id",
                "collection_unit_id",
                "source_sample_count",
            )
        )
        and integer(chronology.get("selected_id"))
        and integer(chronology.get("native_collection_default_reference"))
        and (
            not require_alternative_reference
            or chronology["selected_id"]
            != chronology["native_collection_default_reference"]
        )
        and chronology["selected_native_type"] == "Calibrated radiocarbon years BP"
        and type(chronology["reference_epoch_ad"]) is int
        and chronology["reference_epoch_ad"] == 1950,
        "Explicit native ownership/calibrated-point chronology required",
    )
    sites = [mapping(row["site"]) for row in objects(source["rows"])]
    selected = [
        site
        for site in sites
        if mapping(site["dataset"]).get("datasetid") == identity["dataset_id"]
    ]
    require(len(selected) == 1, "One exact selected native dataset required")
    site = selected[0]
    unit = mapping(site["collectionunit"])
    dataset, outer = mapping(unit["dataset"]), mapping(site["dataset"])
    require(
        all(
            type(container.get(field)) is int and container[field] == expected
            for container, field, expected in (
                (site, "siteid", identity["site_id"]),
                (unit, "collectionunitid", identity["collection_unit_id"]),
                (outer, "datasetid", identity["dataset_id"]),
                (dataset, "datasetid", identity["dataset_id"]),
                (
                    unit,
                    "defaultchronology",
                    chronology["native_collection_default_reference"],
                ),
            )
        )
        and unit.get("handle") == identity["handle"]
        and dataset.get("datasettype") == "pollen",
        "Native nested site/unit/dataset/default identity differs",
    )
    declarations = [mapping(row["chronology"]) for row in objects(unit["chronologies"])]
    require(
        all(integer(row.get("chronologyid")) for row in declarations)
        and len({row["chronologyid"] for row in declarations}) == len(declarations),
        "Ambiguous native chronology declaration IDs",
    )
    chosen = [
        row for row in declarations if row["chronologyid"] == chronology["selected_id"]
    ]
    require(len(chosen) == 1, "Explicit selected chronology declaration missing")
    flags = {
        str(row["chronologyid"]): mapping(row["chronology"]).get("isdefault")
        for row in declarations
    }
    require(
        (
            not exact_default_flags
            or set(flags) == set(chronology["source_default_flags"])
        )
        and all(
            type(value) is bool and flags.get(key) is value
            for key, value in chronology["source_default_flags"].items()
        ),
        "Literal native default assertions differ",
    )
    metadata = mapping(chosen[0]["chronology"])
    require(
        metadata.get("chronologyname") == chronology["selected_name"]
        and metadata.get("modelagetype") == chronology["selected_native_type"],
        "Selected chronology native name/type differs",
    )
    native = objects(dataset["samples"])
    ids = [row.get("sampleid") for row in native]
    require(
        len(native) == identity["source_sample_count"]
        and all(integer(value) for value in ids)
        and len(set(ids)) == len(ids),
        "Complete unique native sample-owner population required",
    )
    samples = [
        sample_account(row, index, chronology, panel_projector)
        for index, row in enumerate(native)
    ]
    unassignable = [
        row["sample_id"]
        for row in samples
        if row["age_disposition"] == "unassignable_selected_age"
    ]
    windows = [
        {
            "window": list(edge),
            **aggregate(
                [row for row in samples if row["window"] == list(edge)], unassignable
            ),
        }
        for edge in WINDOWS
    ]
    totals = aggregate(samples, [])
    totals["known_valid_pollen_cell_sum"] = sum(
        row["known_valid_pollen_cell_sum"] for row in samples
    )
    return {
        "schema_version": schema_version,
        "status": status,
        "key": core["key"],
        "source": deepcopy(core["source"]),
        "identity": deepcopy(identity),
        "native_source_metadata": {
            "site_metadata": deepcopy(
                {
                    key: value
                    for key, value in site.items()
                    if key not in {"collectionunit", "dataset"}
                }
            ),
            "collection_unit_metadata": deepcopy(
                {
                    key: value
                    for key, value in unit.items()
                    if key not in {"dataset", "chronologies"}
                }
            ),
            "dataset_metadata": deepcopy(
                {key: value for key, value in dataset.items() if key != "samples"}
            ),
            "outer_dataset_metadata": deepcopy(outer),
        },
        "chronology": {
            "selected_chronology_id": chronology["selected_id"],
            "selected_native_metadata": deepcopy(metadata),
            "native_collection_default_reference": unit["defaultchronology"],
            "source_chronology_declarations": [
                {
                    "chronology_id": row["chronologyid"],
                    "native_metadata": deepcopy(mapping(row["chronology"])),
                }
                for row in declarations
            ],
            "native_chronology_declarations": deepcopy(unit["chronologies"]),
            "reference_epoch_ad": chronology["reference_epoch_ad"],
            "selection_policy": "explicit_selected_chronology_not_generic_default",
        },
        "samples": samples,
        "windows": windows,
        "population": {
            "samples": len(samples),
            "age_disposition_counts": dict(
                Counter(row["age_disposition"] for row in samples)
            ),
            "selected_age_status_counts": dict(
                Counter(row["selected_age_status"] for row in samples)
            ),
            "panel_complete_samples": sum(row["panel_complete"] for row in samples),
            "full_mass_complete_samples": sum(
                row["pollen_denominator_status"] == "complete" for row in samples
            ),
        },
        "source_totals": totals,
        "support_summary": {
            "supported_windows": sum(row["status"] == "supported" for row in windows),
            "window_status_counts": dict(Counter(row["status"] for row in windows)),
            panel_state_key: dict(
                Counter(taxon["status"] for row in samples for taxon in row["taxa"])
            ),
            "datum_status_counts": dict(
                sum((Counter(row["datum_status_counts"]) for row in samples), Counter())
            ),
        },
        "engine_calls": 0,
        "model_fits": 0,
        "source_acquisition": False,
        "scientific_or_field_admission": False,
        "scope": protocol["scope"],
        "suppression_semantics": protocol["suppression_semantics"],
        "rights_and_attribution": protocol["rights_and_attribution"],
    }
