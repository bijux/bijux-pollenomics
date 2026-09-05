"""Durable world-to-country repository product model."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from ..metrics import _build_core_counts


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
                "owned_paths": ["data/", "docs/report/world/"],
                "meaning": "the broadest public surface and the parent evidence view for all narrower scopes",
            },
            {
                "scope_key": "europe_plus",
                "role": "regional_filter",
                "owned_paths": ["docs/report/regions/europe-plus/"],
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
                "owned_paths": ["docs/report/countries/<country-slug>/"],
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
    scope_lineage = cast(list[dict[str, object]], payload["scope_lineage"])
    for scope_row in scope_lineage:
        owned_paths = cast(list[str], scope_row["owned_paths"])
        lines.append(
            f"| `{scope_row['scope_key']}` | `{scope_row['role']}` | "
            f"{', '.join(f'`{path}`' for path in owned_paths)} | {scope_row['meaning']} |"
        )
    lines.extend(["", "## Shared Runtime Stages", ""])
    for runtime_stage in cast(list[str], payload["shared_runtime_stages"]):
        lines.append(f"- {runtime_stage}")
    lines.extend(["", "## Drift Rules", ""])
    for drift_rule in cast(list[str], payload["drift_rules"]):
        lines.append(f"- {drift_rule}")
    return "\n".join(lines) + "\n"
