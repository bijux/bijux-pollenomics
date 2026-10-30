"""Classify source cells and selected age claims by separate literal predicates."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
import math
from typing import Any

TAXA = (("Betula", 29), ("Ulmus", 310))
WINDOWS = tuple((low, low + 500) for low in range(2700, 5700, 500))
AGE_NAME = "Giesecke et al. 2014 (MADCAP)"
AGE_TYPE = "Calibrated radiocarbon years BP"


def require(condition: object, message: str) -> None:
    """Raise a literal-source refusal when a required condition fails."""
    if not condition:
        raise ValueError("Independent KRAG source support: " + message)


def rows(value: Any) -> list[dict[str, Any]]:
    """Read a list of native objects without coercing row types."""
    require(
        type(value) is list and all(type(row) is dict for row in value),
        "native object array required",
    )
    return list(value)


def source_integer(value: object) -> bool:
    """Identify nonnegative integer counts while excluding booleans."""
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def source_number(value: object) -> int | float | None:
    """Match native age binary64 semantics without coercing count tokens."""
    if type(value) not in (int, float, Decimal):
        return None
    assert isinstance(value, int | float | Decimal)
    try:
        number = float(value)
    except (OverflowError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return value if type(value) is int else number


def count_value(row: dict[str, Any]) -> str:
    """Classify native count presence, type, zero and positive values."""
    if "value" not in row:
        return "missing_native_value"
    if row["value"] is None:
        return "null_native_value"
    if not source_integer(row["value"]):
        return "invalid_count"
    return "measured_zero" if row["value"] == 0 else "measured"


def pollen_metadata(row: dict[str, Any]) -> bool:
    """Check literal pollen metadata and an explicitly null context."""
    return (
        all(
            row.get(key) == value
            for key, value in (
                ("element", "pollen"),
                ("elementtype", "pollen"),
                ("units", "NISP"),
            )
        )
        and "context" in row
        and row["context"] is None
    )


def literal_axes(datum: list[dict[str, Any]]) -> dict[str, Any]:
    """Account independently for the two named taxon axes and their counts."""
    axes = []
    values: list[int | None] = []
    for label, identifier in TAXA:
        positions = [
            i
            for i, cell in enumerate(datum)
            if cell.get("variablename") == label or cell.get("taxonid") == identifier
        ]
        labelled = [i for i in positions if datum[i].get("variablename") == label]
        value = None
        if not labelled:
            state = "missing_literal" if not positions else "id_label_conflict"
        elif len(labelled) > 1:
            state = "duplicate_literal"
        elif (
            len(positions) > 1
            or not source_integer(datum[labelled[0]].get("taxonid"))
            or datum[labelled[0]]["taxonid"] != identifier
        ):
            state = "id_label_conflict"
        elif not pollen_metadata(datum[labelled[0]]):
            state = "incompatible_metadata"
        else:
            state = count_value(datum[labelled[0]])
            if state.startswith("measured"):
                value = datum[labelled[0]]["value"]
        values.append(value)
        axes.append(
            {
                "label": label,
                "taxon_id": identifier,
                "status": state,
                "native_matches": [
                    {"datum_index": i, "native": datum[i]} for i in positions
                ],
            }
        )
    complete = None not in values
    total = sum(value for value in values if value is not None) if complete else None
    return {
        "taxa": axes,
        "panel_counts": values,
        "panel_complete": complete,
        "panel_N": total,
    }


def full_pollen_mass(datum: list[dict[str, Any]]) -> dict[str, Any]:
    """Retain all pollen cells and refuse invalid or duplicate denominator rows."""
    candidates = {
        i
        for i, cell in enumerate(datum)
        if "pollen" in (cell.get("element"), cell.get("elementtype"))
    }
    ids: dict[int, list[int]] = defaultdict(list)
    names: dict[str, list[int]] = defaultdict(list)
    for i in sorted(candidates):
        cell = datum[i]
        if source_integer(cell.get("taxonid")):
            ids[cell["taxonid"]].append(i)
        if type(cell.get("variablename")) is str:
            names[cell["variablename"]].append(i)
    states: dict[str, int] = {}
    problems = []
    known = 0
    for i in sorted(candidates):
        cell = datum[i]
        identity = (
            source_integer(cell.get("taxonid"))
            and type(cell.get("variablename")) is str
            and bool(cell["variablename"])
        )
        metadata, value = pollen_metadata(cell), count_value(cell)
        measured = value in ("measured", "measured_zero")
        if identity and metadata and measured:
            known += cell["value"]
        if not identity:
            state = "invalid_native_identity"
        elif not metadata:
            state = "incompatible_metadata"
        elif not measured:
            state = value
        elif len(ids[cell["taxonid"]]) > 1 or len(names[cell["variablename"]]) > 1:
            state = "duplicate_pollen_identity"
        else:
            state = "valid_pollen_NISP"
        states[state] = states.get(state, 0) + 1
        if state != "valid_pollen_NISP":
            problems.append({"datum_index": i, "status": state, "native": cell})
    outside = len(datum) - len(candidates)
    states["non_pollen"] = outside
    complete = bool(candidates) and len(problems) == 0
    return {
        "datum_row_count": len(datum),
        "datum_status_counts": states,
        "pollen_row_count": len(candidates),
        "non_pollen_row_count": outside,
        "known_valid_pollen_cell_sum": known,
        "pollen_denominator_status": "complete"
        if complete
        else "refused_invalid_or_duplicate_pollen_rows",
        "pollen_N": known if complete else None,
        "pollen_problems": problems,
    }


def age_selection(claims: list[dict[str, Any]]) -> tuple[str, dict[str, Any] | None]:
    """Inspect only the selected chronology and preserve unresolved age states."""
    named = [
        claim
        for claim in claims
        if type(claim.get("chronologyid")) is int and claim["chronologyid"] == 13366
    ]
    if len(named) != 1:
        return ("missing_selected_age" if not named else "duplicate_selected_age"), None
    selected = named[0]
    if (selected.get("agetype"), selected.get("chronologyname")) != (
        AGE_TYPE,
        AGE_NAME,
    ):
        return "incompatible_selected_age_type_or_name", selected
    point = source_number(selected.get("age"))
    if point is None or any(
        key not in selected
        or (selected[key] is not None and source_number(selected[key]) is None)
        for key in ("ageyounger", "ageolder")
    ):
        return "invalid_selected_age_value", selected
    lower = (
        source_number(selected["ageyounger"])
        if selected["ageyounger"] is not None
        else None
    )
    upper = (
        source_number(selected["ageolder"])
        if selected["ageolder"] is not None
        else None
    )
    if (lower is not None and lower > point) or (upper is not None and upper < point):
        return "conflicting_selected_age_bounds", selected
    return "selected_typed_point", selected


def sample_row(source: dict[str, Any], index: int) -> dict[str, Any]:
    """Build an independent sample account with selected-age window membership."""
    datum, ages = rows(source["datum"]), rows(source["ages"])
    state, selected = age_selection(ages)
    window = None
    if state != "selected_typed_point":
        disposition = "unassignable_selected_age"
    else:
        assert selected is not None
        value = source_number(selected["age"])
        assert value is not None
        window = next(([lo, hi] for lo, hi in WINDOWS if lo <= value < hi), None)
        disposition = (
            "negative_native_age_retained"
            if value < 0
            else "in_requested_window"
            if window is not None
            else "outside_requested_windows"
        )
    panel, mass = literal_axes(datum), full_pollen_mass(datum)
    p, n = panel["panel_N"], mass["pollen_N"]
    require(p is None or n is None or p <= n, "panel exceeds complete source mass")
    return {
        "native_sample_index": index,
        "sample_id": source["sampleid"],
        "analysisunit_id": source.get("analysisunitid"),
        "native_depth": source.get("depth"),
        "native_thickness": source.get("thickness"),
        "native_ages": ages,
        "selected_age": selected,
        "selected_age_status": state,
        "age_disposition": disposition,
        "window": window,
        **panel,
        **mass,
        "excluded_pollen_N": None if p is None or n is None else n - p,
    }
