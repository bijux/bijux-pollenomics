"""Final-release language refusal criteria."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from ..documentation import build_repository_docs_scope_validation
from ..metrics import _load_json_or_default


def _release_refusal_row(
    dimension_key: str,
    ready_for_final_release_language: bool,
    finding: str,
    evidence_anchors: list[str],
) -> dict[str, object]:
    return {
        "dimension_key": dimension_key,
        "ready_for_final_release_language": ready_for_final_release_language,
        "finding": finding,
        "evidence_anchors": evidence_anchors,
    }


def build_repository_final_release_refusal(
    *,
    data_root: Path,
    docs_root: Path,
    report_root: Path,
) -> dict[str, object]:
    """Refuse final release language until the critical evidence surfaces are strong enough."""
    _ = data_root
    docs_scope = build_repository_docs_scope_validation(
        data_root=data_root,
        docs_root=docs_root,
        report_root=report_root,
    )
    sample_review = _load_json_or_default(
        report_root / "animal_sample_database_review.json", {}
    )
    sead_review = _load_json_or_default(
        report_root / "repository_sead_legibility_review.json", {}
    )
    report_quality = _load_json_or_default(
        report_root / "report_narrative_quality_review.json",
        {"quality_posture_counts": {}},
    )
    rows = [
        _release_refusal_row(
            "architecture",
            True,
            "the repository now has explicit architecture and product-model surfaces",
            [
                "docs/report/repository_product_model.json",
                "docs/public/pollenomics/foundation/publication-scope-model.md",
            ],
        ),
        _release_refusal_row(
            "data_recovery",
            bool(sample_review.get("region_agnostic_contract_ready")),
            "animal data recovery is still not region-agnostic enough for final release wording",
            [
                "docs/report/animal_sample_database_review.json",
                "docs/report/animal_intake_recovery_review.json",
            ],
        ),
        _release_refusal_row(
            "map_scope",
            all(
                path.exists()
                for path in (
                    report_root / "world" / "world_map.html",
                    report_root / "regions" / "europe-plus" / "europe-plus_map.html",
                    report_root / "regions" / "nordic" / "nordic_map.html",
                )
            ),
            "world, Europe-plus, and Nordic scope surfaces are present and governed as one lineage",
            [
                "docs/report/publication_geography_registry.json",
                "docs/report/publication_geography_subset_validation.json",
            ],
        ),
        _release_refusal_row(
            "temporal_semantics",
            (report_root / "animal_temporal_comparison_review.json").exists(),
            "temporal semantics are governed and published across sample and contextual families",
            [
                "docs/report/animal_temporal_comparison_review.json",
                "docs/report/animal_sample_chronology_review.json",
            ],
        ),
        _release_refusal_row(
            "sead_treatment",
            bool(sead_review.get("comparability_posture_counts"))
            and "unresolved"
            not in cast(
                dict[str, object], sead_review.get("comparability_posture_counts", {})
            ),
            "SEAD still carries unresolved comparability posture and therefore blocks final release language",
            [
                "docs/report/repository_sead_legibility_review.json",
                "docs/public/pollenomics-data/sources/sead.md",
            ],
        ),
        _release_refusal_row(
            "docs_clarity",
            bool(docs_scope.get("overall_ok"))
            and cast(
                int,
                cast(
                    dict[str, object],
                    report_quality.get("quality_posture_counts", {}),
                ).get("link_farm_risk", 0),
            )
            == 0,
            "docs breadth holds and the report tree now routes readers through explanation-first pages",
            [
                "docs/report/repository_docs_scope_validation.json",
                "docs/report/report_narrative_quality_review.json",
            ],
        ),
        _release_refusal_row(
            "geographic_extensibility",
            (report_root / "publication_country_onboarding_contract.json").exists(),
            "country publication onboarding is a governed contract instead of tribal knowledge",
            [
                "docs/report/publication_country_onboarding_contract.json",
                "docs/internal/pollenomics-dev/country-publication-onboarding.md",
            ],
        ),
    ]
    blocking_dimensions = [
        row["dimension_key"]
        for row in rows
        if not bool(row["ready_for_final_release_language"])
    ]
    return {
        "schema_version": "repository-final-release-refusal.v1",
        "final_release_language_allowed": False,
        "overall_posture": "final_release_language_refused",
        "blocking_dimension_count": len(blocking_dimensions),
        "blocking_dimensions": blocking_dimensions,
        "rows": rows,
    }


def render_repository_final_release_refusal_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Repository final release refusal",
        "",
        f"- Overall posture: `{payload['overall_posture']}`",
        f"- Final release language allowed: `{str(payload['final_release_language_allowed']).lower()}`",
        f"- Blocking dimensions: `{payload['blocking_dimension_count']}`",
        "",
        "| Dimension | Ready | Finding |",
        "| --- | --- | --- |",
    ]
    for row in cast(list[dict[str, object]], payload["rows"]):
        lines.append(
            f"| `{row['dimension_key']}` | `{str(row['ready_for_final_release_language']).lower()}` | {row['finding']} |"
        )
    return "\n".join(lines) + "\n"
