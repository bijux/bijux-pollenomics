"""Rebuild repository-owned SEAD surfaces from governed source evidence."""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, date, datetime
from pathlib import Path

from bijux_pollenomics.collection.contracts.artifacts import (
    SEAD_POINT_CSV,
    SEAD_POINT_GEOJSON,
)
from bijux_pollenomics.collection.sources.boundaries.store import (
    load_repository_country_boundaries,
)
from bijux_pollenomics.collection.sources.sead.acquisition.archive import (
    SEAD_LINKED_SOURCE_TABLES,
)
from bijux_pollenomics.collection.sources.sead.acquisition.governed import (
    validate_governed_sead_admission,
)
from bijux_pollenomics.collection.sources.sead.catalog.site_inventory import (
    build_sead_site_rows_from_acquisition_tables,
)
from bijux_pollenomics.collection.sources.sead.evidence.claims import (
    write_sead_chronology_claim_bundle_from_snapshot,
)
from bijux_pollenomics.collection.sources.sead.evidence.normalization import (
    normalize_sead_rows,
    normalize_sead_temporal_evidence,
)
from bijux_pollenomics.collection.sources.sead.evidence.review import (
    build_sead_scientific_classification_review,
    write_sead_scientific_classification_review,
)

from .model import (
    SEAD_GOVERNED_ACQUISITION_ID,
    SEAD_LEGACY_CHRONOLOGY_SUMMARY_RELATIVE_PATH,
    SeadDataReport,
)
from .publication import write_repository_surfaces
from .repository import (
    attach_sead_country_decisions,
    load_sead_acquisition_rows,
    validate_repository_site_archive,
)
from .repository_surfaces import (
    abort_repository_surface_transaction,
    prepare_repository_surface_transaction,
    publish_repository_surface_candidate,
    require_source_snapshot_unchanged,
)
from .validation import validate_sead_rows


def materialize_sead_repository_surfaces(data_root: Path) -> SeadDataReport:
    """Refresh the exact legacy surface set as one recoverable transaction."""
    data_root = validated_repository_data_root(data_root)
    output_root = data_root / "sead"
    raw_path = output_root / "raw" / "nordic_sites.json"
    validate_repository_site_archive(raw_path)
    acquisition_root = (
        output_root / "raw" / "acquisitions" / SEAD_GOVERNED_ACQUISITION_ID
    )
    validated_snapshot = validate_governed_sead_admission(
        acquisition_root, data_root=data_root
    )
    rows_by_table = {
        table: load_sead_acquisition_rows(validated_snapshot.copied_files, table)
        for table in SEAD_LINKED_SOURCE_TABLES
    }
    rows, _ = build_sead_site_rows_from_acquisition_tables(rows_by_table)
    attach_sead_country_decisions(validated_snapshot.copied_files, rows)
    validate_sead_rows("tbl_sites", rows)
    country_boundaries = load_repository_country_boundaries(data_root)
    records = normalize_sead_rows(rows, country_boundaries=country_boundaries)
    temporal_records = normalize_sead_temporal_evidence(
        rows, country_boundaries=country_boundaries
    )
    generated_on = source_snapshot_date(
        validated_snapshot.copied_files,
        expected_run_id=str(validated_snapshot.admission["run_id"]),
    )
    classification_packet = build_sead_scientific_classification_review(data_root)
    transaction = prepare_repository_surface_transaction(
        data_root,
        artifacts_root=(
            data_root.parent
            / "artifacts"
            / "execution-control"
            / "sead-repository-surfaces"
        ),
    )
    try:
        write_sead_chronology_claim_bundle_from_snapshot(
            validated_snapshot,
            transaction.candidate_data_root
            / SEAD_LEGACY_CHRONOLOGY_SUMMARY_RELATIVE_PATH,
        )
        write_repository_surfaces(
            transaction.candidate_data_root,
            context_data_root=data_root,
            rows=rows,
            records=records,
            temporal_records=temporal_records,
            admission=dict(validated_snapshot.admission),
            generated_on=generated_on,
        )
        write_sead_scientific_classification_review(
            transaction.candidate_data_root / "sead" / "review",
            classification_packet,
        )
        require_source_snapshot_unchanged(
            acquisition_root, validated_snapshot.copied_files
        )
    except BaseException as error:
        abort_repository_surface_transaction(transaction, error)
        raise
    publish_repository_surface_candidate(transaction)
    return SeadDataReport(
        output_dir=output_root,
        point_count=len(records),
        raw_path=raw_path,
        normalized_csv_path=SEAD_POINT_CSV.path_under(data_root),
        normalized_geojson_path=SEAD_POINT_GEOJSON.path_under(data_root),
    )


def validated_repository_data_root(data_root: Path) -> Path:
    candidate = Path(data_root)
    absolute = candidate if candidate.is_absolute() else Path.cwd() / candidate
    if absolute == Path(absolute.anchor):
        raise ValueError("SEAD repository data root must not be a filesystem root")
    cursor = Path(absolute.anchor)
    for component in absolute.parts[1:]:
        cursor /= component
        if cursor.is_symlink():
            raise ValueError("SEAD repository data root must not traverse a symlink")
    try:
        resolved = absolute.resolve(strict=True)
    except OSError as error:
        raise ValueError("SEAD repository data root must exist") from error
    if resolved == Path(resolved.anchor):
        raise ValueError(
            "SEAD repository data root must not resolve to a filesystem root"
        )
    if not resolved.is_dir():
        raise ValueError("SEAD repository data root must be a directory")
    return resolved


def source_snapshot_date(
    copied_files: Mapping[str, bytes], *, expected_run_id: str
) -> date:
    """Return the governed capture date rather than the wall-clock run date."""
    try:
        receipt = json.loads(copied_files["receipts/tbl_sites.json"])
        started_at = receipt["started_at"]
        run_id = receipt["run_id"]
    except (KeyError, TypeError, json.JSONDecodeError) as error:
        raise ValueError("SEAD site receipt lacks a governed capture date") from error
    if not isinstance(started_at, str):
        raise TypeError("SEAD site receipt capture date is invalid")
    if run_id != expected_run_id:
        raise ValueError("SEAD site receipt run identity differs")
    try:
        captured_at = datetime.fromisoformat(started_at)
    except ValueError as error:
        raise ValueError("SEAD site receipt capture date is invalid") from error
    if captured_at.tzinfo is None:
        raise ValueError("SEAD site receipt capture date must include a timezone")
    return captured_at.astimezone(UTC).date()
