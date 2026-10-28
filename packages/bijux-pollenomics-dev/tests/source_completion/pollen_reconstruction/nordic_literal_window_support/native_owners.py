"""Bind native owners and explicitly named ages without a generic default selector."""

from __future__ import annotations

from typing import Any

from tests.source_completion.pollen_reconstruction.krageholm_regional_source_support.native_rows import (
    full_pollen_mass,
    literal_axes,
    rows,
    source_integer,
    source_number,
)


def require(condition: object, message: str) -> None:
    if not condition:
        raise ValueError("Independent Nordic literal support: " + message)


def native_owner(
    source: dict[str, Any], core: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    identity, policy = core["identity"], core["chronology"]
    candidates = []
    for wrapper in rows(source["rows"]):
        site = wrapper.get("site")
        require(type(site) is dict, "native site object")
        assert isinstance(site, dict)
        outer, unit = site.get("dataset"), site.get("collectionunit")
        require(type(outer) is dict, "native outer dataset object")
        assert isinstance(outer, dict)
        inner = unit.get("dataset") if type(unit) is dict else None
        if outer.get("datasetid") == identity["dataset_id"] or (
            type(inner) is dict and inner.get("datasetid") == identity["dataset_id"]
        ):
            candidates.append(site)
    require(len(candidates) == 1, "unique native dataset ownership")
    site = candidates[0]
    unit = site.get("collectionunit")
    require(
        type(unit) is dict and type(unit.get("dataset")) is dict, "native unit dataset"
    )
    assert isinstance(unit, dict)
    dataset = unit["dataset"]
    actual_ids = [
        site.get("siteid"),
        site["dataset"].get("datasetid"),
        unit.get("collectionunitid"),
        dataset.get("datasetid"),
    ]
    require(
        all(type(x) is int for x in actual_ids)
        and actual_ids
        == [
            identity["site_id"],
            identity["dataset_id"],
            identity["collection_unit_id"],
            identity["dataset_id"],
        ]
        and unit.get("handle") == identity["handle"]
        and dataset.get("datasettype") == "pollen",
        "exact source site/unit/dataset/handle",
    )
    require(
        type(unit.get("defaultchronology")) is int
        and unit["defaultchronology"] == policy["native_collection_default_reference"],
        "collection default reference is separate from selected chronology",
    )
    native_declarations = rows(unit["chronologies"])
    declarations = []
    for wrapper in native_declarations:
        declaration = wrapper.get("chronology")
        require(
            type(declaration) is dict
            and type(declaration.get("chronologyid")) is int
            and type(declaration.get("chronology")) is dict,
            "native chronology declaration wrapper",
        )
        assert isinstance(declaration, dict)
        declarations.append(declaration)
    ids = [r["chronologyid"] for r in declarations]
    require(len(ids) == len(set(ids)), "unique chronology declarations")
    metadata = {r["chronologyid"]: r["chronology"] for r in declarations}
    for identifier, flag in policy["source_default_flags"].items():
        require(
            type(flag) is bool
            and int(identifier) in metadata
            and type(metadata[int(identifier)].get("isdefault")) is bool
            and metadata[int(identifier)]["isdefault"] is flag,
            "literal source isdefault flag",
        )
    selected_id = policy["selected_id"]
    require(
        type(selected_id) is int and selected_id in metadata,
        "explicit selected chronology declaration",
    )
    selected = metadata[selected_id]
    require(
        selected.get("chronologyname") == policy["selected_name"]
        and selected.get("modelagetype")
        == policy["selected_native_type"]
        == "Calibrated radiocarbon years BP"
        and policy["reference_epoch_ad"] == 1950,
        "named source calibrated point chronology",
    )
    samples = rows(dataset["samples"])
    owners = [sample.get("sampleid") for sample in samples]
    require(
        type(identity["source_sample_count"]) is int
        and len(samples) == identity["source_sample_count"]
        and all(source_integer(x) for x in owners)
        and len(set(owners)) == len(owners),
        "all unique native sample owners in source order",
    )
    chronology = {
        "selected_chronology_id": selected_id,
        "selected_native_metadata": selected,
        "native_collection_default_reference": unit["defaultchronology"],
        "source_chronology_declarations": [
            {"chronology_id": r["chronologyid"], "native_metadata": r["chronology"]}
            for r in declarations
        ],
        "native_chronology_declarations": native_declarations,
        "reference_epoch_ad": 1950,
        "selection_policy": "explicit_selected_chronology_not_generic_default",
    }
    native_metadata = {
        "site_metadata": {
            k: v for k, v in site.items() if k not in ("dataset", "collectionunit")
        },
        "collection_unit_metadata": {
            k: v for k, v in unit.items() if k not in ("dataset", "chronologies")
        },
        "dataset_metadata": {k: v for k, v in dataset.items() if k != "samples"},
        "outer_dataset_metadata": site["dataset"],
    }
    return chronology, native_metadata, samples


def selected_age(
    claims: list[dict[str, Any]], core: dict[str, Any]
) -> tuple[str, dict[str, Any] | None]:
    policy = core["chronology"]
    selected = [
        r
        for r in claims
        if type(r.get("chronologyid")) is int
        and r["chronologyid"] == policy["selected_id"]
    ]
    if len(selected) != 1:
        return (
            "missing_selected_age" if not selected else "duplicate_selected_age"
        ), None
    claim = selected[0]
    if (
        claim.get("chronologyname") != policy["selected_name"]
        or claim.get("agetype") != policy["selected_native_type"]
    ):
        return "incompatible_selected_age_type_or_name", claim
    point = source_number(claim.get("age"))
    if point is None or any(
        claim[key] is not None and source_number(claim[key]) is None
        for key in ("ageyounger", "ageolder")
        if key in claim
    ):
        return "invalid_selected_age_value", claim
    lo, hi = (
        source_number(claim.get("ageyounger")),
        source_number(claim.get("ageolder")),
    )
    if (lo is not None and lo > point) or (hi is not None and hi < point):
        return "conflicting_selected_age_bounds", claim
    return "selected_typed_point", claim


def sample_account(
    source: dict[str, Any], index: int, core: dict[str, Any], windows: list[list[int]]
) -> dict[str, Any]:
    datum, ages = rows(source["datum"]), rows(source["ages"])
    status, selected = selected_age(ages, core)
    window = None
    if status != "selected_typed_point":
        disposition = "unassignable_selected_age"
    else:
        assert selected is not None
        point = source_number(selected["age"])
        assert point is not None
        window = next((pair for pair in windows if pair[0] <= point < pair[1]), None)
        disposition = (
            "negative_native_age_retained"
            if point < 0
            else "in_requested_window"
            if window is not None
            else "outside_requested_windows"
        )
    panel, mass = literal_axes(datum), full_pollen_mass(datum)
    p, n = panel["panel_N"], mass["pollen_N"]
    require(
        p is None or n is None or p <= n,
        "panel cannot exceed complete literal full mass",
    )
    return {
        "native_sample_index": index,
        "sample_id": source["sampleid"],
        "analysisunit_id": source.get("analysisunitid"),
        "native_depth": source.get("depth"),
        "native_thickness": source.get("thickness"),
        "native_ages": ages,
        "selected_age": selected,
        "selected_age_status": status,
        "age_disposition": disposition,
        "window": window,
        **panel,
        **mass,
        "excluded_pollen_N": None if p is None or n is None else n - p,
    }
