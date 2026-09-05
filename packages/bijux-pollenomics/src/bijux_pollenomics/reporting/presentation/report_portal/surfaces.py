from __future__ import annotations

from collections import Counter
from pathlib import Path

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
