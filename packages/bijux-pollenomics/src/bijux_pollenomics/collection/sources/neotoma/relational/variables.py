"""Source-native Neotoma variable identities and unit families."""

from __future__ import annotations

import copy
from collections.abc import Mapping

from .....core.text import clean_optional_text
from .diagnostics import conflict_record
from .identifiers import digest, optional_source_id


def register_variable(
    variables: dict[str, dict[str, object]],
    *,
    variable_id: str,
    datum: Mapping[str, object],
    source_snapshot_id: str,
    build_id: str,
    conflicts: list[dict[str, object]],
) -> None:
    semantics = {
        "source_taxon_group": copy.deepcopy(datum.get("taxongroup")),
        "source_ecological_group": copy.deepcopy(datum.get("ecologicalgroup")),
        "source_element": copy.deepcopy(datum.get("element")),
        "source_element_type": copy.deepcopy(datum.get("elementtype")),
    }
    unit = clean_optional_text(datum.get("units"))
    record = variables.get(variable_id)
    if record is None:
        variables[variable_id] = {
            "variable_id": variable_id,
            "source_taxon_id": copy.deepcopy(datum.get("taxonid")),
            "source_reported_name": copy.deepcopy(datum.get("variablename")),
            "source_semantics_by_digest": {digest(semantics): semantics},
            "source_units": {unit} if unit else set(),
            "source_snapshot_id": source_snapshot_id,
            "build_id": build_id,
        }
        return
    if record.get("source_taxon_id") != datum.get("taxonid") or record.get(
        "source_reported_name"
    ) != datum.get("variablename"):
        conflicts.append(
            conflict_record(
                "variable_identity_conflict",
                variable_id,
                {
                    "existing_taxon_id": record.get("source_taxon_id"),
                    "incoming_taxon_id": datum.get("taxonid"),
                    "existing_name": record.get("source_reported_name"),
                    "incoming_name": datum.get("variablename"),
                },
            )
        )
    semantics_by_digest = record["source_semantics_by_digest"]
    if isinstance(semantics_by_digest, dict):
        semantics_by_digest.setdefault(digest(semantics), semantics)
    source_units = record["source_units"]
    if isinstance(source_units, set) and unit:
        source_units.add(unit)


def finalize_variables(variables: list[dict[str, object]]) -> None:
    for variable in variables:
        semantics = variable.pop("source_semantics_by_digest", {})
        if isinstance(semantics, dict):
            variable["source_semantics"] = [semantics[key] for key in sorted(semantics)]
        units = variable.get("source_units")
        if isinstance(units, set):
            variable["source_units"] = sorted(units)


def variable_id(datum: Mapping[str, object]) -> str:
    taxon_id = optional_source_id(datum.get("taxonid"))
    name = clean_optional_text(datum.get("variablename"))
    if taxon_id is not None:
        return f"neotoma:variable:{taxon_id}"
    return f"neotoma:variable:unidentified:{digest({'name': name})[:20]}"


def unit_family(unit: str) -> str:
    return {
        "NISP": "count",
        "NISP digitized": "count",
        "number": "count",
        "NISP/tablet": "count_per_tablet",
        "grains/tablet": "count_per_tablet",
        "number/tablet": "count_per_tablet",
        "cm3": "volume",
        "cm^3": "volume",
        "ml": "volume",
        "g": "mass",
        "mg": "mass",
        "grains/cm3": "concentration_per_volume",
        "grains/ml": "concentration_per_volume",
        "grains/g": "concentration_per_mass",
        "grains/g sample": "concentration_per_mass",
        "grains/mg": "concentration_per_mass",
        "grains/cm²/yr": "influx_per_area_time",
        "particles/cm²/yr": "influx_per_area_time",
        "yr/cm": "sedimentation_time_per_depth",
    }.get(unit, "unresolved")
