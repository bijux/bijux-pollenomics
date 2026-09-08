"""Canonical temporal-grid GeoJSON feature construction."""

from __future__ import annotations


def _temporal_grid_feature(
    *,
    dataset_id: str,
    cell_id: str,
    cell_label: str,
    time_window: str,
    country: str,
    geometry: dict[str, object],
    provenance_path: str,
    provenance_locator: str,
    value_unit: str,
) -> dict[str, object]:
    from . import (
        LANDCLIM_DATASET_METADATA,
        LANDCLIM_TEMPORAL_GRID_LAYER_KEY,
        _bibliography_reference_keys,
        build_temporal_semantics,
        mean_bp_year_from_interval,
        parse_bp_window_label,
        re,
    )

    interval = parse_bp_window_label(time_window)
    if interval is None:
        raise ValueError(f"LandClim time window is not numeric: {time_window}")
    metadata = LANDCLIM_DATASET_METADATA[dataset_id]
    temporal_semantics = build_temporal_semantics(
        source_family="landclim",
        evidence_class="modeled_vegetation_time_window",
        precision_posture="published_reveals_grid_window",
        comparability_posture="numeric_interval_with_caveat",
        time_start_bp=interval[0],
        time_end_bp=interval[1],
        summary_label=time_window,
        comparison_note=(
            "This interval belongs to a modeled REVEALS grid estimate; it is not a "
            "sample-owned chronology or a continuous value between published windows."
        ),
        provenance_path=provenance_path,
        provenance_locator=provenance_locator,
        original_labels=(time_window,),
        normalized_labels=(time_window,),
    ).as_dict()
    window_key = re.sub(r"[^a-z0-9]+", "-", time_window.casefold()).strip("-")
    return {
        "type": "Feature",
        "geometry": geometry,
        "properties": {
            "source": "LandClim",
            "layer_key": LANDCLIM_TEMPORAL_GRID_LAYER_KEY,
            "layer_label": "LandClim REVEALS time-window grids",
            "category": "Vegetation reconstruction time window",
            "country": country,
            "record_id": f"{dataset_id}:{cell_id}:{window_key}",
            "parent_grid_record_id": cell_id,
            "name": f"{cell_label} · {time_window}",
            "geometry_type": "Polygon",
            "subtitle": "Published REVEALS vegetation reconstruction for one grid cell and time window",
            "description": (
                "One published LandClim REVEALS model window retained separately so "
                "atlas time filtering does not treat the full Holocene span as continuous."
            ),
            "source_url": metadata["doi"],
            "dataset_id": dataset_id,
            "dataset_label": metadata["label"],
            "bibliography_reference_keys": _bibliography_reference_keys(dataset_id),
            "value_unit": value_unit,
            "record_count": 1,
            "time_start_bp": interval[0],
            "time_end_bp": interval[1],
            "time_mean_bp": mean_bp_year_from_interval(interval),
            "time_label": time_window,
            "temporal_semantics": temporal_semantics,
            "temporal_window_key": temporal_semantics["temporal_window_key"],
            "temporal_window_label": temporal_semantics["temporal_window_label"],
            "temporal_comparability_posture": temporal_semantics[
                "comparability_posture"
            ],
            "temporal_comparison_note": temporal_semantics["comparison_note"],
            "popup_rows": [
                {"label": "Dataset", "value": metadata["label"]},
                {"label": "DOI", "value": metadata["doi"]},
                {"label": "Country", "value": country},
                {"label": "Grid cell", "value": cell_id},
                {"label": "Time window", "value": time_window},
                {"label": "Value unit", "value": value_unit.replace("_", " ")},
            ],
            "reconstruction_values": {},
            "standard_errors": {},
        },
    }


def _bibliography_reference_keys(dataset_id: str) -> list[str]:
    primary_reference_by_dataset = {
        "900966": "marquer-et-al-2017",
        "897303": "trondman-et-al-2015",
        "937075": "githumbi-et-al-2022",
    }
    return [primary_reference_by_dataset[dataset_id], "sugita-2007-reveals"]
