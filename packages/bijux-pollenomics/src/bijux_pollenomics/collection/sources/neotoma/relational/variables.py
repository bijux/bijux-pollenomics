"""Source-native Neotoma variable identities and unit families.

Conflicting identity variants share one diagnostic and a canonical JSON minimum
lookup representative. This serialization choice does not resolve taxonomy;
every observation retains its literal name, taxon ID, semantics and payload.
"""

from __future__ import annotations

from collections.abc import Mapping
import copy

from .....core.text import clean_optional_text
from .diagnostics import merge_conflict_variants
from .identifiers import digest, invalid_source_reference, optional_source_id


def is_native_pollen(element: object, element_type: object) -> bool:
    """Require both literal specimen labels before admitting native pollen rows."""
    return element == element_type == "pollen"


def source_element_status(value: object, element_type: object) -> str:
    """Retain normalized review labels without promoting conflicting specimens."""
    if not isinstance(value, str) or not value.strip():
        return "source_element_missing"
    if not isinstance(element_type, str) or not element_type.strip():
        return "source_element_type_missing"
    normalized_value = value.strip().casefold()
    normalized_type = element_type.strip().casefold()
    if normalized_value != normalized_type:
        return "source_element_labels_disagree"
    return (
        "source_label_pollen"
        if is_native_pollen(normalized_value, normalized_type)
        else "source_element_not_pollen"
    )


def register_variable(
    variables: dict[str, dict[str, object]],
    *,
    variable_id: str,
    datum: Mapping[str, object],
    source_snapshot_id: str,
    build_id: str,
    conflicts: list[dict[str, object]],
) -> None:
    """Register identity variants without changing native observation semantics."""
    identity = {
        "source_taxon_id": copy.deepcopy(datum.get("taxonid")),
        "source_reported_name": copy.deepcopy(datum.get("variablename")),
    }
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
            **identity,
            "source_semantics_by_digest": {digest(semantics): semantics},
            "source_units": {unit} if unit else set(),
            "source_snapshot_id": source_snapshot_id,
            "build_id": build_id,
        }
        if invalid_source_reference(datum.get("taxonid")):
            variables[variable_id]["source_taxon_identifier_status"] = (
                "invalid_source_identifier"
            )
        return
    existing_identity = {field: record.get(field) for field in identity}
    if digest(existing_identity) != digest(identity):
        variants = merge_conflict_variants(
            conflicts,
            conflict_kind="variable_identity_conflict",
            subject_id=variable_id,
            records=(existing_identity, identity),
        )
        # This is a serialization representative, never a synonymy decision.
        # Observation rows retain their own literal identity and source payload.
        record.update(variants[0])
    semantics_by_digest = record["source_semantics_by_digest"]
    if isinstance(semantics_by_digest, dict):
        semantics_by_digest.setdefault(digest(semantics), semantics)
    source_units = record["source_units"]
    if isinstance(source_units, set) and unit:
        source_units.add(unit)


def finalize_variables(variables: list[dict[str, object]]) -> None:
    """Serialize accumulated native semantics and exact unit labels."""
    for variable in variables:
        semantics = variable.pop("source_semantics_by_digest", {})
        if isinstance(semantics, dict):
            variable["source_semantics"] = [semantics[key] for key in sorted(semantics)]
        units = variable.get("source_units")
        if isinstance(units, set):
            variable["source_units"] = sorted(units)


def variable_id(datum: Mapping[str, object]) -> str:
    """Use the native taxon key or an explicit unidentified-name key."""
    name = clean_optional_text(datum.get("variablename"))
    if invalid_source_reference(datum.get("taxonid")):
        token = digest({"invalid_taxon_id": datum.get("taxonid"), "source_name": name})[
            :20
        ]
        return f"neotoma:invalid-variable:{token}"
    taxon_id = optional_source_id(datum.get("taxonid"))
    if taxon_id is not None:
        return f"neotoma:variable:{taxon_id}"
    return f"neotoma:variable:unidentified:{digest({'name': name})[:20]}"


def unit_family(unit: str) -> str:
    """Classify a literal unit label without converting its values."""
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
