from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

from .text import escape_pipes

__all__ = ["publish_report_portal"]

_PORTAL_FILES = {
    "index.md",
    "how-to-read.md",
    "maps/index.md",
    "scopes/index.md",
    "reviews/index.md",
    "caveats/index.md",
    "maintenance/index.md",
    "report_surface_registry.json",
    "report_surface_registry.md",
    "report_narrative_quality_review.json",
    "report_narrative_quality_review.md",
}

_FAMILY_LABELS = {
    "maps": "Map surfaces",
    "scopes": "Scope-filtered outputs",
    "reviews": "Evidence reviews",
    "caveats": "Scientific caveats",
    "maintenance": "Maintainer truth surfaces",
    "portal": "Portal guidance",
}

_AUDIENCE_LABELS = {
    "public_reading_surface": "Public reading surface",
    "scientific_review_surface": "Scientific review surface",
    "maintainer_diagnostic": "Maintainer diagnostic",
}


def publish_report_portal(output_root: Path) -> dict[str, str]:
    """Publish a human-facing portal and classification registry for docs/report."""
    output_root = Path(output_root)
    existing_rows = _build_existing_surface_rows(output_root)
    portal_pages = _render_portal_pages(output_root, existing_rows)
    portal_rows = _build_portal_rows(output_root, portal_pages)
    all_rows = [*existing_rows, *portal_rows]

    registry_payload = _build_report_surface_registry(all_rows)
    quality_payload = _build_report_narrative_quality_review(
        output_root=output_root,
        existing_rows=existing_rows,
        portal_pages=portal_pages,
    )

    for relative_path, content in portal_pages.items():
        path = output_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    (output_root / "report_surface_registry.json").write_text(
        json.dumps(registry_payload, indent=2),
        encoding="utf-8",
    )
    (output_root / "report_surface_registry.md").write_text(
        _render_report_surface_registry_markdown(registry_payload),
        encoding="utf-8",
    )
    (output_root / "report_narrative_quality_review.json").write_text(
        json.dumps(quality_payload, indent=2),
        encoding="utf-8",
    )
    (output_root / "report_narrative_quality_review.md").write_text(
        _render_report_narrative_quality_review_markdown(quality_payload),
        encoding="utf-8",
    )

    return {
        "report_portal_index": "index.md",
        "report_portal_how_to_read": "how-to-read.md",
        "report_portal_maps": "maps/index.md",
        "report_portal_scopes": "scopes/index.md",
        "report_portal_reviews": "reviews/index.md",
        "report_portal_caveats": "caveats/index.md",
        "report_portal_maintenance": "maintenance/index.md",
        "report_surface_registry_json": "report_surface_registry.json",
        "report_surface_registry_markdown": "report_surface_registry.md",
        "report_narrative_quality_review_json": "report_narrative_quality_review.json",
        "report_narrative_quality_review_markdown": "report_narrative_quality_review.md",
    }


def _build_existing_surface_rows(output_root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in sorted(path for path in output_root.rglob("*") if path.is_file()):
        relative_path = path.relative_to(output_root).as_posix()
        if relative_path in _PORTAL_FILES:
            continue
        rows.append(_classify_surface(output_root, relative_path))
    return rows


def _classify_surface(output_root: Path, relative_path: str) -> dict[str, object]:
    path = Path(relative_path)
    suffix = path.suffix.lstrip(".") or "none"
    family = _family_for_path(path)
    audience = _audience_for_path(path, family)
    geography = _geography_for_path(path)
    caution = _caution_level_for_path(path, family)
    return {
        "repository_path": f"docs/report/{relative_path}",
        "family": family,
        "family_label": _FAMILY_LABELS[family],
        "audience": audience,
        "audience_label": _AUDIENCE_LABELS[audience],
        "format": suffix,
        "geography": geography,
        "caution_level": caution,
        "explanation": _explanation_for_path(path, family, audience),
        "reader_route": _reader_route_for_path(path, family),
    }


def _family_for_path(path: Path) -> str:
    relative_path = path.as_posix()
    stem = path.stem
    if relative_path.startswith(("world/", "regions/")):
        if (
            path.suffix == ".html"
            or "map_" in stem
            or "point_traceability" in stem
            or "candidate_" in stem
            or "evidence_surface" in stem
            or "scientific_review" in stem
            or "atlas_evidence" in stem
            or "localities" in stem
            or "samples" in stem
            or "environmental_sites" in stem
            or "pollen_site" in stem
            or "archaeology_" in stem
            or "country_boundaries" in stem
        ):
            return "maps"
        return "scopes"
    if relative_path.startswith("countries/"):
        return "scopes"
    if stem.startswith(("repository_", "publication_")):
        return "maintenance"
    if stem == "published_reports_summary":
        return "scopes"
    if (
        "caveat" in stem
        or "honesty" in stem
        or "exclusion" in stem
        or "release_gate" in stem
        or "legibility" in stem
    ):
        return "caveats"
    if stem.startswith(("animal_", "nordic_farming_history_scenario")):
        return "reviews"
    return "maintenance"


def _audience_for_path(path: Path, family: str) -> str:
    stem = path.stem
    if family == "maintenance":
        return "maintainer_diagnostic"
    if family == "caveats":
        return "scientific_review_surface"
    if family == "reviews":
        return "scientific_review_surface"
    if family == "maps":
        if path.suffix == ".html" or path.name == "README.md":
            return "public_reading_surface"
        if "bundle" in stem or "manifest" in stem:
            return "maintainer_diagnostic"
        return "scientific_review_surface"
    if family == "scopes" and (
        path.name == "README.md" or path.suffix in {".md", ".json", ".csv", ".geojson"}
    ):
        return "public_reading_surface"
    return "public_reading_surface"


def _geography_for_path(path: Path) -> str:
    relative_path = path.as_posix()
    if relative_path.startswith("world/"):
        return "world"
    if relative_path.startswith("regions/europe-plus/"):
        return "europe_plus"
    if relative_path.startswith("regions/nordic/"):
        return "nordic"
    if relative_path.startswith("countries/"):
        return path.parts[1]
    return "report_root"


def _caution_level_for_path(path: Path, family: str) -> str:
    stem = path.stem
    if family in {"caveats", "maintenance"}:
        return "high"
    if "scientific_review" in stem or "evidence" in stem or "traceability" in stem:
        return "high"
    if path.suffix == ".html" or path.name == "README.md":
        return "medium"
    return "medium"


def _explanation_for_path(path: Path, family: str, audience: str) -> str:
    stem = path.stem
    if path.name == "README.md":
        return "Reader-facing entry page for one scope bundle."
    if family == "maps" and path.suffix == ".html":
        return "Interactive map surface for one governed publication scope."
    if family == "maps" and "traceability" in stem:
        return "Traceability surface for visible mapped points and overlays."
    if family == "maps" and "contract" in stem:
        return "Governed publication contract for one map scope."
    if family == "scopes" and "summary" in stem:
        return "Scope summary surface for direct inspection or downstream filtering."
    if family == "scopes" and "samples" in stem:
        return "Scope-filtered sample or locality export."
    if family == "reviews":
        return "Scientific review surface for animal evidence, chronology, or recovery posture."
    if family == "caveats":
        return "Caution-oriented surface describing blocked, thin, or overclaim-sensitive publication posture."
    if audience == "maintainer_diagnostic":
        return "Maintainer-facing truth or governance surface."
    return "Governed report artifact."


def _reader_route_for_path(path: Path, family: str) -> str:
    if path.name == "README.md":
        return "start_here"
    if family == "maps":
        return "map_detail"
    if family == "scopes":
        return "scope_bundle"
    if family == "reviews":
        return "evidence_review"
    if family == "caveats":
        return "caution_check"
    return "maintainer_truth"


def _build_portal_rows(
    output_root: Path,
    portal_pages: dict[str, str],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for relative_path in sorted(portal_pages):
        path = Path(relative_path)
        family = "portal" if path.parts[0] not in _FAMILY_LABELS else path.parts[0]
        rows.append(
            {
                "repository_path": f"docs/report/{relative_path}",
                "family": family,
                "family_label": _FAMILY_LABELS.get(family, "Portal guidance"),
                "audience": "public_reading_surface",
                "audience_label": _AUDIENCE_LABELS["public_reading_surface"],
                "format": path.suffix.lstrip("."),
                "geography": "report_root",
                "caution_level": "medium",
                "explanation": "Reader-facing portal page for navigating the report tree.",
                "reader_route": "start_here",
            }
        )
    return rows


def _build_report_surface_registry(rows: list[dict[str, object]]) -> dict[str, object]:
    family_counts = Counter(str(row["family"]) for row in rows)
    audience_counts = Counter(str(row["audience"]) for row in rows)
    geography_counts = Counter(str(row["geography"]) for row in rows)
    return {
        "schema_version": "report-surface-registry.v1",
        "surface_count": len(rows),
        "family_counts": dict(sorted(family_counts.items())),
        "audience_counts": dict(sorted(audience_counts.items())),
        "geography_counts": dict(sorted(geography_counts.items())),
        "rows": rows,
    }


def _build_report_narrative_quality_review(
    *,
    output_root: Path,
    existing_rows: list[dict[str, object]],
    portal_pages: dict[str, str],
) -> dict[str, object]:
    review_rows: list[dict[str, object]] = []
    markdown_paths = [
        row["repository_path"].removeprefix("docs/report/")
        for row in existing_rows
        if str(row["format"]) == "md"
    ]
    for relative_path in sorted(markdown_paths):
        text = (output_root / relative_path).read_text(encoding="utf-8")
        review_rows.append(_build_quality_row(relative_path, text))
    for relative_path, text in sorted(portal_pages.items()):
        if not relative_path.endswith(".md"):
            continue
        review_rows.append(_build_quality_row(relative_path, text))

    posture_counts = Counter(str(row["quality_posture"]) for row in review_rows)
    return {
        "schema_version": "report-narrative-quality-review.v1",
        "page_count": len(review_rows),
        "quality_posture_counts": dict(sorted(posture_counts.items())),
        "rows": review_rows,
    }


def _build_quality_row(relative_path: str, text: str) -> dict[str, object]:
    prose_paragraph_count = _count_prose_paragraphs(text)
    link_bullet_count = sum(
        1 for line in text.splitlines() if line.lstrip().startswith("- [")
    )
    bullet_sentence_count = sum(
        1 for line in text.splitlines() if _looks_like_sentence_bullet(line.strip())
    )
    heading_count = sum(1 for line in text.splitlines() if line.startswith("#"))
    table_line_count = sum(
        1 for line in text.splitlines() if line.strip().startswith("|")
    )
    quality_posture = "reader_ready"
    note = "Page explains its purpose before or alongside artifact links."
    if link_bullet_count > 14 and prose_paragraph_count < 2:
        quality_posture = "link_farm_risk"
        note = (
            "Page carries many artifact links without enough explanation around them."
        )
    elif prose_paragraph_count == 0 and table_line_count >= 4:
        quality_posture = "structured_reference"
        note = "Page is table-heavy, but it behaves like a reference surface rather than a loose link dump."
    elif prose_paragraph_count == 0 and bullet_sentence_count >= 3:
        quality_posture = "structured_reference"
        note = "Page is bullet-led, but those bullets still explain posture and evidence role."
    elif prose_paragraph_count == 0:
        quality_posture = "link_farm_risk"
        note = (
            "Page lacks explanatory prose and risks reading like a bare artifact index."
        )
    elif heading_count < 2:
        quality_posture = "thin_structure"
        note = "Page explains itself but still needs stronger internal wayfinding."
    return {
        "repository_path": f"docs/report/{relative_path}",
        "prose_paragraph_count": prose_paragraph_count,
        "link_bullet_count": link_bullet_count,
        "bullet_sentence_count": bullet_sentence_count,
        "heading_count": heading_count,
        "table_line_count": table_line_count,
        "quality_posture": quality_posture,
        "note": note,
    }


def _count_prose_paragraphs(text: str) -> int:
    paragraphs = 0
    current: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            if _looks_like_prose_block(current):
                paragraphs += 1
            current = []
            continue
        current.append(line)
    if _looks_like_prose_block(current):
        paragraphs += 1
    return paragraphs


def _looks_like_prose_block(lines: list[str]) -> bool:
    if not lines:
        return False
    first = lines[0]
    if first.startswith(("#", "|", "```", "<")):
        return False
    if first.startswith("- ") and not any(
        _looks_like_sentence_bullet(line) for line in lines
    ):
        return False
    joined = " ".join(lines)
    alpha_count = sum(1 for char in joined if char.isalpha())
    return alpha_count >= 60


def _looks_like_sentence_bullet(line: str) -> bool:
    if not line.startswith("- "):
        return False
    if line.startswith(("- `", "- [")):
        return False
    alpha_count = sum(1 for char in line if char.isalpha())
    return alpha_count >= 24


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


def _render_report_surface_registry_markdown(payload: dict[str, object]) -> str:
    family_rows = "\n".join(
        f"| {escape_pipes(_FAMILY_LABELS.get(str(key), str(key)))} | {value} |"
        for key, value in payload.get("family_counts", {}).items()
    )
    audience_rows = "\n".join(
        f"| {escape_pipes(_AUDIENCE_LABELS.get(str(key), str(key)))} | {value} |"
        for key, value in payload.get("audience_counts", {}).items()
    )
    artifact_rows = "\n".join(
        f"| `{row['repository_path']}` | {escape_pipes(str(row['family_label']))} | {escape_pipes(str(row['audience_label']))} | `{row['geography']}` | `{row['format']}` | {escape_pipes(str(row['explanation']))} |"
        for row in payload.get("rows", [])
    )
    return f"""# Report surface registry

This registry classifies the current `docs/report/` tree by family, audience,
scope, and explanation role so the publication system can be navigated as one
coherent report surface instead of a loose artifact dump.

- Surface count: `{payload["surface_count"]}`

## Family Counts

| Family | Count |
| --- | ---: |
{family_rows}

## Audience Counts

| Audience | Count |
| --- | ---: |
{audience_rows}

## Classified Surfaces

| Path | Family | Audience | Geography | Format | Explanation |
| --- | --- | --- | --- | --- | --- |
{artifact_rows}
"""


def _render_report_narrative_quality_review_markdown(payload: dict[str, object]) -> str:
    posture_rows = "\n".join(
        f"| `{key}` | {value} |"
        for key, value in payload.get("quality_posture_counts", {}).items()
    )
    review_rows = "\n".join(
        f"| `{row['repository_path']}` | `{row['quality_posture']}` | {row['prose_paragraph_count']} | {row['link_bullet_count']} | {row['bullet_sentence_count']} | {row['table_line_count']} | {row['heading_count']} | {escape_pipes(str(row['note']))} |"
        for row in payload.get("rows", [])
    )
    return f"""# Report narrative quality review

This review checks whether the report-facing Markdown surfaces explain
themselves in prose or structured reference form instead of behaving like bare
link farms or coded operator notes.

- Reviewed markdown pages: `{payload["page_count"]}`

## Quality Postures

| Posture | Count |
| --- | ---: |
{posture_rows}

## Reviewed Pages

| Path | Posture | Prose paragraphs | Link bullets | Sentence bullets | Table lines | Headings | Note |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
{review_rows}
"""
