"""Publish repository-truth review outputs into the report tree."""

from __future__ import annotations

from collections.abc import Callable
import json
from pathlib import Path

from ...foundation import (
    build_repository_atlas_input_audit,
    build_repository_brutal_honesty_review,
    build_repository_claim_audit,
    build_repository_credibility_dashboard,
    build_repository_cross_domain_evidence_matrix,
    build_repository_docs_recovery_review,
    build_repository_docs_restoration_ledger,
    build_repository_docs_scope_validation,
    build_repository_extension_review,
    build_repository_final_release_refusal,
    build_repository_governance_artifact_review,
    build_repository_output_sustainability_review,
    build_repository_product_model,
    build_repository_recovery_review,
    build_repository_scientific_progress_audit,
    build_repository_source_acquisition_queue,
    build_repository_source_explainer_audit,
    build_repository_source_family_matrix,
    build_repository_truth_posture,
    render_repository_atlas_input_audit_markdown,
    render_repository_brutal_honesty_review_markdown,
    render_repository_claim_audit_markdown,
    render_repository_credibility_dashboard_markdown,
    render_repository_cross_domain_evidence_matrix_markdown,
    render_repository_docs_recovery_review_markdown,
    render_repository_docs_restoration_ledger_markdown,
    render_repository_docs_scope_validation_markdown,
    render_repository_extension_review_markdown,
    render_repository_final_release_refusal_markdown,
    render_repository_governance_artifact_review_markdown,
    render_repository_output_sustainability_review_markdown,
    render_repository_product_model_markdown,
    render_repository_recovery_review_markdown,
    render_repository_scientific_progress_audit_markdown,
    render_repository_source_acquisition_queue_markdown,
    render_repository_source_explainer_audit_markdown,
    render_repository_source_family_matrix_markdown,
    render_repository_truth_posture_markdown,
)
from .sead_context_outputs import (
    build_repository_sead_legibility_review,
    render_repository_sead_legibility_review_markdown,
)

__all__ = ["publish_repository_truth_outputs"]


def publish_repository_truth_outputs(
    output_root: Path,
    *,
    data_root: Path,
    docs_root: Path,
) -> dict[str, str]:
    """Publish repository-level truth reviews beside the tracked report tree."""
    output_root = Path(output_root)
    data_root = Path(data_root)
    docs_root = Path(docs_root)

    specs = _build_repository_output_specs(
        data_root=data_root,
        docs_root=docs_root,
        report_root=output_root,
    )
    _validate_repository_output_specs(specs)
    policy_payload = _build_repository_generated_output_policy(specs)

    payloads = {
        spec["stem"]: (spec["payload"], spec["render_markdown"]) for spec in specs
    }
    payloads["repository_generated_output_policy"] = (
        policy_payload,
        _render_repository_generated_output_policy_markdown,
    )

    for stem, (payload, render_markdown) in payloads.items():
        (output_root / f"{stem}.json").write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )
        (output_root / f"{stem}.md").write_text(
            render_markdown(payload),
            encoding="utf-8",
        )
    return {f"{stem}_json": f"{stem}.json" for stem in payloads} | {
        f"{stem}_markdown": f"{stem}.md" for stem in payloads
    }


def _build_repository_output_specs(
    *,
    data_root: Path,
    docs_root: Path,
    report_root: Path,
) -> list[dict[str, object]]:
    return [
        _repository_output_spec(
            stem="repository_truth_posture",
            payload=build_repository_truth_posture(
                data_root=data_root,
                docs_root=docs_root,
                report_root=report_root,
            ),
            render_markdown=render_repository_truth_posture_markdown,
            audience="maintainer_diagnostic",
            information_role="root truth posture",
            coexistence_rule="coexists with deeper review surfaces and summarizes their shared release posture",
            docs_anchor="docs/report/maintenance/index.md",
            test_anchor="packages/bijux-pollenomics/tests/unit/test_repository_truth.py",
        ),
        _repository_output_spec(
            stem="repository_product_model",
            payload=build_repository_product_model(
                data_root=data_root,
                docs_root=docs_root,
                report_root=report_root,
            ),
            render_markdown=render_repository_product_model_markdown,
            audience="maintainer_diagnostic",
            information_role="end-state product model",
            coexistence_rule="coexists with the runtime and data handbooks as the report-root statement of world-to-country product shape",
            docs_anchor="docs/01-bijux-pollenomics/foundation/end-state-product-model.md",
            test_anchor="packages/bijux-pollenomics/tests/unit/test_repository_truth.py",
        ),
        _repository_output_spec(
            stem="repository_credibility_dashboard",
            payload=build_repository_credibility_dashboard(
                data_root=data_root,
                docs_root=docs_root,
                report_root=report_root,
            ),
            render_markdown=render_repository_credibility_dashboard_markdown,
            audience="maintainer_diagnostic",
            information_role="cross-domain credibility dashboard",
            coexistence_rule="coexists with detailed audits and compresses them into release-facing dimension scores",
            docs_anchor="docs/internal/pollenomics-dev/release-support.md",
            test_anchor="packages/bijux-pollenomics/tests/unit/test_repository_truth.py",
        ),
        _repository_output_spec(
            stem="repository_recovery_review",
            payload=build_repository_recovery_review(
                data_root=data_root,
                docs_root=docs_root,
                report_root=report_root,
            ),
            render_markdown=render_repository_recovery_review_markdown,
            audience="maintainer_diagnostic",
            information_role="repository recovery review",
            coexistence_rule="coexists with truth posture and provides per-surface scoring rather than one summary sentence",
            docs_anchor="docs/report/maintenance/index.md",
            test_anchor="packages/bijux-pollenomics/tests/unit/test_repository_truth.py",
        ),
        _repository_output_spec(
            stem="repository_output_sustainability_review",
            payload=build_repository_output_sustainability_review(
                data_root=data_root,
                docs_root=docs_root,
                report_root=report_root,
            ),
            render_markdown=render_repository_output_sustainability_review_markdown,
            audience="maintainer_diagnostic",
            information_role="generated-output sustainability review",
            coexistence_rule="coexists with the generated-output policy and names where the repository is still paying complexity tax",
            docs_anchor="docs/internal/pollenomics-dev/release-support.md",
            test_anchor="packages/bijux-pollenomics/tests/unit/test_repository_truth.py",
        ),
        _repository_output_spec(
            stem="repository_extension_review",
            payload=build_repository_extension_review(
                data_root=data_root,
                docs_root=docs_root,
                report_root=report_root,
            ),
            render_markdown=render_repository_extension_review_markdown,
            audience="maintainer_diagnostic",
            information_role="extensibility and interpretability review",
            coexistence_rule="coexists with the country onboarding contract and checks whether new work improves global extensibility without making local reasoning worse",
            docs_anchor="docs/internal/pollenomics-dev/future-country-onboarding-playbook.md",
            test_anchor="packages/bijux-pollenomics/tests/unit/test_repository_truth.py",
        ),
        _repository_output_spec(
            stem="repository_source_family_matrix",
            payload=build_repository_source_family_matrix(
                data_root=data_root,
                docs_root=docs_root,
                report_root=report_root,
            ),
            render_markdown=render_repository_source_family_matrix_markdown,
            audience="maintainer_diagnostic",
            information_role="source-family coverage matrix",
            coexistence_rule="coexists with source explainers and the cross-domain matrix as the fastest source-family inventory view",
            docs_anchor="docs/report/maintenance/index.md",
            test_anchor="packages/bijux-pollenomics/tests/unit/test_repository_truth.py",
        ),
        _repository_output_spec(
            stem="repository_source_explainer_audit",
            payload=build_repository_source_explainer_audit(
                data_root=data_root,
                docs_root=docs_root,
                report_root=report_root,
            ),
            render_markdown=render_repository_source_explainer_audit_markdown,
            audience="maintainer_diagnostic",
            information_role="source explainer audit",
            coexistence_rule="coexists with source-family coverage and guards the reader-facing handbook against cross-domain blind spots",
            docs_anchor="docs/report/maintenance/index.md",
            test_anchor="packages/bijux-pollenomics/tests/unit/test_repository_truth.py",
        ),
        _repository_output_spec(
            stem="repository_atlas_input_audit",
            payload=build_repository_atlas_input_audit(
                data_root=data_root,
                docs_root=docs_root,
                report_root=report_root,
            ),
            render_markdown=render_repository_atlas_input_audit_markdown,
            audience="maintainer_diagnostic",
            information_role="atlas input audit",
            coexistence_rule="coexists with cross-domain evidence review and keeps map-facing inputs accountable by source family",
            docs_anchor="docs/report/maintenance/index.md",
            test_anchor="packages/bijux-pollenomics/tests/unit/test_repository_truth.py",
        ),
        _repository_output_spec(
            stem="repository_cross_domain_evidence_matrix",
            payload=build_repository_cross_domain_evidence_matrix(
                data_root=data_root,
                docs_root=docs_root,
                report_root=report_root,
            ),
            render_markdown=render_repository_cross_domain_evidence_matrix_markdown,
            audience="maintainer_diagnostic",
            information_role="cross-domain evidence matrix",
            coexistence_rule="coexists with source-family audits and explains how pollen, archaeology, boundary, fieldwork, and animal evidence differ in role",
            docs_anchor="docs/report/maintenance/index.md",
            test_anchor="packages/bijux-pollenomics/tests/unit/test_repository_truth.py",
        ),
        _repository_output_spec(
            stem="repository_docs_restoration_ledger",
            payload=build_repository_docs_restoration_ledger(
                data_root=data_root,
                docs_root=docs_root,
                report_root=report_root,
            ),
            render_markdown=render_repository_docs_restoration_ledger_markdown,
            audience="maintainer_diagnostic",
            information_role="docs restoration ledger",
            coexistence_rule="coexists with scope validation and records how handbook breadth was restored or merged",
            docs_anchor="docs/report/maintenance/index.md",
            test_anchor="packages/bijux-pollenomics/tests/unit/test_repository_truth.py",
        ),
        _repository_output_spec(
            stem="repository_docs_scope_validation",
            payload=build_repository_docs_scope_validation(
                data_root=data_root,
                docs_root=docs_root,
                report_root=report_root,
            ),
            render_markdown=render_repository_docs_scope_validation_markdown,
            audience="maintainer_diagnostic",
            information_role="docs breadth validation",
            coexistence_rule="coexists with docs recovery review and fails narrow rewrites before they harden",
            docs_anchor="docs/report/maintenance/index.md",
            test_anchor="packages/bijux-pollenomics/tests/unit/test_repository_truth.py",
        ),
        _repository_output_spec(
            stem="repository_docs_recovery_review",
            payload=build_repository_docs_recovery_review(
                data_root=data_root,
                docs_root=docs_root,
                report_root=report_root,
            ),
            render_markdown=render_repository_docs_recovery_review_markdown,
            audience="maintainer_diagnostic",
            information_role="docs recovery review",
            coexistence_rule="coexists with docs restoration and scope validation as the maintainer-facing summary of docs integrity",
            docs_anchor="docs/report/maintenance/index.md",
            test_anchor="packages/bijux-pollenomics/tests/unit/test_repository_truth.py",
        ),
        _repository_output_spec(
            stem="repository_source_acquisition_queue",
            payload=build_repository_source_acquisition_queue(
                data_root=data_root,
                docs_root=docs_root,
                report_root=report_root,
            ),
            render_markdown=render_repository_source_acquisition_queue_markdown,
            audience="maintainer_diagnostic",
            information_role="source acquisition queue",
            coexistence_rule="coexists with recovery and progress reviews as the explicit next-source pressure list",
            docs_anchor="docs/report/maintenance/index.md",
            test_anchor="packages/bijux-pollenomics/tests/unit/test_repository_truth.py",
        ),
        _repository_output_spec(
            stem="repository_governance_artifact_review",
            payload=build_repository_governance_artifact_review(
                data_root=data_root,
                report_root=report_root,
            ),
            render_markdown=render_repository_governance_artifact_review_markdown,
            audience="maintainer_diagnostic",
            information_role="governance artifact review",
            coexistence_rule="coexists with output sustainability review and records which legacy report surfaces should be kept, reframed, or retired",
            docs_anchor="docs/report/maintenance/index.md",
            test_anchor="packages/bijux-pollenomics/tests/unit/test_repository_truth.py",
        ),
        _repository_output_spec(
            stem="repository_claim_audit",
            payload=build_repository_claim_audit(
                data_root=data_root,
                docs_root=docs_root,
                report_root=report_root,
            ),
            render_markdown=render_repository_claim_audit_markdown,
            audience="maintainer_diagnostic",
            information_role="claim audit",
            coexistence_rule="coexists with release refusal and prevents broader public language from outrunning governed evidence",
            docs_anchor="docs/internal/pollenomics-dev/release-support.md",
            test_anchor="packages/bijux-pollenomics/tests/unit/test_repository_truth.py",
        ),
        _repository_output_spec(
            stem="repository_brutal_honesty_review",
            payload=build_repository_brutal_honesty_review(
                data_root=data_root,
                docs_root=docs_root,
                report_root=report_root,
            ),
            render_markdown=render_repository_brutal_honesty_review_markdown,
            audience="maintainer_diagnostic",
            information_role="brutal honesty review",
            coexistence_rule="coexists with the credibility dashboard and compresses the harsher qualitative release questions into one recurring review",
            docs_anchor="docs/internal/pollenomics-dev/release-support.md",
            test_anchor="packages/bijux-pollenomics/tests/unit/test_repository_truth.py",
        ),
        _repository_output_spec(
            stem="repository_final_release_refusal",
            payload=build_repository_final_release_refusal(
                data_root=data_root,
                docs_root=docs_root,
                report_root=report_root,
            ),
            render_markdown=render_repository_final_release_refusal_markdown,
            audience="maintainer_diagnostic",
            information_role="final release refusal",
            coexistence_rule="coexists with animal release gates and names the repository-wide reasons final release language is still refused",
            docs_anchor="docs/internal/pollenomics-dev/release-support.md",
            test_anchor="packages/bijux-pollenomics/tests/unit/test_repository_truth.py",
        ),
        _repository_output_spec(
            stem="repository_scientific_progress_audit",
            payload=build_repository_scientific_progress_audit(
                data_root=data_root,
                docs_root=docs_root,
                report_root=report_root,
            ),
            render_markdown=render_repository_scientific_progress_audit_markdown,
            audience="maintainer_diagnostic",
            information_role="scientific progress audit",
            coexistence_rule="coexists with recovery reviews and rejects raw artifact growth as a progress story",
            docs_anchor="docs/report/maintenance/index.md",
            test_anchor="packages/bijux-pollenomics/tests/unit/test_repository_truth.py",
        ),
        _repository_output_spec(
            stem="repository_sead_legibility_review",
            payload=build_repository_sead_legibility_review(data_root),
            render_markdown=render_repository_sead_legibility_review_markdown,
            audience="scientific_review_surface",
            information_role="SEAD legibility review",
            coexistence_rule="coexists with source-family and temporal reviews as the SEAD-specific honesty surface",
            docs_anchor="docs/02-bijux-pollenomics-data/sources/sead.md",
            test_anchor="packages/bijux-pollenomics/tests/unit/test_context_data.py",
        ),
    ]


def _repository_output_spec(
    *,
    stem: str,
    payload: dict[str, object],
    render_markdown: Callable[[dict[str, object]], str],
    audience: str,
    information_role: str,
    coexistence_rule: str,
    docs_anchor: str,
    test_anchor: str,
) -> dict[str, object]:
    return {
        "stem": stem,
        "payload": payload,
        "render_markdown": render_markdown,
        "audience": audience,
        "information_role": information_role,
        "root_location": "docs/report",
        "coexistence_rule": coexistence_rule,
        "docs_anchor": docs_anchor,
        "test_anchor": test_anchor,
    }


def _validate_repository_output_specs(specs: list[dict[str, object]]) -> None:
    seen: set[str] = set()
    required_fields = {
        "stem",
        "payload",
        "render_markdown",
        "audience",
        "information_role",
        "root_location",
        "coexistence_rule",
        "docs_anchor",
        "test_anchor",
    }
    for spec in specs:
        missing = required_fields.difference(spec)
        if missing:
            missing_labels = ", ".join(sorted(missing))
            raise ValueError(
                f"Repository truth output spec missing fields: {missing_labels}"
            )
        stem = str(spec["stem"])
        if stem in seen:
            raise ValueError(f"Duplicate repository truth output stem: {stem}")
        seen.add(stem)


def _build_repository_generated_output_policy(
    specs: list[dict[str, object]],
) -> dict[str, object]:
    rows = [
        {
            "stem": str(spec["stem"]),
            "json_path": f"docs/report/{spec['stem']}.json",
            "markdown_path": f"docs/report/{spec['stem']}.md",
            "audience": str(spec["audience"]),
            "information_role": str(spec["information_role"]),
            "root_location": str(spec["root_location"]),
            "coexistence_rule": str(spec["coexistence_rule"]),
            "docs_anchor": str(spec["docs_anchor"]),
            "test_anchor": str(spec["test_anchor"]),
        }
        for spec in specs
    ]
    rows.append(
        {
            "stem": "repository_generated_output_policy",
            "json_path": "docs/report/repository_generated_output_policy.json",
            "markdown_path": "docs/report/repository_generated_output_policy.md",
            "audience": "maintainer_diagnostic",
            "information_role": "generated-output publication policy",
            "root_location": "docs/report",
            "coexistence_rule": "coexists with the report portal and repository truth reviews as the rule that governs new root outputs",
            "docs_anchor": "docs/internal/pollenomics-dev/release-support.md",
            "test_anchor": "packages/bijux-pollenomics/tests/unit/test_repository_truth.py",
        }
    )
    return {
        "schema_version": "repository-generated-output-policy.v1",
        "rule": (
            "no generated root output may be published unless its audience, information role, root location, and coexistence rule are explicit in code, docs, and tests"
        ),
        "row_count": len(rows),
        "rows": rows,
    }


def _render_repository_generated_output_policy_markdown(
    payload: dict[str, object],
) -> str:
    rows = "\n".join(
        f"| `{row['stem']}` | `{row['audience']}` | {row['information_role']} | `{row['root_location']}` | {row['coexistence_rule']} | `{row['docs_anchor']}` | `{row['test_anchor']}` |"
        for row in payload["rows"]
    )
    return f"""# Repository generated output policy

This policy exists to stop `docs/report/` from turning back into a root-level
artifact spill. A new generated output is allowed only when its audience,
information role, root location, and coexistence logic are explicit in the code
that publishes it, in reader or maintainer documentation, and in tests that
will fail if the contract drifts.

- Rule: {payload["rule"]}
- Governed outputs: `{payload["row_count"]}`

## Governed Root Outputs

| Stem | Audience | Information role | Root location | Coexistence rule | Docs anchor | Test anchor |
| --- | --- | --- | --- | --- | --- | --- |
{rows}
"""
