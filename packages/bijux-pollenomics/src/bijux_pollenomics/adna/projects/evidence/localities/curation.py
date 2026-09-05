from __future__ import annotations

from collections import defaultdict
from functools import cache
from pathlib import Path

from ....sources.archive import build_archive_project_catalog
from .evidence_rows import build_project_sample_locality_evidence_rows
from .semantics import _normalize_text
from .worksheets import build_project_locality_worksheet_rows


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
