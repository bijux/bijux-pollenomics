"""Project finite native support aggregates without publishing raw archaeology rows."""

from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path
from typing import cast

from .independent import records


def aggregate(private: Path) -> dict[str, object]:
    """Build public support counts without admitting dates or events."""
    source = json.loads((private / "report.json").read_bytes())
    if (
        source["chronology_intervals"] is not None
        or source["chronology_admission"] is not False
        or source["scientific_admission"] is not False
    ):
        raise ValueError("native lead support cannot admit chronology or science")
    sets: dict[str, set[str]] = defaultdict(set)
    geometry_roles: Counter[str] = Counter()
    for row in records(
        private, "geometry.ndjson.gz", source["output_files"]["geometry.ndjson.gz"]
    ):
        geometry_roles[str(row["role"])] += 1
    for row in records(
        private, "support.ndjson.gz", source["output_files"]["support.ndjson.gz"]
    ):
        uuid = row["native_uuid"]
        if not isinstance(uuid, str):
            continue
        lead = str(row["lead_id"])
        role = str(row["role"])
        sets[lead + ":candidate:" + role].add(uuid)
        for support in cast(list[dict[str, object]], row["support"]):
            sets[
                lead
                + ":"
                + str(support["radius_metres"])
                + ":"
                + role
                + ":"
                + str(support["status"])
            ].add(uuid)
    types: Counter[str] = Counter()
    for row in records(
        private,
        "native-owners.ndjson.gz",
        source["output_files"]["native-owners.ndjson.gz"],
    ):
        families = cast(dict[str, dict[str, object]], row["families"])
        for attribute in cast(
            list[dict[str, dict[str, object]]], families["egenskap"]["rows"]
        ):
            value = attribute["typ"]
            if value["sqlite_type"] == "text":
                types[str(value["value"])] += 1
    if (
        source["source"]["sha256"]
        != "96bbe197a84c70b64f047873ded15ce5df568198dc0794870a782decb82fed0b"
    ):
        raise ValueError("native archaeology source identity differs")
    source_identity = {
        key: source["source"][key] for key in ("sha256", "bytes", "recorded_capture")
    }
    source_identity.update(
        source_id="raa/lamningar-v1", relative_path="lamningar_sverige.gpkg"
    )
    return {
        "schema_version": "raa-native-lead-support-aggregate.v1",
        "source_identity": source_identity,
        "scope": "Read-only finite indexed archaeology context around four source-owned modern-reference coordinates. Fifth named study object unresolved. These are source records and geometries, not independent events, population density, an admitted lake cohort or a field recommendation.",
        "leads": source["leads"],
        "unique_native_geometry_occurrences": source["unique_geometry_occurrences"],
        "unique_native_source_record_uuids": source["unique_native_uuids"],
        "lead_geometry_candidate_links": source["support_links"],
        "unique_geometry_occurrences_by_role": dict(sorted(geometry_roles.items())),
        "distinct_native_uuid_counts_by_support_class": {
            key: len(value) for key, value in sorted(sets.items())
        },
        "native_field_storage_type_counts": source["native_field_storage_type_counts"],
        "native_owner_lookup_status_counts": source[
            "native_owner_lookup_status_counts"
        ],
        "direct_attribute_native_type_counts": dict(sorted(types.items())),
        "native_date_roles": {
            "publiceringsdatum": "source record publication date; not archaeological event time",
            "uttagsdatum": "source extraction date; not archaeological event time",
            "egenskap.typ/varde": "verbatim native attribute names and text values retained privately; no numeric age/period crosswalk adopted",
            "general_update_timestamp": "no independently qualified general update timestamp inferred from publication/extraction fields",
        },
        "geometry_method": "Native EPSG:3006 projected metres. Indexed 20 km bounding-square candidates are classified at 10 km and 20 km. Points use the source coordinate norm; lines/polygons retain envelope lower/upper bounds, with uncertain shape overlap explicit. Positional-uncertainty polygons are a separate role. No geodesic distance, centroid, exact polygon-circle intersection or provider-index completeness claim.",
        "private_witness_files": source["output_files"],
        "private_decoded_witness_bytes": source["decoded_witness_bytes"],
        "chronology_intervals": None,
        "eligible_archaeological_event_count": 0,
        "field_permission": False,
        "scientific_admission": False,
        "canonical_source_adoption": False,
        "historical_density_equivalence": False,
        "textual_period_numeric_conversion": False,
        "rights_scope": "The existing source descriptor records the provider's Public Domain product description version 3.0. This consumer records no new rights decision and grants no linked-media or field-access permission.",
        "remaining": "Reconcile national source UUIDs/classes/population with the historical WFS/density layer, qualify archaeological dates and geometry interpretation, indirect attribute ownership, source-specific review and named field identity/access. The original 106-cell degraded/refusal branch and zero governed field candidates remain separate.",
    }
