from __future__ import annotations

from functools import cache
from pathlib import Path

from ....sources.archive import build_archive_project_catalog
from .evidence_rows import build_project_sample_locality_evidence_rows
from .semantics import _normalize_text
from .worksheets import build_project_locality_worksheet_rows


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
