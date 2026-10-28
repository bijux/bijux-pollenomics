"""Apply the published author target lookup without filling absent native counts."""

from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from typing import Any, cast

from ...physical_forward.inputs import require
from ..native_window_support.projection import project as project_native
from ..regional_source_support import (
    WINDOWS,
    count_metadata,
    count_state,
    integer,
    objects,
)


def panel(
    datum: list[dict[str, Any]],
    axes: list[dict[str, Any]],
    lookup: list[dict[str, Any]],
) -> dict[str, Any]:
    """Preserve native cells, exact lookup lines and every count-state distinction."""
    by_name: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in lookup:
        by_name[row["oldvar"]].append(row)
    targets = {a["author_target"] for a in axes}
    accounting = []
    for index, row in enumerate(datum):
        name = row.get("variablename")
        assignments = by_name.get(name, []) if type(name) is str else []
        target = assignments[0]["author_target"] if assignments else None
        pollen = row.get("element") == "pollen" or row.get("elementtype") == "pollen"
        require(
            not (pollen and target in targets)
            or any(
                row.get("taxonid") == a["taxon_id"] or name == a["source_name"]
                for a in axes
            ),
            "Unexpected additional native concept mapping to author panel",
        )
        disposition = (
            "non_pollen"
            if not pollen
            else "selected_author_target"
            if target in targets
            else "unmapped_native_name"
            if target is None
            else "author_excluded_target"
            if target in {"zz.do not use", "aage.cal.BP"}
            else "other_author_target"
        )
        accounting.append(
            {
                "datum_index": index,
                "native": deepcopy(row),
                "count_state": count_state(row),
                "author_target": target,
                "lookup_row_numbers": [r["row_number"] for r in assignments],
                "disposition": disposition,
            }
        )
    taxa = []
    counts: list[int | None] = []
    for axis in axes:
        name, code, target = (
            axis["source_name"],
            axis["taxon_id"],
            axis["author_target"],
        )
        require(
            by_name.get(name)
            and all(r["author_target"] == target for r in by_name[name]),
            "Required native name lacks its exact author lookup assignment",
        )
        matches = [
            (i, r)
            for i, r in enumerate(datum)
            if r.get("taxonid") == code or r.get("variablename") == name
        ]
        count = None
        if not matches:
            status = "missing_native_axis"
        elif len(matches) != 1:
            status = "duplicate_native_axis"
        elif (
            not integer(matches[0][1].get("taxonid"))
            or matches[0][1].get("taxonid") != code
            or matches[0][1].get("variablename") != name
        ):
            status = "id_label_conflict"
        elif not count_metadata(matches[0][1]):
            status = "incompatible_metadata"
        else:
            status = count_state(matches[0][1])
            if status in {"measured", "measured_zero"}:
                count = matches[0][1]["value"]
        counts.append(count)
        taxa.append(
            {
                **deepcopy(axis),
                "status": status,
                "native_matches": [
                    {"datum_index": i, "native": deepcopy(r)} for i, r in matches
                ],
                "lookup_rows": deepcopy(by_name[name]),
            }
        )
    complete = all(value is not None for value in counts)
    return {
        "taxa": taxa,
        "panel_counts": counts,
        "panel_complete": complete,
        "panel_N": sum(cast(list[int], counts)) if complete else None,
        "datum_accounting": accounting,
    }


def project(
    source: dict[str, Any],
    core: dict[str, Any],
    protocol: dict[str, Any],
    lookup: list[dict[str, Any]],
) -> dict[str, Any]:
    """Use the shared native-owner engine with a separately declared author axis."""
    require(
        protocol["schema_version"] == "nordic-author-window-support-protocol.v1"
        and core in objects(protocol["cores"])
        and protocol["taxa"] == ["Betula", "Pinus"]
        and protocol["windows"] == [list(edge) for edge in WINDOWS],
        "Declared author core/panel/window contract differs",
    )
    result = project_native(
        source,
        core,
        protocol,
        panel_projector=lambda datum: panel(datum, core["native_axes"], lookup),
        schema_version="nordic-author-core-support.v1",
        status="author_target_source_support_accounted",
        exact_default_flags=True,
        panel_state_key="author_target_state_counts",
    )
    return {
        **result,
        "country": core["country"],
        "physical_family": core["physical_family"],
        "native_axes": deepcopy(core["native_axes"]),
        "taxon_axis": deepcopy(protocol["taxa"]),
    }
