"""Repository product credibility, sustainability, and release posture."""

from __future__ import annotations

from pathlib import Path

from .documentation import build_repository_docs_scope_validation
from .integrity import build_repository_governance_artifact_review
from .metrics import (
    SCORE_MAX,
    _build_core_counts,
    _count_suffix_files,
    _count_tree_files,
    _load_json_or_default,
)

__all__ = [
    "build_repository_product_model",
    "render_repository_product_model_markdown",
    "build_repository_credibility_dashboard",
    "render_repository_credibility_dashboard_markdown",
    "build_repository_output_sustainability_review",
    "render_repository_output_sustainability_review_markdown",
    "build_repository_extension_review",
    "render_repository_extension_review_markdown",
    "build_repository_brutal_honesty_review",
    "render_repository_brutal_honesty_review_markdown",
    "build_repository_final_release_refusal",
    "render_repository_final_release_refusal_markdown",
]


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


def build_repository_product_model(
    *,
    data_root: Path,
    docs_root: Path,
    report_root: Path,
) -> dict[str, object]:
    """Describe the durable product shape from world scale to country scale."""
    counts = _build_core_counts(data_root, docs_root, report_root)
    return {
        "schema_version": "repository-product-model.v1",
        "product_name": "bijux-pollenomics",
        "governing_model": "world_parent_with_filtered_regional_and_country_derivatives",
        "mission": (
            "collect world-scale tracked evidence families once, keep Europe-plus and Nordic as governed filtered specializations, and publish country bundles as narrower views of the same accountable repository state"
        ),
        "scope_lineage": [
            {
                "scope_key": "world",
                "role": "governing_parent_surface",
                "owned_paths": [
                    "data/",
                    "docs/report/world/",
                ],
                "meaning": "the broadest public surface and the parent evidence view for all narrower scopes",
            },
            {
                "scope_key": "europe_plus",
                "role": "regional_filter",
                "owned_paths": [
                    "docs/report/regions/europe-plus/",
                ],
                "meaning": "the stable European bridge between world coverage and Nordic specialization",
            },
            {
                "scope_key": "nordic",
                "role": "dense_regional_specialization",
                "owned_paths": [
                    "docs/report/regions/nordic/",
                    "docs/public/nordic-atlas/",
                ],
                "meaning": "the narrow regional surface where contextual overlays become intentionally denser",
            },
            {
                "scope_key": "country",
                "role": "derived_country_bundle",
                "owned_paths": [
                    "docs/report/countries/<country-slug>/",
                ],
                "meaning": "reader-facing country bundles derived from the same upstream evidence and scope rules",
            },
        ],
        "shared_runtime_stages": [
            "collect source-family data into tracked raw trees",
            "normalize source-family evidence into reviewable files under data/",
            "review recovery depth, chronology meaning, and publication caveats",
            "publish world, regional, and country outputs from one governed state",
        ],
        "drift_rules": [
            "world is the governing parent surface; narrower scopes may filter it but may not fork separate truth rules",
            "Europe-plus exists as a stable region definition rather than as an ad hoc pre-Nordic convenience layer",
            "Nordic specialization may increase contextual density, but it may not invent a second publication model",
            "country bundles answer geography-first reader questions and must remain derivations of one broader evidence state",
        ],
        "current_state_counts": {
            "published_country_bundle_count": counts["published_country_bundle_count"],
            "published_world_animal_points": counts["published_atlas_point_count"],
            "source_explainer_count": counts["source_explainer_count"],
        },
        "evidence_anchors": [
            "docs/report/publication_geography_registry.json",
            "docs/report/publication_geography_subset_validation.json",
            "docs/report/publication_country_onboarding_contract.json",
            "docs/public/pollenomics/foundation/publication-scope-model.md",
        ],
    }


def render_repository_product_model_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Repository product model",
        "",
        f"- Product: `{payload['product_name']}`",
        f"- Governing model: `{payload['governing_model']}`",
        f"- Mission: {payload['mission']}",
        "",
        "## Scope Lineage",
        "",
        "| Scope | Role | Owned paths | Meaning |",
        "| --- | --- | --- | --- |",
    ]
    for row in payload["scope_lineage"]:
        lines.append(
            f"| `{row['scope_key']}` | `{row['role']}` | "
            f"{', '.join(f'`{path}`' for path in row['owned_paths'])} | {row['meaning']} |"
        )
    lines.extend(
        [
            "",
            "## Shared Runtime Stages",
            "",
        ]
    )
    for row in payload["shared_runtime_stages"]:
        lines.append(f"- {row}")
    lines.extend(
        [
            "",
            "## Drift Rules",
            "",
        ]
    )
    for row in payload["drift_rules"]:
        lines.append(f"- {row}")
    return "\n".join(lines) + "\n"


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
    report_quality_counts = dict(report_quality.get("quality_posture_counts", {}))
    sample_review = _load_json_or_default(
        report_root / "animal_sample_database_review.json",
        {},
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
            [
                "README.md",
                "docs/report/index.md",
            ],
        ),
        _credibility_row(
            "source_family_coverage",
            "Source-family coverage",
            4 if int(counts["source_explainer_count"]) >= 15 else 3,
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
            and int(report_quality_counts.get("link_farm_risk", 0)) == 0
            else 2,
            "handbook breadth holds and the report tree no longer carries link-farm pages at the root",
            [
                "docs/report/report_narrative_quality_review.json",
                "docs/report/repository_docs_scope_validation.json",
            ],
        ),
    ]
    average_score = round(
        sum(int(row["score"]) for row in rows) / len(rows),
        2,
    )
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
    for row in payload["rows"]:
        lines.append(f"| {row['display_name']} | {row['score']} | {row['finding']} |")
    return "\n".join(lines) + "\n"


def build_repository_output_sustainability_review(
    *,
    data_root: Path,
    docs_root: Path,
    report_root: Path,
) -> dict[str, object]:
    """Review whether the balance of code, tracked data, and public outputs stays maintainable."""
    governance_review = build_repository_governance_artifact_review(
        data_root=data_root,
        report_root=report_root,
    )
    rows = [
        {
            "surface_key": "report_root_navigation",
            "current_posture": "reader_portal_governed",
            "action": "keep",
            "finding": "the report root now routes readers through portal families instead of leaving them in a bare artifact spill",
            "evidence_anchor": "docs/report/report_surface_registry.json",
        },
        {
            "surface_key": "generated_root_diagnostics",
            "current_posture": "policy_gated",
            "action": "keep_only_with_explicit_role",
            "finding": "new root outputs are now governed by an explicit publication policy instead of being justified only by emitter convenience",
            "evidence_anchor": "docs/report/repository_generated_output_policy.json",
        },
        {
            "surface_key": "legacy_diagnostic_overlap",
            "current_posture": "one_retirement_still_named",
            "action": "retire_or_reframe",
            "finding": (
                f"the governance review still names {governance_review['summary']['retire']} root artifact for retirement or reframing"
            ),
            "evidence_anchor": "docs/report/repository_governance_artifact_review.json",
        },
        {
            "surface_key": "world_to_country_publication_balance",
            "current_posture": "derived_scope_family",
            "action": "keep",
            "finding": "world, regional, and country outputs now share one scope lineage instead of multiplying separate product trees",
            "evidence_anchor": "docs/report/publication_geography_registry.json",
        },
    ]
    return {
        "schema_version": "repository-output-sustainability-review.v1",
        "balance_counts": {
            "runtime_python_file_count": _count_suffix_files(
                docs_root.parent / "packages" / "bijux-pollenomics" / "src",
                ".py",
            ),
            "tracked_data_file_count": _count_tree_files(data_root),
            "report_file_count": _count_tree_files(report_root),
            "maintainer_root_review_file_count": sum(
                1 for path in report_root.glob("repository_*.json")
            ),
        },
        "rows": rows,
    }


def render_repository_output_sustainability_review_markdown(
    payload: dict[str, object],
) -> str:
    lines = [
        "# Repository output sustainability review",
        "",
        "| Surface | Current posture | Action | Finding |",
        "| --- | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| `{row['surface_key']}` | `{row['current_posture']}` | `{row['action']}` | {row['finding']} |"
        )
    lines.extend(
        [
            "",
            "## Balance Counts",
            "",
            f"- Runtime Python files: `{payload['balance_counts']['runtime_python_file_count']}`",
            f"- Tracked data files: `{payload['balance_counts']['tracked_data_file_count']}`",
            f"- Report files: `{payload['balance_counts']['report_file_count']}`",
            f"- Maintainer root review files: `{payload['balance_counts']['maintainer_root_review_file_count']}`",
        ]
    )
    return "\n".join(lines) + "\n"


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
    rows = [
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
            if all(int(row["score"]) >= 4 for row in rows)
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
    for row in payload["rows"]:
        lines.append(
            f"| `{row['dimension_key']}` | {row['score']} | {row['finding']} |"
        )
    return "\n".join(lines) + "\n"


def build_repository_brutal_honesty_review(
    *,
    data_root: Path,
    docs_root: Path,
    report_root: Path,
) -> dict[str, object]:
    """Ask the harsh release questions instead of celebrating machinery count."""
    credibility = build_repository_credibility_dashboard(
        data_root=data_root,
        docs_root=docs_root,
        report_root=report_root,
    )
    sustainability = build_repository_output_sustainability_review(
        data_root=data_root,
        docs_root=docs_root,
        report_root=report_root,
    )
    extension = build_repository_extension_review(
        data_root=data_root,
        docs_root=docs_root,
        report_root=report_root,
    )
    sample_review = _load_json_or_default(
        report_root / "animal_sample_database_review.json",
        {},
    )
    rows = [
        {
            "question_key": "more_elegant",
            "score": 4,
            "answer": "yes, because the repository now explains one product model and one generated-output policy instead of relying on accidental sprawl",
            "evidence_anchors": [
                "docs/report/repository_product_model.json",
                "docs/report/repository_generated_output_policy.json",
                "docs/report/repository_output_sustainability_review.json",
            ],
        },
        {
            "question_key": "more_trustworthy",
            "score": 3,
            "answer": "partly: the honesty surfaces are stronger, but animal extraction depth still materially lags the broader product story",
            "evidence_anchors": [
                "docs/report/repository_credibility_dashboard.json",
                "docs/report/animal_sample_database_review.json",
            ],
        },
        {
            "question_key": "more_extensible",
            "score": int(extension["rows"][0]["score"]),
            "answer": "yes, because world, region, and country publication are now explicitly contract-driven",
            "evidence_anchors": [
                "docs/report/publication_country_onboarding_contract.json",
                "docs/report/repository_extension_review.json",
            ],
        },
        {
            "question_key": "more_readable",
            "score": 4
            if credibility["overall_posture"] == "credible_but_still_recovery_bound"
            else 3,
            "answer": "yes, because the public mission and report portal now teach the product shape instead of assuming the reader already knows the file tree",
            "evidence_anchors": [
                "README.md",
                "docs/report/index.md",
                "docs/report/report_narrative_quality_review.json",
            ],
        },
        {
            "question_key": "only_more_impressive_looking",
            "score": 1
            if bool(sample_review.get("region_agnostic_contract_ready"))
            else 2,
            "answer": "no, but only because the repo now carries explicit refusal and credibility surfaces that stop the machinery from pretending it equals final readiness",
            "evidence_anchors": [
                "docs/report/repository_final_release_refusal.json",
                "docs/report/repository_output_sustainability_review.json",
            ],
        },
    ]
    average_score = round(sum(int(row["score"]) for row in rows) / len(rows), 2)
    return {
        "schema_version": "repository-brutal-honesty-review.v1",
        "overall_posture": (
            "harder_to_fool_yourself"
            if average_score >= 3.0
            else "still_too_easy_to_hide_behind_machinery"
        ),
        "average_score": average_score,
        "rows": rows,
        "governance_note": sustainability["rows"][1]["finding"],
    }


def render_repository_brutal_honesty_review_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Repository brutal honesty review",
        "",
        f"- Overall posture: `{payload['overall_posture']}`",
        f"- Average score: `{payload['average_score']}` / `{SCORE_MAX}`",
        f"- Governance note: {payload['governance_note']}",
        "",
        "| Question | Score | Answer |",
        "| --- | ---: | --- |",
    ]
    for row in payload["rows"]:
        lines.append(f"| `{row['question_key']}` | {row['score']} | {row['answer']} |")
    return "\n".join(lines) + "\n"


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
        report_root / "animal_sample_database_review.json",
        {},
    )
    sead_review = _load_json_or_default(
        report_root / "repository_sead_legibility_review.json",
        {},
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
            not in dict(sead_review.get("comparability_posture_counts", {})),
            "SEAD still carries unresolved comparability posture and therefore blocks final release language",
            [
                "docs/report/repository_sead_legibility_review.json",
                "docs/public/pollenomics-data/sources/sead.md",
            ],
        ),
        _release_refusal_row(
            "docs_clarity",
            bool(docs_scope.get("overall_ok"))
            and int(
                dict(report_quality.get("quality_posture_counts", {})).get(
                    "link_farm_risk", 0
                )
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
    for row in payload["rows"]:
        lines.append(
            f"| `{row['dimension_key']}` | `{str(row['ready_for_final_release_language']).lower()}` | {row['finding']} |"
        )
    return "\n".join(lines) + "\n"
