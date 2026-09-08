"""Repository-wide evidence counts assembled from governed surfaces."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any, cast

from bijux_pollenomics.collection.sources.raa import assess_raa_density_authority

from .filesystem import (
    _count_files,
    _count_geojson_features,
    _count_tree_files,
    _load_json_or_default,
)

__all__: list[str] = []


def _build_core_counts(
    data_root: Path,
    docs_root: Path,
    report_root: Path,
) -> dict[str, object]:
    paper_registry = _load_json_or_default(
        data_root / "adna" / "governance" / "source_library" / "paper_registry.json",
        {"rows": []},
    )
    reference_stash_reconciliation = _load_json_or_default(
        data_root
        / "adna"
        / "governance"
        / "source_library"
        / "reference_stash_reconciliation.json",
        {"rows": []},
    )
    reference_stash_doi_integrity = _load_json_or_default(
        data_root
        / "adna"
        / "governance"
        / "source_library"
        / "reference_stash_doi_integrity_audit.json",
        {"reference_stash_doi_count": 0},
    )
    map_readiness_path = (
        data_root / "adna" / "governance" / "cross_species_map_readiness.json"
    )
    map_readiness = _load_json_or_default(
        map_readiness_path,
        {
            "totals": {
                "direct_coordinate_backed": 0,
                "indirectly_geocoded": 0,
                "unresolved_sample_count": 0,
                "refused_coordinate_provenance_count": 0,
            }
        },
    )
    sample_database_review_path = report_root / "animal_sample_database_review.json"
    sample_database_review = _load_json_or_default(
        sample_database_review_path,
        {"counts": {}},
    )
    collection_summary = _load_json_or_default(
        data_root / "collection_summary.json", {}
    )
    landclim_summary = _load_json_or_default(
        data_root / "landclim" / "normalized" / "landclim_summary.json",
        {"site_count": 0, "grid_cell_count": 0},
    )
    neotoma_sites = _load_json_or_default(
        data_root / "neotoma" / "raw" / "neotoma_pollen_sites.json",
        {"site_count": 0},
    )
    sead_sites = _load_json_or_default(
        data_root / "sead" / "raw" / "nordic_sites.json",
        {"row_count": 0},
    )
    raa_layer = _load_json_or_default(
        data_root / "raa" / "normalized" / "sweden_archaeology_layer.json",
        {"density_feature_count": 0, "counts": {}},
    )
    raa_authority = assess_raa_density_authority(data_root)

    paper_rows = list(cast(Iterable[dict[str, object]], paper_registry.get("rows", [])))
    totals = dict(cast(Mapping[str, object], map_readiness.get("totals", {})))
    zero_collection_surfaces = [
        key
        for key in (
            "landclim_site_count",
            "landclim_grid_cell_count",
            "neotoma_point_count",
            "sead_point_count",
            "raa_total_site_count",
            "raa_heritage_site_count",
        )
        if int(cast(Any, collection_summary.get(key, 0))) == 0
    ]
    sample_counts = cast(Mapping[str, object], sample_database_review.get("counts", {}))
    map_readiness_available = map_readiness_path.is_file()
    sample_database_review_available = sample_database_review_path.is_file()
    tracked_sample_count = _surface_count(
        sample_counts,
        "sample_row_count",
        available=sample_database_review_available,
    )
    mapped_sample_count = _surface_count(
        sample_counts,
        "mapped_sample_count",
        available=sample_database_review_available,
    )
    if (
        mapped_sample_count is not None
        and tracked_sample_count is not None
        and mapped_sample_count > tracked_sample_count
    ):
        raise ValueError("Animal mapped samples exceed tracked samples")
    blocked_sample_count = (
        tracked_sample_count - mapped_sample_count
        if tracked_sample_count is not None and mapped_sample_count is not None
        else None
    )
    unresolved_sample_count = _surface_count(
        totals,
        "unresolved_sample_count",
        available=map_readiness_available,
    )
    coordinate_mappable_count = _surface_count(
        totals,
        "coordinate_provenance_mappable_count",
        available=map_readiness_available,
    )
    coordinate_refused_count = _surface_count(
        totals,
        "refused_coordinate_provenance_count",
        available=map_readiness_available,
    )
    coordinate_total = _surface_count(
        totals,
        "coordinate_provenance_row_count",
        available=map_readiness_available,
    )
    coordinate_not_materialized_count = _surface_count(
        totals,
        "not_materialized_count",
        available=map_readiness_available,
    )
    publication_candidate_count = _surface_count(
        totals,
        "publication_candidate_count",
        available=map_readiness_available,
    )
    published_atlas_point_count = _surface_count(
        sample_counts,
        "published_atlas_point_count",
        available=sample_database_review_available,
    )
    if map_readiness_available:
        coordinate_mappable_count = _require_surface_count(
            coordinate_mappable_count, "coordinate_provenance_mappable_count"
        )
        coordinate_refused_count = _require_surface_count(
            coordinate_refused_count, "refused_coordinate_provenance_count"
        )
        coordinate_total = _require_surface_count(
            coordinate_total, "coordinate_provenance_row_count"
        )
        coordinate_not_materialized_count = _require_surface_count(
            coordinate_not_materialized_count, "not_materialized_count"
        )
        publication_candidate_count = _require_surface_count(
            publication_candidate_count, "publication_candidate_count"
        )
        unresolved_sample_count = _require_surface_count(
            unresolved_sample_count, "unresolved_sample_count"
        )
        if coordinate_mappable_count + coordinate_refused_count != coordinate_total:
            raise ValueError("Animal coordinate-provenance counts do not reconcile")
        if (
            publication_candidate_count + coordinate_not_materialized_count
            != coordinate_mappable_count
        ):
            raise ValueError("Animal coordinate publication counts do not reconcile")
        if (
            blocked_sample_count is not None
            and unresolved_sample_count > blocked_sample_count
        ):
            raise ValueError("Animal unresolved samples exceed blocked samples")
    if (
        sample_database_review_available
        and map_readiness_available
        and published_atlas_point_count != publication_candidate_count
    ):
        raise ValueError(
            "Animal sample publication and coordinate readiness counts do not reconcile"
        )
    return {
        "tracked_paper_count": len(paper_rows),
        "papers_with_archived_supplements": sum(
            cast(
                Iterable[int],
                (
                    1
                    for row in paper_rows
                    if int(cast(Any, row.get("supplementary_count", 0))) > 0
                ),
            )
        ),
        "published_atlas_point_count": published_atlas_point_count,
        "published_country_bundle_count": _surface_count(
            sample_counts,
            "published_country_bundle_count",
            available=sample_database_review_available,
        ),
        "reference_stash_doi_count": int(
            cast(
                Any,
                reference_stash_doi_integrity.get("reference_stash_doi_count", 0),
            )
        ),
        "tracked_aadr_release_file_count": _count_tree_files(
            data_root / "aadr" / "v66"
        ),
        "papers_with_local_reference_supplements": sum(
            1
            for row in cast(
                Iterable[dict[str, object]],
                reference_stash_reconciliation.get("rows", []),
            )
            if bool(row.get("paper_registry_present"))
            and row.get("local_reference_supplement_status") == "local_reference_staged"
        ),
        "animal_sample_database_review_available": sample_database_review_available,
        "animal_map_readiness_available": map_readiness_available,
        "animal_tracked_sample_count": tracked_sample_count,
        "animal_mapped_sample_count": mapped_sample_count,
        "animal_blocked_sample_count": blocked_sample_count,
        "animal_unresolved_sample_count": unresolved_sample_count,
        "animal_coordinate_mappable_provenance_count": coordinate_mappable_count,
        "animal_coordinate_refused_provenance_count": coordinate_refused_count,
        "animal_coordinate_provenance_count": coordinate_total,
        "animal_coordinate_not_materialized_count": coordinate_not_materialized_count,
        "tracked_landclim_site_count": int(
            cast(Any, landclim_summary.get("site_count", 0))
        ),
        "tracked_landclim_grid_cell_count": int(
            cast(Any, landclim_summary.get("grid_cell_count", 0))
        ),
        "tracked_neotoma_site_count": int(
            cast(Any, neotoma_sites.get("site_count", 0))
        ),
        "tracked_sead_site_count": int(cast(Any, sead_sites.get("row_count", 0))),
        "tracked_raa_published_site_count": (
            int(
                cast(
                    Any,
                    dict(cast(Mapping[str, object], raa_layer.get("counts", {}))).get(
                        "all_published_sites", 0
                    ),
                )
            )
            if raa_authority.admitted
            else 0
        ),
        "tracked_raa_density_cell_count": (
            int(cast(Any, raa_layer.get("density_feature_count", 0)))
            if raa_authority.admitted
            else 0
        ),
        "raa_density_admitted": raa_authority.admitted,
        "raa_density_reason_codes": list(raa_authority.reason_codes),
        "tracked_boundary_feature_count": _count_geojson_features(
            data_root
            / "boundaries"
            / "normalized"
            / "nordic_country_boundaries.geojson"
        ),
        "pollen_normalized_file_count": _count_files(
            data_root / "landclim" / "normalized"
        )
        + _count_files(data_root / "neotoma" / "normalized"),
        "archaeology_normalized_file_count": _count_files(
            data_root / "sead" / "normalized"
        )
        + _count_files(data_root / "raa" / "normalized"),
        "boundary_raw_file_count": _count_files(data_root / "boundaries" / "raw"),
        "boundary_normalized_file_count": _count_files(
            data_root / "boundaries" / "normalized"
        ),
        "fieldwork_page_count": sum(
            1 for _ in (docs_root / "public" / "fieldwork").rglob("index.md")
        ),
        "source_explainer_count": sum(
            1
            for path in (docs_root / "public" / "pollenomics-data" / "sources").glob(
                "*.md"
            )
            if path.name
            not in {
                "index.md",
                "animal-source-intake.md",
            }
        ),
        "landing_page_count": sum(
            int(path.exists())
            for path in (
                docs_root / "index.md",
                docs_root / "public" / "index.md",
                docs_root / "public" / "pollenomics" / "index.md",
                docs_root / "public" / "pollenomics-data" / "index.md",
                docs_root / "internal" / "index.md",
                docs_root / "public" / "fieldwork" / "index.md",
                docs_root / "public" / "nordic-atlas" / "index.md",
            )
        ),
        "zero_collection_summary_surfaces": zero_collection_surfaces,
    }


def _surface_count(
    payload: Mapping[str, object],
    field: str,
    *,
    available: bool,
) -> int | None:
    if not available:
        return None
    value = payload.get(field)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"Repository truth {field} must be a nonnegative integer")
    return value


def _require_surface_count(value: int | None, field: str) -> int:
    if value is None:
        raise ValueError(f"Repository truth {field} is unavailable")
    return value
