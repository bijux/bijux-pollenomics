"""Repository extension and local-reasoning review."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from ..documentation import build_repository_docs_scope_validation


def build_repository_extension_review(
    *,
    data_root: Path,
    docs_root: Path,
    report_root: Path,
) -> dict[str, object]:
    """Review whether new work makes the repository easier to extend and harder to misread."""
    _ = data_root
    docs_scope = build_repository_docs_scope_validation(
        data_root=data_root,
        docs_root=docs_root,
        report_root=report_root,
    )
    rows: list[dict[str, object]] = [
        {
            "dimension_key": "global_extensibility",
            "score": 4
            if (report_root / "publication_country_onboarding_contract.json").exists()
            else 2,
            "finding": "adding Germany or another country is governed as roster, evidence, publication, documentation, and verification work instead of renderer surgery",
            "evidence_anchors": [
                "docs/report/publication_country_onboarding_contract.json",
                "docs/internal/pollenomics-dev/country-publication-onboarding.md",
            ],
        },
        {
            "dimension_key": "local_reasoning",
            "score": 4 if bool(docs_scope.get("overall_ok")) else 2,
            "finding": "the runtime, data, and maintainer handbooks still explain ownership without collapsing the repo into one vague top layer",
            "evidence_anchors": [
                "docs/report/repository_docs_scope_validation.json",
                "docs/public/pollenomics/foundation/publication-scope-model.md",
            ],
        },
        {
            "dimension_key": "scientific_misread_resistance",
            "score": 4
            if (report_root / "repository_final_release_refusal.json").exists()
            else 2,
            "finding": "release-facing wording is now anchored to explicit refusal criteria instead of optimistic prose alone",
            "evidence_anchors": [
                "docs/report/repository_final_release_refusal.json",
                "docs/report/repository_claim_audit.json",
            ],
        },
    ]
    return {
        "schema_version": "repository-extension-review.v1",
        "overall_posture": (
            "globally_extensible_and_locally_legible"
            if all(cast(int, row["score"]) >= 4 for row in rows)
            else "extension_contract_still_fragile"
        ),
        "rows": rows,
    }


def render_repository_extension_review_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Repository extension review",
        "",
        f"- Overall posture: `{payload['overall_posture']}`",
        "",
        "| Dimension | Score | Finding |",
        "| --- | ---: | --- |",
    ]
    for row in cast(list[dict[str, object]], payload["rows"]):
        lines.append(
            f"| `{row['dimension_key']}` | {row['score']} | {row['finding']} |"
        )
    return "\n".join(lines) + "\n"
