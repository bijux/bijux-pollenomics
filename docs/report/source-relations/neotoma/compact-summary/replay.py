"""Recompute one compact Neotoma site field from retained relational evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from bijux_pollenomics.evidence.sources.neotoma import (
    validate_neotoma_relational_materialization,
)


ROOT = Path(__file__).resolve().parents[5]
COMPACT = ROOT / "data/neotoma/normalized/nordic_pollen_sites.geojson"
LINEAGE = ROOT / "data/neotoma/review/compact_relational_lineage.json"
RELATIONAL = ROOT / "data/neotoma/relational"
SITE_ID = "neotoma:site:12"
RECORD_ID = "12"


def _read_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_bytes())
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _part(
    manifest: dict[str, object], surface: str, relative_path: str
) -> dict[str, object]:
    surface_manifest = manifest["surfaces"][surface]
    part = next(
        (item for item in surface_manifest["parts"] if item["path"] == relative_path),
        None,
    )
    if part is None:
        raise ValueError(f"Unregistered {surface} part: {relative_path}")
    path = RELATIONAL / relative_path
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != part["sha256"]:
        raise ValueError(f"Changed {surface} part: {relative_path}")
    payload = json.loads(content)
    if len(payload["rows"]) != part["row_count"]:
        raise ValueError(f"Changed {surface} row count: {relative_path}")
    return payload


def _located_row(
    manifest: dict[str, object], surface: str, locator: dict[str, object]
) -> dict[str, object]:
    prefix = "data/neotoma/relational/"
    path = locator["path"]
    if not isinstance(path, str) or not path.startswith(prefix):
        raise ValueError(f"Invalid {surface} locator path")
    pointer = locator["json_pointer"]
    if not isinstance(pointer, str) or not pointer.startswith("/rows/"):
        raise ValueError(f"Invalid {surface} locator pointer")
    row = _part(manifest, surface, path.removeprefix(prefix))["rows"][
        int(pointer.removeprefix("/rows/"))
    ]
    if row[locator["identity_field"]] != locator["identity_value"]:
        raise ValueError(f"Stale {surface} locator identity")
    return row


def build_report() -> dict[str, object]:
    """Treat relational samples as authority and compare the compact display."""
    manifest = validate_neotoma_relational_materialization(RELATIONAL)
    lineage = _read_json(LINEAGE)
    if lineage["status"] != "complete":
        raise ValueError("Compact lineage is incomplete")
    compact_bytes = COMPACT.read_bytes()
    if (
        hashlib.sha256(compact_bytes).hexdigest()
        != lineage["input_artifacts"]["compact_site_layer"]["sha256"]
    ):
        raise ValueError("Compact layer differs from its lineage input")
    relational_input = lineage["input_artifacts"]["relational_detail"]
    for key in ("source_snapshot_id", "build_id", "materialization_sha256"):
        if relational_input[key] != manifest[key]:
            raise ValueError(f"Relational {key} differs from compact lineage input")

    compact = json.loads(compact_bytes)
    matching_features = [
        (index, feature)
        for index, feature in enumerate(compact["features"])
        if feature["properties"].get("record_id") == RECORD_ID
    ]
    if len(matching_features) != 1:
        raise ValueError("Expected one compact feature for site 12")
    feature_index, feature = matching_features[0]
    popup_values = [
        row["value"]
        for row in feature["properties"]["popup_rows"]
        if row["label"] == "Samples"
    ]
    if len(popup_values) != 1:
        raise ValueError("Expected one Samples popup field")

    matching_lineage = [
        row
        for row in lineage["compact_to_relational"]
        if row["compact_record_id"] == RECORD_ID
    ]
    if len(matching_lineage) != 1:
        raise ValueError("Expected one compact-to-relational trace")
    trace = matching_lineage[0]
    if (
        trace["relational_site_id"] != SITE_ID
        or trace["compact_locator"]["json_pointer"]
        != f"/features/{feature_index}/properties"
    ):
        raise ValueError("Compact site locator does not match relational site")

    sample_rows = [
        row
        for part in manifest["surfaces"]["samples"]["parts"]
        for row in _part(manifest, "samples", part["path"])["rows"]
        if row["site_id"] == SITE_ID
    ]
    sample_ids = [row["sample_id"] for row in sample_rows]
    if len(set(sample_ids)) != len(sample_ids):
        raise ValueError("Duplicate site sample identity")
    derived_count = len(sample_ids)
    if trace["detail_row_counts"]["samples"] != derived_count:
        raise ValueError("Lineage sample count differs from relational evidence")
    if popup_values[0] != str(derived_count):
        raise ValueError("Compact Samples field differs from relational evidence")

    sample_locator = trace["sample_evidence_locator"]
    observation_locator = trace["observation_evidence_locator"]
    sample = _located_row(manifest, "samples", sample_locator)
    observation = _located_row(manifest, "observations", observation_locator)
    if (
        sample["site_id"] != SITE_ID
        or sample["sample_id"] not in sample_ids
        or observation["site_id"] != SITE_ID
        or observation["sample_id"] != sample["sample_id"]
        or observation["dataset_id"] != sample["dataset_id"]
        or observation["collection_unit_id"] != sample["collection_unit_id"]
    ):
        raise ValueError("Representative observation is not owned by traced sample")
    if (
        sample["source_snapshot_id"] != manifest["source_snapshot_id"]
        or observation["source_snapshot_id"] != manifest["source_snapshot_id"]
    ):
        raise ValueError("Representative evidence belongs to another source snapshot")

    return {
        "schema_version": "neotoma-compact-sample-derivation.v1",
        "status": "matched",
        "authority": "relational_samples",
        "compact_role": "derived_display_only",
        "site_id": SITE_ID,
        "source_snapshot_id": manifest["source_snapshot_id"],
        "relational_materialization_sha256": manifest["materialization_sha256"],
        "compact_sha256": hashlib.sha256(compact_bytes).hexdigest(),
        "compact_field": {
            "path": "data/neotoma/normalized/nordic_pollen_sites.geojson",
            "json_pointer": f"/features/{feature_index}/properties/popup_rows",
            "label": "Samples",
            "displayed_value": popup_values[0],
        },
        "derivation": {
            "operation": "count_distinct_sample_id_where_site_id_equals_site",
            "relational_sample_count": derived_count,
            "distinct_sample_id_count": len(set(sample_ids)),
            "sample_id_set_sha256": hashlib.sha256(
                ("\n".join(sorted(sample_ids)) + "\n").encode()
            ).hexdigest(),
            "sample_surface_paths": [
                "data/neotoma/relational/" + part["path"]
                for part in manifest["surfaces"]["samples"]["parts"]
            ],
        },
        "reverse_trace": {
            "sample_id": sample["sample_id"],
            "sample_locator": sample_locator,
            "observation_id": observation["observation_id"],
            "observation_locator": observation_locator,
            "observation_parent_sample_id": observation["sample_id"],
        },
    }


if __name__ == "__main__":
    print(json.dumps(build_report(), indent=2, ensure_ascii=False, sort_keys=True))
