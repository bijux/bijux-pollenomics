from __future__ import annotations

import json
from pathlib import Path

from bijux_pollenomics.adna.workflow.paths import adna_species_dir, adna_species_root


def _species_root(data_root: Path, species_name: str) -> Path:
    return adna_species_root(Path(data_root), species_name)


def _species_roots(data_root: Path) -> list[Path]:
    species_dir = adna_species_dir(Path(data_root))
    if not species_dir.is_dir():
        return []
    return [path for path in sorted(species_dir.iterdir()) if path.is_dir()]


def _load_sample_rows(species_root: Path) -> list[dict[str, object]]:
    path = species_root / "normalized" / "sample_records.json"
    if not path.is_file():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("samples", [])
    return [row for row in rows if isinstance(row, dict)]


def _load_coordinate_provenance_rows(species_root: Path) -> list[dict[str, object]]:
    path = species_root / "normalized" / "coordinate_provenance.json"
    if not path.is_file():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("coordinate_provenance", [])
    return [row for row in rows if isinstance(row, dict)]


def _load_all_sample_rows_by_id(data_root: Path) -> dict[str, dict[str, object]]:
    lookup: dict[str, dict[str, object]] = {}
    species_root = adna_species_dir(Path(data_root))
    for sample_path in species_root.glob("*/normalized/sample_records.json"):
        rows = _load_sample_rows(sample_path.parent.parent)
        for row in rows:
            stable_token = str(row.get("identity", {}).get("stable_token", "")).strip()
            if stable_token:
                lookup[stable_token] = row
    return lookup


def _load_mapped_sample_ids_by_species(data_root: Path) -> dict[str, set[str]]:
    from bijux_pollenomics.reporting.adna import (
        build_tracked_animal_atlas_evidence_rows,
    )

    rows = build_tracked_animal_atlas_evidence_rows(Path(data_root))
    mapped: dict[str, set[str]] = {}
    for row in rows:
        mapped.setdefault(row.species_latin_name, set()).update(row.sample_record_ids)
    return mapped


def _load_country_sample_ids_by_species(report_root: Path) -> dict[str, set[str]]:
    sample_ids: dict[str, set[str]] = {}
    country_root = report_root / "countries"
    if not country_root.exists():
        return sample_ids
    for country_dir in country_root.iterdir():
        if not country_dir.is_dir():
            continue
        for summary_path in sorted(country_dir.glob("*_animal_adna_*_summary.json")):
            payload = json.loads(summary_path.read_text(encoding="utf-8"))
            rows = payload.get("sample_rows", [])
            if not isinstance(rows, list):
                continue
            for row in rows:
                if not isinstance(row, dict):
                    continue
                species_name = str(row.get("species_latin_name", "")).strip()
                sample_id = str(row.get("sample_record_id", "")).strip()
                if species_name and sample_id:
                    sample_ids.setdefault(species_name, set()).add(sample_id)
    return sample_ids


def _count_sample_rows_by_mapping_posture(
    species_root: Path, mapping_posture: str
) -> int:
    return sum(
        1
        for row in _load_coordinate_provenance_rows(species_root)
        if str(row.get("mapping_posture", "")) == mapping_posture
    )


def _species_output_count(
    root: Path,
    latin_name: str,
    common_name: str,
) -> int:
    if not root.exists():
        return 0
    del common_name
    latin_token = latin_name.casefold()
    explicit_markers = (
        "species_latin_name",
        "species_common_name",
        "support_class",
        "nordic_relevance",
    )
    matches = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.name in {
            "animal_output_audit.json",
            "animal_output_audit.md",
            "published_reports_summary.json",
        }:
            continue
        if path.suffix.lower() not in {".json", ".md", ".csv", ".geojson", ".html"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").casefold()
        if latin_token in text and any(marker in text for marker in explicit_markers):
            matches += 1
    return matches


def _country_output_count(
    report_root: Path,
    latin_name: str,
    common_name: str,
) -> int:
    country_root = report_root / "countries"
    if not country_root.exists():
        return 0
    return sum(
        1
        for path in country_root.iterdir()
        if path.is_dir() and _species_output_count(path, latin_name, common_name) > 0
    )


def _atlas_layer_count(
    atlas_root: Path,
    latin_name: str,
    common_name: str,
) -> int:
    summary_path = atlas_root / "world_summary.json"
    if summary_path.is_file():
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
        animal_atlas = payload.get("animal_atlas", {})
        if isinstance(animal_atlas, dict):
            species_layers = animal_atlas.get("species_layers", [])
            if isinstance(species_layers, list):
                for row in species_layers:
                    if not isinstance(row, dict):
                        continue
                    if str(row.get("latin_name", "")).strip() == latin_name:
                        return int(row.get("locality_count", 0) or 0)
    return _species_output_count(atlas_root, latin_name, common_name)
