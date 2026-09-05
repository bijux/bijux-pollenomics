from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from bijux_pollenomics.adna.sources.archive import build_archive_project_catalog


def _dynamic_row(row: dict[str, object]) -> dict[str, Any]:
    """Mark a validated external report row as dynamically keyed JSON."""
    return cast(dict[str, Any], row)


def _int_value(value: object) -> int:
    """Apply the report layer's established integer coercion explicitly."""
    return int(cast(Any, value))


def _sample_evidence_depth_counts(output_root: Path) -> dict[str, int]:
    output_root = Path(output_root)
    counts = {
        "sample_identity_only": 0,
        "sample_with_site": 0,
        "sample_with_site_and_chronology": 0,
        "sample_with_site_chronology_and_coordinates": 0,
    }
    species_root = output_root / "adna" / "species"
    if not species_root.is_dir():
        return counts
    for root in species_root.iterdir():
        sample_path = root / "normalized" / "sample_records.json"
        if not sample_path.is_file():
            continue
        payload = json.loads(sample_path.read_text(encoding="utf-8"))
        for row in payload.get("samples", []):
            has_site = bool(
                str(row.get("locality", "") or row.get("site_label", "")).strip()
            ) or bool(row.get("locality_identity"))
            has_chronology = str(
                row.get("chronology_normalization_status", "")
            ).strip() in {
                "normalized_interval",
                "normalized_point",
            }
            coords = row.get("coordinates", {})
            has_coordinates = bool(
                str(coords.get("latitude_text", "")).strip()
                and str(coords.get("longitude_text", "")).strip()
            )
            if not has_site:
                counts["sample_identity_only"] += 1
            elif has_site and not has_chronology:
                counts["sample_with_site"] += 1
            elif has_site and has_chronology and not has_coordinates:
                counts["sample_with_site_and_chronology"] += 1
            else:
                counts["sample_with_site_chronology_and_coordinates"] += 1
    return counts


def _coordinate_counts_by_project(output_root: Path) -> dict[str, dict[str, int]]:
    output_root = Path(output_root)
    species_root = output_root / "adna" / "species"
    counts: dict[str, dict[str, int]] = {}
    if not species_root.is_dir():
        return counts
    for root in species_root.iterdir():
        payload_path = root / "normalized" / "coordinate_provenance.json"
        if not payload_path.is_file():
            continue
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
        for row in payload.get("coordinate_provenance", []):
            project_accession = str(row.get("project_accession", "")).strip()
            if not project_accession:
                continue
            project_counts = counts.setdefault(project_accession, {})
            posture = str(row.get("mapping_posture", "")).strip()
            project_counts[posture] = project_counts.get(posture, 0) + 1
    return counts


def _count_rows(
    rows: list[dict[str, Any]] | tuple[dict[str, Any], ...], *, key: str
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key, "")).strip()
        if not value:
            continue
        counts[value] = counts.get(value, 0) + 1
    return counts


def _project_species(project_accession: str) -> str:
    for project in build_archive_project_catalog():
        if project.project_accession == project_accession:
            return project.species_latin_name
    return ""


def _nonempty_paths(paths: list[str]) -> list[str]:
    seen: set[str] = set()
    rows: list[str] = []
    for path in paths:
        candidate = str(path).strip()
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        rows.append(candidate)
    return rows


def _cache_key(output_root: Path) -> str:
    return str(Path(output_root).resolve())
