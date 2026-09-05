"""Trace compact Neotoma site records to retained relational evidence."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
import hashlib
import json
from pathlib import Path, PurePosixPath

from .materialization import validate_neotoma_relational_materialization

__all__ = [
    "build_neotoma_compact_lineage",
    "write_neotoma_compact_lineage",
]

LINEAGE_SCHEMA_VERSION = "neotoma-compact-relational-lineage.v1"
_DETAIL_SURFACES = (
    "collection_units",
    "datasets",
    "chronologies",
    "chronology_controls",
    "samples",
    "age_claims",
    "observations",
)
_SURFACE_ID_FIELDS = {
    "sites": "site_id",
    "collection_units": "collection_unit_id",
    "datasets": "dataset_id",
    "chronologies": "chronology_id",
    "chronology_controls": "chronology_control_id",
    "samples": "sample_id",
    "age_claims": "chronology_claim_id",
    "observations": "observation_id",
}


def build_neotoma_compact_lineage(
    *,
    compact_geojson_path: Path,
    relational_root: Path,
    compact_public_path: str = "data/neotoma/normalized/nordic_pollen_sites.geojson",
    relational_public_root: str = "data/neotoma/relational",
) -> dict[str, object]:
    """Build complete forward and reverse locators without copying detail rows."""
    compact_public_path = _safe_public_path(compact_public_path)
    relational_public_root = _safe_public_path(relational_public_root)
    missing = [
        role
        for role, path in (
            ("compact_site_layer", Path(compact_geojson_path)),
            ("relational_detail", Path(relational_root)),
        )
        if not path.exists()
    ]
    if missing:
        return _refusal_payload(
            compact_public_path=compact_public_path,
            relational_public_root=relational_public_root,
            reasons=[f"missing_{role}" for role in missing],
        )

    compact_bytes = _read_regular_file(Path(compact_geojson_path))
    compact_payload = _json_object(compact_bytes, compact_public_path)
    features = compact_payload.get("features")
    if not isinstance(features, list):
        raise ValueError("Neotoma compact GeoJSON features must be a list")
    manifest = validate_neotoma_relational_materialization(Path(relational_root))
    source_snapshot_id = _required_text(
        manifest.get("source_snapshot_id"), "relational source_snapshot_id"
    )
    build_id = _required_text(manifest.get("build_id"), "relational build_id")
    materialization_sha256 = _required_text(
        manifest.get("materialization_sha256"), "relational materialization_sha256"
    )

    compact_records: dict[str, dict[str, object]] = {}
    for feature_index, feature_value in enumerate(features):
        feature = _mapping(feature_value, f"compact feature {feature_index}")
        properties = _mapping(
            feature.get("properties"), f"compact feature {feature_index} properties"
        )
        if properties.get("source") != "Neotoma":
            raise ValueError(f"Compact feature {feature_index} is not Neotoma")
        compact_record_id = _required_text(
            properties.get("record_id"), f"compact feature {feature_index} record_id"
        )
        if compact_record_id in compact_records:
            raise ValueError(
                f"Duplicate compact Neotoma record_id: {compact_record_id}"
            )
        compact_records[compact_record_id] = {
            "feature_index": feature_index,
            "site_name": properties.get("name"),
        }

    surface_indexes = {
        surface: _index_surface(
            Path(relational_root),
            manifest,
            surface=surface,
            id_field=_SURFACE_ID_FIELDS[surface],
            public_root=relational_public_root,
        )
        for surface in ("sites", *_DETAIL_SURFACES)
    }
    relational_sites = surface_indexes["sites"]
    rows: list[dict[str, object]] = []
    missing_relational: list[str] = []
    for compact_record_id, compact_record in sorted(compact_records.items()):
        site_id = f"neotoma:site:{compact_record_id}"
        site_entry = relational_sites.get(site_id)
        if site_entry is None or site_entry["row_count"] != 1:
            missing_relational.append(compact_record_id)
        detail_counts = {
            surface: _index_count(surface_indexes[surface], site_id)
            for surface in _DETAIL_SURFACES
        }
        sample_locator = _first_locator(surface_indexes["samples"], site_id)
        observation_locator = _first_locator(surface_indexes["observations"], site_id)
        if sample_locator is not None and observation_locator is not None:
            sample_identity = _mapping(sample_locator, "sample locator").get(
                "identity_value"
            )
            observation_parents = _mapping(
                _mapping(observation_locator, "observation locator").get(
                    "parent_identities"
                ),
                "observation parent identities",
            )
            if observation_parents.get("sample_id") != sample_identity:
                raise ValueError(
                    "Representative Neotoma observation does not belong to "
                    f"representative sample for {site_id}"
                )
        rows.append(
            {
                "compact_record_id": compact_record_id,
                "compact_locator": {
                    "path": compact_public_path,
                    "json_pointer": (
                        f"/features/{compact_record['feature_index']}/properties"
                    ),
                    "identity_field": "record_id",
                    "identity_value": compact_record_id,
                },
                "site_name": compact_record["site_name"],
                "relational_site_id": site_id,
                "relational_site_locator": (
                    site_entry["first_locator"]
                    if site_entry is not None and site_entry["row_count"] == 1
                    else None
                ),
                "relational_detail_query": {
                    "identity_field": "site_id",
                    "identity_value": site_id,
                    "surfaces": list(_DETAIL_SURFACES),
                },
                "detail_row_counts": detail_counts,
                "sample_evidence_locator": sample_locator,
                "observation_evidence_locator": observation_locator,
                "sample_evidence_status": (
                    "linked" if sample_locator is not None else "not_provided_for_site"
                ),
            }
        )

    reverse_rows: list[dict[str, object]] = []
    missing_compact: list[str] = []
    for site_id, entry in sorted(relational_sites.items()):
        if entry["row_count"] != 1:
            raise ValueError(f"Relational site index is not unique: {site_id}")
        compact_record_id = site_id.removeprefix("neotoma:site:")
        reverse_compact_record = compact_records.get(compact_record_id)
        if reverse_compact_record is None:
            missing_compact.append(site_id)
            compact_locator = None
        else:
            compact_locator = {
                "path": compact_public_path,
                "json_pointer": (
                    f"/features/{reverse_compact_record['feature_index']}/properties"
                ),
                "identity_field": "record_id",
                "identity_value": compact_record_id,
            }
        reverse_rows.append(
            {
                "relational_site_id": site_id,
                "relational_site_locator": entry["first_locator"],
                "compact_record_id": compact_record_id,
                "compact_locator": compact_locator,
            }
        )

    linked_count = len(rows) - len(missing_relational)
    status = "complete" if not missing_relational and not missing_compact else "refused"
    refusal_reasons = []
    if missing_relational:
        refusal_reasons.append("compact_records_without_relational_site")
    if missing_compact:
        refusal_reasons.append("relational_sites_without_compact_record")
    detail_totals: Counter[str] = Counter()
    for row in rows:
        counts_mapping = _mapping(row["detail_row_counts"], "detail_row_counts")
        detail_totals.update(
            {
                surface: _integer(counts_mapping[surface], surface)
                for surface in _DETAIL_SURFACES
            }
        )
    sample_reverse_rows = [
        {
            "sample_id": _mapping(
                row["sample_evidence_locator"], "sample evidence locator"
            )["identity_value"],
            "sample_locator": row["sample_evidence_locator"],
            "relational_site_id": row["relational_site_id"],
            "compact_record_id": row["compact_record_id"],
            "compact_locator": row["compact_locator"],
        }
        for row in rows
        if row["sample_evidence_locator"] is not None
    ]
    return {
        "schema_version": LINEAGE_SCHEMA_VERSION,
        "source_family": "neotoma",
        "status": status,
        "refusal_reasons": refusal_reasons,
        "input_artifacts": {
            "compact_site_layer": {
                "path": compact_public_path,
                "sha256": hashlib.sha256(compact_bytes).hexdigest(),
            },
            "relational_detail": {
                "path": relational_public_root,
                "source_snapshot_id": source_snapshot_id,
                "build_id": build_id,
                "materialization_sha256": materialization_sha256,
            },
        },
        "summary": {
            "compact_record_count": len(compact_records),
            "relational_site_count": len(relational_sites),
            "linked_compact_record_count": linked_count,
            "compact_without_relational_count": len(missing_relational),
            "relational_without_compact_count": len(missing_compact),
            "sites_with_sample_evidence_count": sum(
                _index_count(surface_indexes["samples"], f"neotoma:site:{record_id}")
                > 0
                for record_id in compact_records
            ),
            "representative_sample_reverse_trace_count": len(sample_reverse_rows),
            "detail_row_totals": dict(sorted(detail_totals.items())),
        },
        "compact_without_relational_record_ids": missing_relational,
        "relational_without_compact_site_ids": missing_compact,
        "compact_to_relational": rows,
        "relational_to_compact": reverse_rows,
        "representative_sample_to_compact": sample_reverse_rows,
    }


def write_neotoma_compact_lineage(
    output_path: Path,
    *,
    compact_geojson_path: Path,
    relational_root: Path,
    compact_public_path: str = "data/neotoma/normalized/nordic_pollen_sites.geojson",
    relational_public_root: str = "data/neotoma/relational",
) -> Path:
    """Atomically write the deterministic compact-to-detail lineage review."""
    payload = build_neotoma_compact_lineage(
        compact_geojson_path=compact_geojson_path,
        relational_root=relational_root,
        compact_public_path=compact_public_path,
        relational_public_root=relational_public_root,
    )
    _write_atomic_json(Path(output_path), payload)
    return Path(output_path)


def _index_surface(
    root: Path,
    manifest: Mapping[str, object],
    *,
    surface: str,
    id_field: str,
    public_root: str,
) -> dict[str, dict[str, object]]:
    surfaces = _mapping(manifest.get("surfaces"), "relational surfaces")
    surface_manifest = _mapping(surfaces.get(surface), f"surface {surface}")
    parts = surface_manifest.get("parts")
    if not isinstance(parts, list):
        raise ValueError(f"Relational surface parts must be a list: {surface}")
    indexed: dict[str, dict[str, object]] = {}
    for part_value in parts:
        part = _mapping(part_value, f"surface {surface} part")
        relative_path = _safe_public_path(
            _required_text(part.get("path"), f"surface {surface} part path")
        )
        payload = _json_object(
            _read_regular_file(root.joinpath(*PurePosixPath(relative_path).parts)),
            relative_path,
        )
        rows = payload.get("rows")
        if not isinstance(rows, list):
            raise ValueError(f"Relational surface rows must be a list: {relative_path}")
        for row_index, row_value in enumerate(rows):
            row = _mapping(row_value, f"{relative_path} row {row_index}")
            site_id = _required_text(row.get("site_id"), f"{surface} site_id")
            row_id = _required_text(row.get(id_field), f"{surface} {id_field}")
            entry = indexed.setdefault(site_id, {"row_count": 0, "first_locator": None})
            entry["row_count"] = _integer(entry["row_count"], "row_count") + 1
            if entry["first_locator"] is None:
                entry["first_locator"] = {
                    "path": f"{public_root}/{relative_path}",
                    "json_pointer": f"/rows/{row_index}",
                    "identity_field": id_field,
                    "identity_value": row_id,
                    "parent_identities": {
                        field: row[field]
                        for field in (
                            "site_id",
                            "collection_unit_id",
                            "dataset_id",
                            "sample_id",
                            "chronology_id",
                        )
                        if field in row
                    },
                }
    return indexed


def _index_count(index: Mapping[str, Mapping[str, object]], site_id: str) -> int:
    entry = index.get(site_id)
    return 0 if entry is None else _integer(entry.get("row_count"), "row_count")


def _first_locator(index: Mapping[str, Mapping[str, object]], site_id: str) -> object:
    entry = index.get(site_id)
    return None if entry is None else entry.get("first_locator")


def _refusal_payload(
    *, compact_public_path: str, relational_public_root: str, reasons: list[str]
) -> dict[str, object]:
    return {
        "schema_version": LINEAGE_SCHEMA_VERSION,
        "source_family": "neotoma",
        "status": "refused",
        "refusal_reasons": sorted(reasons),
        "input_artifacts": {
            "compact_site_layer": {"path": compact_public_path, "sha256": None},
            "relational_detail": {
                "path": relational_public_root,
                "source_snapshot_id": None,
                "build_id": None,
                "materialization_sha256": None,
            },
        },
        "summary": {
            "compact_record_count": 0,
            "relational_site_count": 0,
            "linked_compact_record_count": 0,
            "compact_without_relational_count": 0,
            "relational_without_compact_count": 0,
            "sites_with_sample_evidence_count": 0,
            "representative_sample_reverse_trace_count": 0,
            "detail_row_totals": {},
        },
        "compact_without_relational_record_ids": [],
        "relational_without_compact_site_ids": [],
        "compact_to_relational": [],
        "relational_to_compact": [],
        "representative_sample_to_compact": [],
    }


def _write_atomic_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink() or path.parent.is_symlink():
        raise ValueError(f"Neotoma lineage output cannot use symlinks: {path}")
    content = _canonical_json(payload)
    candidate = path.parent / f".{path.name}.candidate"
    if candidate.exists() or candidate.is_symlink():
        raise FileExistsError(f"Neotoma lineage candidate path exists: {candidate}")
    try:
        with candidate.open("xb") as stream:
            stream.write(content)
        candidate.replace(path)
    finally:
        if candidate.exists():
            candidate.unlink()


def _read_regular_file(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Neotoma lineage input is not a regular file: {path}")
    return path.read_bytes()


def _json_object(content: bytes, label: str) -> dict[str, object]:
    try:
        payload = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Invalid JSON for {label}") from error
    if not isinstance(payload, dict):
        raise ValueError(f"JSON must be an object for {label}")
    return payload


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"Expected object for {label}")
    return value


def _required_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Expected non-empty text for {label}")
    return value


def _integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"Expected non-negative integer for {label}")
    return value


def _safe_public_path(value: str) -> str:
    candidate = PurePosixPath(value)
    if not value or candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"Unsafe Neotoma public path: {value!r}")
    return candidate.as_posix()


def _canonical_json(payload: object) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
