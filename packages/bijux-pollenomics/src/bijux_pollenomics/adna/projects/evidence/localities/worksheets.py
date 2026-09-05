from __future__ import annotations

from collections import defaultdict
from functools import cache
from pathlib import Path

from ..coordinates import resolve_project_context_coordinate_provenance
from ..sites import resolve_project_context_site_evidence
from .evidence_rows import build_project_sample_locality_evidence_rows
from .semantics import (
    _classify_context_place,
    _geocoding_safe_token,
    _looks_like_country,
    _normalize_text,
    _normalized_display_spelling,
    _source_surface_for_context,
)


@cache
def build_project_locality_worksheet_rows(
    output_root: Path,
    project_accession: str,
) -> tuple[dict[str, object], ...]:
    sample_packets = build_project_sample_locality_evidence_rows(
        output_root, project_accession
    )
    worksheet_rows: list[dict[str, object]] = []
    seen: set[tuple[str, str, str, str]] = set()

    grouped_packets: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for packet in sample_packets:
        grouped_packets[
            (
                _normalize_text(str(packet["assigned_locality_text"])),
                _normalize_text(
                    str(packet["country_name"] or packet["broader_geography"])
                ),
            )
        ].append(packet)
    for packets in grouped_packets.values():
        first = packets[0]
        source_path = str(first["location_evidence_artifact_path"])
        source_kind = str(first["location_evidence_artifact_kind"])
        source_surface = _source_surface_for_context(source_path, source_kind)
        resolution_status = str(first["locality_resolution_status"])
        claim_scope = (
            "sample_owned_locality"
            if resolution_status == "direct_sample_site"
            else "sample_group_locality"
            if resolution_status == "sample_group_site"
            else "project_context_site"
        )
        key = (
            source_surface,
            str(first["assigned_locality_text"]),
            source_path,
            str(first["location_evidence_locator"]),
        )
        if key in seen:
            continue
        seen.add(key)
        worksheet_rows.append(
            {
                "project_accession": first["project_accession"],
                "species_latin_name": first["species_latin_name"],
                "source_surface": source_surface,
                "source_claim_scope": claim_scope,
                "supporting_sample_count": len(packets),
                "original_locality_text": first["assigned_locality_text"],
                "resolved_locality_text": first["normalized_display_spelling"],
                "locality_class": first["assigned_locality_class"],
                "site_name": first["site_name"],
                "municipality_name": first["municipality_name"],
                "region_name": first["region_name"],
                "country_name": first["country_name"],
                "broader_geography": first["broader_geography"],
                "geocoding_safe_token": first["geocoding_safe_token"],
                "source_artifact_path": first["location_evidence_artifact_path"],
                "source_artifact_kind": first["location_evidence_artifact_kind"],
                "source_locator": first["location_evidence_locator"],
                "source_excerpt": first["location_evidence_text"],
            }
        )

    for row in resolve_project_context_site_evidence(project_accession):
        locality_class = _classify_context_place(
            locality_text=row.site_label,
            political_entity=row.political_entity or "",
        )
        key = (
            _source_surface_for_context(
                row.source_artifact_path, row.source_artifact_kind
            ),
            row.site_label,
            row.source_artifact_path,
            row.source_locator,
        )
        if key in seen:
            continue
        seen.add(key)
        worksheet_rows.append(
            {
                "project_accession": row.project_accession,
                "species_latin_name": row.species_latin_name,
                "source_surface": _source_surface_for_context(
                    row.source_artifact_path,
                    row.source_artifact_kind,
                ),
                "source_claim_scope": "project_context_site",
                "supporting_sample_count": 0,
                "original_locality_text": row.site_label,
                "resolved_locality_text": _normalized_display_spelling(
                    row.site_label,
                    row.site_label,
                ),
                "locality_class": locality_class,
                "site_name": row.site_label
                if locality_class == "excavation_site"
                else "",
                "municipality_name": "",
                "region_name": "",
                "country_name": row.political_entity
                if _looks_like_country(row.political_entity or "")
                else "",
                "broader_geography": ""
                if _looks_like_country(row.political_entity or "")
                else (row.political_entity or ""),
                "geocoding_safe_token": _geocoding_safe_token(row.site_label),
                "source_artifact_path": row.source_artifact_path,
                "source_artifact_kind": row.source_artifact_kind,
                "source_locator": row.source_locator,
                "source_excerpt": row.exact_source_text,
            }
        )

    for coordinate_row in resolve_project_context_coordinate_provenance(
        project_accession
    ):
        source_surface = _source_surface_for_context(
            coordinate_row.source_artifact_path, ""
        )
        original_key = (
            source_surface,
            coordinate_row.original_place_text,
            coordinate_row.source_artifact_path,
            f"{coordinate_row.source_locator}:original",
        )
        if coordinate_row.original_place_text and original_key not in seen:
            seen.add(original_key)
            worksheet_rows.append(
                {
                    "project_accession": coordinate_row.project_accession,
                    "species_latin_name": coordinate_row.species_latin_name,
                    "source_surface": source_surface,
                    "source_claim_scope": "original_place_string",
                    "supporting_sample_count": 0,
                    "original_locality_text": coordinate_row.original_place_text,
                    "resolved_locality_text": coordinate_row.original_place_text,
                    "locality_class": _classify_context_place(
                        locality_text=coordinate_row.original_place_text,
                        political_entity=coordinate_row.political_entity or "",
                    ),
                    "site_name": "",
                    "municipality_name": "",
                    "region_name": "",
                    "country_name": coordinate_row.political_entity
                    if _looks_like_country(coordinate_row.political_entity or "")
                    else "",
                    "broader_geography": ""
                    if _looks_like_country(coordinate_row.political_entity or "")
                    else (coordinate_row.political_entity or ""),
                    "geocoding_safe_token": _geocoding_safe_token(
                        coordinate_row.original_place_text
                    ),
                    "source_artifact_path": coordinate_row.source_artifact_path,
                    "source_artifact_kind": "coordinate_provenance_original_place",
                    "source_locator": coordinate_row.source_locator,
                    "source_excerpt": coordinate_row.confidence_rationale,
                }
            )
        resolved_key = (
            "coordinate_resolution",
            coordinate_row.resolved_place_text,
            coordinate_row.source_artifact_path,
            f"{coordinate_row.source_locator}:resolved",
        )
        if coordinate_row.resolved_place_text and resolved_key not in seen:
            seen.add(resolved_key)
            worksheet_rows.append(
                {
                    "project_accession": coordinate_row.project_accession,
                    "species_latin_name": coordinate_row.species_latin_name,
                    "source_surface": "coordinate_resolution",
                    "source_claim_scope": "resolved_place_string",
                    "supporting_sample_count": 0,
                    "original_locality_text": coordinate_row.resolved_place_text,
                    "resolved_locality_text": _normalized_display_spelling(
                        coordinate_row.resolved_place_text,
                        coordinate_row.site_label,
                    ),
                    "locality_class": _classify_context_place(
                        locality_text=coordinate_row.resolved_place_text,
                        political_entity=coordinate_row.political_entity or "",
                    ),
                    "site_name": coordinate_row.site_label
                    if coordinate_row.mapping_posture == "mappable_point"
                    else "",
                    "municipality_name": "",
                    "region_name": "",
                    "country_name": coordinate_row.political_entity
                    if _looks_like_country(coordinate_row.political_entity or "")
                    else "",
                    "broader_geography": ""
                    if _looks_like_country(coordinate_row.political_entity or "")
                    else (coordinate_row.political_entity or ""),
                    "geocoding_safe_token": _geocoding_safe_token(
                        coordinate_row.resolved_place_text
                    ),
                    "source_artifact_path": coordinate_row.source_artifact_path,
                    "source_artifact_kind": "coordinate_provenance_resolved_place",
                    "source_locator": coordinate_row.source_locator,
                    "source_excerpt": coordinate_row.confidence_rationale,
                }
            )

    worksheet_rows.sort(
        key=lambda item: (
            str(item["project_accession"]),
            str(item["source_surface"]),
            str(item["resolved_locality_text"]).casefold(),
            str(item["source_locator"]),
        )
    )
    return tuple(worksheet_rows)
