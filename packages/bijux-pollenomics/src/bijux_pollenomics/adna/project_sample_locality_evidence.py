from __future__ import annotations

from collections import defaultdict
from functools import cache
from pathlib import Path

from ..core.files import write_json, write_text
from .catalogs import render_csv_rows
from .coordinate_provenance import resolve_project_context_coordinate_provenance
from .ena import build_archive_project_catalog
from .project_sample_sites import (
    build_project_sample_site_rows,
)
from .site_evidence import resolve_project_context_site_evidence

__all__ = [
    "ADNA_LOCALITY_CLASSES",
    "build_project_locality_completeness_rows",
    "build_project_locality_worksheet_rows",
    "build_project_locality_substitution_ledger",
    "build_project_sample_locality_evidence_rows",
    "build_sample_locality_conflict_ledger",
    "build_sample_locality_manual_curation_workflow_rows",
    "build_site_name_normalization_dictionary_rows",
    "build_species_locality_completeness_rows",
    "materialize_project_sample_locality_evidence_library",
]

ADNA_LOCALITY_CLASSES = (
    "excavation_site",
    "broader_locality",
    "municipality",
    "region",
    "country",
    "inferred_place_string",
    "unresolved",
)

_BROADER_PLACE_MARKERS = (
    "archipelago",
    "basin",
    "central europe",
    "context",
    "dispersal",
    "europe",
    "galicia",
    "lake ",
    "levant",
    "near east",
    "north africa",
    "peninsula",
    "plateau",
    "region",
    "steppe",
    "transect",
)


@cache
def build_project_sample_locality_evidence_rows(
    output_root: Path,
    project_accession: str,
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for row in build_project_sample_site_rows(output_root, project_accession):
        locality_class = _classify_sample_site_row(row)
        rows.append(
            {
                "project_accession": row.project_accession,
                "species_latin_name": row.species_latin_name,
                "species_common_name": row.species_common_name,
                "repo_stable_sample_id": row.repo_stable_sample_id,
                "preferred_sample_label": row.preferred_sample_label,
                "sample_basis": row.sample_basis,
                "sample_evidence_status": row.sample_evidence_status,
                "sample_identity_resolution": row.sample_identity_resolution,
                "sample_ambiguity_note": row.sample_ambiguity_note,
                "assigned_locality_text": row.locality_text,
                "locality_resolution_status": row.locality_resolution_status,
                "assigned_locality_class": locality_class,
                "normalized_display_spelling": _normalized_display_spelling(
                    row.locality_text,
                    row.site_name,
                ),
                "geocoding_safe_token": _geocoding_safe_token(
                    _normalized_display_spelling(row.locality_text, row.site_name)
                ),
                "site_name": row.site_name,
                "municipality_name": row.municipality_name,
                "region_name": row.region_name,
                "country_name": row.country_name,
                "broader_geography": row.broader_geography,
                "evidence_source_surface": _source_surface_for_packet(row),
                "location_evidence_artifact_path": row.location_evidence_artifact_path,
                "location_evidence_artifact_kind": row.location_evidence_artifact_kind,
                "location_evidence_locator": row.location_evidence_locator,
                "location_evidence_text": row.location_evidence_text,
                "coordinate_basis": row.coordinate_basis,
                "coordinate_mapping_posture": row.coordinate_mapping_posture,
                "coordinate_confidence": row.coordinate_confidence,
                "chronology_text": row.chronology_text,
                "locality_evidence_bucket": _locality_evidence_bucket(
                    locality_class=locality_class,
                    locality_resolution_status=row.locality_resolution_status,
                ),
                "review_note": row.review_note,
            }
        )
    rows.sort(
        key=lambda item: (
            str(item["project_accession"]),
            str(item["repo_stable_sample_id"]),
        )
    )
    return tuple(rows)


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
        key = (
            "supplementary_table",
            str(first["assigned_locality_text"]),
            str(first["location_evidence_artifact_path"]),
            str(first["location_evidence_locator"]),
        )
        if key in seen:
            continue
        seen.add(key)
        worksheet_rows.append(
            {
                "project_accession": first["project_accession"],
                "species_latin_name": first["species_latin_name"],
                "source_surface": "supplementary_table",
                "source_claim_scope": "sample_owned_locality",
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

    for row in resolve_project_context_coordinate_provenance(project_accession):
        source_surface = _source_surface_for_context(row.source_artifact_path, "")
        original_key = (
            source_surface,
            row.original_place_text,
            row.source_artifact_path,
            f"{row.source_locator}:original",
        )
        if row.original_place_text and original_key not in seen:
            seen.add(original_key)
            worksheet_rows.append(
                {
                    "project_accession": row.project_accession,
                    "species_latin_name": row.species_latin_name,
                    "source_surface": source_surface,
                    "source_claim_scope": "original_place_string",
                    "supporting_sample_count": 0,
                    "original_locality_text": row.original_place_text,
                    "resolved_locality_text": row.original_place_text,
                    "locality_class": _classify_context_place(
                        locality_text=row.original_place_text,
                        political_entity=row.political_entity or "",
                    ),
                    "site_name": "",
                    "municipality_name": "",
                    "region_name": "",
                    "country_name": row.political_entity
                    if _looks_like_country(row.political_entity or "")
                    else "",
                    "broader_geography": ""
                    if _looks_like_country(row.political_entity or "")
                    else (row.political_entity or ""),
                    "geocoding_safe_token": _geocoding_safe_token(
                        row.original_place_text
                    ),
                    "source_artifact_path": row.source_artifact_path,
                    "source_artifact_kind": "coordinate_provenance_original_place",
                    "source_locator": row.source_locator,
                    "source_excerpt": row.confidence_rationale,
                }
            )
        resolved_key = (
            "coordinate_resolution",
            row.resolved_place_text,
            row.source_artifact_path,
            f"{row.source_locator}:resolved",
        )
        if row.resolved_place_text and resolved_key not in seen:
            seen.add(resolved_key)
            worksheet_rows.append(
                {
                    "project_accession": row.project_accession,
                    "species_latin_name": row.species_latin_name,
                    "source_surface": "coordinate_resolution",
                    "source_claim_scope": "resolved_place_string",
                    "supporting_sample_count": 0,
                    "original_locality_text": row.resolved_place_text,
                    "resolved_locality_text": _normalized_display_spelling(
                        row.resolved_place_text,
                        row.site_label,
                    ),
                    "locality_class": _classify_context_place(
                        locality_text=row.resolved_place_text,
                        political_entity=row.political_entity or "",
                    ),
                    "site_name": row.site_label
                    if row.mapping_posture == "mappable_point"
                    else "",
                    "municipality_name": "",
                    "region_name": "",
                    "country_name": row.political_entity
                    if _looks_like_country(row.political_entity or "")
                    else "",
                    "broader_geography": ""
                    if _looks_like_country(row.political_entity or "")
                    else (row.political_entity or ""),
                    "geocoding_safe_token": _geocoding_safe_token(
                        row.resolved_place_text
                    ),
                    "source_artifact_path": row.source_artifact_path,
                    "source_artifact_kind": "coordinate_provenance_resolved_place",
                    "source_locator": row.source_locator,
                    "source_excerpt": row.confidence_rationale,
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


@cache
def build_sample_locality_conflict_ledger(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for project in build_archive_project_catalog():
        sample_packets = build_project_sample_locality_evidence_rows(
            output_root,
            project.project_accession,
        )
        context_rows = build_project_locality_worksheet_rows(
            output_root, project.project_accession
        )
        comparison_rows = [
            row
            for row in context_rows
            if row["source_claim_scope"] != "sample_owned_locality"
        ]
        for packet in sample_packets:
            if not str(packet["assigned_locality_text"]).strip():
                continue
            for context in comparison_rows:
                if _normalize_text(
                    str(packet["assigned_locality_text"])
                ) == _normalize_text(
                    str(
                        context["resolved_locality_text"]
                        or context["original_locality_text"]
                    )
                ):
                    continue
                rows.append(
                    {
                        "project_accession": packet["project_accession"],
                        "species_latin_name": packet["species_latin_name"],
                        "repo_stable_sample_id": packet["repo_stable_sample_id"],
                        "preferred_sample_label": packet["preferred_sample_label"],
                        "sample_locality_text": packet["assigned_locality_text"],
                        "sample_locality_class": packet["assigned_locality_class"],
                        "sample_resolution_status": packet[
                            "locality_resolution_status"
                        ],
                        "conflicting_source_surface": context["source_surface"],
                        "conflicting_claim_scope": context["source_claim_scope"],
                        "conflicting_locality_text": context["resolved_locality_text"]
                        or context["original_locality_text"],
                        "conflicting_locality_class": context["locality_class"],
                        "source_artifact_path": context["source_artifact_path"],
                        "source_locator": context["source_locator"],
                        "conflict_reason": _conflict_reason(packet, context),
                    }
                )
    rows.sort(
        key=lambda item: (
            str(item["project_accession"]),
            str(item["repo_stable_sample_id"]),
            str(item["conflicting_source_surface"]),
            str(item["conflicting_locality_text"]),
        )
    )
    return tuple(rows)


@cache
def build_sample_locality_manual_curation_workflow_rows(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for project in build_archive_project_catalog():
        sample_packets = build_project_sample_locality_evidence_rows(
            output_root,
            project.project_accession,
        )
        worksheet_rows = build_project_locality_worksheet_rows(
            output_root, project.project_accession
        )
        grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
        for packet in sample_packets:
            status = str(packet["locality_resolution_status"])
            if status not in {
                "project_level_site_only",
                "region_only",
                "unresolved",
                "named_place_inferred",
            }:
                continue
            grouped[
                (
                    status,
                    str(packet["assigned_locality_text"]),
                )
            ].append(packet)
        for (status, locality_text), packets in grouped.items():
            candidate_matches = _candidate_matches_for_locality(
                locality_text, worksheet_rows
            )
            rows.append(
                {
                    "project_accession": project.project_accession,
                    "species_latin_name": project.species_latin_name,
                    "decision_status": "pending_manual_curation",
                    "locality_resolution_status": status,
                    "unresolved_place_string": locality_text,
                    "candidate_matches": candidate_matches,
                    "final_decision": "",
                    "decision_rationale": "",
                    "queued_sample_count": len(packets),
                    "queued_sample_ids": [
                        str(packet["repo_stable_sample_id"]) for packet in packets
                    ],
                    "recommended_source_surfaces": sorted(
                        {
                            str(row["source_surface"])
                            for row in worksheet_rows
                            if str(row["source_claim_scope"]) != "sample_owned_locality"
                        }
                    ),
                }
            )
    rows.sort(
        key=lambda item: (
            str(item["project_accession"]),
            str(item["locality_resolution_status"]),
            str(item["unresolved_place_string"]).casefold(),
        )
    )
    return tuple(rows)


@cache
def build_project_locality_substitution_ledger(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for project in build_archive_project_catalog():
        sample_packets = build_project_sample_locality_evidence_rows(
            output_root,
            project.project_accession,
        )
        if not sample_packets:
            continue
        worksheet_rows = build_project_locality_worksheet_rows(
            output_root, project.project_accession
        )
        sample_owned_localities = {
            _normalize_text(str(packet["normalized_display_spelling"]))
            for packet in sample_packets
            if str(packet["locality_evidence_bucket"]) == "exact_site_evidence"
        }
        blocked_packets = [
            packet
            for packet in sample_packets
            if str(packet["locality_evidence_bucket"]) != "exact_site_evidence"
        ]
        context_rows = [
            row
            for row in worksheet_rows
            if row["source_claim_scope"] != "sample_owned_locality"
        ]
        if len(sample_owned_localities) > 1 and context_rows:
            rows.append(
                {
                    "project_accession": project.project_accession,
                    "species_latin_name": project.species_latin_name,
                    "publication_blocked": False,
                    "reason": "project_context_rows_cannot_substitute_for_multi_site_sample_owned_localities",
                    "distinct_sample_owned_locality_count": len(
                        sample_owned_localities
                    ),
                    "project_context_row_count": len(context_rows),
                    "blocked_sample_count": 0,
                }
            )
        elif blocked_packets and len(sample_packets) > 1:
            rows.append(
                {
                    "project_accession": project.project_accession,
                    "species_latin_name": project.species_latin_name,
                    "publication_blocked": True,
                    "reason": "project_level_locality_row_cannot_stand_in_for_all_samples",
                    "distinct_sample_owned_locality_count": len(
                        sample_owned_localities
                    ),
                    "project_context_row_count": len(context_rows),
                    "blocked_sample_count": len(blocked_packets),
                }
            )
    rows.sort(key=lambda item: (str(item["project_accession"]), str(item["reason"])))
    return tuple(rows)


@cache
def build_site_name_normalization_dictionary_rows(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    grouped: dict[tuple[str, str], dict[str, object]] = {}
    for project in build_archive_project_catalog():
        for row in build_project_locality_worksheet_rows(
            output_root, project.project_accession
        ):
            token = _geocoding_safe_token(
                str(row["resolved_locality_text"] or row["original_locality_text"])
            )
            if not token:
                continue
            key = (str(row["project_accession"]), token)
            current = grouped.setdefault(
                key,
                {
                    "project_accession": row["project_accession"],
                    "species_latin_name": row["species_latin_name"],
                    "normalized_display_spelling": str(
                        row["resolved_locality_text"] or row["original_locality_text"]
                    ),
                    "geocoding_safe_token": token,
                    "original_source_spellings": set(),
                    "alternative_spellings": set(),
                    "source_surfaces": set(),
                    "locality_classes": set(),
                },
            )
            spelling = str(row["original_locality_text"]).strip()
            if spelling:
                current["original_source_spellings"].add(spelling)
                if spelling != current["normalized_display_spelling"]:
                    current["alternative_spellings"].add(spelling)
            current["source_surfaces"].add(str(row["source_surface"]))
            current["locality_classes"].add(str(row["locality_class"]))
    rows = []
    for row in grouped.values():
        rows.append(
            {
                "project_accession": row["project_accession"],
                "species_latin_name": row["species_latin_name"],
                "normalized_display_spelling": row["normalized_display_spelling"],
                "geocoding_safe_token": row["geocoding_safe_token"],
                "original_source_spellings": sorted(row["original_source_spellings"]),
                "alternative_spellings": sorted(row["alternative_spellings"]),
                "source_surfaces": sorted(row["source_surfaces"]),
                "locality_classes": sorted(row["locality_classes"]),
            }
        )
    rows.sort(
        key=lambda item: (
            str(item["project_accession"]),
            str(item["normalized_display_spelling"]).casefold(),
        )
    )
    return tuple(rows)


@cache
def build_species_locality_completeness_rows(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for project in build_archive_project_catalog():
        grouped[project.species_latin_name].extend(
            build_project_sample_locality_evidence_rows(
                output_root, project.project_accession
            )
        )
    rows: list[dict[str, object]] = []
    for species_name, packets in sorted(grouped.items()):
        rows.append(
            {
                "species_latin_name": species_name,
                **_locality_completeness_counts(packets),
            }
        )
    return tuple(rows)


@cache
def build_project_locality_completeness_rows(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for project in build_archive_project_catalog():
        packets = build_project_sample_locality_evidence_rows(
            output_root, project.project_accession
        )
        rows.append(
            {
                "project_accession": project.project_accession,
                "species_latin_name": project.species_latin_name,
                **_locality_completeness_counts(packets),
            }
        )
    return tuple(rows)


def materialize_project_sample_locality_evidence_library(output_root: Path) -> None:
    output_root = Path(output_root)
    source_root = output_root / "adna" / "governance" / "source_library"
    source_root.mkdir(parents=True, exist_ok=True)

    conflict_rows = list(build_sample_locality_conflict_ledger(output_root))
    curation_rows = list(
        build_sample_locality_manual_curation_workflow_rows(output_root)
    )
    substitution_rows = list(build_project_locality_substitution_ledger(output_root))
    dictionary_rows = list(build_site_name_normalization_dictionary_rows(output_root))
    species_rows = list(build_species_locality_completeness_rows(output_root))
    project_rows = list(build_project_locality_completeness_rows(output_root))

    for project in build_archive_project_catalog():
        project_root = source_root / "projects" / project.project_accession
        project_root.mkdir(parents=True, exist_ok=True)
        worksheet_rows = list(
            build_project_locality_worksheet_rows(
                output_root, project.project_accession
            )
        )
        packet_rows = list(
            build_project_sample_locality_evidence_rows(
                output_root, project.project_accession
            )
        )
        write_json(
            project_root / "locality_worksheet.json",
            {
                "schema_version": "animal-project-locality-worksheet.v1",
                "project_accession": project.project_accession,
                "species_latin_name": project.species_latin_name,
                "row_count": len(worksheet_rows),
                "rows": worksheet_rows,
            },
        )
        write_text(
            project_root / "locality_worksheet.csv",
            render_csv_rows(tuple(worksheet_rows)),
        )
        write_json(
            project_root / "sample_locality_evidence.json",
            {
                "schema_version": "animal-project-sample-locality-evidence.v1",
                "project_accession": project.project_accession,
                "species_latin_name": project.species_latin_name,
                "row_count": len(packet_rows),
                "rows": packet_rows,
            },
        )
        write_text(
            project_root / "sample_locality_evidence.csv",
            render_csv_rows(tuple(packet_rows)),
        )

    write_json(
        source_root / "sample_locality_conflict_ledger.json",
        {
            "schema_version": "animal-sample-locality-conflict-ledger.v1",
            "rows": conflict_rows,
        },
    )
    write_text(
        source_root / "sample_locality_conflict_ledger.md",
        _render_sample_locality_conflict_ledger_markdown(conflict_rows),
    )
    write_json(
        source_root / "sample_locality_manual_curation_workflow.json",
        {
            "schema_version": "animal-sample-locality-manual-curation-workflow.v1",
            "rows": curation_rows,
        },
    )
    write_text(
        source_root / "sample_locality_manual_curation_workflow.md",
        _render_sample_locality_manual_curation_workflow_markdown(curation_rows),
    )
    write_json(
        source_root / "project_locality_substitution_ledger.json",
        {
            "schema_version": "animal-project-locality-substitution-ledger.v1",
            "rows": substitution_rows,
        },
    )
    write_text(
        source_root / "project_locality_substitution_ledger.md",
        _render_project_locality_substitution_ledger_markdown(substitution_rows),
    )
    write_json(
        source_root / "site_name_normalization_dictionary.json",
        {
            "schema_version": "animal-site-name-normalization-dictionary.v1",
            "rows": dictionary_rows,
        },
    )
    write_text(
        source_root / "site_name_normalization_dictionary.csv",
        render_csv_rows(tuple(dictionary_rows)),
    )
    write_json(
        source_root / "species_locality_completeness.json",
        {
            "schema_version": "animal-species-locality-completeness.v1",
            "rows": species_rows,
        },
    )
    write_text(
        source_root / "species_locality_completeness.csv",
        render_csv_rows(tuple(species_rows)),
    )
    write_json(
        source_root / "project_locality_completeness.json",
        {
            "schema_version": "animal-project-locality-completeness.v1",
            "rows": project_rows,
        },
    )
    write_text(
        source_root / "project_locality_completeness.csv",
        render_csv_rows(tuple(project_rows)),
    )


def _classify_sample_site_row(row: object) -> str:
    status = str(getattr(row, "locality_resolution_status", "")).strip()
    locality_text = str(getattr(row, "locality_text", "")).strip()
    site_name = str(getattr(row, "site_name", "")).strip()
    municipality_name = str(getattr(row, "municipality_name", "")).strip()
    region_name = str(getattr(row, "region_name", "")).strip()
    country_name = str(getattr(row, "country_name", "")).strip()
    broader_geography = str(getattr(row, "broader_geography", "")).strip()
    if not locality_text or status == "unresolved":
        return "unresolved"
    if status == "named_place_inferred":
        return "inferred_place_string"
    if municipality_name and not site_name:
        return "municipality"
    if region_name and not site_name:
        return "region"
    if (
        country_name
        and locality_text == country_name
        and not site_name
        and not region_name
    ):
        return "country"
    if broader_geography and not site_name:
        return "broader_locality"
    if _looks_broad(locality_text):
        return "broader_locality"
    return "excavation_site"


def _classify_context_place(*, locality_text: str, political_entity: str) -> str:
    if not locality_text.strip():
        return "unresolved"
    if _looks_like_country(locality_text):
        return "country"
    if _looks_broad(locality_text) or (
        _looks_broad(political_entity) and not _looks_like_country(political_entity)
    ):
        return "broader_locality"
    return "excavation_site"


def _source_surface_for_packet(row: object) -> str:
    kind = str(getattr(row, "location_evidence_artifact_kind", "")).strip()
    path = str(getattr(row, "location_evidence_artifact_path", "")).strip()
    return _source_surface_for_context(path, kind)


def _source_surface_for_context(path: str, kind: str) -> str:
    lowered_kind = kind.casefold()
    lowered_path = path.casefold()
    if (
        "supplementary" in lowered_kind
        or "supplementary" in lowered_path
        or path.endswith(".xlsx")
    ):
        return "supplementary_table"
    if "archive" in lowered_kind or "archive_metadata" in lowered_path:
        return "archive_metadata"
    if "crossref" in lowered_kind or lowered_path.endswith("crossref.json"):
        return "crossref_metadata"
    if lowered_path.endswith(".html") or "article" in lowered_kind:
        return "article_text"
    return "tracked_source_artifact"


def _normalized_display_spelling(locality_text: str, site_name: str) -> str:
    return site_name.strip() or locality_text.strip()


def _geocoding_safe_token(value: str) -> str:
    return _normalize_text(value)


def _normalize_text(value: str) -> str:
    return "".join(character for character in value.casefold() if character.isalnum())


def _looks_like_country(value: str) -> bool:
    stripped = value.strip()
    return (
        bool(stripped)
        and all(marker not in stripped.casefold() for marker in _BROADER_PLACE_MARKERS)
        and "," not in stripped
        and " and " not in stripped.casefold()
    )


def _looks_broad(value: str) -> bool:
    lowered = value.casefold()
    return any(marker in lowered for marker in _BROADER_PLACE_MARKERS)


def _locality_evidence_bucket(
    *, locality_class: str, locality_resolution_status: str
) -> str:
    if (
        locality_resolution_status == "direct_sample_site"
        and locality_class == "excavation_site"
    ):
        return "exact_site_evidence"
    if locality_resolution_status == "unresolved":
        return "unresolved_geography"
    if locality_class in {
        "broader_locality",
        "municipality",
        "region",
        "country",
        "inferred_place_string",
    }:
        return "broader_locality_evidence"
    if locality_resolution_status in {"project_level_site_only", "region_only"}:
        return "broader_locality_evidence"
    return "exact_site_evidence"


def _candidate_matches_for_locality(
    locality_text: str,
    worksheet_rows: tuple[dict[str, object], ...],
) -> list[str]:
    token = _normalize_text(locality_text)
    candidates = []
    for row in worksheet_rows:
        resolved = str(
            row["resolved_locality_text"] or row["original_locality_text"]
        ).strip()
        if not resolved:
            continue
        resolved_token = _normalize_text(resolved)
        if (
            not token
            or token == resolved_token
            or token in resolved_token
            or resolved_token in token
        ):
            candidates.append(resolved)
    return sorted(set(candidates))


def _conflict_reason(packet: dict[str, object], context: dict[str, object]) -> str:
    packet_bucket = str(packet["locality_evidence_bucket"])
    if packet_bucket == "exact_site_evidence":
        return "project_context_disagrees_with_sample_owned_site"
    if str(context["source_claim_scope"]) == "resolved_place_string":
        return "coordinate_resolution_names_a_different_place_than_the_sample_row"
    return "project_context_cannot_substitute_for_sample_owned_or_unresolved_sample_locality"


def _locality_completeness_counts(
    packets: list[dict[str, object]] | tuple[dict[str, object], ...],
) -> dict[str, object]:
    exact_count = 0
    broader_count = 0
    unresolved_count = 0
    class_counts = dict.fromkeys(ADNA_LOCALITY_CLASSES, 0)
    for packet in packets:
        class_counts[str(packet["assigned_locality_class"])] += 1
        bucket = str(packet["locality_evidence_bucket"])
        if bucket == "exact_site_evidence":
            exact_count += 1
        elif bucket == "broader_locality_evidence":
            broader_count += 1
        else:
            unresolved_count += 1
    sample_count = len(packets)
    return {
        "recovered_sample_row_count": sample_count,
        "exact_site_evidence_count": exact_count,
        "broader_locality_evidence_count": broader_count,
        "unresolved_geography_count": unresolved_count,
        "excavation_site_count": class_counts["excavation_site"],
        "broader_locality_count": class_counts["broader_locality"],
        "municipality_count": class_counts["municipality"],
        "region_count": class_counts["region"],
        "country_count": class_counts["country"],
        "inferred_place_string_count": class_counts["inferred_place_string"],
        "locality_unresolved_count": class_counts["unresolved"],
        "locality_completeness_ratio": 0.0
        if sample_count == 0
        else round(exact_count / sample_count, 4),
    }


def _render_sample_locality_conflict_ledger_markdown(
    rows: list[dict[str, object]],
) -> str:
    lines = [
        "# Sample locality conflict ledger",
        "",
        f"- Conflicting rows: `{len(rows)}`",
        "",
    ]
    if not rows:
        lines.append("No sample-locality conflicts are currently published.")
        lines.append("")
        return "\n".join(lines)
    lines.extend(
        [
            "| Project accession | Sample id | Sample locality | Conflicting surface | Conflicting locality | Reason |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['project_accession']} | {row['repo_stable_sample_id']} | "
            f"{row['sample_locality_text']} | {row['conflicting_source_surface']} | "
            f"{row['conflicting_locality_text']} | {row['conflict_reason']} |"
        )
    lines.append("")
    return "\n".join(lines)


def _render_sample_locality_manual_curation_workflow_markdown(
    rows: list[dict[str, object]],
) -> str:
    lines = [
        "# Sample locality manual curation workflow",
        "",
        f"- Queued locality strings: `{len(rows)}`",
        "",
    ]
    if not rows:
        lines.append("No locality strings currently require manual curation.")
        lines.append("")
        return "\n".join(lines)
    lines.extend(
        [
            "| Project accession | Status | Unresolved place string | Candidate matches | Queued samples |",
            "| --- | --- | --- | --- | ---: |",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['project_accession']} | {row['locality_resolution_status']} | "
            f"{row['unresolved_place_string']} | {', '.join(row['candidate_matches']) or '-'} | "
            f"{row['queued_sample_count']} |"
        )
    lines.append("")
    return "\n".join(lines)


def _render_project_locality_substitution_ledger_markdown(
    rows: list[dict[str, object]],
) -> str:
    lines = [
        "# Project locality substitution ledger",
        "",
        f"- Flagged projects: `{len(rows)}`",
        "",
    ]
    if not rows:
        lines.append("No project currently relies on a locality substitution posture.")
        lines.append("")
        return "\n".join(lines)
    lines.extend(
        [
            "| Project accession | Publication blocked | Reason | Distinct sample-owned localities | Blocked sample count |",
            "| --- | --- | --- | ---: | ---: |",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['project_accession']} | {str(row['publication_blocked']).lower()} | "
            f"{row['reason']} | {row['distinct_sample_owned_locality_count']} | "
            f"{row['blocked_sample_count']} |"
        )
    lines.append("")
    return "\n".join(lines)
