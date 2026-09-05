from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from ..relational import CountryAttributionInput
from .models import (
    NeotomaProductionConfig,
    NeotomaProductionReport,
    _BoundaryAuthority,
    _RawArchive,
)


def run_production(
    *,
    raw_archive_root: Path,
    boundary_root: Path,
    output_root: Path,
    approved_output_parent: Path,
    config: NeotomaProductionConfig | None,
    validate_output: Callable[[Path, Path], Path],
    load_raw_archive: Callable[[Path], _RawArchive],
    load_boundary_authority: Callable[[Path], _BoundaryAuthority],
    build_id: Any,
    build_country_decisions: Any,
    build_snapshot: Any,
    materialize_snapshot: Any,
    parse_mapping: Callable[[object, str], Mapping[str, object]],
    parse_integer: Callable[[object, str], int],
) -> NeotomaProductionReport:
    resolved_output = validate_output(output_root, approved_output_parent)
    production_config = (config or NeotomaProductionConfig()).validated()
    raw_archive = load_raw_archive(Path(raw_archive_root))
    boundary_authority = load_boundary_authority(Path(boundary_root))
    production_build_id = build_id(
        source_snapshot_id=raw_archive.source_snapshot_id,
        boundary_authority_id=boundary_authority.authority_id,
        config=production_config,
    )
    decisions = build_country_decisions(
        raw_archive.rows,
        boundary_authority.boundaries,
        boundary_artifact_digest=boundary_authority.artifact_digest,
        boundary_version=boundary_authority.version,
        raw_country_aliases=dict(production_config.raw_country_aliases),
        proximity_tolerance=production_config.proximity_tolerance,
    )
    country_inputs: dict[object, CountryAttributionInput] = dict(decisions.items())
    snapshot = build_snapshot(
        raw_archive.rows,
        source_snapshot_id=raw_archive.source_snapshot_id,
        build_id=production_build_id,
        country_by_site_id=country_inputs,
    )
    manifest_path = materialize_snapshot(
        resolved_output,
        snapshot,
        rows_per_part=production_config.rows_per_part,
    )
    reconciliation = parse_mapping(snapshot.get("reconciliation"), "reconciliation")
    country_reconciliation = parse_mapping(
        reconciliation.get("country_counts"), "country_counts"
    )
    country_counts = {
        code: parse_integer(
            parse_mapping(country_reconciliation.get(code), code).get("sites"), code
        )
        for code in ("SE", "DK", "NO", "FI", "UNASSIGNED")
    }
    attribution = parse_mapping(
        reconciliation.get("country_attribution_counts"),
        "country_attribution_counts",
    )
    statuses = parse_mapping(attribution.get("decision_statuses"), "decision_statuses")
    site_rows = snapshot.get("sites")
    if not isinstance(site_rows, list):
        raise ValueError("Relational snapshot sites must be a list")
    return NeotomaProductionReport(
        manifest_path=str(manifest_path),
        source_snapshot_id=raw_archive.source_snapshot_id,
        boundary_authority_id=boundary_authority.authority_id,
        build_id=production_build_id,
        raw_part_count=len(raw_archive.part_digests),
        raw_row_count=len(raw_archive.rows),
        site_count=len(site_rows),
        country_counts=country_counts,
        country_decision_counts={
            status: parse_integer(statuses.get(status, 0), status)
            for status in ("assigned", "review", "unassigned", "refused")
        },
    )
