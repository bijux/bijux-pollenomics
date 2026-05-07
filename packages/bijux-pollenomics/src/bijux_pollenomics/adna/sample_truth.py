from __future__ import annotations

import json
from pathlib import Path
import re

from .paths import adna_species_root
from .species import resolve_species_definition
from .tracked_species import TRACKED_ADNA_SPECIES

__all__ = [
    "build_animal_sample_aggregation_warnings",
    "build_animal_sample_foundation_truth",
    "build_animal_sample_product_contract",
    "build_project_locality_count_drift",
    "build_species_sample_count_drift",
    "render_animal_sample_aggregation_warnings_markdown",
    "render_animal_sample_foundation_truth_markdown",
    "render_animal_sample_product_contract_markdown",
]

_SPECIES_SAMPLE_COUNT_RE = re.compile(r"- Curated sample rows: `(?P<count>\d+)`")


def build_animal_sample_product_contract() -> dict[str, object]:
    """Describe the minimum durable contract for non-human animal aDNA sample rows."""
    return {
        "schema_version": "animal-sample-product-contract.v1",
        "primary_durable_unit": "sample_record",
        "required_fields": [
            {
                "field": "identity.stable_token",
                "meaning": "stable sample identifier inside the repository",
            },
            {
                "field": "species_latin_name",
                "meaning": "species assignment carried by the sample row",
            },
            {
                "field": "project_accession",
                "meaning": "archive project or accession family anchor for the sample",
            },
            {
                "field": "paper_doi_or_paper_url",
                "meaning": "primary publication anchor for the sample claim",
            },
            {
                "field": "supplementary_source_or_supporting_source_url",
                "meaning": "supporting file or source artifact behind location or sample detail",
            },
            {
                "field": "locality_identity.locality_text",
                "meaning": "site or locality label attached to the sample",
            },
            {
                "field": "chronology.original_text",
                "meaning": "raw chronology claim kept before normalization",
            },
            {
                "field": "chronology.time_start_bp",
                "meaning": "older bound of the normalized BP interval when defensible",
            },
            {
                "field": "chronology.time_end_bp",
                "meaning": "younger bound of the normalized BP interval when defensible",
            },
            {
                "field": "coordinates.latitude_text",
                "meaning": "latitude text retained from direct coordinates or later resolution",
            },
            {
                "field": "coordinates.longitude_text",
                "meaning": "longitude text retained from direct coordinates or later resolution",
            },
            {
                "field": "coordinate_basis",
                "meaning": "how the repository derived or withheld coordinates for the sample",
            },
            {
                "field": "coordinates.confidence",
                "meaning": "confidence class carried by the coordinate claim",
            },
            {
                "field": "inclusion_status",
                "meaning": "current publication posture or blocking state for the sample row",
            },
        ],
        "reader_questions_answered": [
            "which sample exists",
            "which species it belongs to",
            "which project and paper describe it",
            "which supporting source anchors its site claim",
            "what chronology claim the repository keeps",
            "what coordinate basis and confidence the repository keeps",
            "whether the row is publishable, blocked, or still weak",
        ],
    }


def build_animal_sample_foundation_truth(data_root: Path) -> dict[str, object]:
    """Count sample-foundation truth classes across species and projects."""
    species_rows: list[dict[str, object]] = []
    project_rows: list[dict[str, object]] = []
    for species_name in TRACKED_ADNA_SPECIES:
        species = resolve_species_definition(species_name)
        species_root = _species_root(Path(data_root), species_name)
        sample_rows = _load_sample_rows(species_root)
        locality_rows = _load_locality_rows(species_root)
        species_project_rows: list[dict[str, object]] = []
        grouped_samples = _group_sample_rows_by_project(sample_rows)
        for project_accession, project_sample_rows in sorted(grouped_samples.items()):
            project_row = _build_project_truth_row(
                species_latin_name=species.latin_name,
                species_common_name=species.common_name,
                project_accession=project_accession,
                sample_rows=project_sample_rows,
                locality_rows=locality_rows,
            )
            project_rows.append(project_row)
            species_project_rows.append(project_row)
        species_rows.append(
            _build_species_truth_row(
                species_latin_name=species.latin_name,
                species_common_name=species.common_name,
                species_root=species_root,
                sample_rows=sample_rows,
                project_rows=species_project_rows,
            )
        )
    summary = {
        "tracked_species_count": len(species_rows),
        "tracked_project_count": len(project_rows),
        "sample_row_count": sum(int(row["sample_row_count"]) for row in species_rows),
        "fully_grounded_count": sum(
            int(row["fully_grounded_count"]) for row in species_rows
        ),
        "partially_grounded_count": sum(
            int(row["partially_grounded_count"]) for row in species_rows
        ),
        "blocked_missing_metadata_count": sum(
            int(row["blocked_missing_metadata_count"]) for row in species_rows
        ),
        "blocked_missing_location_detail_count": sum(
            int(row["blocked_missing_location_detail_count"]) for row in species_rows
        ),
        "blocked_weak_chronology_count": sum(
            int(row["blocked_weak_chronology_count"]) for row in species_rows
        ),
    }
    return {
        "schema_version": "animal-sample-foundation-truth.v1",
        "summary": summary,
        "species_rows": species_rows,
        "project_rows": project_rows,
    }


def build_project_locality_count_drift(data_root: Path) -> tuple[dict[str, object], ...]:
    """Compare project locality summaries against sample-backed site counts."""
    rows: list[dict[str, object]] = []
    for species_name in TRACKED_ADNA_SPECIES:
        species = resolve_species_definition(species_name)
        species_root = _species_root(Path(data_root), species_name)
        sample_rows = _load_sample_rows(species_root)
        locality_rows = _load_locality_rows(species_root)
        grouped_samples = _group_sample_rows_by_project(sample_rows)
        for project_accession, project_sample_rows in sorted(grouped_samples.items()):
            sample_site_count = _sample_backed_site_count(project_sample_rows)
            locality_summary_count = sum(
                1
                for row in locality_rows
                if project_accession
                in {
                    str(item).strip()
                    for item in row.get("project_accessions", [])
                    if str(item).strip()
                }
            )
            drift_detected = (
                sample_site_count > 0 and locality_summary_count != sample_site_count
            )
            rows.append(
                {
                    "species_latin_name": species.latin_name,
                    "project_accession": project_accession,
                    "sample_row_count": len(project_sample_rows),
                    "sample_backed_site_count": sample_site_count,
                    "project_locality_summary_count": locality_summary_count,
                    "drift_detected": drift_detected,
                }
            )
    return tuple(
        row
        for row in rows
        if bool(row["drift_detected"])
    )


def build_species_sample_count_drift(data_root: Path) -> tuple[dict[str, object], ...]:
    """Compare species README sample claims against current sample-master counts."""
    rows: list[dict[str, object]] = []
    for species_name in TRACKED_ADNA_SPECIES:
        species = resolve_species_definition(species_name)
        species_root = _species_root(Path(data_root), species_name)
        sample_rows = _load_sample_rows(species_root)
        readme_count = _readme_curated_sample_count(species_root / "README.md")
        if readme_count is None:
            continue
        drift_detected = readme_count != len(sample_rows)
        if not drift_detected:
            continue
        rows.append(
            {
                "species_latin_name": species.latin_name,
                "species_common_name": species.common_name,
                "readme_curated_sample_count": readme_count,
                "actual_sample_row_count": len(sample_rows),
                "drift_detected": drift_detected,
            }
        )
    return tuple(rows)


def build_animal_sample_aggregation_warnings(
    data_root: Path,
    report_root: Path,
) -> dict[str, object]:
    """Count current outputs that still rely on project- or site-level aggregation."""
    truth = build_animal_sample_foundation_truth(data_root)
    project_rows = truth["project_rows"]
    project_locality_drift_rows = build_project_locality_count_drift(data_root)
    species_sample_drift_rows = build_species_sample_count_drift(data_root)
    sample_rows = _load_all_sample_rows(Path(data_root))
    locality_rows = _load_all_locality_rows(Path(data_root))
    summary = {
        "total_sample_row_count": len(sample_rows),
        "project_accession_anchor_count": sum(
            1
            for row in sample_rows
            if str(row.get("sample_basis", "")) == "project_accession_anchor"
        ),
        "accession_range_anchor_count": sum(
            1
            for row in sample_rows
            if str(row.get("sample_basis", "")) == "accession_range_anchor"
        ),
        "sample_accession_anchor_count": sum(
            1
            for row in sample_rows
            if str(row.get("sample_basis", "")) == "sample_accession_anchor"
        ),
        "project_locality_summary_count": sum(
            1
            for row in locality_rows
            if str(row.get("sample_namespace", "")).endswith("project_locality")
        ),
        "projects_with_project_level_sample_anchors": sum(
            1
            for row in project_rows
            if bool(row["uses_project_level_sample_anchor"])
        ),
        "projects_with_locality_count_drift": len(project_locality_drift_rows),
        "species_with_summary_count_drift": len(species_sample_drift_rows),
    }
    warning_rows = [
        {
            "warning_class": "project_level_sample_anchors",
            "count": summary["projects_with_project_level_sample_anchors"],
            "detail": "Projects whose current sample rows are still anchored at project or accession-range level rather than true per-sample identifiers.",
        },
        {
            "warning_class": "project_locality_summary_rows",
            "count": summary["project_locality_summary_count"],
            "detail": "Locality rows that are still summarized at project-locality level rather than explicit per-sample site rows.",
        },
        {
            "warning_class": "locality_count_drift",
            "count": summary["projects_with_locality_count_drift"],
            "detail": "Projects where project-level locality summaries disagree with sample-backed site counts.",
        },
        {
            "warning_class": "species_summary_count_drift",
            "count": summary["species_with_summary_count_drift"],
            "detail": "Species summaries that disagree with the current sample-master counts.",
        },
    ]
    return {
        "schema_version": "animal-sample-aggregation-warnings.v1",
        "summary": summary,
        "warning_rows": warning_rows,
        "project_locality_drift_rows": list(project_locality_drift_rows),
        "species_sample_drift_rows": list(species_sample_drift_rows),
    }


def render_animal_sample_product_contract_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Animal sample product contract",
        "",
        f"- Primary durable unit: `{payload['primary_durable_unit']}`",
        "",
        "## Required fields",
        "",
        "| Field | Meaning |",
        "| --- | --- |",
    ]
    for row in payload["required_fields"]:
        lines.append(f"| {row['field']} | {row['meaning']} |")
    lines.extend(["", "## Reader questions answered", ""])
    for question in payload["reader_questions_answered"]:
        lines.append(f"- {question}")
    lines.append("")
    return "\n".join(lines)


def render_animal_sample_foundation_truth_markdown(payload: dict[str, object]) -> str:
    summary = payload["summary"]
    lines = [
        "# Animal sample foundation truth",
        "",
        f"- Tracked species: `{summary['tracked_species_count']}`",
        f"- Tracked projects: `{summary['tracked_project_count']}`",
        f"- Sample rows: `{summary['sample_row_count']}`",
        f"- Fully grounded rows: `{summary['fully_grounded_count']}`",
        f"- Partially grounded rows: `{summary['partially_grounded_count']}`",
        f"- Blocked by missing metadata: `{summary['blocked_missing_metadata_count']}`",
        f"- Blocked by missing location detail: `{summary['blocked_missing_location_detail_count']}`",
        f"- Blocked by weak chronology: `{summary['blocked_weak_chronology_count']}`",
        "",
        "## Species rows",
        "",
        "| Species | Sample rows | Fully grounded | Missing metadata | Missing location detail | Weak chronology |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["species_rows"]:
        lines.append(
            f"| {row['species_latin_name']} | {row['sample_row_count']} | "
            f"{row['fully_grounded_count']} | {row['blocked_missing_metadata_count']} | "
            f"{row['blocked_missing_location_detail_count']} | {row['blocked_weak_chronology_count']} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_animal_sample_aggregation_warnings_markdown(payload: dict[str, object]) -> str:
    summary = payload["summary"]
    lines = [
        "# Animal sample aggregation warnings",
        "",
        f"- Project accession anchors: `{summary['project_accession_anchor_count']}`",
        f"- Accession-range anchors: `{summary['accession_range_anchor_count']}`",
        f"- Sample accession anchors: `{summary['sample_accession_anchor_count']}`",
        f"- Project-locality summaries: `{summary['project_locality_summary_count']}`",
        f"- Projects with project-level sample anchors: `{summary['projects_with_project_level_sample_anchors']}`",
        f"- Projects with locality count drift: `{summary['projects_with_locality_count_drift']}`",
        f"- Species with summary count drift: `{summary['species_with_summary_count_drift']}`",
        "",
    ]
    for row in payload["warning_rows"]:
        lines.append(f"- `{row['warning_class']}`: `{row['count']}`. {row['detail']}")
    lines.append("")
    return "\n".join(lines)


def _build_project_truth_row(
    *,
    species_latin_name: str,
    species_common_name: str,
    project_accession: str,
    sample_rows: list[dict[str, object]],
    locality_rows: list[dict[str, object]],
) -> dict[str, object]:
    status_counts = _status_counts(sample_rows)
    sample_basis_values = {
        str(row.get("sample_basis", "")).strip()
        for row in sample_rows
        if str(row.get("sample_basis", "")).strip()
    }
    locality_summary_count = sum(
        1
        for row in locality_rows
        if project_accession
        in {
            str(item).strip()
            for item in row.get("project_accessions", [])
            if str(item).strip()
        }
    )
    return {
        "species_latin_name": species_latin_name,
        "species_common_name": species_common_name,
        "project_accession": project_accession,
        "sample_row_count": len(sample_rows),
        "fully_grounded_count": status_counts["fully_grounded"],
        "partially_grounded_count": status_counts["partially_grounded"],
        "blocked_missing_metadata_count": status_counts["blocked_missing_metadata"],
        "blocked_missing_location_detail_count": status_counts["blocked_missing_location_detail"],
        "blocked_weak_chronology_count": status_counts["blocked_weak_chronology"],
        "sample_backed_site_count": _sample_backed_site_count(sample_rows),
        "project_locality_summary_count": locality_summary_count,
        "uses_project_level_sample_anchor": any(
            value in {"project_accession_anchor", "accession_range_anchor"}
            for value in sample_basis_values
        ),
        "sample_basis_values": sorted(sample_basis_values),
    }


def _build_species_truth_row(
    *,
    species_latin_name: str,
    species_common_name: str,
    species_root: Path,
    sample_rows: list[dict[str, object]],
    project_rows: list[dict[str, object]],
) -> dict[str, object]:
    status_counts = _status_counts(sample_rows)
    readme_count = _readme_curated_sample_count(species_root / "README.md")
    return {
        "species_latin_name": species_latin_name,
        "species_common_name": species_common_name,
        "sample_row_count": len(sample_rows),
        "fully_grounded_count": status_counts["fully_grounded"],
        "partially_grounded_count": status_counts["partially_grounded"],
        "blocked_missing_metadata_count": status_counts["blocked_missing_metadata"],
        "blocked_missing_location_detail_count": status_counts["blocked_missing_location_detail"],
        "blocked_weak_chronology_count": status_counts["blocked_weak_chronology"],
        "project_count": len(project_rows),
        "reported_curated_sample_count": readme_count,
        "uses_project_level_sample_anchor": any(
            bool(row["uses_project_level_sample_anchor"]) for row in project_rows
        ),
    }


def _status_counts(sample_rows: list[dict[str, object]]) -> dict[str, int]:
    counts = {
        "fully_grounded": 0,
        "partially_grounded": 0,
        "blocked_missing_metadata": 0,
        "blocked_missing_location_detail": 0,
        "blocked_weak_chronology": 0,
    }
    for row in sample_rows:
        counts[_sample_truth_status(row)] += 1
    return counts


def _sample_truth_status(sample_row: dict[str, object]) -> str:
    if not _has_any_linkage(sample_row):
        return "blocked_missing_metadata"
    if str(sample_row.get("inclusion_status", "")) == "sample_context_blocked":
        return "blocked_missing_location_detail"
    chronology = sample_row.get("chronology", {})
    if not isinstance(chronology, dict):
        return "blocked_weak_chronology"
    if chronology.get("time_start_bp") is None or chronology.get("time_end_bp") is None:
        return "blocked_weak_chronology"
    coordinates = sample_row.get("coordinates", {})
    if not isinstance(coordinates, dict):
        return "partially_grounded"
    has_coordinates = bool(
        str(coordinates.get("latitude_text", "")).strip()
        and str(coordinates.get("longitude_text", "")).strip()
    )
    if (
        has_coordinates
        and str(coordinates.get("confidence", "")).strip() != "withheld"
    ):
        return "fully_grounded"
    return "partially_grounded"


def _has_any_linkage(sample_row: dict[str, object]) -> bool:
    return bool(
        str(sample_row.get("paper_doi", "")).strip()
        or str(sample_row.get("paper_url", "")).strip()
        or str(sample_row.get("supplementary_source", "")).strip()
    )


def _sample_backed_site_count(sample_rows: list[dict[str, object]]) -> int:
    return len(
        {
            str(row.get("locality_identity", {}).get("stable_token", "")).strip()
            for row in sample_rows
            if isinstance(row.get("locality_identity"), dict)
            and str(row.get("inclusion_status", "")) != "sample_context_blocked"
            and str(row.get("locality_identity", {}).get("stable_token", "")).strip()
        }
    )


def _readme_curated_sample_count(path: Path) -> int | None:
    if not path.is_file():
        return None
    match = _SPECIES_SAMPLE_COUNT_RE.search(path.read_text(encoding="utf-8"))
    if match is None:
        return None
    return int(match.group("count"))


def _group_sample_rows_by_project(
    sample_rows: list[dict[str, object]],
) -> dict[str, list[dict[str, object]]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for row in sample_rows:
        accession = str(row.get("project_accession", "")).strip()
        if accession:
            grouped.setdefault(accession, []).append(row)
    return grouped


def _load_all_sample_rows(data_root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for species_name in TRACKED_ADNA_SPECIES:
        rows.extend(_load_sample_rows(_species_root(data_root, species_name)))
    return rows


def _load_all_locality_rows(data_root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for species_name in TRACKED_ADNA_SPECIES:
        rows.extend(_load_locality_rows(_species_root(data_root, species_name)))
    return rows


def _load_sample_rows(species_root: Path) -> list[dict[str, object]]:
    path = species_root / "normalized" / "sample_records.json"
    if not path.is_file():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("samples", [])
    return [row for row in rows if isinstance(row, dict)]


def _load_locality_rows(species_root: Path) -> list[dict[str, object]]:
    path = species_root / "normalized" / "locality_summaries.json"
    if not path.is_file():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("localities", [])
    return [row for row in rows if isinstance(row, dict)]


def _species_root(data_root: Path, species_name: str) -> Path:
    return adna_species_root(Path(data_root), species_name)
