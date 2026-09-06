from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path


def _coverage_metrics(
    output_root: Path,
    counts: Mapping[str, int],
    source_key: str,
    *,
    governed_metrics: Mapping[str, int | None] | None,
) -> dict[str, int | None]:
    if governed_metrics is not None:
        return dict(governed_metrics)
    if source_key == "landclim":
        return {
            "landclim_site_count": int(counts.get("landclim_site_count", 0)),
            "landclim_grid_cell_count": int(counts.get("landclim_grid_cell_count", 0)),
            "landclim_temporal_grid_feature_count": int(
                counts.get("landclim_temporal_grid_feature_count", 0)
            ),
        }
    if source_key == "neotoma":
        return {"neotoma_point_count": int(counts.get("neotoma_point_count", 0))}
    if source_key == "sead":
        return {"sead_point_count": int(counts.get("sead_point_count", 0))}
    if source_key == "aadr":
        return {"aadr_file_count": int(counts.get("aadr_file_count", 0))}
    if source_key == "animal_adna":
        return _animal_adna_metrics(output_root)
    return {}


def _geojson_feature_count(path: Path) -> int:
    if not path.is_file():
        return 0
    payload = json.loads(path.read_text(encoding="utf-8"))
    features = payload.get("features", [])
    if not isinstance(features, list):
        return 0
    return len(features)


def _animal_adna_metrics(output_root: Path) -> dict[str, int | None]:
    species_root = output_root / "adna" / "species"
    source_library_root = output_root / "adna" / "governance" / "source_library"
    truth_path = (
        output_root / "adna" / "governance" / "animal_sample_foundation_truth.json"
    )
    sample_count = 0
    project_count = 0
    if truth_path.is_file():
        payload = json.loads(truth_path.read_text(encoding="utf-8"))
        summary = payload.get("summary", {})
        if isinstance(summary, dict):
            sample_count = int(summary.get("sample_row_count", 0))
    project_registry = source_library_root / "project_registry.json"
    if project_registry.is_file():
        payload = json.loads(project_registry.read_text(encoding="utf-8"))
        rows = payload.get("rows", [])
        if isinstance(rows, list):
            project_count = len(rows)
    species_count = (
        sum(
            1
            for child in species_root.iterdir()
            if child.is_dir() and child.name != "homo_sapiens"
        )
        if species_root.is_dir()
        else 0
    )
    return {
        "animal_species_count": species_count,
        "animal_project_count": project_count,
        "animal_sample_count": sample_count,
    }
