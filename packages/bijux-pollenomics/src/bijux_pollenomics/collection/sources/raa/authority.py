from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from ....core.geospatial.geojson import as_mapping
from ....core.text import clean_optional_text
from .inventory import (
    declared_population,
    decode_source_object,
    non_negative_count,
    source_features,
    validate_inventory,
)

__all__ = ["RaaDensityAuthorityDecision", "assess_raa_density_authority"]


@dataclass(frozen=True)
class RaaDensityAuthorityDecision:
    """Content-based decision for admitting the RAÄ density surface."""

    admitted: bool
    reason_codes: tuple[str, ...]
    archived_feature_count: int | None
    heritage_site_count: int | None
    density_site_count: int | None
    density_feature_count: int | None
    reviewer_id: str | None


def assess_raa_density_authority(context_root: Path) -> RaaDensityAuthorityDecision:
    """Admit RAÄ density only when raw, normalized, and human review reconcile."""
    family_root = Path(context_root) / "raa"
    raw_path = family_root / "raw" / "publicerade_lamningar_centrumpunkt.geojson"
    summary_path = (
        family_root / "raw" / "publicerade_lamningar_centrumpunkt_summary.json"
    )
    metadata_path = family_root / "normalized" / "sweden_archaeology_layer.json"
    density_path = family_root / "normalized" / "sweden_archaeology_density.geojson"
    review_path = family_root / "review" / "spatiotemporal_review.json"
    required_paths = {
        "missing_raw_inventory": raw_path,
        "missing_raw_summary": summary_path,
        "missing_normalized_metadata": metadata_path,
        "missing_density_surface": density_path,
        "missing_scientific_review": review_path,
    }
    reasons = [reason for reason, path in required_paths.items() if not path.is_file()]
    if reasons:
        return RaaDensityAuthorityDecision(
            admitted=False,
            reason_codes=tuple(reasons),
            archived_feature_count=None,
            heritage_site_count=None,
            density_site_count=None,
            density_feature_count=None,
            reviewer_id=None,
        )

    try:
        raw = _load_object(raw_path)
        summary = _load_object(summary_path)
        metadata = _load_object(metadata_path)
        density = _load_object(density_path)
        review = _load_object(review_path)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return RaaDensityAuthorityDecision(
            admitted=False,
            reason_codes=("invalid_authority_artifact",),
            archived_feature_count=None,
            heritage_site_count=None,
            density_site_count=None,
            density_feature_count=None,
            reviewer_id=None,
        )

    try:
        raw_features = validate_inventory(raw)
        density_features = source_features(density)
    except ValueError:
        return RaaDensityAuthorityDecision(
            admitted=False,
            reason_codes=("invalid_authority_inventory",),
            archived_feature_count=None,
            heritage_site_count=None,
            density_site_count=None,
            density_feature_count=None,
            reviewer_id=None,
        )
    heritage_site_count = sum(
        1
        for feature in raw_features
        for properties in (as_mapping(feature.get("properties")),)
        if properties is not None
        and clean_optional_text(properties.get("antikvariskbedomningtyp_namn"))
        == "Fornlämning"
    )
    density_counts = [
        non_negative_count(properties.get("count")) if properties is not None else None
        for feature in density_features
        for properties in (as_mapping(feature.get("properties")),)
    ]
    density_site_count = (
        sum(count for count in density_counts if count is not None)
        if all(count is not None for count in density_counts)
        else None
    )
    if density_site_count is None:
        reasons.append("invalid_density_cell_count")
    archived_feature_count = len(raw_features)
    metadata_counts = as_mapping(metadata.get("counts")) or {}
    possible_site_count = sum(
        1
        for feature in raw_features
        for properties in (as_mapping(feature.get("properties")),)
        if properties is not None
        and clean_optional_text(properties.get("antikvariskbedomningtyp_namn"))
        in {"Fornlämning", "Möjlig fornlämning"}
    )
    expected_values = {
        "summary_population_mismatch": (
            non_negative_count(summary.get("number_matched")),
            declared_population(raw),
        ),
        "summary_identified_count_mismatch": (
            non_negative_count(summary.get("identified_feature_count")),
            archived_feature_count,
        ),
        "metadata_archived_count_mismatch": (
            non_negative_count(metadata_counts.get("all_published_sites")),
            archived_feature_count,
        ),
        "summary_possible_heritage_count_mismatch": (
            non_negative_count(summary.get("heritage_or_possible_site_count")),
            possible_site_count,
        ),
        "metadata_possible_heritage_count_mismatch": (
            non_negative_count(metadata_counts.get("fornlamning_or_possible")),
            possible_site_count,
        ),
        "summary_archived_count_mismatch": (
            non_negative_count(summary.get("archived_feature_count")),
            archived_feature_count,
        ),
        "summary_heritage_count_mismatch": (
            non_negative_count(summary.get("heritage_site_count")),
            heritage_site_count,
        ),
        "metadata_heritage_count_mismatch": (
            non_negative_count(metadata_counts.get("fornlamning")),
            heritage_site_count,
        ),
        "density_site_count_mismatch": (density_site_count, heritage_site_count),
        "density_feature_count_mismatch": (
            non_negative_count(metadata.get("density_feature_count")),
            len(density_features),
        ),
    }
    reasons.extend(
        reason
        for reason, (reported, observed) in expected_values.items()
        if reported is None or reported != observed
    )
    reviewer_id = clean_optional_text(review.get("reviewer_id")) or None
    if review.get("release_status") != "accepted" or reviewer_id is None:
        reasons.append("scientific_review_not_accepted")
    return RaaDensityAuthorityDecision(
        admitted=not reasons,
        reason_codes=tuple(reasons),
        archived_feature_count=archived_feature_count,
        heritage_site_count=heritage_site_count,
        density_site_count=density_site_count,
        density_feature_count=len(density_features),
        reviewer_id=reviewer_id,
    )


def _load_object(path: Path) -> dict[str, object]:
    return decode_source_object(path.read_text(encoding="utf-8"))
