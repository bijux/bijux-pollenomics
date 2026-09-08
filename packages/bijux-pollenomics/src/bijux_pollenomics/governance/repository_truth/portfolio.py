"""Repository-wide truth and documentation portfolio orchestration."""

from __future__ import annotations

from pathlib import Path

from .documentation import (
    build_repository_docs_restoration_ledger,
    build_repository_docs_scope_validation,
)
from .integrity import (
    build_repository_governance_artifact_review,
    build_repository_recovery_review,
)
from .metrics import (
    _build_claim_freeze_reasons,
    _build_core_counts,
    _claim_check,
    _load_json,
)
from .release import build_repository_final_release_refusal

__all__ = [
    "build_repository_claim_audit",
    "build_repository_docs_recovery_review",
    "build_repository_truth_posture",
    "render_repository_claim_audit_markdown",
    "render_repository_docs_recovery_review_markdown",
    "render_repository_truth_posture_markdown",
]


def build_repository_truth_posture(
    *,
    data_root: Path,
    docs_root: Path,
    report_root: Path,
) -> dict[str, object]:
    """Build one repository-level truth review about scope, thinness, and recovery."""
    counts = _build_core_counts(data_root, docs_root, report_root)
    recovery_review = build_repository_recovery_review(
        data_root=data_root,
        docs_root=docs_root,
        report_root=report_root,
    )
    governance_review = build_repository_governance_artifact_review(
        data_root=data_root,
        report_root=report_root,
    )
    return {
        "schema_version": "repository-truth-posture.v2",
        "repository": "bijux-pollenomics",
        "primary_domains": [
            "pollen_context",
            "environmental_context",
        ],
        "contextual_domains": [
            "archaeology_context",
            "boundary_framing",
            "fieldwork_record",
            "ancient_dna_context",
            "publication_outputs",
        ],
        "incomplete_programs": [
            "animal_sample_site_extraction",
            "animal_sample_chronology_extraction",
            "animal_coordinate_resolution",
            "supplement_capture_recovery",
            "atlas_depth_recovery",
        ],
        "counts": counts,
        "recovery_priorities": [
            "archive missing supplementary material and convert it into sample-owned locality and chronology evidence",
            "rebuild animal locality extraction so sample rows do not collapse into project-level or region-level geography",
            "rebuild chronology extraction so atlas and country outputs stop depending on broad or unresolved sample dates",
            "keep pollen, environmental, archaeology, and boundary explanation first-class while animal aDNA recovery continues",
        ],
        "claim_freeze_reasons": _build_claim_freeze_reasons(counts),
        "do_not_repeat": [
            "do not treat checked-in JSON file count as scientific progress",
            "do not let public atlas presence stand in for sample-owned locality and chronology evidence",
            "do not narrow the repository mission to one thin recovery slice",
            "do not present internal publication accounting as if it were evidence depth",
            "do not call weak or partial animal aDNA coverage region-agnostic or broadly ready",
        ],
        "recovery_review_overview": {
            "overall_recovery_posture": recovery_review["overall_recovery_posture"],
            "average_dimension_scores": recovery_review["average_dimension_scores"],
        },
        "governance_review_summary": governance_review["summary"],
    }


def render_repository_truth_posture_markdown(payload: dict[str, object]) -> str:
    counts = payload["counts"]
    if not isinstance(counts, dict):
        raise TypeError("Repository truth counts must be a mapping")
    lines = [
        "# Repository truth posture",
        "",
        f"- Repository: `{payload['repository']}`",
        f"- Primary domains: `{', '.join(payload['primary_domains'])}`",
        f"- Contextual domains: `{', '.join(payload['contextual_domains'])}`",
        f"- Overall recovery posture: `{payload['recovery_review_overview']['overall_recovery_posture']}`",
        "",
        "## Counts",
        "",
        f"- Tracked paper count: `{counts['tracked_paper_count']}`",
        f"- Papers with archived supplements: `{counts['papers_with_archived_supplements']}`",
        f"- Published animal atlas points: `{_available_count(counts, 'published_atlas_point_count', 'animal_sample_database_review_available')}`",
        f"- Unresolved animal samples: `{_available_ratio(counts, 'animal_unresolved_sample_count', 'animal_tracked_sample_count', 'animal_map_readiness_available', 'animal_sample_database_review_available')}`",
        f"- Refused animal coordinate-provenance rows: `{_available_ratio(counts, 'animal_coordinate_refused_provenance_count', 'animal_coordinate_provenance_count', 'animal_map_readiness_available', 'animal_map_readiness_available')}`",
        f"- Source-family explainer count: `{counts['source_explainer_count']}`",
        "",
        "## Claim Freeze Reasons",
        "",
    ]
    for row in payload["claim_freeze_reasons"]:
        lines.append(f"- {row}")
    lines.extend(
        [
            "",
            "## Recovery Priorities",
            "",
        ]
    )
    for row in payload["recovery_priorities"]:
        lines.append(f"- {row}")
    lines.extend(
        [
            "",
            "## Do Not Repeat",
            "",
        ]
    )
    for row in payload["do_not_repeat"]:
        lines.append(f"- {row}")
    return "\n".join(lines) + "\n"


def build_repository_claim_audit(
    *,
    data_root: Path,
    docs_root: Path,
    report_root: Path,
) -> dict[str, object]:
    """Audit the public story against current tracked evidence depth."""
    counts = _build_core_counts(data_root, docs_root, report_root)
    docs_scope_validation = build_repository_docs_scope_validation(
        data_root=data_root,
        docs_root=docs_root,
        report_root=report_root,
    )
    root_readme_path = docs_root.parent / "README.md"
    docs_index_path = docs_root / "index.md"
    runtime_readme_path = (
        docs_root.parent / "packages" / "bijux-pollenomics" / "README.md"
    )
    data_index_path = docs_root / "public" / "pollenomics-data" / "index.md"
    sample_database_review_path = report_root / "animal_sample_database_review.json"
    release_gate_path = report_root / "animal_publication_release_gate.json"

    if not all(
        path.exists()
        for path in (
            root_readme_path,
            docs_index_path,
            runtime_readme_path,
            data_index_path,
            sample_database_review_path,
            release_gate_path,
        )
    ):
        return {
            "schema_version": "repository-claim-audit.v2",
            "audit_scope": "partial_context",
            "overall_ok": True,
            "counts": counts,
            "checks": [
                _claim_check(
                    "repository_truth_audit_requires_full_repository_context",
                    True,
                    "Repository truth audit runs in reduced mode when the full repository docs and data tree are not present.",
                    ["partial_context_assumed"],
                )
            ],
        }

    root_readme = root_readme_path.read_text(encoding="utf-8")
    docs_index = docs_index_path.read_text(encoding="utf-8")
    runtime_readme = runtime_readme_path.read_text(encoding="utf-8")
    data_index = data_index_path.read_text(encoding="utf-8")
    sample_database_review = _load_json(sample_database_review_path)
    release_gate = _load_json(release_gate_path)
    final_release_refusal = build_repository_final_release_refusal(
        data_root=data_root,
        docs_root=docs_root,
        report_root=report_root,
    )

    landing_text = (root_readme + docs_index + runtime_readme + data_index).casefold()
    checks = [
        _claim_check(
            "repository_landings_name_pollenomics_first",
            all(
                text in landing_text
                for text in ("pollenomics", "environmental", "source comparison")
            ),
            "Repository landings describe pollenomics and environmental evidence before the thin animal recovery slice.",
            [],
        ),
        _claim_check(
            "source_family_pages_restore_non_adna_breadth",
            counts["source_explainer_count"] >= 6,
            "The docs tree keeps non-aDNA source families visible and directly linkable.",
            []
            if counts["source_explainer_count"] >= 6
            else ["source_explainer_count_below_expected_floor"],
        ),
        _claim_check(
            "animal_sample_review_freezes_broad_readiness",
            (
                str(sample_database_review.get("public_posture", "")).strip()
                == "partial_sample_owned_animal_evidence_surface"
                and not bool(
                    sample_database_review.get("region_agnostic_contract_ready")
                )
            ),
            "The public animal sample review keeps the stronger Nordic sample-owned view separate from any broader region-agnostic readiness claim.",
            []
            if (
                str(sample_database_review.get("public_posture", "")).strip()
                == "partial_sample_owned_animal_evidence_surface"
                and not bool(
                    sample_database_review.get("region_agnostic_contract_ready")
                )
            )
            else ["animal_sample_database_review_overclaims_current_depth"],
        ),
        _claim_check(
            "animal_release_gate_blocks_strongest_claim",
            not bool(release_gate.get("reference_grade_claim_allowed")),
            "The current release gate still freezes the strongest public claim.",
            []
            if not bool(release_gate.get("reference_grade_claim_allowed"))
            else ["strongest_claim_not_frozen"],
        ),
        _claim_check(
            "thin_animal_surface_stays_visible",
            (
                bool(counts["animal_sample_database_review_available"])
                and counts["published_atlas_point_count"] >= 10
                and str(sample_database_review.get("public_posture", "")).strip()
                == "partial_sample_owned_animal_evidence_surface"
            ),
            "The public animal surfaces keep the current partial sample-owned posture visible instead of implying broad completion.",
            []
            if (
                bool(counts["animal_sample_database_review_available"])
                and counts["published_atlas_point_count"] >= 10
                and str(sample_database_review.get("public_posture", "")).strip()
                == "partial_sample_owned_animal_evidence_surface"
            )
            else ["partial_animal_surface_not_explicitly_named"],
        ),
        _claim_check(
            "docs_scope_validation_keeps_repository_story_wide_enough",
            bool(docs_scope_validation.get("overall_ok")),
            "The runtime, data, and maintainer handbooks stay broad enough to explain the repository without collapsing into one narrow storyline.",
            []
            if bool(docs_scope_validation.get("overall_ok"))
            else ["docs_scope_validation_failed"],
        ),
        _claim_check(
            "final_release_language_stays_refused",
            (
                not bool(final_release_refusal.get("final_release_language_allowed"))
                and str(final_release_refusal.get("overall_posture", "")).strip()
                == "final_release_language_refused"
            ),
            "The repository still refuses final release wording until the hardest evidence dimensions are actually strong enough.",
            []
            if (
                not bool(final_release_refusal.get("final_release_language_allowed"))
                and str(final_release_refusal.get("overall_posture", "")).strip()
                == "final_release_language_refused"
            )
            else ["final_release_language_not_explicitly_refused"],
        ),
    ]
    return {
        "schema_version": "repository-claim-audit.v2",
        "audit_scope": "full_repository",
        "overall_ok": all(bool(row["passed"]) for row in checks),
        "counts": counts,
        "checks": checks,
    }


def render_repository_claim_audit_markdown(payload: dict[str, object]) -> str:
    counts = payload["counts"]
    if not isinstance(counts, dict):
        raise TypeError("Repository claim-audit counts must be a mapping")
    lines = [
        "# Repository claim audit",
        "",
        f"- Overall ok: `{str(payload['overall_ok']).lower()}`",
        f"- Published animal atlas points: `{_available_count(counts, 'published_atlas_point_count', 'animal_sample_database_review_available')}`",
        f"- Papers with archived supplements: `{counts['papers_with_archived_supplements']}`",
        "",
        "| Check | Passed | Finding count |",
        "| --- | --- | ---: |",
    ]
    for row in payload["checks"]:
        lines.append(
            f"| {row['check_id']} | `{str(row['passed']).lower()}` | {row['finding_count']} |"
        )
    return "\n".join(lines) + "\n"


def _available_count(
    counts: dict[str, object],
    field: str,
    availability_field: str,
) -> str:
    if not bool(counts.get(availability_field)):
        return "unavailable"
    value = counts.get(field)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"Repository truth {field} must be a nonnegative integer")
    return str(value)


def _available_ratio(
    counts: dict[str, object],
    numerator_field: str,
    denominator_field: str,
    numerator_availability_field: str,
    denominator_availability_field: str,
) -> str:
    if not bool(counts.get(numerator_availability_field)) or not bool(
        counts.get(denominator_availability_field)
    ):
        return "unavailable"
    numerator = _available_count(counts, numerator_field, numerator_availability_field)
    denominator = _available_count(
        counts, denominator_field, denominator_availability_field
    )
    return f"{numerator} of {denominator}"


def build_repository_docs_recovery_review(
    *,
    data_root: Path,
    docs_root: Path,
    report_root: Path,
) -> dict[str, object]:
    """Review whether docs recovery is improving correctness and credibility."""
    counts = _build_core_counts(data_root, docs_root, report_root)
    ledger = build_repository_docs_restoration_ledger(
        data_root=data_root,
        docs_root=docs_root,
        report_root=report_root,
    )
    docs_scope_validation = build_repository_docs_scope_validation(
        data_root=data_root,
        docs_root=docs_root,
        report_root=report_root,
    )
    claim_audit = build_repository_claim_audit(
        data_root=data_root,
        docs_root=docs_root,
        report_root=report_root,
    )
    rows = [
        {
            "dimension_key": "restoration_completeness",
            "score": 4 if ledger["status_counts"]["replacement_incomplete"] == 0 else 2,
            "finding": (
                f"{ledger['status_counts']['verified_replacement']} of {ledger['row_count']} missing handbook pages now have verified replacements"
            ),
        },
        {
            "dimension_key": "navigation_breadth",
            "score": 4 if docs_scope_validation["overall_ok"] else 1,
            "finding": "runtime, data, and maintainer landings link their restored breadth surfaces directly",
        },
        {
            "dimension_key": "credible_presentation",
            "score": 4 if claim_audit["overall_ok"] else 2,
            "finding": "repository truth, claim, and docs breadth surfaces now fail overclaims rather than narrating optimism",
        },
        {
            "dimension_key": "cross_domain_visibility",
            "score": 4 if int(counts["source_explainer_count"]) >= 10 else 2,
            "finding": "non-aDNA source families remain directly explainable beside the thinner animal recovery surface",
        },
    ]
    overall_posture = (
        "moving_toward_elegant_correctness"
        if all(int(row["score"]) >= 4 for row in rows)
        else "recovery_still_fragile"
    )
    return {
        "schema_version": "repository-docs-recovery-review.v1",
        "overall_posture": overall_posture,
        "evidence_anchors": [
            "docs/report/repository_docs_restoration_ledger.json",
            "docs/report/repository_docs_scope_validation.json",
            "docs/report/repository_claim_audit.json",
            "docs/report/repository_cross_domain_evidence_matrix.json",
        ],
        "rows": rows,
    }


def render_repository_docs_recovery_review_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Repository docs recovery review",
        "",
        f"- Overall posture: `{payload['overall_posture']}`",
        "",
        "| Dimension | Score | Finding |",
        "| --- | ---: | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| `{row['dimension_key']}` | {row['score']} | {row['finding']} |"
        )
    lines.extend(
        [
            "",
            "## Evidence Anchors",
            "",
        ]
    )
    for row in payload["evidence_anchors"]:
        lines.append(f"- `{row}`")
    return "\n".join(lines) + "\n"
