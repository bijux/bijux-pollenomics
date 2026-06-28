from __future__ import annotations

import csv
from pathlib import Path

from ..context.points import build_external_point_layer

__all__ = ["build_sweden_lake_atlas_layers"]

_SCENARIO_KEYS = (
    "aggregate",
    "consensus",
    "fieldwork_shortlist",
    "radius_10km",
    "radius_20km",
    "radius_30km",
    "radius_40km",
    "radius_50km",
)

_LAYER_METADATA = {
    "aggregate": (
        "sweden-lake-aggregate-top40",
        "Sweden lake aggregate top 40",
        "Aggregate",
    ),
    "consensus": (
        "sweden-lake-consensus-top40",
        "Sweden lake consensus top 40",
        "Consensus",
    ),
    "fieldwork_shortlist": (
        "sweden-lake-fieldwork-top40",
        "Sweden lake fieldwork top 40",
        "Fieldwork shortlist",
    ),
    "radius_10km": (
        "sweden-lake-10km-top40",
        "Sweden lake 10 km top 40",
        "10 km",
    ),
    "radius_20km": (
        "sweden-lake-20km-top40",
        "Sweden lake 20 km top 40",
        "20 km",
    ),
    "radius_30km": (
        "sweden-lake-30km-top40",
        "Sweden lake 30 km top 40",
        "30 km",
    ),
    "radius_40km": (
        "sweden-lake-40km-top40",
        "Sweden lake 40 km top 40",
        "40 km",
    ),
    "radius_50km": (
        "sweden-lake-50km-top40",
        "Sweden lake 50 km top 40",
        "50 km",
    ),
}


def build_sweden_lake_atlas_layers(
    *,
    version: str,
    staging_output_dir: Path,
    published_output_dir: Path,
) -> list[dict[str, object]]:
    """Build optional Nordic atlas layers from the published Sweden lake packet."""
    scenario_csv_path = _find_sweden_scenario_csv(
        version=version,
        staging_output_dir=staging_output_dir,
        published_output_dir=published_output_dir,
    )
    if scenario_csv_path is None:
        return []

    grouped_rows = _load_grouped_scenario_rows(scenario_csv_path)
    traceability_reference = _build_traceability_reference(
        version=version,
        staging_output_dir=staging_output_dir,
        published_output_dir=published_output_dir,
    )
    point_layers: list[dict[str, object]] = []
    for scenario_key in _SCENARIO_KEYS:
        rows = grouped_rows.get(scenario_key, [])
        if not rows:
            continue
        feature_collection = _build_feature_collection(
            rows=rows,
            scenario_key=scenario_key,
        )
        layer = build_external_point_layer(
            feature_collection,
            source_path=scenario_csv_path,
        )
        layer["default_enabled"] = False
        if traceability_reference:
            layer["traceability_reference"] = traceability_reference
        point_layers.append(layer)
    return point_layers


def _find_sweden_scenario_csv(
    *,
    version: str,
    staging_output_dir: Path,
    published_output_dir: Path,
) -> Path | None:
    filename = f"sweden_lake_evidence_richness_{version}_scenarios.csv"
    search_roots = (
        staging_output_dir,
        *staging_output_dir.parents,
        published_output_dir,
        *published_output_dir.parents,
    )
    seen: set[Path] = set()
    for root in search_roots:
        candidate = Path(root)
        if candidate in seen:
            continue
        seen.add(candidate)
        for scoped_path in (
            candidate / "countries" / "sweden" / filename,
            candidate / "report" / "countries" / "sweden" / filename,
        ):
            if scoped_path.is_file():
                return scoped_path
    return None


def _build_traceability_reference(
    *,
    version: str,
    staging_output_dir: Path,
    published_output_dir: Path,
) -> str:
    filename = f"sweden_lake_evidence_richness_{version}.md"
    search_roots = (
        staging_output_dir,
        *staging_output_dir.parents,
        published_output_dir,
        *published_output_dir.parents,
    )
    seen: set[Path] = set()
    for root in search_roots:
        candidate = Path(root)
        if candidate in seen:
            continue
        seen.add(candidate)
        for scoped_path in (
            candidate / "countries" / "sweden" / filename,
            candidate / "report" / "countries" / "sweden" / filename,
        ):
            if scoped_path.is_file():
                return scoped_path.name
    return ""


def _load_grouped_scenario_rows(
    scenario_csv_path: Path,
) -> dict[str, list[dict[str, str]]]:
    grouped_rows = {key: [] for key in _SCENARIO_KEYS}
    with scenario_csv_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            scenario_key = str(row.get("scenario_key", "")).strip()
            rank = _parse_int(row.get("rank", ""))
            if scenario_key not in grouped_rows or rank is None or rank > 40:
                continue
            grouped_rows[scenario_key].append(row)
    for rows in grouped_rows.values():
        rows.sort(key=lambda row: int(row["rank"]))
    return grouped_rows


def _build_feature_collection(
    *,
    rows: list[dict[str, str]],
    scenario_key: str,
) -> dict[str, object]:
    layer_key, layer_label, scenario_label = _LAYER_METADATA[scenario_key]
    features = []
    for row in rows:
        latitude = float(row["latitude"])
        longitude = float(row["longitude"])
        lake_area = _parse_float(row.get("lake_area_km2", ""))
        sampling_fit = _parse_float(row.get("lake_sampling_fit", ""))
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [longitude, latitude],
                },
                "properties": {
                    "source": "bijux-pollenomics",
                    "layer_key": layer_key,
                    "layer_label": layer_label,
                    "category": "Lake evidence candidate",
                    "country": "Sweden",
                    "record_id": row["lake_token"],
                    "name": row["lake_label"],
                    "geometry_type": "Point",
                    "subtitle": "Optional Sweden lake ranking overlay",
                    "description": (
                        row.get("ambiguity_note", "").strip()
                        or "Published Sweden lake ranking candidate."
                    ),
                    "source_url": row.get("google_maps_url", "").strip(),
                    "record_count": 1,
                    "media_links": [],
                    "popup_rows": [
                        {"label": "Scenario", "value": scenario_label},
                        {"label": "Scenario rank", "value": row["rank"]},
                        {"label": "Scenario score", "value": _format_score(row["score"])},
                        {
                            "label": "Aggregate rank",
                            "value": row.get("aggregate_rank", "").strip()
                            or "Not available",
                        },
                        {
                            "label": "Aggregate score",
                            "value": _format_score(row.get("aggregate_score", "")),
                        },
                        {
                            "label": "Coordinates",
                            "value": f"{latitude:.6f}, {longitude:.6f}",
                        },
                        {
                            "label": "Lake registry id",
                            "value": row.get("lake_registry_id", "").strip()
                            or "Not available",
                        },
                        {
                            "label": "Lake area",
                            "value": (
                                f"{lake_area:.3f} km²"
                                if lake_area is not None
                                else "Not available"
                            ),
                        },
                        {
                            "label": "Sampling posture",
                            "value": row.get("lake_sampling_posture", "").strip()
                            or "Not available",
                        },
                        {
                            "label": "Sampling fit",
                            "value": (
                                f"{sampling_fit:.4f}"
                                if sampling_fit is not None
                                else "Not available"
                            ),
                        },
                        {
                            "label": "Sampling notes",
                            "value": row.get("lake_sampling_notes", "").strip()
                            or "Not available",
                        },
                        {
                            "label": "Identity diagnostics",
                            "value": row.get("ambiguity_flags", "").strip()
                            or "No explicit identity warning.",
                        },
                        {
                            "label": "Identity note",
                            "value": row.get("ambiguity_note", "").strip()
                            or "No explicit identity warning.",
                        },
                        {
                            "label": "Scenario top-20 presence count",
                            "value": row.get(
                                "scenario_top20_presence_count", ""
                            ).strip()
                            or "0",
                        },
                        {
                            "label": "Scenario top-20 labels",
                            "value": row.get("scenario_top20_labels", "").strip()
                            or "None",
                        },
                    ],
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}


def _parse_float(value: str) -> float | None:
    stripped = value.strip()
    if not stripped:
        return None
    return float(stripped)


def _parse_int(value: str) -> int | None:
    stripped = value.strip()
    if not stripped:
        return None
    return int(stripped)


def _format_score(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        return "Not available"
    return f"{float(stripped):.4f}"
