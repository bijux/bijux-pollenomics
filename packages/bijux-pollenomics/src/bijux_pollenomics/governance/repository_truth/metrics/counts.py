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
    map_readiness = _load_json_or_default(
        data_root / "adna" / "governance" / "cross_species_map_readiness.json",
        {
            "totals": {
                "direct_coordinate_backed": 0,
                "indirectly_geocoded": 0,
                "unresolved": 0,
                "refused_from_mapping": 0,
            }
        },
    )
    sample_database_review = _load_json_or_default(
        report_root / "animal_sample_database_review.json",
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
        "published_atlas_point_count": int(
            cast(
                Any,
                cast(
                    Mapping[str, object],
                    sample_database_review.get("counts", {}),
                ).get("published_atlas_point_count", 0),
            )
        ),
        "published_country_bundle_count": int(
            cast(
                Any,
                cast(
                    Mapping[str, object],
                    sample_database_review.get("counts", {}),
                ).get("published_country_bundle_count", 0),
            )
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
        "animal_sample_row_count": int(
            cast(
                Any,
                cast(
                    Mapping[str, object],
                    sample_database_review.get("counts", {}),
                ).get("sample_row_count", 0),
            )
        ),
        "animal_map_supported_rows": int(
            cast(Any, totals.get("direct_coordinate_backed", 0))
        )
        + int(cast(Any, totals.get("indirectly_geocoded", 0))),
        "animal_map_unresolved_rows": int(cast(Any, totals.get("unresolved", 0))),
        "animal_map_refused_rows": int(
            cast(Any, totals.get("refused_from_mapping", 0))
        ),
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
