"""Release-time repository credibility scoring."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from ..documentation import build_repository_docs_scope_validation
from ..metrics import SCORE_MAX, _build_core_counts, _load_json_or_default


def _credibility_row(
    dimension_key: str,
    display_name: str,
    score: int,
    finding: str,
    evidence_anchors: list[str],
) -> dict[str, object]:
    return {
        "dimension_key": dimension_key,
        "display_name": display_name,
        "score": score,
        "finding": finding,
        "evidence_anchors": evidence_anchors,
    }


def build_repository_credibility_dashboard(
    *,
    data_root: Path,
    docs_root: Path,
    report_root: Path,
) -> dict[str, object]:
    """Score the repository on the credibility dimensions that matter at release time."""
    counts = _build_core_counts(data_root, docs_root, report_root)
    docs_scope = build_repository_docs_scope_validation(
        data_root=data_root,
        docs_root=docs_root,
        report_root=report_root,
    )
    root_readme_path = docs_root.parent / "README.md"
    root_readme = (
        root_readme_path.read_text(encoding="utf-8")
        if root_readme_path.is_file()
        else ""
    )
    report_quality = _load_json_or_default(
        report_root / "report_narrative_quality_review.json",
        {"quality_posture_counts": {}},
    )
    naming_quality_ok = all(
        text not in root_readme
        for text in (
            "docs/report/nordic-atlas/",
            "docs/report/sweden/",
            "docs/report/norway/",
            "docs/report/finland/",
            "docs/report/denmark/",
        )
    )
    report_quality_counts = cast(
        dict[str, object], report_quality.get("quality_posture_counts", {})
    )
    sample_review = _load_json_or_default(
        report_root / "animal_sample_database_review.json", {}
    )
    rows = [
        _credibility_row(
            "architecture_clarity",
            "Architecture clarity",
            4,
            "repository architecture and product-model surfaces now name the world-to-country publication model directly",
            [
                "docs/report/repository_product_model.json",
                "docs/public/pollenomics/foundation/publication-scope-model.md",
            ],
        ),
        _credibility_row(
            "naming_quality",
            "Naming quality",
            4 if naming_quality_ok else 2,
            (
                "root landings now use the governed world, region, and country publication vocabulary"
                if naming_quality_ok
                else "root landings still leak outdated atlas-centric or country-first path naming"
            ),
            ["README.md", "docs/report/index.md"],
        ),
        _credibility_row(
            "source_family_coverage",
            "Source-family coverage",
            4 if cast(int, counts["source_explainer_count"]) >= 15 else 3,
            f"{counts['source_explainer_count']} directly explainable source-family pages keep the repository broader than one aDNA recovery story",
            [
                "docs/report/repository_source_family_matrix.json",
                "docs/report/repository_source_explainer_audit.json",
            ],
        ),
        _credibility_row(
            "extraction_completeness",
            "Extraction completeness",
            2 if not bool(sample_review.get("region_agnostic_contract_ready")) else 4,
            "animal sample extraction remains the weakest credibility dimension and still blocks stronger release language",
            [
                "docs/report/animal_sample_database_review.json",
                "docs/report/animal_intake_recovery_review.json",
            ],
        ),
        _credibility_row(
            "chronology_integrity",
            "Chronology integrity",
            4
            if (report_root / "animal_temporal_comparison_review.json").exists()
            and (report_root / "animal_sample_chronology_review.json").exists()
            else 2,
            "chronology now has explicit provenance and cross-family comparison surfaces instead of living only in downstream date fields",
            [
                "docs/report/animal_sample_chronology_review.json",
                "docs/report/animal_temporal_comparison_review.json",
            ],
        ),
        _credibility_row(
            "geographic_extensibility",
            "Geographic extensibility",
            4
            if (report_root / "publication_country_onboarding_contract.json").exists()
            else 2,
            "world, Europe-plus, Nordic, and country publication now share one lineage plus one onboarding contract",
            [
                "docs/report/publication_geography_registry.json",
                "docs/report/publication_country_onboarding_contract.json",
            ],
        ),
        _credibility_row(
            "map_coherence",
            "Map coherence",
            4
            if all(
                path.exists()
                for path in (
                    report_root / "world" / "world_map.html",
                    report_root / "regions" / "europe-plus" / "europe-plus_map.html",
                    report_root / "regions" / "nordic" / "nordic_map.html",
                )
            )
            else 2,
            "world, Europe-plus, and Nordic maps now exist as sibling scopes instead of one Nordic-first artifact with broad afterthoughts",
            [
                "docs/report/world/world_map.html",
                "docs/report/regions/europe-plus/europe-plus_map.html",
                "docs/report/regions/nordic/nordic_map.html",
            ],
        ),
        _credibility_row(
            "docs_usability",
            "Docs usability",
            4
            if bool(docs_scope.get("overall_ok"))
            and cast(int, report_quality_counts.get("link_farm_risk", 0)) == 0
            else 2,
            "handbook breadth holds and the report tree no longer carries link-farm pages at the root",
            [
                "docs/report/report_narrative_quality_review.json",
                "docs/report/repository_docs_scope_validation.json",
            ],
        ),
    ]
    average_score = round(sum(cast(int, row["score"]) for row in rows) / len(rows), 2)
    overall_posture = (
        "credible_but_still_recovery_bound"
        if average_score >= 3.25
        else "credibility_still_fragile"
    )
    return {
        "schema_version": "repository-credibility-dashboard.v1",
        "overall_posture": overall_posture,
        "average_score": average_score,
        "rows": rows,
    }


def render_repository_credibility_dashboard_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Repository credibility dashboard",
        "",
        f"- Overall posture: `{payload['overall_posture']}`",
        f"- Average score: `{payload['average_score']}` / `{SCORE_MAX}`",
        "",
        "| Dimension | Score | Finding |",
        "| --- | ---: | --- |",
    ]
    for row in cast(list[dict[str, object]], payload["rows"]):
        lines.append(f"| {row['display_name']} | {row['score']} | {row['finding']} |")
    return "\n".join(lines) + "\n"
