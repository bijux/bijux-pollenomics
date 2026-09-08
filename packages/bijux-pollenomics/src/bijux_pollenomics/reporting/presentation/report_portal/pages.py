from __future__ import annotations

from collections import Counter
from pathlib import Path


def _render_portal_pages(
    output_root: Path,
    rows: list[dict[str, object]],
) -> dict[str, str]:
    family_rows = {
        family: [row for row in rows if row["family"] == family]
        for family in ("maps", "scopes", "reviews", "caveats", "maintenance")
    }
    quality_counts = Counter(str(row["audience_label"]) for row in rows)
    return {
        "index.md": _render_report_portal_index(rows, family_rows, quality_counts),
        "how-to-read.md": _render_report_how_to_read(),
        "maps/index.md": _render_maps_portal_page(family_rows["maps"]),
        "scopes/index.md": _render_scopes_portal_page(family_rows["scopes"]),
        "reviews/index.md": _render_reviews_portal_page(family_rows["reviews"]),
        "caveats/index.md": _render_caveats_portal_page(family_rows["caveats"]),
        "maintenance/index.md": _render_maintenance_portal_page(
            family_rows["maintenance"]
        ),
    }


def _render_report_portal_index(
    rows: list[dict[str, object]],
    family_rows: dict[str, list[dict[str, object]]],
    audience_counts: Counter[str],
) -> str:
    family_lines = "\n".join(
        f"| {label} | `{len(family_rows[key])}` | {summary} |"
        for key, label, summary in (
            (
                "maps",
                "Map surfaces",
                "interactive surfaces, traceability, contracts, and atlas-facing evidence rows",
            ),
            (
                "scopes",
                "Scope-filtered outputs",
                "world, regional, and country bundles that answer geography-first reading questions",
            ),
            (
                "reviews",
                "Evidence reviews",
                "animal evidence, chronology, recovery, and cross-family review surfaces",
            ),
            (
                "caveats",
                "Scientific caveats",
                "blocked, thin, overclaim-sensitive, and honesty-oriented publication surfaces",
            ),
            (
                "maintenance",
                "Maintainer truth surfaces",
                "repository truth, docs integrity, source audits, and geography governance surfaces",
            ),
        )
    )
    audience_lines = "\n".join(
        f"- {label}: `{count}`" for label, count in sorted(audience_counts.items())
    )
    return f"""---
title: Report Portal
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-reporting
last_reviewed: 2026-05-09
---

# Report Portal

`docs/report/` is the repository's public publication tree. It contains maps,
country and regional bundles, scientific review surfaces, and maintainer truth
surfaces. The tree is now organized around reader questions instead of the
internal functions that emitted each file.

## Start Here

- [how to read the report tree](./how-to-read.md) if you are new to the repository
- [map surfaces](./maps/index.md) if you want the interactive world, Europe-plus, or Nordic view
- [scope-filtered outputs](./scopes/index.md) if your question is world, region, or country specific
- [evidence reviews](./reviews/index.md) if you want chronology, intake, sample-database, or point-support reviews
- [scientific caveats](./caveats/index.md) if you want honesty, exclusion, or release-boundary checks
- [maintainer truth surfaces](./maintenance/index.md) if you need repository integrity, docs integrity, or governance surfaces

## What This Tree Contains

| Family | Surface count | Reader value |
| --- | ---: | --- |
{family_lines}

## Geographic Scopes

- [world](./world/README.md) is the parent publication surface and the broadest public map
- [Europe-plus](./regions/europe-plus/README.md) is the regional bridge between world and Nordic
- [Nordic](./regions/nordic/README.md) is the detail surface where context overlays become intentionally dense
- [countries](./countries/sweden/README.md) are the narrowest public bundles for direct country-filter reading

## Caution Levels

Use the tree in this order: reader portal first, scope bundle second, evidence review third, caveat surface fourth. A map or country bundle can be useful on its own, but the scientific meaning always depends on the review and caveat surfaces next to it.

## Audience Mix

{audience_lines}
"""


def _render_report_how_to_read() -> str:
    return """---
title: How To Read Reports
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-reporting
last_reviewed: 2026-05-09
---

# How To Read Reports

The report tree is easiest to read if you begin with the question you actually
have instead of opening random JSON or Markdown files from the root.

## If Your Question Is Geographic

1. Open [scope-filtered outputs](./scopes/index.md).
2. Start with [world](./world/README.md) if you need the parent surface.
3. Drop to [Europe-plus](./regions/europe-plus/README.md), [Nordic](./regions/nordic/README.md), or one country bundle only after you know why the narrower filter exists.

## If Your Question Is Map Interpretation

1. Open [map surfaces](./maps/index.md).
2. Read the scope README before the HTML map itself.
3. Use map publication contracts and point traceability surfaces when a visible layer needs justification.

## If Your Question Is Scientific Trust

1. Open [evidence reviews](./reviews/index.md).
2. Check [scientific caveats](./caveats/index.md) before repeating a strong claim.
3. Use [repository_sead_legibility_review.md](./repository_sead_legibility_review.md) or [animal_sample_database_review.md](./animal_sample_database_review.md) when source-family strength matters more than map appearance.

## If Your Question Is Repository Integrity

1. Open [maintainer truth surfaces](./maintenance/index.md).
2. Start with [repository_truth_posture.md](./repository_truth_posture.md).
3. Use docs, claim, and source-family audits when you need to understand why a public statement is allowed or blocked.
"""


def _render_maps_portal_page(rows: list[dict[str, object]]) -> str:
    map_count = sum(1 for row in rows if str(row["format"]) == "html")
    review_count = sum(
        1 for row in rows if "traceability" in str(row["repository_path"])
    )
    return f"""---
title: Map Surfaces
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-reporting
last_reviewed: 2026-05-09
---

# Map Surfaces

This family covers the interactive world, Europe-plus, and Nordic surfaces plus
the contracts and traceability files that explain what each map is allowed to
show.

## Start Here

- [world surface](../world/README.md)
- [Europe-plus surface](../regions/europe-plus/README.md)
- [Nordic surface](../regions/nordic/README.md)

## What This Family Includes

- interactive map HTML files for governed scopes
- map publication contracts that explain layer roles, bounds, and caveats
- point traceability surfaces that connect visible points to evidence
- atlas evidence and scientific review surfaces that summarize what the map can and cannot claim

## Current Counts

- interactive maps: `{map_count}`
- traceability surfaces: `{review_count}`
- total map-family artifacts: `{len(rows)}`
"""


def _render_scopes_portal_page(rows: list[dict[str, object]]) -> str:
    country_rows = [row for row in rows if "/countries/" in str(row["repository_path"])]
    return f"""---
title: Scope-Filtered Outputs
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-reporting
last_reviewed: 2026-05-09
---

# Scope-Filtered Outputs

These surfaces answer geography-first questions. They are filtered views of one
governed publication system, not separate products with unrelated truth rules.

## Start Here

- [world parent surface](../world/README.md)
- [Europe-plus regional surface](../regions/europe-plus/README.md)
- [Nordic regional surface](../regions/nordic/README.md)
- [country bundles](../countries/sweden/README.md)

## Reading Order

- start at world when you need the broadest publication posture
- use Europe-plus when Nordic needs to be read inside a wider European frame
- use Nordic when contextual overlays matter
- use country bundles when the question is one country filter, one sample table, or one local warning set

## Current Counts

- total scope artifacts: `{len(rows)}`
- country-family artifacts: `{len(country_rows)}`
"""


def _render_reviews_portal_page(rows: list[dict[str, object]]) -> str:
    return f"""---
title: Evidence Reviews
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-reporting
last_reviewed: 2026-05-09
---

# Evidence Reviews

Evidence reviews explain whether the repository's visible outputs are actually
supported by sample, chronology, coordinate, intake, and cross-family evidence.

## Start Here

- [animal sample database review](../animal_sample_database_review.md)
- [animal point evidence review](../animal_point_evidence_review.md)
- [animal intake recovery review](../animal_intake_recovery_review.md)
- [animal temporal comparison review](../animal_temporal_comparison_review.md)
- [SEAD legibility review](../repository_sead_legibility_review.md)

## What This Family Is For

- deciding whether a visible point is well-supported
- checking whether chronology comparisons are actually comparable
- seeing where intake remains thin or incomplete
- identifying source-family strength before making a public claim

## Current Count

- review artifacts: `{len(rows)}`
"""


def _render_caveats_portal_page(rows: list[dict[str, object]]) -> str:
    return f"""---
title: Scientific Caveats
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-reporting
last_reviewed: 2026-05-09
---

# Scientific Caveats

This family is where the repository says no, not yet, or only under stated
limits. These are the surfaces to read before repeating a strong claim from a
map or country bundle.

## Start Here

- [animal output honesty](../animal_output_honesty.md)
- [animal atlas exclusion report](../animal_atlas_exclusion_report.md)
- [animal scientific caveat ledger](../animal_scientific_caveat_ledger.md)
- [animal publication release gate](../animal_publication_release_gate.md)
- [SEAD legibility review](../repository_sead_legibility_review.md)

## What This Family Prevents

- treating blocked or thin rows as published support
- confusing visible points with equally strong evidence
- collapsing access-constrained contextual layers into fixed truth
- claiming release readiness when the governed gates still disagree

## Current Count

- caveat artifacts: `{len(rows)}`
"""


def _render_maintenance_portal_page(rows: list[dict[str, object]]) -> str:
    return f"""---
title: Maintainer Truth Surfaces
audience: maintainer
type: explanation
status: canonical
owner: bijux-pollenomics-reporting
last_reviewed: 2026-05-09
---

# Maintainer Truth Surfaces

These surfaces are not where a newcomer should start, but they are where the
repository states whether its public story is coherent, overclaimed, or still
structurally weak.

## Start Here

- [repository truth posture](../repository_truth_posture.md)
- [repository product model](../repository_product_model.md)
- [repository credibility dashboard](../repository_credibility_dashboard.md)
- [repository recovery review](../repository_recovery_review.md)
- [repository claim audit](../repository_claim_audit.md)
- [repository final release refusal](../repository_final_release_refusal.md)
- [repository docs recovery review](../repository_docs_recovery_review.md)
- [repository source family matrix](../repository_source_family_matrix.md)
- [repository generated output policy](../repository_generated_output_policy.md)
- [publication geography registry](../publication_geography_registry.md)

## What This Family Covers

- repository-wide truth and overclaim checks
- docs integrity and docs breadth recovery
- source acquisition, source explainer, and atlas-input audits
- geography governance, country onboarding, and generated-output policy contracts

## Current Count

- maintainer artifacts: `{len(rows)}`
"""
