from __future__ import annotations

import json
from pathlib import Path

from ...foundation import (
    build_repository_atlas_input_audit,
    build_repository_claim_audit,
    build_repository_cross_domain_evidence_matrix,
    build_repository_docs_scope_validation,
    build_repository_docs_recovery_review,
    build_repository_docs_restoration_ledger,
    build_repository_governance_artifact_review,
    build_repository_recovery_review,
    build_repository_source_acquisition_queue,
    build_repository_source_explainer_audit,
    build_repository_source_family_matrix,
    build_repository_scientific_progress_audit,
    build_repository_truth_posture,
    render_repository_atlas_input_audit_markdown,
    render_repository_claim_audit_markdown,
    render_repository_cross_domain_evidence_matrix_markdown,
    render_repository_docs_scope_validation_markdown,
    render_repository_docs_recovery_review_markdown,
    render_repository_docs_restoration_ledger_markdown,
    render_repository_governance_artifact_review_markdown,
    render_repository_recovery_review_markdown,
    render_repository_source_acquisition_queue_markdown,
    render_repository_source_explainer_audit_markdown,
    render_repository_source_family_matrix_markdown,
    render_repository_scientific_progress_audit_markdown,
    render_repository_truth_posture_markdown,
)

__all__ = ["publish_repository_truth_outputs"]


def publish_repository_truth_outputs(
    output_root: Path,
    *,
    data_root: Path,
    docs_root: Path,
) -> dict[str, str]:
    """Publish repository-level truth packets beside the tracked report tree."""
    output_root = Path(output_root)
    data_root = Path(data_root)
    docs_root = Path(docs_root)

    payloads = {
        "repository_truth_posture": (
            build_repository_truth_posture(
                data_root=data_root,
                docs_root=docs_root,
                report_root=output_root,
            ),
            render_repository_truth_posture_markdown,
        ),
        "repository_recovery_review": (
            build_repository_recovery_review(
                data_root=data_root,
                docs_root=docs_root,
                report_root=output_root,
            ),
            render_repository_recovery_review_markdown,
        ),
        "repository_source_family_matrix": (
            build_repository_source_family_matrix(
                data_root=data_root,
                docs_root=docs_root,
                report_root=output_root,
            ),
            render_repository_source_family_matrix_markdown,
        ),
        "repository_source_explainer_audit": (
            build_repository_source_explainer_audit(
                data_root=data_root,
                docs_root=docs_root,
                report_root=output_root,
            ),
            render_repository_source_explainer_audit_markdown,
        ),
        "repository_atlas_input_audit": (
            build_repository_atlas_input_audit(
                data_root=data_root,
                docs_root=docs_root,
                report_root=output_root,
            ),
            render_repository_atlas_input_audit_markdown,
        ),
        "repository_cross_domain_evidence_matrix": (
            build_repository_cross_domain_evidence_matrix(
                data_root=data_root,
                docs_root=docs_root,
                report_root=output_root,
            ),
            render_repository_cross_domain_evidence_matrix_markdown,
        ),
        "repository_docs_restoration_ledger": (
            build_repository_docs_restoration_ledger(
                data_root=data_root,
                docs_root=docs_root,
                report_root=output_root,
            ),
            render_repository_docs_restoration_ledger_markdown,
        ),
        "repository_docs_scope_validation": (
            build_repository_docs_scope_validation(
                data_root=data_root,
                docs_root=docs_root,
                report_root=output_root,
            ),
            render_repository_docs_scope_validation_markdown,
        ),
        "repository_docs_recovery_review": (
            build_repository_docs_recovery_review(
                data_root=data_root,
                docs_root=docs_root,
                report_root=output_root,
            ),
            render_repository_docs_recovery_review_markdown,
        ),
        "repository_source_acquisition_queue": (
            build_repository_source_acquisition_queue(
                data_root=data_root,
                docs_root=docs_root,
                report_root=output_root,
            ),
            render_repository_source_acquisition_queue_markdown,
        ),
        "repository_governance_artifact_review": (
            build_repository_governance_artifact_review(
                data_root=data_root,
                report_root=output_root,
            ),
            render_repository_governance_artifact_review_markdown,
        ),
        "repository_claim_audit": (
            build_repository_claim_audit(
                data_root=data_root,
                docs_root=docs_root,
                report_root=output_root,
            ),
            render_repository_claim_audit_markdown,
        ),
        "repository_scientific_progress_audit": (
            build_repository_scientific_progress_audit(
                data_root=data_root,
                docs_root=docs_root,
                report_root=output_root,
            ),
            render_repository_scientific_progress_audit_markdown,
        ),
    }
    for stem, (payload, render_markdown) in payloads.items():
        (output_root / f"{stem}.json").write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )
        (output_root / f"{stem}.md").write_text(
            render_markdown(payload),
            encoding="utf-8",
        )
    return {
        f"{stem}_json": f"{stem}.json" for stem in payloads
    } | {
        f"{stem}_markdown": f"{stem}.md" for stem in payloads
    }
