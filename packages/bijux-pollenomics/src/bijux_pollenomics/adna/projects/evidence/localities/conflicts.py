from __future__ import annotations

from functools import cache
from pathlib import Path

from ....sources.archive import build_archive_project_catalog
from .evidence_rows import build_project_sample_locality_evidence_rows
from .semantics import _normalize_text
from .worksheets import build_project_locality_worksheet_rows


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


def _conflict_reason(packet: dict[str, object], context: dict[str, object]) -> str:
    packet_bucket = str(packet["locality_evidence_bucket"])
    if packet_bucket == "exact_site_evidence":
        return "project_context_disagrees_with_sample_owned_site"
    if str(context["source_claim_scope"]) == "resolved_place_string":
        return "coordinate_resolution_names_a_different_place_than_the_sample_row"
    return "project_context_cannot_substitute_for_sample_owned_or_unresolved_sample_locality"
