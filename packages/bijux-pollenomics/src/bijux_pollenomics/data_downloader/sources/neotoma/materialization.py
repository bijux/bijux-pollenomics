"""Deterministic atomic publication for Neotoma relational snapshots."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
import copy
import hashlib
import json
from pathlib import Path, PurePosixPath
import re

from ....core.owned_tree import (
    build_recovery_output_dir,
    build_staging_output_dir,
    remove_output_tree,
    replace_output_tree,
)

__all__ = [
    "materialize_neotoma_relational_snapshot",
    "validate_neotoma_relational_materialization",
]

MATERIALIZATION_MANIFEST_SCHEMA_VERSION = (
    "neotoma-relational-materialization-manifest.v1"
)
PART_SCHEMA_VERSION = "neotoma-relational-part.v1"
RECONCILIATION_SCHEMA_VERSION = "neotoma-relational-reconciliation.v2"
RELATIONAL_SNAPSHOT_SCHEMA_VERSION = "neotoma-relational-snapshot.v2"
DEFAULT_ROWS_PER_PART = 50_000

_SURFACE_ID_FIELDS = {
    "sites": "site_id",
    "collection_units": "collection_unit_id",
    "datasets": "dataset_id",
    "chronologies": "chronology_id",
    "chronology_controls": "chronology_control_id",
    "samples": "sample_id",
    "age_claims": "chronology_claim_id",
    "variables": "variable_id",
    "observations": "observation_id",
    "conflicts": "conflict_id",
    "orphans": "orphan_id",
}
_RELATIONAL_TABLE_SURFACES = tuple(_SURFACE_ID_FIELDS)[:9]
_COUNTRY_CODES = ("SE", "DK", "NO", "FI", "UNASSIGNED")
_COUNTRY_SURFACE_COUNT_FIELDS = {
    "sites": "sites",
    "collection_units": "collection_units",
    "datasets": "datasets",
    "chronologies": "chronologies",
    "chronology_controls": "chronology_controls",
    "samples": "samples",
    "age_claims": "age_claim_rows",
    "observations": "observation_rows",
}
_COUNTRY_DECISION_STATUSES = ("assigned", "review", "unassigned", "refused")
_PROPAGATION_ELIGIBILITY = ("eligible", "blocked")
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}\Z")


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


def validate_neotoma_relational_materialization(
    output_root: Path,
) -> dict[str, object]:
    """Validate schemas, counts, paths, ordering, and all published digests."""
    root = Path(output_root)
    if not root.is_absolute():
        raise ValueError("Neotoma materialization path must be absolute")
    if root.is_symlink() or not root.is_dir():
        raise ValueError(f"Neotoma materialization root is not a directory: {root}")
    manifest_path = root / "manifest.json"
    manifest = _read_json_object(manifest_path)
    _expect_equal(
        manifest.get("schema_version"),
        MATERIALIZATION_MANIFEST_SCHEMA_VERSION,
        "manifest schema_version",
    )
    _expect_equal(
        manifest.get("relational_snapshot_schema_version"),
        RELATIONAL_SNAPSHOT_SCHEMA_VERSION,
        "relational snapshot schema_version",
    )
    _expect_equal(manifest.get("source_family"), "neotoma", "manifest source_family")
    source_snapshot_id = _required_text(
        manifest.get("source_snapshot_id"), "manifest source_snapshot_id"
    )
    build_id = _required_text(manifest.get("build_id"), "manifest build_id")
    rows_per_part = _positive_integer(
        manifest.get("rows_per_part"), "manifest rows_per_part"
    )
    surfaces = manifest.get("surfaces")
    if not isinstance(surfaces, Mapping) or set(surfaces) != set(_SURFACE_ID_FIELDS):
        raise ValueError("Manifest surfaces do not match the Neotoma v2 surfaces")

    expected_files = {"manifest.json"}
    digest_records: list[dict[str, str]] = []
    surface_row_counts: dict[str, int] = {}
    country_partitions: dict[str, Counter[str]] = {}
    site_statuses: Counter[str] = Counter()
    site_eligibility: Counter[str] = Counter()
    for surface_name, id_field in _SURFACE_ID_FIELDS.items():
        surface = surfaces.get(surface_name)
        if not isinstance(surface, Mapping):
            raise ValueError(f"Invalid surface manifest: {surface_name}")
        surface_schema = _surface_schema_version(surface_name)
        _expect_equal(
            surface.get("schema_version"),
            surface_schema,
            f"{surface_name} schema_version",
        )
        _expect_equal(surface.get("id_field"), id_field, f"{surface_name} id_field")
        row_count = _non_negative_integer(
            surface.get("row_count"), f"{surface_name} row_count"
        )
        surface_row_counts[surface_name] = row_count
        part_count = _non_negative_integer(
            surface.get("part_count"), f"{surface_name} part_count"
        )
        parts = surface.get("parts")
        if not isinstance(parts, list) or len(parts) != part_count:
            raise ValueError(f"Invalid part count for surface {surface_name}")
        observed_rows = 0
        observed_ids: list[str] = []
        country_partition: Counter[str] | None = None
        if surface_name in _COUNTRY_SURFACE_COUNT_FIELDS:
            country_partition = Counter({code: 0 for code in _COUNTRY_CODES})
        for expected_number, part in enumerate(parts, start=1):
            if not isinstance(part, Mapping):
                raise ValueError(f"Invalid part manifest for surface {surface_name}")
            _expect_equal(
                part.get("schema_version"),
                PART_SCHEMA_VERSION,
                f"{surface_name} part manifest schema_version",
            )
            _expect_equal(
                part.get("surface_schema_version"),
                surface_schema,
                f"{surface_name} part manifest surface_schema_version",
            )
            _expect_equal(
                part.get("part_number"),
                expected_number,
                f"{surface_name} part manifest part_number",
            )
            expected_relative_path = (
                f"surfaces/{surface_name}/part-{expected_number:05d}.json"
            )
            relative_path = _safe_relative_path(part.get("path"))
            _expect_equal(
                relative_path,
                expected_relative_path,
                f"{surface_name} part path",
            )
            if relative_path in expected_files:
                raise ValueError(f"Duplicate materialization path: {relative_path}")
            expected_files.add(relative_path)
            part_path = root.joinpath(*PurePosixPath(relative_path).parts)
            digest = _validated_sha256(part.get("sha256"), relative_path)
            actual_digest = hashlib.sha256(_read_regular_file(part_path)).hexdigest()
            if actual_digest != digest:
                raise ValueError(f"SHA-256 mismatch for {relative_path}")
            part_payload = _read_json_object(part_path)
            _expect_equal(
                part_payload.get("schema_version"),
                PART_SCHEMA_VERSION,
                f"{relative_path} schema_version",
            )
            _expect_equal(
                part_payload.get("surface_schema_version"),
                surface_schema,
                f"{relative_path} surface_schema_version",
            )
            _expect_equal(
                part_payload.get("relational_snapshot_schema_version"),
                RELATIONAL_SNAPSHOT_SCHEMA_VERSION,
                f"{relative_path} snapshot schema_version",
            )
            _expect_equal(
                part_payload.get("source_snapshot_id"),
                source_snapshot_id,
                f"{relative_path} source_snapshot_id",
            )
            _expect_equal(
                part_payload.get("build_id"), build_id, f"{relative_path} build_id"
            )
            _expect_equal(
                part_payload.get("surface"), surface_name, f"{relative_path} surface"
            )
            _expect_equal(
                part_payload.get("part_number"),
                expected_number,
                f"{relative_path} part_number",
            )
            _expect_equal(
                part_payload.get("part_count"),
                part_count,
                f"{relative_path} part_count",
            )
            rows = part_payload.get("rows")
            if not isinstance(rows, list):
                raise ValueError(f"Part rows must be a list: {relative_path}")
            part_row_count = _non_negative_integer(
                part_payload.get("row_count"), f"{relative_path} row_count"
            )
            manifest_part_row_count = _non_negative_integer(
                part.get("row_count"), f"{relative_path} manifest row_count"
            )
            _expect_equal(
                manifest_part_row_count,
                part_row_count,
                f"{relative_path} manifest rows",
            )
            if part_row_count != len(rows):
                raise ValueError(f"Part row loss detected: {relative_path}")
            if part_row_count > rows_per_part:
                raise ValueError(f"Part exceeds rows_per_part: {relative_path}")
            row_ids = _row_ids(rows, id_field=id_field, surface_name=surface_name)
            if country_partition is not None:
                _accumulate_country_partition(
                    rows,
                    surface_name=surface_name,
                    partition=country_partition,
                )
            if surface_name == "sites":
                _accumulate_site_attribution(
                    rows,
                    statuses=site_statuses,
                    eligibility=site_eligibility,
                )
            if row_ids != sorted(row_ids):
                raise ValueError(f"Rows are not stably ordered: {relative_path}")
            observed_ids.extend(row_ids)
            observed_rows += part_row_count
            digest_records.append({"path": relative_path, "sha256": digest})
        if observed_rows != row_count:
            raise ValueError(f"Surface row loss detected: {surface_name}")
        if len(observed_ids) != len(set(observed_ids)):
            raise ValueError(f"Duplicate row identifiers in surface {surface_name}")
        if observed_ids != sorted(observed_ids):
            raise ValueError(f"Parts are not globally ordered: {surface_name}")
        if country_partition is not None:
            country_partitions[surface_name] = country_partition

    reconciliation = manifest.get("reconciliation")
    if not isinstance(reconciliation, Mapping):
        raise ValueError("Manifest reconciliation artifact is missing")
    _expect_equal(
        reconciliation.get("schema_version"),
        RECONCILIATION_SCHEMA_VERSION,
        "reconciliation manifest schema_version",
    )
    reconciliation_path = _safe_relative_path(reconciliation.get("path"))
    _expect_equal(reconciliation_path, "reconciliation.json", "reconciliation path")
    if reconciliation_path in expected_files:
        raise ValueError(f"Duplicate materialization path: {reconciliation_path}")
    expected_files.add(reconciliation_path)
    reconciliation_digest = _validated_sha256(
        reconciliation.get("sha256"), reconciliation_path
    )
    reconciliation_file = root / reconciliation_path
    actual_reconciliation_digest = hashlib.sha256(
        _read_regular_file(reconciliation_file)
    ).hexdigest()
    if actual_reconciliation_digest != reconciliation_digest:
        raise ValueError("SHA-256 mismatch for reconciliation.json")
    reconciliation_payload = _read_json_object(reconciliation_file)
    _expect_equal(
        reconciliation_payload.get("schema_version"),
        RECONCILIATION_SCHEMA_VERSION,
        "reconciliation schema_version",
    )
    _expect_equal(
        reconciliation_payload.get("relational_snapshot_schema_version"),
        RELATIONAL_SNAPSHOT_SCHEMA_VERSION,
        "reconciliation snapshot schema_version",
    )
    _expect_equal(
        reconciliation_payload.get("source_family"),
        "neotoma",
        "reconciliation source_family",
    )
    _expect_equal(
        reconciliation_payload.get("source_snapshot_id"),
        source_snapshot_id,
        "reconciliation source_snapshot_id",
    )
    _expect_equal(
        reconciliation_payload.get("build_id"),
        build_id,
        "reconciliation build_id",
    )
    if not isinstance(reconciliation_payload.get("reconciliation"), Mapping):
        raise ValueError("Reconciliation payload is missing its accounting object")
    reconciliation_accounting = reconciliation_payload["reconciliation"]
    if not isinstance(reconciliation_accounting, Mapping):
        raise ValueError("Reconciliation payload is missing its accounting object")
    _validate_reconciliation_counts(
        reconciliation_accounting,
        surface_row_counts,
        country_partitions=country_partitions,
        site_statuses=site_statuses,
        site_eligibility=site_eligibility,
    )
    digest_records.append(
        {"path": reconciliation_path, "sha256": reconciliation_digest}
    )
    _expect_equal(
        manifest.get("materialization_sha256"),
        _materialization_digest(digest_records),
        "materialization_sha256",
    )

    actual_files: set[str] = set()
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"Symlinks are not allowed in materialization: {path}")
        if path.is_file():
            actual_files.add(path.relative_to(root).as_posix())
    if actual_files != expected_files:
        unexpected = sorted(actual_files - expected_files)
        missing = sorted(expected_files - actual_files)
        raise ValueError(
            f"Materialization file-set mismatch; unexpected={unexpected}, missing={missing}"
        )
    return copy.deepcopy(dict(manifest))


def _write_materialization(
    staging_root: Path,
    *,
    snapshot: Mapping[str, object],
    rows_per_part: int,
) -> None:
    _expect_equal(
        snapshot.get("schema_version"),
        RELATIONAL_SNAPSHOT_SCHEMA_VERSION,
        "input snapshot schema_version",
    )
    _expect_equal(snapshot.get("source_family"), "neotoma", "input source_family")
    source_snapshot_id = _required_text(
        snapshot.get("source_snapshot_id"), "input source_snapshot_id"
    )
    build_id = _required_text(snapshot.get("build_id"), "input build_id")
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
    for surface_name, id_field in _SURFACE_ID_FIELDS.items():
        raw_rows = snapshot.get(surface_name)
        if not isinstance(raw_rows, list):
            raise ValueError(f"Input snapshot surface must be a list: {surface_name}")
        rows = _normalized_rows(
            raw_rows,
            id_field=id_field,
            surface_name=surface_name,
        )
        surface_row_counts[surface_name] = len(rows)
        if surface_name in _COUNTRY_SURFACE_COUNT_FIELDS:
            partition: Counter[str] = Counter({code: 0 for code in _COUNTRY_CODES})
            _accumulate_country_partition(
                rows,
                surface_name=surface_name,
                partition=partition,
            )
            country_partitions[surface_name] = partition
        if surface_name == "sites":
            _accumulate_site_attribution(
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
                "surface_schema_version": _surface_schema_version(surface_name),
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
                "surface_schema_version": _surface_schema_version(surface_name),
                "part_number": part_number,
                "row_count": len(chunk),
                "sha256": digest,
            }
            part_records.append(part_record)
            digest_records.append({"path": relative_path, "sha256": digest})
        surface_manifests[surface_name] = {
            "schema_version": _surface_schema_version(surface_name),
            "id_field": id_field,
            "row_count": len(rows),
            "part_count": len(chunks),
            "parts": part_records,
        }

    _validate_reconciliation_counts(
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
        "materialization_sha256": _materialization_digest(digest_records),
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
        identifier = _required_text(row.get(id_field), f"{surface_name}.{id_field}")
        if identifier in identifiers:
            raise ValueError(
                f"Duplicate {id_field} in surface {surface_name}: {identifier}"
            )
        identifiers.add(identifier)
        rows.append(row)
    rows.sort(key=lambda row: str(row[id_field]))
    return rows


def _row_ids(rows: list[object], *, id_field: str, surface_name: str) -> list[str]:
    identifiers: list[str] = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError(f"Non-object row in surface {surface_name}")
        identifiers.append(
            _required_text(row.get(id_field), f"{surface_name}.{id_field}")
        )
    return identifiers


def _validate_reconciliation_counts(
    reconciliation: Mapping[str, object],
    surface_row_counts: Mapping[str, int],
    *,
    country_partitions: Mapping[str, Counter[str]],
    site_statuses: Counter[str],
    site_eligibility: Counter[str],
) -> None:
    normalized_counts = reconciliation.get("normalized_row_counts")
    if not isinstance(normalized_counts, Mapping):
        raise ValueError("Reconciliation normalized_row_counts must be an object")
    for surface_name in _RELATIONAL_TABLE_SURFACES:
        expected = _non_negative_integer(
            normalized_counts.get(surface_name),
            f"reconciliation normalized_row_counts.{surface_name}",
        )
        _expect_equal(
            surface_row_counts[surface_name],
            expected,
            f"reconciled {surface_name} row_count",
        )
    for surface_name, reconciliation_field in (
        ("conflicts", "conflict_count"),
        ("orphans", "orphan_count"),
    ):
        expected = _non_negative_integer(
            reconciliation.get(reconciliation_field),
            f"reconciliation {reconciliation_field}",
        )
        _expect_equal(
            surface_row_counts[surface_name],
            expected,
            f"reconciled {surface_name} row_count",
        )

    country_counts = reconciliation.get("country_counts")
    if not isinstance(country_counts, Mapping) or set(country_counts) != set(
        _COUNTRY_CODES
    ):
        raise ValueError(
            "Reconciliation country_counts must contain exactly "
            "SE, DK, NO, FI, and UNASSIGNED"
        )
    for surface_name, reconciliation_field in _COUNTRY_SURFACE_COUNT_FIELDS.items():
        partition = country_partitions.get(surface_name)
        if partition is None:
            raise ValueError(f"Missing country partition for surface {surface_name}")
        if sum(partition.values()) != surface_row_counts[surface_name]:
            raise ValueError(f"Country partition does not cover surface {surface_name}")
        for country_code in _COUNTRY_CODES:
            country = country_counts.get(country_code)
            if not isinstance(country, Mapping):
                raise ValueError(f"Invalid country_counts bin: {country_code}")
            reconciled_count = _non_negative_integer(
                country.get(reconciliation_field),
                f"country_counts.{country_code}.{reconciliation_field}",
            )
            _expect_equal(
                partition[country_code],
                reconciled_count,
                f"{surface_name} {country_code} country partition",
            )

    attribution_counts = reconciliation.get("country_attribution_counts")
    if not isinstance(attribution_counts, Mapping):
        raise ValueError("Reconciliation country_attribution_counts must be an object")
    _validate_named_partition(
        attribution_counts.get("decision_statuses"),
        names=_COUNTRY_DECISION_STATUSES,
        observed=site_statuses,
        expected_total=surface_row_counts["sites"],
        label="country attribution decision statuses",
    )
    _validate_named_partition(
        attribution_counts.get("propagation_eligibility"),
        names=_PROPAGATION_ELIGIBILITY,
        observed=site_eligibility,
        expected_total=surface_row_counts["sites"],
        label="country attribution propagation eligibility",
    )
    _validate_named_partition(
        attribution_counts.get("final_country_codes"),
        names=_COUNTRY_CODES,
        observed=country_partitions["sites"],
        expected_total=surface_row_counts["sites"],
        label="country attribution final country codes",
    )


def _accumulate_country_partition(
    rows: Iterable[object],
    *,
    surface_name: str,
    partition: Counter[str],
) -> None:
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError(f"Non-object row in surface {surface_name}")
        country_code = row.get("country_code")
        if country_code not in _COUNTRY_CODES:
            raise ValueError(
                f"Invalid or missing country_code in surface {surface_name}: "
                f"{country_code!r}"
            )
        partition[str(country_code)] += 1


def _accumulate_site_attribution(
    rows: Iterable[object],
    *,
    statuses: Counter[str],
    eligibility: Counter[str],
) -> None:
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("Non-object row in surface sites")
        status = row.get("country_decision_status")
        if status not in _COUNTRY_DECISION_STATUSES:
            raise ValueError(f"Invalid country decision status on site: {status!r}")
        statuses[str(status)] += 1
        propagation_eligible = row.get("country_propagation_eligible")
        if not isinstance(propagation_eligible, bool):
            raise ValueError("Site country_propagation_eligible must be boolean")
        eligibility["eligible" if propagation_eligible else "blocked"] += 1


def _validate_named_partition(
    value: object,
    *,
    names: tuple[str, ...],
    observed: Counter[str],
    expected_total: int,
    label: str,
) -> None:
    if not isinstance(value, Mapping) or not set(value).issubset(names):
        raise ValueError(f"Invalid {label}")
    reconciled = {
        name: _non_negative_integer(value.get(name, 0), f"{label}.{name}")
        for name in names
    }
    if sum(reconciled.values()) != expected_total:
        raise ValueError(f"{label} do not sum to site rows")
    for name in names:
        _expect_equal(observed[name], reconciled[name], f"{label}.{name}")


def _surface_schema_version(surface_name: str) -> str:
    return f"neotoma-relational-{surface_name.replace('_', '-')}.v2"


def _write_json_exclusive(path: Path, payload: object) -> str:
    content = _canonical_json(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(content)
        stream.flush()
    return hashlib.sha256(content).hexdigest()


def _canonical_json(payload: object) -> bytes:
    return (
        json.dumps(
            payload,
            allow_nan=False,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def _materialization_digest(records: list[dict[str, str]]) -> str:
    return hashlib.sha256(
        _canonical_json({"files": sorted(records, key=lambda row: row["path"])})
    ).hexdigest()


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


def _safe_relative_path(value: object) -> str:
    text = _required_text(value, "manifest relative path")
    path = PurePosixPath(text)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"Unsafe materialization path: {text}")
    if path.as_posix() != text:
        raise ValueError(f"Non-canonical materialization path: {text}")
    return text


def _read_regular_file(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Materialization file is missing or unsafe: {path}")
    return path.read_bytes()


def _read_json_object(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(_read_regular_file(path))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError(f"Invalid JSON materialization file: {path}") from error
    if not isinstance(payload, dict):
        raise ValueError(f"Materialization JSON root must be an object: {path}")
    return payload


def _required_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _positive_integer(value: object, label: str) -> int:
    number = _non_negative_integer(value, label)
    if number < 1:
        raise ValueError(f"{label} must be at least 1")
    return number


def _non_negative_integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")
    return value


def _validated_sha256(value: object, label: str) -> str:
    if not isinstance(value, str) or _SHA256_PATTERN.fullmatch(value) is None:
        raise ValueError(f"Invalid SHA-256 for {label}")
    return value


def _expect_equal(actual: object, expected: object, label: str) -> None:
    if actual != expected:
        raise ValueError(f"Unexpected {label}: {actual!r}; expected {expected!r}")
