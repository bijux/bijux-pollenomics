"""Authenticate non-quantitative evidence for EMPD2--NFI inclusion intent."""

from __future__ import annotations

import json
import math
from hashlib import sha256
from typing import Any, cast

from bijux_pollenomics.analysis.lra_validation.contracts import canonical_json
from bijux_pollenomics.core.geospatial.distance import wgs84_inverse_geodesic

from .pollen_index import INDEX_ROW_KEYS
from .projection import _json_object, digest, identities, identity, sha_identity

_MANIFEST_KEYS = {
    "schema_version",
    "projection_sha256",
    "reviewer_id",
    "reviewer_authority",
    "decision_date",
    "rows",
}
_ROW_KEYS = {
    "record_id",
    "source_row_sha256",
    "pollen_collection_period",
    "pollen_support",
    "vegetation_support",
    "paired_footprint",
    "nfi_inventory_date_source_native",
    "inventory_time_binding",
    "vegetation_observation_period",
    "pollen_source_binding",
    "estimand",
    "nfi_rights_evidence_reference_ids",
    "independence_status",
    "independence_evidence_reference_ids",
}
_PERIOD_KEYS = {"younger_bp", "older_bp", "age_type", "evidence_reference_ids"}
_SUPPORT_KEYS = {
    "latitude",
    "longitude",
    "radius_m",
    "coordinate_uncertainty_m",
    "younger_bp",
    "older_bp",
    "footprint_sha256",
    "coordinate_crs",
    "spatial_profile",
    "temporal_profile",
}
_PAIR_KEYS = {
    "source_distance_m_wgs84",
    "reviewed_max_pair_distance_m",
    "relation",
    "evidence_reference_ids",
}
_TIME_KEYS = {
    "native_inventory_date",
    "conversion_profile",
    "converted_interval_sha256",
    "evidence_reference_ids",
}
_POLLEN_BINDING_KEYS = {
    "index_row",
    "pollen_count_index_sha256",
    "producer_attestation_sha256",
    "payload_access_status",
    "count_closure_status",
}
_ESTIMAND_KEYS = {"estimand_id", "rows", "support_role"}
_ESTIMAND_ROW_KEYS = {"taxon_id", "source_column", "variable_id", "unit"}
_NFI_SCHEMA_KEYS = {
    "acquisition_receipt_sha256",
    "candidate_estimand",
    "data_dimension_declared_not_counted",
    "data_rows_opened",
    "final_test_labels_opened",
    "header_count",
    "headers",
    "readme_dimension",
    "regional_area_cover_truth_admitted",
    "schema_version",
    "selected_readme_descriptions",
    "sheet_names",
    "source_byte_count",
    "source_sha256",
}
_NFI_DESCRIPTIONS = {
    "BaBirch": "Basal area of birch (m2/ha)",
    "BaPine": "Basal area of pine (m2/ha)",
    "BaSpruce": "Basal area of spruce (m2/ha)",
    "Easting": "Meters. Sweref99TM",
    "Inventory_Date": "YYYY-MM-DD",
    "LandUseClass": (
        "National classification according to table. Only plots from Forestland "
        "according to FAO-definitions included."
    ),
    "NoStemsPine": "No of stems of pine (no/ha)",
    "Northing": "Meters. Sweref99TM",
    "PlotArea": "Circular plot r=7 => 153.94 m2 (only un-divided plots included)",
    "VolBirch": "Volume of birch (m3/ha)",
    "VolPine": "Volume of pine (m3/ha)",
    "VolSpruce": "Volume of spruce (m3/ha)",
    "Year": "Year of inventory (2007-2025)",
}
_GENUS_SUFFIX = {
    "Betula": "Birch",
    "Picea": "Spruce",
    "Pinus": "Pine",
}
_MEASURES = {
    "Ba": ("basal-area", "unit:m2-per-ha", "(m2/ha)"),
    "Vol": ("stem-volume", "unit:m3-per-ha", "(m3/ha)"),
    "NoStems": ("stem-count", "unit:count-per-ha", "(no/ha)"),
}
_MEASURE_ESTIMAND_IDS = {
    "Ba": "nfi:point-plot-tree-basal-area",
    "Vol": "nfi:point-plot-tree-stem-volume",
    "NoStems": "nfi:point-plot-tree-stem-count",
}


def _finite(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{field} must be finite")
    return result


def _period(value: object, field: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != _PERIOD_KEYS:
        raise ValueError(f"{field} fields differ from the evidence schema")
    period = cast(dict[str, Any], value)
    younger = _finite(period["younger_bp"], f"{field}.younger_bp")
    older = _finite(period["older_bp"], f"{field}.older_bp")
    if younger > older or period["age_type"] != "BP":
        raise ValueError(f"{field} is not a bounded BP interval")
    identities(period["evidence_reference_ids"], f"{field} evidence")
    return period


def _support(value: object, period: dict[str, Any], field: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != _SUPPORT_KEYS:
        raise ValueError(f"{field} fields differ from the evidence schema")
    support = cast(dict[str, Any], value)
    latitude = _finite(support["latitude"], f"{field}.latitude")
    longitude = _finite(support["longitude"], f"{field}.longitude")
    radius = _finite(support["radius_m"], f"{field}.radius_m")
    uncertainty = _finite(
        support["coordinate_uncertainty_m"], f"{field}.coordinate_uncertainty_m"
    )
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise ValueError(f"{field} coordinates are out of range")
    if radius < 0 or uncertainty < 0:
        raise ValueError(f"{field} radius and uncertainty must be nonnegative")
    if (
        support["younger_bp"] != period["younger_bp"]
        or support["older_bp"] != period["older_bp"]
        or support["coordinate_crs"] != "EPSG:4326"
        or support["spatial_profile"] != "bounded-footprint-radius-v1"
        or support["temporal_profile"] != "typed-bp-interval-v1"
    ):
        raise ValueError(f"{field} differs from its reviewed period or profile")
    footprint_sha = sha_identity(
        support["footprint_sha256"], f"{field}.footprint_sha256"
    )
    footprint_payload = {
        key: item for key, item in support.items() if key != "footprint_sha256"
    }
    if footprint_sha != digest(footprint_payload):
        raise ValueError(f"{field} footprint digest differs from its exact fields")
    return support


def _distance_m(first: dict[str, Any], second: dict[str, Any]) -> float:
    return (
        1000.0
        * wgs84_inverse_geodesic(
            latitude_a=float(first["latitude"]),
            longitude_a=float(first["longitude"]),
            latitude_b=float(second["latitude"]),
            longitude_b=float(second["longitude"]),
        ).distance_km_unrounded
    )


def _validate_row(
    row: dict[str, Any],
    candidate: dict[str, Any],
    pollen_index_row: dict[str, Any],
    pollen_count_index_sha256: str,
    producer_attestation_sha256: str,
    accepted_taxa: list[str],
    accepted_taxon_names: dict[str, str],
    nfi_columns: dict[str, str],
) -> None:
    if set(row) != _ROW_KEYS:
        raise ValueError("evidence row fields differ from the exact schema")
    if (
        row["record_id"] != candidate["record_id"]
        or row["source_row_sha256"] != candidate["source_row_sha256"]
        or row["nfi_inventory_date_source_native"]
        != candidate["nfi_inventory_date_source_native"]
    ):
        raise ValueError("evidence row targets another source row")
    pollen_period = _period(row["pollen_collection_period"], "pollen period")
    vegetation_period = _period(
        row["vegetation_observation_period"], "vegetation period"
    )
    if max(pollen_period["younger_bp"], vegetation_period["younger_bp"]) > min(
        pollen_period["older_bp"], vegetation_period["older_bp"]
    ):
        raise ValueError("pollen and vegetation evidence periods do not overlap")
    time_binding = row["inventory_time_binding"]
    if not isinstance(time_binding, dict) or set(time_binding) != _TIME_KEYS:
        raise ValueError("inventory time binding fields differ from the exact schema")
    if (
        time_binding["native_inventory_date"]
        != candidate["nfi_inventory_date_source_native"]
        or time_binding["conversion_profile"]
        != "reviewed-native-date-to-bp-interval.v1"
        or time_binding["converted_interval_sha256"] != digest(vegetation_period)
    ):
        raise ValueError("NFI native date is not bound to its reviewed BP interval")
    identities(time_binding["evidence_reference_ids"], "inventory-time evidence")
    pollen = _support(row["pollen_support"], pollen_period, "pollen support")
    vegetation = _support(
        row["vegetation_support"], vegetation_period, "vegetation support"
    )
    if (
        pollen["latitude"] != candidate["pollen_latitude"]
        or pollen["longitude"] != candidate["pollen_longitude"]
    ):
        raise ValueError("pollen support differs from the exact source location")
    pair = row["paired_footprint"]
    if not isinstance(pair, dict) or set(pair) != _PAIR_KEYS:
        raise ValueError("paired footprint fields differ from the exact schema")
    declared_distance = _finite(
        pair["source_distance_m_wgs84"], "paired source distance"
    )
    maximum_distance = _finite(
        pair["reviewed_max_pair_distance_m"], "reviewed pair-distance bound"
    )
    calculated_distance = _distance_m(pollen, vegetation)
    if (
        pair["relation"] != "reviewed_proximity_support_compatible"
        or abs(declared_distance - candidate["distance_m_wgs84"]) > 1e-6
        or abs(calculated_distance - declared_distance) > 0.05
        or maximum_distance < 0
        or declared_distance > maximum_distance
    ):
        raise ValueError("paired supports are incompatible with the source distance")
    identities(pair["evidence_reference_ids"], "paired-footprint evidence")
    binding = row["pollen_source_binding"]
    if not isinstance(binding, dict) or set(binding) != _POLLEN_BINDING_KEYS:
        raise ValueError("pollen source binding fields differ from the exact schema")
    index_row = binding["index_row"]
    if (
        not isinstance(index_row, dict)
        or set(index_row) != INDEX_ROW_KEYS
        or index_row != pollen_index_row
        or binding["pollen_count_index_sha256"] != pollen_count_index_sha256
        or binding["producer_attestation_sha256"] != producer_attestation_sha256
        or binding["payload_access_status"] != "sealed_unopened"
        or binding["count_closure_status"] != "externally_attested_not_runtime_verified"
    ):
        raise ValueError("pollen source binding differs from the sealed index")
    estimand = row["estimand"]
    if not isinstance(estimand, dict) or set(estimand) != _ESTIMAND_KEYS:
        raise ValueError("estimand fields differ from the exact schema")
    estimand_rows = estimand["rows"]
    if (
        not isinstance(estimand_rows, list)
        or any(
            not isinstance(item, dict) or set(item) != _ESTIMAND_ROW_KEYS
            for item in estimand_rows
        )
        or estimand["support_role"] != "point_plot_tree_measurement_not_area_cover"
    ):
        raise ValueError("estimand is not a compatible point/plot declaration")
    taxa, columns, variables, measures = [], [], [], []
    for item in cast(list[dict[str, Any]], estimand_rows):
        taxon = identity(item["taxon_id"], "estimand taxon")
        taxa.append(taxon)
        column = identity(item["source_column"], "estimand source column")
        columns.append(column)
        description = nfi_columns.get(column)
        if description is None:
            raise ValueError(
                "estimand source column is absent from the pinned NFI schema"
            )
        suffix = _GENUS_SUFFIX.get(accepted_taxon_names.get(taxon, ""))
        measure = next(
            (prefix for prefix in _MEASURES if column == f"{prefix}{suffix}"), None
        )
        if suffix is None or measure is None:
            raise ValueError("estimand taxon and NFI source column do not match")
        variable_name, unit, description_unit = _MEASURES[measure]
        variable = identity(item["variable_id"], "estimand variable")
        variables.append(variable)
        measures.append(measure)
        if (
            variable != f"variable:{suffix.lower()}-{variable_name}"
            or item["unit"] != unit
            or description_unit not in description
        ):
            raise ValueError(
                "estimand variable or unit differs from governed NFI semantics"
            )
    if (
        taxa != accepted_taxa
        or len(set(columns)) != len(columns)
        or len(set(variables)) != len(variables)
        or len(set(measures)) != 1
    ):
        raise ValueError("estimand rows do not close the accepted taxon denominator")
    estimand_id = identity(estimand["estimand_id"], "estimand_id")
    if estimand_id != _MEASURE_ESTIMAND_IDS[measures[0]]:
        raise ValueError("estimand_id differs from the governed common measure")
    identities(row["nfi_rights_evidence_reference_ids"], "NFI rights evidence")
    identities(row["independence_evidence_reference_ids"], "independence evidence")
    if row["independence_status"] != "reviewed_independent":
        raise ValueError("independence must be explicitly reviewed")


def authenticated_evidence_rows(
    content: bytes,
    pinned_sha256: str,
    projection: dict[str, Any],
    reviewer_id: str,
    decision_date: str,
    pollen_index_rows: dict[str, dict[str, Any]],
    pollen_count_index_sha256: str,
    producer_attestation_sha256: str,
    accepted_taxa: list[str],
    accepted_taxon_names: dict[str, str],
    nfi_schema_bytes: bytes,
    nfi_schema_sha256: str,
) -> dict[str, dict[str, Any]]:
    """Return exact rows from canonical content matching an external content pin.

    The pin authenticates content only. It does not authenticate reviewer identity,
    reviewer qualification, or scientific acceptance.
    """
    pinned = sha_identity(pinned_sha256, "evidence_manifest_sha256")
    if sha256(content).hexdigest() != pinned:
        raise ValueError(
            "evidence manifest bytes differ from the external trust anchor"
        )
    try:
        raw = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("evidence manifest is not canonical JSON") from exc
    if (
        not isinstance(raw, dict)
        or set(raw) != _MANIFEST_KEYS
        or canonical_json(raw).encode() != content
        or raw.get("schema_version") != "empd2-nfi-reference-evidence.v1"
        or raw.get("projection_sha256") != projection["projection_sha256"]
        or raw.get("reviewer_authority") != "declared_not_authenticated"
        or raw.get("reviewer_id") != reviewer_id
        or raw.get("decision_date") != decision_date
    ):
        raise ValueError("evidence manifest content differs from the exact schema")
    if (
        sha_identity(nfi_schema_sha256, "nfi_schema_sha256")
        != projection["source_identities"]["nfi_schema"]
        or sha256(nfi_schema_bytes).hexdigest() != nfi_schema_sha256
    ):
        raise ValueError("NFI schema bytes differ from the projected source identity")
    nfi_schema = _json_object(nfi_schema_bytes, "NFI schema")
    if (
        set(nfi_schema) != _NFI_SCHEMA_KEYS
        or nfi_schema.get("schema_version") != "nfi-workbook-schema-review.v1"
        or nfi_schema.get("header_count") != 47
        or not isinstance(nfi_schema.get("headers"), list)
        or len(nfi_schema["headers"]) != 47
        or len(set(nfi_schema["headers"])) != 47
        or nfi_schema.get("data_rows_opened") != 0
        or nfi_schema.get("final_test_labels_opened") is not False
        or nfi_schema.get("regional_area_cover_truth_admitted") is not False
        or nfi_schema.get("source_sha256")
        != projection["source_identities"]["nfi_workbook"]
        or not isinstance(nfi_schema.get("selected_readme_descriptions"), dict)
        or nfi_schema["selected_readme_descriptions"] != _NFI_DESCRIPTIONS
    ):
        raise ValueError("NFI schema differs from the exact structural schema")
    header_values = [identity(value, "NFI header") for value in nfi_schema["headers"]]
    headers = set(header_values)
    descriptions = cast(dict[str, Any], nfi_schema["selected_readme_descriptions"])
    nfi_columns = {
        identity(key, "NFI described column"): identity(value, "NFI description")
        for key, value in descriptions.items()
    }
    if not set(nfi_columns) <= headers:
        raise ValueError("NFI descriptions name columns absent from the header")
    rows = raw.get("rows")
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError("evidence rows must be an object array")
    candidates = {row["record_id"]: row for row in projection["candidate_rows"]}
    mapped: dict[str, dict[str, Any]] = {}
    for value in cast(list[dict[str, Any]], rows):
        record_id = value.get("record_id")
        candidate = candidates.get(record_id)
        if candidate is None or record_id in mapped:
            raise ValueError("evidence row identity is unknown or duplicated")
        _validate_row(
            value,
            candidate,
            pollen_index_rows[candidate["pollen_sample"]],
            pollen_count_index_sha256,
            producer_attestation_sha256,
            accepted_taxa,
            accepted_taxon_names,
            nfi_columns,
        )
        mapped[cast(str, record_id)] = value
    if list(mapped) != sorted(candidates) or set(mapped) != set(candidates):
        raise ValueError("evidence manifest does not canonically close all 16 leads")
    reference_estimand = next(iter(mapped.values()))["estimand"]
    if any(row["estimand"] != reference_estimand for row in mapped.values()):
        raise ValueError("evidence rows must share one exact estimand contract")
    reconciled: dict[tuple[str, str, str, str], tuple[object, ...]] = {}
    for record_id, row in mapped.items():
        candidate = candidates[record_id]
        key = (
            projection["source_identities"]["nfi_workbook"],
            candidate["nfi_tract"],
            candidate["nfi_plot"],
            candidate["nfi_year"],
        )
        owned = tuple(
            row[field]
            for field in (
                "vegetation_support",
                "vegetation_observation_period",
                "inventory_time_binding",
                "estimand",
                "nfi_rights_evidence_reference_ids",
            )
        )
        previous = reconciled.setdefault(key, owned)
        if previous != owned:
            raise ValueError("shared NFI observation evidence is inconsistent")
    return mapped
