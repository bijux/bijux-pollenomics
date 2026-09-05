from __future__ import annotations

ADNA_LOCALITY_CLASSES = (
    "excavation_site",
    "broader_locality",
    "municipality",
    "region",
    "country",
    "inferred_place_string",
    "unresolved",
)

_BROADER_PLACE_MARKERS = (
    "archipelago",
    "basin",
    "central europe",
    "context",
    "dispersal",
    "europe",
    "galicia",
    "lake ",
    "levant",
    "near east",
    "north africa",
    "peninsula",
    "plateau",
    "region",
    "steppe",
    "transect",
)


def _classify_sample_site_row(row: object) -> str:
    status = str(getattr(row, "locality_resolution_status", "")).strip()
    locality_text = str(getattr(row, "locality_text", "")).strip()
    site_name = str(getattr(row, "site_name", "")).strip()
    municipality_name = str(getattr(row, "municipality_name", "")).strip()
    region_name = str(getattr(row, "region_name", "")).strip()
    country_name = str(getattr(row, "country_name", "")).strip()
    broader_geography = str(getattr(row, "broader_geography", "")).strip()
    if not locality_text or status == "unresolved":
        return "unresolved"
    if status == "named_place_inferred":
        return "inferred_place_string"
    if municipality_name and not site_name:
        return "municipality"
    if region_name and not site_name:
        return "region"
    if (
        country_name
        and locality_text == country_name
        and not site_name
        and not region_name
    ):
        return "country"
    if broader_geography and not site_name:
        return "broader_locality"
    if _looks_broad(locality_text):
        return "broader_locality"
    return "excavation_site"


def _classify_context_place(*, locality_text: str, political_entity: str) -> str:
    if not locality_text.strip():
        return "unresolved"
    if _looks_like_country(locality_text):
        return "country"
    if _looks_broad(locality_text) or (
        _looks_broad(political_entity) and not _looks_like_country(political_entity)
    ):
        return "broader_locality"
    return "excavation_site"


def _source_surface_for_packet(row: object) -> str:
    kind = str(getattr(row, "location_evidence_artifact_kind", "")).strip()
    path = str(getattr(row, "location_evidence_artifact_path", "")).strip()
    return _source_surface_for_context(path, kind)


def _source_surface_for_context(path: str, kind: str) -> str:
    lowered_kind = kind.casefold()
    lowered_path = path.casefold()
    if (
        "supplementary" in lowered_kind
        or "supplementary" in lowered_path
        or path.endswith(".xlsx")
    ):
        return "supplementary_table"
    if "archive" in lowered_kind or "archive_metadata" in lowered_path:
        return "archive_metadata"
    if "crossref" in lowered_kind or lowered_path.endswith("crossref.json"):
        return "crossref_metadata"
    if lowered_path.endswith(".html") or "article" in lowered_kind:
        return "article_text"
    return "tracked_source_artifact"


def _normalized_display_spelling(locality_text: str, site_name: str) -> str:
    return site_name.strip() or locality_text.strip()


def _geocoding_safe_token(value: str) -> str:
    return _normalize_text(value)


def _normalize_text(value: str) -> str:
    return "".join(character for character in value.casefold() if character.isalnum())


def _looks_like_country(value: str) -> bool:
    stripped = value.strip()
    return (
        bool(stripped)
        and all(marker not in stripped.casefold() for marker in _BROADER_PLACE_MARKERS)
        and "," not in stripped
        and " and " not in stripped.casefold()
    )


def _looks_broad(value: str) -> bool:
    lowered = value.casefold()
    return any(marker in lowered for marker in _BROADER_PLACE_MARKERS)


def _locality_evidence_bucket(
    *, locality_class: str, locality_resolution_status: str
) -> str:
    if (
        locality_resolution_status == "direct_sample_site"
        and locality_class == "excavation_site"
    ):
        return "exact_site_evidence"
    if locality_resolution_status == "unresolved":
        return "unresolved_geography"
    if locality_class in {
        "broader_locality",
        "municipality",
        "region",
        "country",
        "inferred_place_string",
    }:
        return "broader_locality_evidence"
    if locality_resolution_status in {"project_level_site_only", "region_only"}:
        return "broader_locality_evidence"
    return "exact_site_evidence"
