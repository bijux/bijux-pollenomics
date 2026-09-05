"""Animal foundation repository responsibilities."""

from __future__ import annotations
from typing import Any
import json
from pathlib import Path
from ....adna.workflow.paths import adna_species_dir
from ....adna.projects.evidence.chronology import (
    ADNA_CHRONOLOGY_NORMALIZATION_STATUSES,
    build_sample_chronology_review_rows,
)
from ....adna.projects.registry.sites import (
    ADNA_LOCALITY_RESOLUTION_STATUSES,
    build_project_sample_site_rows,
)
from ....adna.sources.ena import build_archive_project_catalog


def _load_json_rows(path: Path, key: str) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get(key, [])
    return (
        [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []
    )


def _load_json_if_present(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _species_roots(data_root: Path) -> list[Path]:
    species_dir = adna_species_dir(Path(data_root))
    if not species_dir.is_dir():
        return []
    return [path for path in sorted(species_dir.iterdir()) if path.is_dir()]


def _load_all_sample_rows(data_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for root in _species_roots(data_root):
        rows.extend(
            _load_json_rows(root / "normalized" / "sample_records.json", "samples")
        )
    return rows


def _load_all_site_evidence_rows(data_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for root in _species_roots(data_root):
        rows.extend(
            _load_json_rows(root / "normalized" / "site_evidence.json", "site_evidence")
        )
    return rows


def _load_all_coordinate_rows(data_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for root in _species_roots(data_root):
        rows.extend(
            _load_json_rows(
                root / "normalized" / "coordinate_provenance.json",
                "coordinate_provenance",
            )
        )
    return rows


def _load_all_project_sample_site_rows(data_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    project_root = (
        Path(data_root) / "adna" / "governance" / "source_library" / "projects"
    )
    paths = (
        sorted(project_root.glob("*/sample_sites.json"))
        if project_root.is_dir()
        else []
    )
    if paths:
        for path in paths:
            payload = json.loads(path.read_text(encoding="utf-8"))
            project_rows = payload.get("rows", [])
            if not isinstance(project_rows, list):
                continue
            for row in project_rows:
                if not isinstance(row, dict):
                    continue
                status = str(row.get("locality_resolution_status", ""))
                if status and status not in ADNA_LOCALITY_RESOLUTION_STATUSES:
                    continue
                rows.append(row)
        return rows
    for project in build_archive_project_catalog():
        rows.extend(
            row.as_dict()
            for row in build_project_sample_site_rows(
                data_root, project.project_accession
            )
        )
    return rows


def _load_all_project_sample_chronology_rows(
    data_root: Path,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    project_root = (
        Path(data_root) / "adna" / "governance" / "source_library" / "projects"
    )
    paths = (
        sorted(project_root.glob("*/sample_chronology.json"))
        if project_root.is_dir()
        else []
    )
    if paths:
        for path in paths:
            payload = json.loads(path.read_text(encoding="utf-8"))
            project_rows = payload.get("rows", [])
            if not isinstance(project_rows, list):
                continue
            for row in project_rows:
                if not isinstance(row, dict):
                    continue
                status = str(row.get("chronology_normalization_status", ""))
                if status and status not in ADNA_CHRONOLOGY_NORMALIZATION_STATUSES:
                    continue
                rows.append(row)
        return rows
    rows.extend(dict(row) for row in build_sample_chronology_review_rows(data_root))
    return rows


def _group_sample_rows_by_species(
    data_root: Path,
) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in _load_all_sample_rows(data_root):
        grouped.setdefault(str(row.get("species_latin_name", "")), []).append(row)
    return grouped


def _group_site_rows_by_species(data_root: Path) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in _load_all_site_evidence_rows(data_root):
        grouped.setdefault(str(row.get("species_latin_name", "")), []).append(row)
    return grouped


def _group_coordinate_rows_by_species(
    data_root: Path,
) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in _load_all_coordinate_rows(data_root):
        grouped.setdefault(str(row.get("species_latin_name", "")), []).append(row)
    return grouped


def _build_sample_lookup(data_root: Path) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for row in _load_all_sample_rows(data_root):
        token = str(row.get("identity", {}).get("stable_token", "")).strip()
        if token:
            lookup[token] = row
    return lookup


def _build_site_lookup(data_root: Path) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("project_accession", "")).strip(): row
        for row in _load_all_site_evidence_rows(data_root)
        if str(row.get("project_accession", "")).strip()
    }


def _build_coordinate_lookup(data_root: Path) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("project_accession", "")).strip(): row
        for row in _load_all_coordinate_rows(data_root)
        if str(row.get("project_accession", "")).strip()
    }


def _count_rows_by_project(rows: tuple[dict[str, Any], ...]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        project = str(row.get("project_accession", "")).strip()
        if project:
            counts[project] = counts.get(project, 0) + 1
    return counts


def _build_comparator_only_rows(data_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for root in _species_roots(data_root):
        review_path = root / "review" / "species_review.json"
        if not review_path.is_file():
            continue
        payload = json.loads(review_path.read_text(encoding="utf-8"))
        for row in payload.get("project_reviews", []):
            if not isinstance(row, dict):
                continue
            if str(row.get("domestication_scope", "")) != "comparator_only":
                continue
            rows.append(
                {
                    "species_latin_name": row.get("species_latin_name", ""),
                    "project_accession": row.get("project_accession", ""),
                    "evidence_strength": row.get("evidence_strength", ""),
                    "blocking_reasons": row.get("blocking_reasons", []),
                }
            )
    rows.sort(
        key=lambda row: (str(row["species_latin_name"]), str(row["project_accession"]))
    )
    return rows


def _load_country_payloads(report_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    report_root = Path(report_root)
    if not report_root.is_dir():
        return rows
    country_root = report_root / "countries"
    for country_dir in sorted(country_root.iterdir() if country_root.is_dir() else ()):
        if not country_dir.is_dir():
            continue
        for summary_path in country_dir.glob("*_animal_adna_*_summary.json"):
            payload = json.loads(summary_path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                rows.append(payload)
    return rows
