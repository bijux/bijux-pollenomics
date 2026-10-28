"""Independent native ownership and selected-point chronology, without defaults."""

from __future__ import annotations

from typing import Any

from tests.source_completion.pollen_reconstruction.krageholm_regional_source_support.native_rows import (
    count_value,
    full_pollen_mass,
    pollen_metadata,
    rows,
    source_integer,
    source_number,
)


def require(condition: object, message: str) -> None:
    if not condition:
        raise ValueError("Independent author-window support: " + message)


def native_owner(
    source: dict[str, Any], core: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    identity, policy = core["identity"], core["chronology"]
    candidates = []
    for wrapper in rows(source["rows"]):
        site = wrapper.get("site")
        require(
            type(site) is dict and type(site.get("dataset")) is dict,
            "native site and outer dataset",
        )
        assert isinstance(site, dict)
        unit = site.get("collectionunit")
        inner = unit.get("dataset") if type(unit) is dict else None
        if site["dataset"].get("datasetid") == identity["dataset_id"] or (
            type(inner) is dict and inner.get("datasetid") == identity["dataset_id"]
        ):
            candidates.append(site)
    require(len(candidates) == 1, "unique selected native dataset")
    site = candidates[0]
    unit = site.get("collectionunit")
    require(
        type(unit) is dict and type(unit.get("dataset")) is dict,
        "native collection dataset",
    )
    assert isinstance(unit, dict)
    dataset = unit["dataset"]
    ids = [
        site.get("siteid"),
        site["dataset"].get("datasetid"),
        unit.get("collectionunitid"),
        dataset.get("datasetid"),
        unit.get("defaultchronology"),
    ]
    require(
        all(type(value) is int for value in ids)
        and ids
        == [
            identity["site_id"],
            identity["dataset_id"],
            identity["collection_unit_id"],
            identity["dataset_id"],
            policy["native_collection_default_reference"],
        ]
        and unit.get("handle") == identity["handle"]
        and dataset.get("datasettype") == "pollen",
        "typed native ownership and collection reference",
    )
    declarations = []
    for wrapper in rows(unit["chronologies"]):
        value = wrapper.get("chronology")
        require(
            type(value) is dict
            and type(value.get("chronologyid")) is int
            and type(value.get("chronology")) is dict,
            "typed chronology wrapper",
        )
        assert isinstance(value, dict)
        declarations.append(value)
    codes = [row["chronologyid"] for row in declarations]
    require(len(set(codes)) == len(codes), "unique chronology declarations")
    declared = {row["chronologyid"]: row["chronology"] for row in declarations}
    require(
        {str(code) for code in declared} == set(policy["source_default_flags"]),
        "complete declared chronology flag population",
    )
    for code, flag in policy["source_default_flags"].items():
        require(
            type(flag) is bool
            and int(code) in declared
            and type(declared[int(code)].get("isdefault")) is bool
            and declared[int(code)]["isdefault"] is flag,
            "literal source default flags",
        )
    chosen = policy["selected_id"]
    require(
        type(chosen) is int and chosen in declared,
        "explicit selected chronology declaration",
    )
    selected = declared[chosen]
    require(
        selected.get("chronologyname") == policy["selected_name"]
        and selected.get("modelagetype")
        == policy["selected_native_type"]
        == "Calibrated radiocarbon years BP"
        and type(policy["reference_epoch_ad"]) is int
        and policy["reference_epoch_ad"] == 1950,
        "named calibrated chronology and reference epoch",
    )
    owners = rows(dataset["samples"])
    owner_ids = [row.get("sampleid") for row in owners]
    require(
        type(identity["source_sample_count"]) is int
        and len(owners) == identity["source_sample_count"]
        and all(source_integer(value) for value in owner_ids)
        and len(set(owner_ids)) == len(owner_ids),
        "complete ordered unique sample owners",
    )
    return (
        {
            "selected_chronology_id": chosen,
            "selected_native_metadata": selected,
            "native_collection_default_reference": unit["defaultchronology"],
            "source_chronology_declarations": [
                {
                    "chronology_id": row["chronologyid"],
                    "native_metadata": row["chronology"],
                }
                for row in declarations
            ],
            "native_chronology_declarations": unit["chronologies"],
            "reference_epoch_ad": 1950,
            "selection_policy": "explicit_selected_chronology_not_generic_default",
        },
        {
            "site_metadata": {
                key: value
                for key, value in site.items()
                if key not in {"collectionunit", "dataset"}
            },
            "collection_unit_metadata": {
                key: value
                for key, value in unit.items()
                if key not in {"dataset", "chronologies"}
            },
            "dataset_metadata": {
                key: value for key, value in dataset.items() if key != "samples"
            },
            "outer_dataset_metadata": site["dataset"],
        },
        owners,
    )


def selected_age(
    ages: list[dict[str, Any]], core: dict[str, Any]
) -> tuple[str, dict[str, Any] | None]:
    policy = core["chronology"]
    selected = [
        age
        for age in ages
        if type(age.get("chronologyid")) is int
        and age["chronologyid"] == policy["selected_id"]
    ]
    if len(selected) != 1:
        return (
            "missing_selected_age" if not selected else "duplicate_selected_age"
        ), None
    age = selected[0]
    if (
        age.get("chronologyname") != policy["selected_name"]
        or age.get("agetype") != policy["selected_native_type"]
    ):
        return "incompatible_selected_age_type_or_name", age
    point = source_number(age.get("age"))
    if point is None or any(
        age[key] is not None and source_number(age[key]) is None
        for key in ("ageyounger", "ageolder")
        if key in age
    ):
        return "invalid_selected_age_value", age
    low, high = source_number(age.get("ageyounger")), source_number(age.get("ageolder"))
    if (low is not None and low > point) or (high is not None and high < point):
        return "conflicting_selected_age_bounds", age
    return "selected_typed_point", age


def author_panel(
    datum: list[dict[str, Any]],
    core: dict[str, Any],
    lookup: dict[str, list[dict[str, Any]]],
    excluded: list[str],
) -> dict[str, Any]:
    axes = core["native_axes"]
    accounting = []
    for index, cell in enumerate(datum):
        name = cell.get("variablename")
        mapping_rows = lookup.get(name, []) if isinstance(name, str) else []
        target = mapping_rows[0]["author_target"] if mapping_rows else None
        pollen = cell.get("element") == "pollen" or cell.get("elementtype") == "pollen"
        if pollen and target in {axis["author_target"] for axis in axes}:
            require(
                any(
                    cell.get("taxonid") == axis["taxon_id"]
                    or cell.get("variablename") == axis["source_name"]
                    for axis in axes
                ),
                "unexpected additional selected-author concept",
            )
        accounting.append(
            {
                "datum_index": index,
                "native": cell,
                "count_state": count_value(cell),
                "author_target": target,
                "lookup_row_numbers": [row["row_number"] for row in mapping_rows],
                "disposition": "non_pollen"
                if not pollen
                else "selected_author_target"
                if target in {axis["author_target"] for axis in axes}
                else "author_excluded_target"
                if target in excluded
                else "other_author_target"
                if target is not None
                else "unmapped_native_name",
            }
        )
    taxa, values = [], []
    for axis in axes:
        # A declared different element is not another pollen measurement. Unknown
        # or contradictory roles remain candidates and cannot evade refusal.
        matches = [
            (index, cell)
            for index, cell in enumerate(datum)
            if (
                cell.get("taxonid") == axis["taxon_id"]
                or cell.get("variablename") == axis["source_name"]
            )
            and not (
                type(cell.get("element")) is str
                and bool(cell["element"].strip())
                and cell["element"] == cell.get("elementtype")
                and cell["element"] != "pollen"
            )
        ]
        value = None
        if not matches:
            state = "missing_native_axis"
        elif len(matches) != 1:
            state = "duplicate_native_axis"
        elif (
            not source_integer(matches[0][1].get("taxonid"))
            or matches[0][1]["taxonid"] != axis["taxon_id"]
            or matches[0][1].get("variablename") != axis["source_name"]
        ):
            state = "id_label_conflict"
        elif not pollen_metadata(matches[0][1]):
            state = "incompatible_metadata"
        else:
            state = count_value(matches[0][1])
            if state in {"measured", "measured_zero"}:
                value = matches[0][1]["value"]
        require(
            axis["source_name"] in lookup
            and {row["author_target"] for row in lookup[axis["source_name"]]}
            == {axis["author_target"]},
            "exact required author mapping",
        )
        taxa.append(
            {
                **axis,
                "status": state,
                "native_matches": [
                    {"datum_index": index, "native": cell} for index, cell in matches
                ],
                "lookup_rows": lookup[axis["source_name"]],
            }
        )
        values.append(value)
    complete = all(value is not None for value in values)
    return {
        "taxa": taxa,
        "panel_counts": values,
        "panel_complete": complete,
        "panel_N": sum(values) if complete else None,
        "datum_accounting": accounting,
    }


def sample_account(
    owner: dict[str, Any],
    index: int,
    core: dict[str, Any],
    protocol: dict[str, Any],
    lookup: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    ages, datum = rows(owner["ages"]), rows(owner["datum"])
    state, age = selected_age(ages, core)
    window = None
    if state != "selected_typed_point":
        disposition = "unassignable_selected_age"
    else:
        assert age is not None
        point = source_number(age["age"])
        assert point is not None
        window = next(
            (pair for pair in protocol["windows"] if pair[0] <= point < pair[1]), None
        )
        disposition = (
            "negative_native_age_retained"
            if point < 0
            else "in_requested_window"
            if window is not None
            else "outside_requested_windows"
        )
    panel, mass = (
        author_panel(
            datum, core, lookup, protocol["author_lookup_contract"]["excluded_targets"]
        ),
        full_pollen_mass(datum),
    )
    p, n = panel["panel_N"], mass["pollen_N"]
    require(p is None or n is None or p <= n, "panel/full-mass closure")
    return {
        "native_sample_index": index,
        "sample_id": owner["sampleid"],
        "analysisunit_id": owner.get("analysisunitid"),
        "native_depth": owner.get("depth"),
        "native_thickness": owner.get("thickness"),
        "native_ages": ages,
        "selected_age": age,
        "selected_age_status": state,
        "age_disposition": disposition,
        "window": window,
        **panel,
        **mass,
        "excluded_pollen_N": None if p is None or n is None else n - p,
    }
