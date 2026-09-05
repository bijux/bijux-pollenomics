from __future__ import annotations

from bijux_pollenomics.analysis.fieldwork.evidence_richness import (
    LakeEvidenceCandidate,
    LakeEvidenceSourceAnchor,
)


def _google_maps_url(latitude: float, longitude: float) -> str:
    return f"https://www.google.com/maps/search/?api=1&query={latitude:.6f},{longitude:.6f}"


def _render_coordinate_link(latitude: float, longitude: float) -> str:
    label = f"{latitude:.6f}, {longitude:.6f}"
    return f"[{label}]({_google_maps_url(latitude, longitude)})"


def _render_ambiguity_cell(flags: tuple[str, ...]) -> str:
    return ", ".join(flags) if flags else "none"


def _render_source_point_cell(source_point: LakeEvidenceSourceAnchor) -> str:
    return (
        f"{source_point.source_name} "
        f"({source_point.source_layer_key}; "
        f"{source_point.latitude:.6f}, {source_point.longitude:.6f})"
    )


def _render_lake_area(candidate: LakeEvidenceCandidate) -> str:
    if candidate.lake_area_km2 is None:
        return "Not available"
    return f"{candidate.lake_area_km2:.3f}"


def _candidate_description(candidate: LakeEvidenceCandidate) -> str:
    if candidate.representative_source_record.startswith("svar-lakes:"):
        return "Lake candidate anchored to the official Sweden lake registry."
    return "Lake candidate derived from Sweden pollen context."


def _candidate_media_links(candidate: LakeEvidenceCandidate) -> list[dict[str, str]]:
    links = [
        {
            "label": "Open in Google Maps",
            "url": _google_maps_url(candidate.latitude, candidate.longitude),
            "kind": "link",
        }
    ]
    if candidate.representative_source_url:
        links.append(
            {
                "label": "Open representative source",
                "url": candidate.representative_source_url,
                "kind": "link",
            }
        )
    return links
