from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any


def build_baseline(
    *,
    raw_archive_root: Path,
    relational_root: Path,
    compact_geojson_path: Path,
    lineage_path: Path,
    raw_public_root: str,
    relational_public_root: str,
    compact_public_path: str,
    lineage_public_path: str,
    baseline_schema_version: str,
    lineage_schema_version: str,
    safe_public_path: Callable[[str], str],
    load_raw_archive: Any,
    read_file: Callable[[Path], bytes],
    parse_object: Callable[[bytes, str], dict[str, object]],
    parse_mapping: Callable[[object, str], Mapping[str, object]],
    safe_filename: Callable[[str], str],
    required_text: Callable[[object, str], str],
    validate_materialization: Any,
    non_negative_integer: Callable[[object, str], int],
    canonical_json: Callable[[object], bytes],
    hashlib_module: Any,
) -> dict[str, object]:
    for role, path in (
        ("raw_archive", Path(raw_archive_root)),
        ("relational_detail", Path(relational_root)),
        ("compact_site_layer", Path(compact_geojson_path)),
        ("compact_lineage", Path(lineage_path)),
    ):
        if not path.exists():
            raise FileNotFoundError(f"Missing Neotoma baseline input {role}: {path}")

    raw_public_root = safe_public_path(raw_public_root)
    relational_public_root = safe_public_path(relational_public_root)
    compact_public_path = safe_public_path(compact_public_path)
    lineage_public_path = safe_public_path(lineage_public_path)
    raw_rows, source_snapshot_id = load_raw_archive(Path(raw_archive_root))
    raw_manifest_path = Path(raw_archive_root) / "manifest.json"
    raw_manifest_bytes = read_file(raw_manifest_path)
    raw_manifest = parse_object(raw_manifest_bytes, "Neotoma raw manifest")
    parts = raw_manifest.get("parts")
    if not isinstance(parts, list):
        raise ValueError("Neotoma raw manifest parts must be a list")
    raw_part_digests: dict[str, str] = {}
    for part_value in parts:
        part = parse_mapping(part_value, "Neotoma raw part")
        filename = safe_filename(
            required_text(part.get("filename"), "Neotoma raw part filename")
        )
        raw_part_digests[filename] = hashlib_module.sha256(
            read_file(Path(raw_archive_root) / filename)
        ).hexdigest()

    relational_manifest = validate_materialization(Path(relational_root))
    if relational_manifest.get("source_snapshot_id") != source_snapshot_id:
        raise ValueError("Raw and relational Neotoma source snapshot identities differ")
    compact_bytes = read_file(Path(compact_geojson_path))
    compact_payload = parse_object(compact_bytes, "Neotoma compact site layer")
    features = compact_payload.get("features")
    if not isinstance(features, list):
        raise ValueError("Neotoma compact site layer features must be a list")
    lineage_bytes = read_file(Path(lineage_path))
    lineage = parse_object(lineage_bytes, "Neotoma compact lineage")
    if lineage.get("schema_version") != lineage_schema_version:
        raise ValueError("Unexpected Neotoma compact lineage schema")
    if lineage.get("status") != "complete":
        raise ValueError("Cannot baseline a refused Neotoma compact lineage")
    lineage_inputs = parse_mapping(lineage.get("input_artifacts"), "lineage inputs")
    lineage_compact = parse_mapping(
        lineage_inputs.get("compact_site_layer"), "lineage compact input"
    )
    lineage_relational = parse_mapping(
        lineage_inputs.get("relational_detail"), "lineage relational input"
    )
    if (
        lineage_compact.get("sha256")
        != hashlib_module.sha256(compact_bytes).hexdigest()
    ):
        raise ValueError("Neotoma lineage does not bind the candidate compact layer")
    if lineage_relational.get("materialization_sha256") != relational_manifest.get(
        "materialization_sha256"
    ):
        raise ValueError("Neotoma lineage does not bind the candidate materialization")
    for field in ("source_snapshot_id", "build_id"):
        if lineage_relational.get(field) != relational_manifest.get(field):
            raise ValueError(f"Neotoma lineage does not bind candidate {field}")

    surfaces = parse_mapping(relational_manifest.get("surfaces"), "relational surfaces")
    counts = {
        "raw_download_rows": len(raw_rows),
        "raw_archive_parts": non_negative_integer(
            raw_manifest.get("part_count"), "raw part_count"
        ),
        "raw_requested_datasets": non_negative_integer(
            raw_manifest.get("requested_dataset_count"), "requested_dataset_count"
        ),
        "raw_downloaded_datasets": non_negative_integer(
            raw_manifest.get("downloaded_dataset_count"), "downloaded_dataset_count"
        ),
        "compact_records": len(features),
        **{
            f"relational_{name}": non_negative_integer(
                parse_mapping(surface, name).get("row_count"), f"{name} row_count"
            )
            for name, surface in sorted(surfaces.items())
        },
    }
    surface_schemas = {
        name: required_text(
            parse_mapping(surface, name).get("schema_version"), f"{name} schema_version"
        )
        for name, surface in sorted(surfaces.items())
    }
    baseline: dict[str, object] = {
        "schema_version": baseline_schema_version,
        "source_family": "neotoma",
        "input_artifacts": {
            "raw_archive": {
                "path": raw_public_root,
                "manifest_sha256": hashlib_module.sha256(
                    raw_manifest_bytes
                ).hexdigest(),
                "part_sha256": dict(sorted(raw_part_digests.items())),
            },
            "relational_detail": {
                "path": relational_public_root,
                "materialization_sha256": relational_manifest.get(
                    "materialization_sha256"
                ),
            },
            "compact_site_layer": {
                "path": compact_public_path,
                "sha256": hashlib_module.sha256(compact_bytes).hexdigest(),
            },
            "compact_lineage": {
                "path": lineage_public_path,
                "sha256": hashlib_module.sha256(lineage_bytes).hexdigest(),
            },
        },
        "identity": {
            "source_snapshot_id": source_snapshot_id,
            "raw_generated_on": raw_manifest.get("generated_on"),
            "build_id": relational_manifest.get("build_id"),
            "relational_materialization_sha256": relational_manifest.get(
                "materialization_sha256"
            ),
            "compact_sha256": hashlib_module.sha256(compact_bytes).hexdigest(),
            "lineage_sha256": hashlib_module.sha256(lineage_bytes).hexdigest(),
        },
        "schemas": {
            "relational_snapshot": relational_manifest.get(
                "relational_snapshot_schema_version"
            ),
            "relational_manifest": relational_manifest.get("schema_version"),
            "compact_lineage": lineage.get("schema_version"),
            "upstream_archive_contract": {
                field: raw_manifest.get(field)
                for field in (
                    "source",
                    "endpoint_template",
                    "datasettype",
                    "part_count",
                )
            },
            "surfaces": surface_schemas,
        },
        "counts": counts,
    }
    baseline["baseline_id"] = (
        "sha256:" + hashlib_module.sha256(canonical_json(baseline)).hexdigest()
    )
    return baseline
