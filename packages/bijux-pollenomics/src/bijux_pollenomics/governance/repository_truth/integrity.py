"""Repository recovery and governance-artifact integrity assessments."""

from __future__ import annotations

from pathlib import Path

from .metrics import (
    SCORE_MAX,
    _artifact_review_row,
    _build_core_counts,
    _ratio_score,
    _recovery_review_row,
)

__all__ = [
    "build_repository_recovery_review",
    "render_repository_recovery_review_markdown",
    "build_repository_governance_artifact_review",
    "render_repository_governance_artifact_review_markdown",
]


def build_repository_recovery_review(
    *,
    data_root: Path,
    docs_root: Path,
    report_root: Path,
) -> dict[str, object]:
    """Score the main repository surfaces by evidence depth and honesty."""
    counts = _build_core_counts(data_root, docs_root, report_root)
    rows = [
        _recovery_review_row(
            "pollen_context",
            "Pollen context",
            data_completeness=3,
            provenance_clarity=3,
            documentation_clarity=4,
            output_honesty=3,
            metrics={
                "normalized_file_count": counts["pollen_normalized_file_count"],
                "source_pages": 2,
            },
            note="LandClim and Neotoma are real tracked context layers and now have direct explainer pages.",
        ),
        _recovery_review_row(
            "archaeology_context",
            "Archaeology context",
            data_completeness=3,
            provenance_clarity=3,
            documentation_clarity=4,
            output_honesty=3,
            metrics={
                "normalized_file_count": counts["archaeology_normalized_file_count"],
                "source_pages": 2,
            },
            note="SEAD and RAÄ are present and documented, but they remain contextual rather than fully synthesized outputs.",
        ),
        _recovery_review_row(
            "boundary_framing",
            "Boundary framing",
            data_completeness=4,
            provenance_clarity=4,
            documentation_clarity=4,
            output_honesty=4,
            metrics={
                "raw_file_count": counts["boundary_raw_file_count"],
                "normalized_file_count": counts["boundary_normalized_file_count"],
            },
            note="Boundary geometry is one of the strongest and clearest non-aDNA surfaces in the repository.",
        ),
        _recovery_review_row(
            "fieldwork_record",
            "Fieldwork record",
            data_completeness=2,
            provenance_clarity=3,
            documentation_clarity=3,
            output_honesty=4,
            metrics={"fieldwork_page_count": counts["fieldwork_page_count"]},
            note="Fieldwork is intentionally narrow and honest, but it is still only one anchored record surface.",
        ),
        _recovery_review_row(
            "ancient_dna_context",
            "Ancient DNA context",
            data_completeness=_ratio_score(
                counts["papers_with_archived_supplements"],
                counts["tracked_paper_count"],
            ),
            provenance_clarity=_ratio_score(
                counts["animal_map_supported_rows"],
                counts["animal_sample_row_count"],
            ),
            documentation_clarity=3,
            output_honesty=3,
            metrics={
                "tracked_papers": counts["tracked_paper_count"],
                "papers_with_archived_supplements": counts[
                    "papers_with_archived_supplements"
                ],
                "published_atlas_points": counts["published_atlas_point_count"],
                "unresolved_rows": counts["animal_map_unresolved_rows"],
            },
            note="The animal aDNA program has real tracked structure but still weak evidence depth relative to its public surfaces.",
        ),
        _recovery_review_row(
            "publication_outputs",
            "Publication outputs",
            data_completeness=_ratio_score(
                counts["published_atlas_point_count"],
                max(counts["animal_sample_row_count"], 1),
            ),
            provenance_clarity=3,
            documentation_clarity=3,
            output_honesty=3,
            metrics={
                "published_atlas_points": counts["published_atlas_point_count"],
                "published_country_bundles": counts["published_country_bundle_count"],
            },
            note="The publication tree is reviewable and traceable, but the animal point surface remains too thin for stronger readiness language.",
        ),
        _recovery_review_row(
            "documentation_architecture",
            "Documentation architecture",
            data_completeness=3,
            provenance_clarity=3,
            documentation_clarity=4,
            output_honesty=4,
            metrics={
                "source_explainer_count": counts["source_explainer_count"],
                "landing_page_count": counts["landing_page_count"],
            },
            note="Breadth has been restored across repository, data, maintainer, fieldwork, and atlas entry surfaces.",
        ),
    ]
    averages = {
        "data_completeness": round(
            sum(int(row["data_completeness"]) for row in rows) / len(rows), 2
        ),
        "provenance_clarity": round(
            sum(int(row["provenance_clarity"]) for row in rows) / len(rows), 2
        ),
        "documentation_clarity": round(
            sum(int(row["documentation_clarity"]) for row in rows) / len(rows), 2
        ),
        "output_honesty": round(
            sum(int(row["output_honesty"]) for row in rows) / len(rows), 2
        ),
    }
    return {
        "schema_version": "repository-recovery-review.v1",
        "score_max": SCORE_MAX,
        "overall_recovery_posture": (
            "recovery_required"
            if any(int(row["data_completeness"]) <= 1 for row in rows)
            else "moderate_recovery"
        ),
        "average_dimension_scores": averages,
        "rows": rows,
    }


def render_repository_recovery_review_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Repository recovery review",
        "",
        f"- Overall recovery posture: `{payload['overall_recovery_posture']}`",
        f"- Score max: `{payload['score_max']}`",
        "",
        "| Surface | Data completeness | Provenance clarity | Documentation clarity | Output honesty |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['display_name']} | {row['data_completeness']} | "
            f"{row['provenance_clarity']} | {row['documentation_clarity']} | "
            f"{row['output_honesty']} |"
        )
    return "\n".join(lines) + "\n"


def build_repository_governance_artifact_review(
    *,
    data_root: Path,
    report_root: Path,
) -> dict[str, object]:
    """Review current aDNA governance artifacts by evidence value, not file presence."""
    rows = [
        _artifact_review_row(
            "docs/report/animal_publication_release_gate.json",
            "keep",
            "claim_gate",
            "This file blocks strong public claims when traceability or chronology support is missing.",
        ),
        _artifact_review_row(
            "docs/report/animal_foundation_validation.json",
            "keep",
            "validation",
            "This file checks sample, site, coordinate, and source structure instead of just formatting.",
        ),
        _artifact_review_row(
            "data/adna/governance/source_library/project_sample_site_review.json",
            "keep",
            "evidence_review",
            "This file surfaces site-assignment weakness project by project.",
        ),
        _artifact_review_row(
            "data/adna/governance/source_library/project_sample_chronology_review.json",
            "keep",
            "evidence_review",
            "This file surfaces chronology extraction weakness project by project.",
        ),
        _artifact_review_row(
            "docs/report/animal_point_evidence_review.json",
            "keep",
            "traceability",
            "This file keeps published points anchored to sample, site, and coordinate support.",
        ),
        _artifact_review_row(
            "docs/report/animal_atlas_readiness.json",
            "reframe",
            "coverage_summary",
            "The current name reads stronger than the underlying point depth and must always sit beside unresolved and blocked counts.",
        ),
        _artifact_review_row(
            "docs/report/animal_sample_database_review.json",
            "reframe",
            "public_posture",
            "This file should describe partial recovery posture, not broad readiness or region-agnostic support.",
        ),
        _artifact_review_row(
            "data/adna/governance/cross_species_map_readiness.json",
            "reframe",
            "coverage_summary",
            "This file is useful only when readers can also see how many rows remain unresolved or refused.",
        ),
        _artifact_review_row(
            "docs/report/animal_output_audit.json",
            "retire",
            "publication_accounting",
            "This file counts shipped public surfaces but says little about evidence depth and should not lead the scientific story.",
        ),
    ]
    repo_root = data_root.parent
    published_report_prefix = Path("docs/report")

    def artifact_exists(artifact_path: str) -> bool:
        path = Path(artifact_path)
        if path.is_relative_to(published_report_prefix):
            return (report_root / path.relative_to(published_report_prefix)).exists()
        return (repo_root / path).exists()

    existing_rows = [row for row in rows if artifact_exists(str(row["artifact_path"]))]
    summary = {
        "keep": sum(1 for row in existing_rows if row["action"] == "keep"),
        "reframe": sum(1 for row in existing_rows if row["action"] == "reframe"),
        "retire": sum(1 for row in existing_rows if row["action"] == "retire"),
    }
    return {
        "schema_version": "repository-governance-artifact-review.v1",
        "summary": summary,
        "rows": existing_rows,
    }


def render_repository_governance_artifact_review_markdown(
    payload: dict[str, object],
) -> str:
    lines = [
        "# Repository governance artifact review",
        "",
        "| Artifact | Action | Surface kind | Reason |",
        "| --- | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| `{row['artifact_path']}` | `{row['action']}` | `{row['surface_kind']}` | {row['reason']} |"
        )
    return "\n".join(lines) + "\n"
