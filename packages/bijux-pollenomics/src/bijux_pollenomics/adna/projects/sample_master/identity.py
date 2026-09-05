"""Sample identity normalization, deduplication, and reconciliation."""

from __future__ import annotations

from pathlib import Path
import re
from bijux_pollenomics.adna.workflow.source_artifacts import (
    resolve_source_artifact_path,
)
from bijux_pollenomics.adna.sources.library import (
    AdnaPaperRegistryRow,
    build_paper_registry,
    build_project_registry,
)
from .models import AdnaProjectSampleMasterRow


def _taxon_alignment_status(
    *,
    configured_species: str,
    source_native_scientific_names: tuple[str, ...],
) -> str:
    if not source_native_scientific_names:
        return "not_reported"
    if len(source_native_scientific_names) > 1:
        return "archive_taxon_conflict"
    if source_native_scientific_names[0].casefold() == configured_species.casefold():
        return "project_species_match"
    return "project_species_mismatch"


def _deduplicate_sample_rows(
    rows: list[AdnaProjectSampleMasterRow],
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    grouped: dict[str, list[AdnaProjectSampleMasterRow]] = {}
    for row in rows:
        grouped.setdefault(_sample_identity_key(row), []).append(row)

    merged_rows: list[AdnaProjectSampleMasterRow] = []
    for group in grouped.values():
        merged_rows.append(_merge_sample_row_group(group))
    merged_rows.sort(key=lambda row: (row.project_accession, row.repo_stable_sample_id))
    return tuple(merged_rows)


def _sample_identity_key(row: AdnaProjectSampleMasterRow) -> str:
    for candidate in (
        row.archive_native_sample_id,
        row.archive_native_experiment_id,
        row.paper_native_sample_label,
        row.supplementary_table_sample_label,
        row.preferred_sample_label,
    ):
        normalized = _normalize_sample_label(candidate)
        if normalized:
            return normalized
    return row.repo_stable_sample_id


def _normalize_sample_label(value: str) -> str:
    if _is_missing_source_value(value):
        return ""
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def _is_missing_source_value(value: str) -> bool:
    return value.strip().casefold() in {"", "-", "n/a", "na", "not available"}


def _clean_optional_source_text(value: str) -> str:
    return "" if _is_missing_source_value(value) else value.strip()


def _merge_sample_row_group(
    group: list[AdnaProjectSampleMasterRow],
) -> AdnaProjectSampleMasterRow:
    if len(group) == 1:
        return group[0]
    first = group[0]
    locality_values = {row.locality_text for row in group if row.locality_text}
    chronology_values = {row.chronology_text for row in group if row.chronology_text}
    ambiguity_note = ""
    resolution = "final"
    if len(locality_values) > 1 or len(chronology_values) > 1:
        resolution = "ambiguous"
        ambiguity_note = "Multiple source rows appear to reference the same sample label but disagree on locality or chronology fields."
    source_native_scientific_names = tuple(
        dict.fromkeys(
            name.strip()
            for row in group
            for name in row.source_native_scientific_name.split(" || ")
            if name.strip()
        )
    )
    return AdnaProjectSampleMasterRow(
        species_latin_name=first.species_latin_name,
        species_common_name=first.species_common_name,
        project_accession=first.project_accession,
        repo_stable_sample_id=first.repo_stable_sample_id,
        archive_native_sample_id=_first_non_empty(
            *(row.archive_native_sample_id for row in group)
        ),
        paper_native_sample_label=_first_non_empty(
            *(row.paper_native_sample_label for row in group)
        ),
        supplementary_table_sample_label=_first_non_empty(
            *(row.supplementary_table_sample_label for row in group)
        ),
        preferred_sample_label=_first_non_empty(
            *(row.preferred_sample_label for row in group)
        ),
        sample_basis=_first_non_empty(*(row.sample_basis for row in group)),
        sample_evidence_status=_first_non_empty(
            *(row.sample_evidence_status for row in group)
        ),
        sample_lineage_path=_join_distinct(*(row.sample_lineage_path for row in group)),
        sample_lineage_locator=_join_distinct(
            *(row.sample_lineage_locator for row in group)
        ),
        sample_lineage_excerpt=_join_distinct(
            *(row.sample_lineage_excerpt for row in group)
        ),
        sample_identity_resolution=resolution,
        sample_ambiguity_note=ambiguity_note,
        locality_text=_first_non_empty(*(row.locality_text for row in group)),
        political_entity=_first_non_empty(*(row.political_entity for row in group)),
        latitude_text=_first_non_empty(*(row.latitude_text for row in group)),
        longitude_text=_first_non_empty(*(row.longitude_text for row in group)),
        chronology_text=_first_non_empty(*(row.chronology_text for row in group)),
        chronology_dating_basis=_first_non_empty(
            *(row.chronology_dating_basis for row in group)
        ),
        chronology_evidence_class=_first_non_empty(
            *(row.chronology_evidence_class for row in group)
        ),
        chronology_precision_posture=_first_non_empty(
            *(row.chronology_precision_posture for row in group)
        ),
        source_native_tax_id=_join_distinct(
            *(row.source_native_tax_id for row in group)
        ),
        source_native_scientific_name=_join_distinct(
            *(row.source_native_scientific_name for row in group)
        ),
        taxon_alignment_status=_taxon_alignment_status(
            configured_species=first.species_latin_name,
            source_native_scientific_names=source_native_scientific_names,
        ),
        archive_native_experiment_id=_first_non_empty(
            *(row.archive_native_experiment_id for row in group)
        ),
        source_native_identity_kind=_first_non_empty(
            *(row.source_native_identity_kind for row in group)
        ),
    )


def _join_distinct(*values: str) -> str:
    seen: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.append(value)
    return " || ".join(seen)


def _first_non_empty(*values: str) -> str:
    for value in values:
        if value:
            return value
    return ""


def _normalize_horse_panel_label(value: str) -> str:
    text = value.replace("_", " ").strip()
    text = re.sub(r"\bExtract\s*\d+\b", "", text, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", text).strip()


def _derive_horse_locality_text(sample_label: str) -> str:
    normalized = _normalize_horse_panel_label(sample_label)
    tokens = normalized.split()
    if tokens and tokens[-1].isdigit():
        tokens = tokens[:-1]
    locality_tokens: list[str] = []
    for index, token in enumerate(tokens):
        if index > 0 and any(char.isdigit() for char in token):
            break
        locality_tokens.append(token)
    if locality_tokens:
        return " ".join(locality_tokens)
    return normalized


def _format_bp_point_text(value: str) -> str:
    text = value.replace(",", "").strip()
    if not text:
        return ""
    text = re.sub(r"\s*yBP\b", " BP", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+years?\s+ago\b", " BP", text, flags=re.IGNORECASE)
    if text.endswith("BP"):
        return re.sub(r"\s+", " ", text).strip()
    if text.isdigit():
        return f"{text} BP"
    return re.sub(r"\s+", " ", text).strip()


def _format_horse_age_text(value: str) -> str:
    text = value.replace(",", "").strip()
    if _is_missing_source_value(text):
        return ""
    if re.fullmatch(r"\d+\s*-\s*\d+", text):
        range_text = re.sub(r"\s+", "", text)
        return f"{range_text} BP"
    if text.isdigit():
        return f"{text} BP"
    return _format_bp_point_text(text)


def _parse_gps_coordinate_pair(value: str) -> tuple[str, str]:
    text = value.strip()
    if not text or text == "-":
        return "", ""
    parts = [part.strip() for part in text.split(",")]
    if len(parts) != 2:
        return "", ""
    return (
        _normalize_gps_coordinate_component(parts[0], expected_axis="latitude"),
        _normalize_gps_coordinate_component(parts[1], expected_axis="longitude"),
    )


def _normalize_gps_coordinate_component(value: str, *, expected_axis: str) -> str:
    raw = value.strip()
    if not raw or raw == "-" or raw.upper() == "N/A":
        return ""
    match = re.fullmatch(
        r"(?P<number>-?\d+(?:\.\d+)?)\s*(?P<hemisphere>[NSEW])?",
        raw,
        flags=re.IGNORECASE,
    )
    if match is None:
        return raw
    number = float(match.group("number"))
    hemisphere = (match.group("hemisphere") or "").upper()
    if hemisphere in {"S", "W"}:
        number = -abs(number)
    elif hemisphere in {"N", "E"}:
        number = abs(number)
    if expected_axis == "longitude" and hemisphere == "N":
        number = abs(number)
    return str(number)


def _clean_coordinate_text(value: str) -> str:
    text = value.strip()
    if not text or text == "-" or text.upper() == "N/A":
        return ""
    return text


def _clean_sample_chronology_text(value: str) -> str:
    text = value.replace("–", "-").replace("\xa0", " ").strip()
    if not text or text == "-" or text.upper() == "N/A":
        return ""
    text = re.sub(r"(?<=\d)\s*[-]\s*(?=\d)", "-", text)
    text = re.sub(r"(?<=\d)[A-Za-z]+$", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _ensure_bp_chronology_text(value: str) -> str:
    text = value.strip()
    if not text:
        return ""
    if "BP" in text.upper():
        return text
    if re.fullmatch(r"\d{1,5}(?:-\d{1,5})?", text):
        return f"{text} BP"
    return text


def _first_accession(value: str) -> str:
    if not value.strip():
        return ""
    return value.split(";")[0].strip()


def _cell_value(row: tuple[str, ...], index: int) -> str:
    if index >= len(row):
        return ""
    return str(row[index]).strip()


def _paper_row_by_project(
    output_root: Path, project_accession: str
) -> AdnaPaperRegistryRow:
    project_registry = {
        row.project_accession: row for row in build_project_registry(output_root)
    }
    project_row = project_registry[project_accession]
    paper_doi = project_row.primary_paper_doi
    if paper_doi is None:
        raise ValueError(f"Project has no primary paper DOI: {project_accession}")
    paper_registry = {row.paper_doi: row for row in build_paper_registry(output_root)}
    return paper_registry[paper_doi]


def _resolve_data_relative_path(output_root: Path, path: str) -> Path:
    if path.startswith("data/"):
        return resolve_source_artifact_path(output_root / path.removeprefix("data/"))
    return resolve_source_artifact_path(output_root / path)
