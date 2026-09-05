"""Deterministic publication of governed boundary and point review ledgers."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from .authority import _boundary_identity, _build_boundary_review
from .authority import _load_boundary_authority
from .decisions import _decision_summary, build_point_country_decision
from .loaders import _load_governed_points
from .models import BoundaryCountryReviewReport, JsonObject
from .policy import COUNTRY_ORDER
from .serialization import _file_sha256, _write_json_atomic


def materialize_boundary_country_review(
    repository_root: Path,
    *,
    output_root: Path | None = None,
) -> BoundaryCountryReviewReport:
    """Build deterministic boundary and per-point review ledgers from local inputs."""
    root = Path(repository_root).resolve()
    data_root = root / "data"
    authority = _load_boundary_authority(data_root)
    points_by_source, source_artifacts = _load_governed_points(root)
    destination = (
        Path(output_root).resolve()
        if output_root is not None
        else data_root / "boundaries" / "review"
    )
    try:
        destination.relative_to(root)
    except ValueError as error:
        raise ValueError(
            "Boundary review output must remain inside the repository"
        ) from error
    destination.mkdir(parents=True, exist_ok=True)
    decision_root = destination / "country-decisions"
    decision_root.mkdir(parents=True, exist_ok=True)

    boundary_review = _build_boundary_review(authority)
    boundary_review_path = destination / "boundary_review.json"
    _write_json_atomic(boundary_review_path, boundary_review)

    decision_paths: list[Path] = []
    all_decisions: list[JsonObject] = []
    for source_family in sorted(points_by_source):
        decisions = [
            build_point_country_decision(point, authority=authority)
            for point in points_by_source[source_family]
        ]
        decisions.sort(key=lambda row: str(row["decision_id"]))
        all_decisions.extend(decisions)
        ledger = {
            "schema_version": "country-attribution-ledger.v1",
            "source_family": source_family,
            "source_scope": points_by_source[source_family][0].source_scope,
            "coordinate_reference_system": "EPSG:4326",
            "coordinate_axis_order": "longitude,latitude",
            "boundary_authority": _boundary_identity(authority),
            "source_artifacts": source_artifacts[source_family],
            "row_count": len(decisions),
            "summary": _decision_summary(decisions),
            "decisions": decisions,
        }
        ledger_path = decision_root / f"{source_family}.json"
        _write_json_atomic(ledger_path, ledger)
        decision_paths.append(ledger_path)

    point_review_rows = [
        {
            "decision_id": row["decision_id"],
            "source_family": row["source_family"],
            "source_record_id": row["source_record_id"],
            "country_decision_status": row["country_decision_status"],
            "review_reason_codes": row["review_reason_codes"],
            "review_status": "pending",
            "qualified_reviewer": None,
            "qualified_reviewed_at": None,
        }
        for row in all_decisions
        if row["review_requirement"] == "qualified_review_required"
    ]
    point_review_rows.sort(key=lambda row: str(row["decision_id"]))
    review_queue = {
        "schema_version": "boundary-country-review-queue.v1",
        "boundary_artifact_digest": authority.artifact_digest,
        "boundary_items": [
            {
                "country_code": record["country_code"],
                "country_name": record["country_name"],
                "review_status": record["qualified_review_status"],
                "review_reason_codes": record["qualified_review_reason_codes"],
                "qualified_reviewer": None,
                "qualified_reviewed_at": None,
            }
            for record in cast(list[JsonObject], boundary_review["countries"])
        ],
        "point_decision_count": len(point_review_rows),
        "point_decisions": point_review_rows,
        "approval_posture": (
            "No qualified boundary or country-decision approval is inferred by "
            "machine validation."
        ),
    }
    review_queue_path = destination / "review_queue.json"
    _write_json_atomic(review_queue_path, review_queue)

    output_paths = [boundary_review_path, *decision_paths, review_queue_path]
    manifest = {
        "schema_version": "boundary-country-review-manifest.v1",
        "producer": {
            "id": "bijux-pollenomics.boundary-country-review",
            "version": "1",
            "path": (
                "packages/bijux-pollenomics/src/bijux_pollenomics/"
                "collection/sources/boundaries/review/publication.py"
            ),
            "sha256": _file_sha256(Path(__file__)),
        },
        "boundary_authority": _boundary_identity(authority),
        "source_artifacts": source_artifacts,
        "country_order": list(COUNTRY_ORDER),
        "point_count": len(all_decisions),
        "point_review_count": len(point_review_rows),
        "point_surface_scope": {
            "denominator_policy": (
                "Enumerate each source-owned point once from its most complete "
                "governed local surface; do not recount publication derivatives."
            ),
            "included_source_families": [
                "animal_adna",
                "landclim",
                "neotoma",
                "sead",
            ],
            "excluded_duplicate_or_nonpoint_surfaces": [
                {
                    "path": "data/sead/normalized/nordic_environmental_sites.geojson",
                    "reason": (
                        "assigned-only derivative of the complete SEAD decision "
                        "denominator"
                    ),
                },
                {
                    "path": "data/neotoma/normalized/nordic_pollen_sites.geojson",
                    "reason": (
                        "used for geometry but counted through the Neotoma "
                        "relational site denominator"
                    ),
                },
                {
                    "path": (
                        "data/landclim/normalized/nordic_reveals_grid_cells.geojson"
                    ),
                    "reason": "polygon surface; not a point-decision denominator",
                },
                {
                    "path": "data/raa/normalized/sweden_archaeology_density.geojson",
                    "reason": "polygon surface; not a point-decision denominator",
                },
                {
                    "path": "data/svar/review/sweden_lake_candidate_registry.geojson",
                    "reason": (
                        "orphaned review surface without governing source authority"
                    ),
                },
            ],
        },
        "source_summaries": {
            source: _decision_summary(
                [row for row in all_decisions if row["source_family"] == source]
            )
            for source in sorted(points_by_source)
        },
        "outputs": [
            {
                "path": str(path.relative_to(root)),
                "sha256": _file_sha256(path),
                "bytes": path.stat().st_size,
            }
            for path in output_paths
        ],
        "release_posture": "blocked_pending_qualified_boundary_review",
        "release_reason_codes": ["qualified_boundary_inclusion_review_missing"],
    }
    manifest_path = destination / "manifest.json"
    _write_json_atomic(manifest_path, manifest)
    return BoundaryCountryReviewReport(
        output_root=destination,
        boundary_review_path=boundary_review_path,
        country_decision_paths=tuple(decision_paths),
        review_queue_path=review_queue_path,
        manifest_path=manifest_path,
        point_count=len(all_decisions),
        point_review_count=len(point_review_rows),
    )
