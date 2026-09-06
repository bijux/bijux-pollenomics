"""Deterministic atomic publication for Neotoma relational snapshots."""

from __future__ import annotations

import copy
import hashlib
from collections import Counter
from collections.abc import Mapping
from pathlib import Path

from bijux_pollenomics.core.owned_tree import (
    build_recovery_output_dir,
    build_staging_output_dir,
    remove_output_tree,
    replace_output_tree,
)
from bijux_pollenomics.evidence.sources.neotoma import (
    DEFAULT_ROWS_PER_PART,
    validate_neotoma_relational_materialization,
)
from bijux_pollenomics.evidence.sources.neotoma.contract import (
    COUNTRY_CODES,
    COUNTRY_SURFACE_COUNT_FIELDS,
    MATERIALIZATION_MANIFEST_SCHEMA_VERSION,
    PART_SCHEMA_VERSION,
    RECONCILIATION_SCHEMA_VERSION,
    RELATIONAL_SNAPSHOT_SCHEMA_VERSION,
    SURFACE_ID_FIELDS,
    accumulate_country_partition,
    accumulate_site_attribution,
    canonical_json_bytes,
    expect_equal,
    materialization_digest,
    required_text,
    surface_schema_version,
    validate_reconciliation_counts,
)

__all__ = ["materialize_neotoma_relational_snapshot"]


def materialize_neotoma_relational_snapshot(
    final_output_root: Path,
    snapshot: Mapping[str, object],
    *,
    rows_per_part: int = DEFAULT_ROWS_PER_PART,
) -> Path:
    """Publish one validated multipart snapshot through a sibling staging tree."""
    final_root = _validate_publication_target(final_output_root)
    if rows_per_part < 1:
        raise ValueError("rows_per_part must be at least 1")
    if final_root.exists():
        validate_neotoma_relational_materialization(final_root)

    staging_root = build_staging_output_dir(final_root)
    recovery_root = build_recovery_output_dir(final_root)
    if staging_root.exists() or staging_root.is_symlink():
        raise FileExistsError(f"Neotoma staging path collision: {staging_root}")
    if recovery_root.exists() or recovery_root.is_symlink():
        raise FileExistsError(f"Neotoma recovery path collision: {recovery_root}")

    staging_root.mkdir()
    try:
        _write_materialization(
            staging_root,
            snapshot=snapshot,
            rows_per_part=rows_per_part,
        )
        validate_neotoma_relational_materialization(staging_root)
        replace_output_tree(
            final_output_root=final_root,
            staging_output_root=staging_root,
        )
    except Exception:
        remove_output_tree(staging_root)
        raise
    return final_root / "manifest.json"


def _write_materialization(
    staging_root: Path,
    *,
    snapshot: Mapping[str, object],
    rows_per_part: int,
) -> None:
    expect_equal(
        snapshot.get("schema_version"),
        RELATIONAL_SNAPSHOT_SCHEMA_VERSION,
        "input snapshot schema_version",
    )
    expect_equal(snapshot.get("source_family"), "neotoma", "input source_family")
    source_snapshot_id = required_text(
        snapshot.get("source_snapshot_id"), "input source_snapshot_id"
    )
    build_id = required_text(snapshot.get("build_id"), "input build_id")
    reconciliation = snapshot.get("reconciliation")
    if not isinstance(reconciliation, Mapping):
        raise ValueError("Input snapshot reconciliation must be an object")

    surfaces_root = staging_root / "surfaces"
    surfaces_root.mkdir()
    surface_manifests: dict[str, object] = {}
    digest_records: list[dict[str, str]] = []
    surface_row_counts: dict[str, int] = {}
    country_partitions: dict[str, Counter[str]] = {}
    site_statuses: Counter[str] = Counter()
    site_eligibility: Counter[str] = Counter()
    for surface_name, id_field in SURFACE_ID_FIELDS.items():
        raw_rows = snapshot.get(surface_name)
        if not isinstance(raw_rows, list):
            raise ValueError(f"Input snapshot surface must be a list: {surface_name}")
        rows = _normalized_rows(
            raw_rows,
            id_field=id_field,
            surface_name=surface_name,
        )
        surface_row_counts[surface_name] = len(rows)
        if surface_name in COUNTRY_SURFACE_COUNT_FIELDS:
            partition: Counter[str] = Counter(dict.fromkeys(COUNTRY_CODES, 0))
            accumulate_country_partition(
                rows,
                surface_name=surface_name,
                partition=partition,
            )
            country_partitions[surface_name] = partition
        if surface_name == "sites":
            accumulate_site_attribution(
                rows,
                statuses=site_statuses,
                eligibility=site_eligibility,
            )
        surface_root = surfaces_root / surface_name
        surface_root.mkdir()
        chunks = [
            rows[start : start + rows_per_part]
            for start in range(0, len(rows), rows_per_part)
        ]
        part_records: list[dict[str, object]] = []
        for part_number, chunk in enumerate(chunks, start=1):
            relative_path = f"surfaces/{surface_name}/part-{part_number:05d}.json"
            part_payload = {
                "schema_version": PART_SCHEMA_VERSION,
                "surface_schema_version": surface_schema_version(surface_name),
                "relational_snapshot_schema_version": (
                    RELATIONAL_SNAPSHOT_SCHEMA_VERSION
                ),
                "source_family": "neotoma",
                "source_snapshot_id": source_snapshot_id,
                "build_id": build_id,
                "surface": surface_name,
                "part_number": part_number,
                "part_count": len(chunks),
                "row_count": len(chunk),
                "rows": chunk,
            }
            digest = _write_json_exclusive(staging_root / relative_path, part_payload)
            part_record = {
                "path": relative_path,
                "schema_version": PART_SCHEMA_VERSION,
                "surface_schema_version": surface_schema_version(surface_name),
                "part_number": part_number,
                "row_count": len(chunk),
                "sha256": digest,
            }
            part_records.append(part_record)
            digest_records.append({"path": relative_path, "sha256": digest})
        surface_manifests[surface_name] = {
            "schema_version": surface_schema_version(surface_name),
            "id_field": id_field,
            "row_count": len(rows),
            "part_count": len(chunks),
            "parts": part_records,
        }

    validate_reconciliation_counts(
        reconciliation,
        surface_row_counts,
        country_partitions=country_partitions,
        site_statuses=site_statuses,
        site_eligibility=site_eligibility,
    )

    reconciliation_path = "reconciliation.json"
    reconciliation_payload = {
        "schema_version": RECONCILIATION_SCHEMA_VERSION,
        "relational_snapshot_schema_version": RELATIONAL_SNAPSHOT_SCHEMA_VERSION,
        "source_family": "neotoma",
        "source_snapshot_id": source_snapshot_id,
        "build_id": build_id,
        "reconciliation": copy.deepcopy(dict(reconciliation)),
    }
    reconciliation_digest = _write_json_exclusive(
        staging_root / reconciliation_path,
        reconciliation_payload,
    )
    digest_records.append(
        {"path": reconciliation_path, "sha256": reconciliation_digest}
    )
    manifest = {
        "schema_version": MATERIALIZATION_MANIFEST_SCHEMA_VERSION,
        "relational_snapshot_schema_version": RELATIONAL_SNAPSHOT_SCHEMA_VERSION,
        "source_family": "neotoma",
        "source_snapshot_id": source_snapshot_id,
        "build_id": build_id,
        "rows_per_part": rows_per_part,
        "surfaces": surface_manifests,
        "reconciliation": {
            "path": reconciliation_path,
            "schema_version": RECONCILIATION_SCHEMA_VERSION,
            "sha256": reconciliation_digest,
        },
        "materialization_sha256": materialization_digest(digest_records),
    }
    _write_json_exclusive(staging_root / "manifest.json", manifest)


def _normalized_rows(
    raw_rows: list[object],
    *,
    id_field: str,
    surface_name: str,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    identifiers: set[str] = set()
    for raw_row in raw_rows:
        if not isinstance(raw_row, Mapping):
            raise ValueError(f"Non-object row in surface {surface_name}")
        row = copy.deepcopy(dict(raw_row))
        identifier = required_text(row.get(id_field), f"{surface_name}.{id_field}")
        if identifier in identifiers:
            raise ValueError(
                f"Duplicate {id_field} in surface {surface_name}: {identifier}"
            )
        identifiers.add(identifier)
        rows.append(row)
    rows.sort(key=lambda row: str(row[id_field]))
    return rows


def _write_json_exclusive(path: Path, payload: object) -> str:
    content = canonical_json_bytes(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(content)
        stream.flush()
    return hashlib.sha256(content).hexdigest()


def _validate_publication_target(final_output_root: Path) -> Path:
    final_root = Path(final_output_root)
    if not final_root.is_absolute():
        raise ValueError("Neotoma materialization path must be absolute")
    resolved = final_root.resolve(strict=False)
    if resolved == Path(resolved.anchor) or resolved == Path.home().resolve():
        raise ValueError(f"Unsafe Neotoma materialization target: {final_root}")
    if final_root.is_symlink():
        raise ValueError(
            f"Neotoma materialization target cannot be a symlink: {final_root}"
        )
    if final_root.exists() and not final_root.is_dir():
        raise ValueError(
            f"Neotoma materialization target is not a directory: {final_root}"
        )
    if not final_root.parent.is_dir():
        raise ValueError(
            f"Neotoma materialization parent must already exist: {final_root.parent}"
        )
    return final_root
