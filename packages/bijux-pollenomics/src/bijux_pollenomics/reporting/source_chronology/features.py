"""Compact atlas feature projection for source chronology nodes."""

from __future__ import annotations

from bijux_pollenomics.analysis.propagation.source_chronology import (
    SourceChronologyNode,
)
from bijux_pollenomics.core.geospatial.geojson import JsonObject

from .facets import COUNTRY_NAMES, source_ecological_code_label


def build_atlas_feature(node: SourceChronologyNode) -> JsonObject:
    """Project one validated source node without introducing event semantics."""
    code = node.source_ecological_group
    name = node.source_reported_name
    title = (
        node.source_record_id
        if node.node_level == "source_sample_presence"
        else code
        if node.node_level == "source_ecological_code"
        else name
    )
    if title is None:
        raise ValueError("source chronology feature has no source-owned title")
    return {
        "latitude": node.latitude,
        "longitude": node.longitude,
        "country": COUNTRY_NAMES[node.country_code],
        "title": title,
        "subtitle": _subtitle(node.node_level),
        "record_id": canonical_neotoma_site_record_id(node.site_id),
        "node_id": node.node_id,
        "node_level": node.node_level,
        "semantic_role": "source_chronology_context",
        "source_family": node.source_family,
        "source_snapshot_id": node.source_snapshot_id,
        "build_id": node.build_id,
        "source_record_id": node.source_record_id,
        "feature_key": node.feature_key,
        "source_variable_ids": list(node.source_variable_ids),
        "source_taxon_id": node.source_taxon_id,
        "source_reported_name": name,
        "source_ecological_code": code,
        "source_ecological_code_label": source_ecological_code_label(code),
        "source_unit": node.source_unit,
        "observation_denominator": len(node.observation_ids),
        "chronology_claim_id": node.chronology_claim_id,
        "chronology_id": node.chronology_id,
        "chronology_name": node.chronology_name,
        "is_default_chronology": node.is_default_chronology,
        "chronology_selection_posture": node.chronology_selection_posture,
        "time_start_bp": node.younger_bp,
        "time_end_bp": node.older_bp,
        "time_label": _time_label(node.younger_bp, node.older_bp),
        "provenance_record_id": node.provenance_record_id,
        "input_digest": node.input_digest,
        "coordinate_quality": node.coordinate_quality,
        "candidate_generation_status": node.candidate_generation_status,
        "candidate_refusal_reason": node.candidate_refusal_reason,
        "propagation_eligible": node.propagation_eligible,
    }


def _subtitle(node_level: str) -> str:
    return {
        "source_sample_presence": "Neotoma pollen-presence context",
        "source_ecological_code": "Literal Neotoma ecological code",
        "source_taxon": "Exact Neotoma source taxon",
    }[node_level]


def _time_label(younger_bp: float, older_bp: float) -> str:
    if younger_bp == older_bp:
        return f"{younger_bp:g} BP"
    return f"{younger_bp:g}–{older_bp:g} BP"


def canonical_neotoma_site_record_id(site_id: str) -> str:
    """Bind a source-owned site identity to its existing atlas detail record."""
    return site_id if site_id.startswith("neotoma:site:") else f"neotoma:site:{site_id}"


__all__ = ["build_atlas_feature", "canonical_neotoma_site_record_id"]
