"""Deterministic publication of the SEAD classification review packet."""

from __future__ import annotations

import csv
import io
import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import cast

from .service import JsonObject, build_sead_scientific_classification_review
from .validation import validate_sead_scientific_classification_review


def materialize_sead_scientific_classification_review(
    data_root: Path,
) -> dict[str, Path]:
    """Write the governed JSON, Markdown, and reviewer worksheet atomically."""
    root = Path(data_root).resolve()
    review_root = root / "sead" / "review"
    review_root.mkdir(parents=True, exist_ok=True)
    packet = build_sead_scientific_classification_review(root)
    return write_sead_scientific_classification_review(review_root, packet)


def write_sead_scientific_classification_review(
    review_root: Path,
    packet: JsonObject,
) -> dict[str, Path]:
    """Write a prebuilt governed packet to an explicitly owned review root."""
    review_root = Path(review_root)
    review_root.mkdir(parents=True, exist_ok=True)
    validate_sead_scientific_classification_review(packet)
    paths = {
        "json": review_root / "scientific_classification_review.json",
        "markdown": review_root / "scientific_classification_review.md",
        "csv": review_root / "scientific_classification_candidates.csv",
    }
    _atomic_write(paths["json"], render_review_json(packet))
    _atomic_write(paths["markdown"], render_review_markdown(packet))
    _atomic_write(paths["csv"], render_candidate_csv(packet))
    return paths


def render_review_json(packet: JsonObject) -> str:
    """Render canonical human-readable JSON."""
    validate_sead_scientific_classification_review(packet)
    return json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render_candidate_csv(packet: JsonObject) -> str:
    """Render one non-accepting worksheet row per source taxon."""
    validate_sead_scientific_classification_review(packet)
    fieldnames = [
        "source_run_id",
        "build_id",
        "acquisition_manifest_sha256",
        "parent_admission_sha256",
        "evidence_manifest_sha256",
        "evidence_file_set_sha256",
        "candidate_id",
        "taxon_relation_id",
        "taxon_id",
        "source_order_id",
        "source_order_name",
        "source_family_id",
        "source_family_name",
        "source_genus_id",
        "source_genus_name",
        "source_species",
        "source_author_id",
        "source_author_name",
        "source_ecocode_count",
        "source_ecocodes_json",
        "review_priority",
        "review_status",
        "current_classification_status",
        "proposed_accepted_taxon_concept_id",
        "proposed_accepted_taxon_name",
        "proposed_accepted_rank",
        "proposed_primary_group_id",
        "proposed_primary_subgroup_id",
        "proposed_role_ids",
        "evidence_reference_ids",
        "reviewer_id",
        "decision_date",
        "review_rationale",
        "review_confidence",
        "propagation_allowed",
    ]
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    lineage = cast(Mapping[str, object], packet["lineage"])
    for raw in cast(list[object], packet["candidates"]):
        row = dict(cast(Mapping[str, object], raw))
        row.update(lineage)
        row["source_ecocodes_json"] = json.dumps(
            row.pop("source_ecocodes"), ensure_ascii=False, sort_keys=True
        )
        for field in ("proposed_role_ids", "evidence_reference_ids"):
            row[field] = json.dumps(row[field], ensure_ascii=False, sort_keys=True)
        writer.writerow(row)
    return output.getvalue()


def render_review_markdown(packet: JsonObject) -> str:
    """Render the bounded human review guide and exact accounting."""
    validate_sead_scientific_classification_review(packet)
    lineage = cast(Mapping[str, object], packet["lineage"])
    ecology = cast(Mapping[str, object], packet["ecocode_inventory"])
    citations = cast(Mapping[str, object], packet["citation_audit"])
    chronology = cast(Mapping[str, object], packet["chronology_authority_gaps"])
    comparability = cast(Mapping[str, object], chronology["comparability_counts"])
    eligibility = cast(
        Mapping[str, object], chronology["chronology_eligibility_counts"]
    )
    chronology_reasons = cast(Mapping[str, object], chronology["refusal_reason_counts"])
    events = cast(Mapping[str, object], packet["event_refusal_posture"])
    lines = [
        "# SEAD qualified scientific classification review",
        "",
        "This packet prepares source-native SEAD taxonomy and ecocodes for qualified human review. No derived mapping is accepted, no reviewer is impersonated, and propagation remains refused.",
        "",
        "## Governed identity",
        "",
        f"- Source run: `{lineage['source_run_id']}`",
        f"- Build: `{lineage['build_id']}`",
        f"- Acquisition manifest SHA-256: `{lineage['acquisition_manifest_sha256']}`",
        f"- Parent admission SHA-256: `{lineage['parent_admission_sha256']}`",
        f"- Evidence manifest SHA-256: `{lineage['evidence_manifest_sha256']}`",
        f"- Evidence file-set SHA-256: `{lineage['evidence_file_set_sha256']}`",
        "",
        "## Review posture",
        "",
        "- Candidate mappings: `1,974`",
        "- Accepted mappings: `0`",
        "- Accepted qualified mappings: `0`",
        "- Status: `pending_qualified_scientific_review` / `not_accepted`",
        "- Propagation: `refused` (`source_classification_not_accepted`)",
        "",
        "The complete row-level worksheet is `scientific_classification_candidates.csv`. Its target concepts, groups, roles, evidence references, reviewer, and decision date are intentionally empty.",
        "",
        "## Source-native taxonomic and ecocode inventory",
        "",
        "- Taxon relations: `1,974`",
        f"- Ecocode rows: `{ecology['ecocode_row_count']}`",
        f"- Unique taxon-definition pairs: `{ecology['unique_taxon_definition_pair_count']}`",
        f"- Taxa with ecocodes: `{ecology['taxa_with_ecocode_count']}`",
        f"- Taxa without ecocodes: `{ecology['taxa_without_ecocode_count']}`",
        "",
        "| Native ecocode system | Rows | Taxa | Definitions |",
        "| --- | ---: | ---: | ---: |",
    ]
    for raw in cast(list[Mapping[str, object]], ecology["systems"]):
        lines.append(
            f"| {raw['system_name']} | {raw['ecocode_row_count']} | "
            f"{raw['taxon_count']} | {raw['definition_count']} |"
        )
    lines.extend(
        [
            "",
            "The 173 plant-system rows are review priorities, not accepted ecological or pollen mappings. Bugs and Koch ecocodes must not be silently translated into pollen groups.",
            "",
            "## Citation authority audit",
            "",
            f"- Captured bibliography source rows: `{citations['captured_bibliography_source_row_count']}`",
            f"- Chronology-linked bibliography source rows: `{citations['chronology_bibliography_source_row_count']}`",
            f"- Site/sample bibliography relations: `{citations['chronology_bibliography_relation_count']}`",
            "- Accepted classification authorities: `0`",
            "",
            "| Ecocode system | Bibliography ID | Status | Reason |",
            "| --- | ---: | --- | --- |",
        ]
    )
    for raw in cast(list[Mapping[str, object]], citations["systems"]):
        lines.append(
            f"| {raw['system_name']} | {raw['biblio_id'] or 'None'} | "
            f"{raw['citation_status']} | {raw['reason_code']} |"
        )
    lines.extend(
        [
            "",
            "The plant system references bibliography ID 5555, whose captured title concerns Central European Ptinidae beetles. It is retained as a conflicting source assertion, not accepted as plant-classification authority.",
            "",
            "## Chronology authority gaps",
            "",
            f"- Claims: `{chronology['claim_count']}`",
            f"- Comparable and eligible: `{comparability['comparable']}`",
            f"- Context-only: `{comparability['context_only']}`",
            f"- Unresolved: `{comparability['unresolved']}`",
            f"- Refused: `{eligibility['refused']}`",
            (
                "- Post-1950 BP values retained as source-native context and refused "
                f"from numeric BP comparison: `{chronology_reasons['negative_bp']}`"
            ),
            (
                "- Relative periods requiring governed mapping: "
                f"`{chronology_reasons['relative_period_requires_governed_mapping']}`"
            ),
            (
                "- Analysis-entity ages with unspecified basis: "
                f"`{chronology_reasons['analysis_entity_age_basis_unspecified']}`"
            ),
            (
                "- Geochronology rows with unknown calibration posture: "
                f"`{chronology_reasons['geochronology_calibration_posture_unknown']}`"
            ),
            "",
            "`chronology_not_comparable` is an umbrella reason over the refused population. The three specific authority-gap counts are nested within it and must not be added to it.",
            "",
            "## Event consequence",
            "",
            f"- Source observations: `{events['observation_denominator']}`",
            f"- Eligible events: `{events['eligible_event_count']}`",
            f"- Refused events: `{events['refused_event_count']}`",
            "- Every observation is refused for `source_classification_not_accepted`.",
            "- Other refusal reasons overlap; they are not mutually exclusive totals.",
            "",
            "This packet does not establish arrival, migration, causation, or propagation.",
            "",
            "## Qualified reviewer checklist",
            "",
        ]
    )
    for requirement in cast(list[str], packet["review_requirements"]):
        lines.append(f"- {requirement}")
    lines.append("")
    return "\n".join(lines)


def _atomic_write(path: Path, content: str) -> None:
    staging = path.with_name(f".{path.name}.staging-{os.getpid()}")
    if staging.exists() or staging.is_symlink():
        raise FileExistsError(f"SEAD review staging path exists: {staging}")
    try:
        staging.write_text(content, encoding="utf-8")
        os.replace(staging, path)
    finally:
        if staging.exists():
            staging.unlink()
