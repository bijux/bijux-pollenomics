from __future__ import annotations

from collections.abc import Iterable

from ....core.bp_time import build_bp_interval_label
from ....core.temporal_semantics import build_temporal_semantics
from ...models import SampleRecord


def build_aadr_point_layer(
    samples: Iterable[SampleRecord],
    *,
    version: str,
) -> dict[str, object]:
    """Build the AADR point layer payload used by the shared map."""
    features = []
    for sample in samples:
        bp_coverage = sample.time_label or build_bp_interval_label(
            sample.time_start_bp, sample.time_end_bp
        )
        temporal_semantics = build_temporal_semantics(
            source_family="aadr",
            evidence_class="direct_numeric_sample_date",
            precision_posture="sample_interval",
            comparability_posture="numeric_interval",
            time_start_bp=sample.time_start_bp,
            time_end_bp=sample.time_end_bp,
            time_mean_bp=sample.time_mean_bp,
            summary_label=bp_coverage,
            comparison_note=(
                "AADR exposes one sample-level numeric chronology surface here. Interpret it as direct evidence, not as a contextual period label."
            ),
            original_labels=(bp_coverage,) if bp_coverage else (),
        ).as_dict()
        features.append(
            {
                "latitude": sample.latitude,
                "longitude": sample.longitude,
                "country": sample.political_entity,
                "title": sample.genetic_id,
                "subtitle": sample.locality,
                "species_latin_name": sample.species_latin_name,
                "evidence_role": "direct",
                "time_start_bp": sample.time_start_bp,
                "time_end_bp": sample.time_end_bp,
                "time_mean_bp": sample.time_mean_bp,
                "time_year_bp": sample.time_mean_bp,
                "time_label": bp_coverage,
                "temporal_semantics": temporal_semantics,
                "temporal_window_key": temporal_semantics["temporal_window_key"],
                "temporal_window_label": temporal_semantics["temporal_window_label"],
                "popup_rows": [
                    {"label": "Species", "value": sample.species_latin_name},
                    {"label": "Evidence role", "value": "direct"},
                    {"label": "Source family", "value": sample.source_family},
                    {"label": "Source release", "value": sample.source_release},
                    {"label": "Record modality", "value": sample.record_modality},
                    {"label": "Review strength", "value": sample.review_strength},
                    {"label": "Provenance quality", "value": sample.provenance_quality},
                    {
                        "label": "Coordinate confidence",
                        "value": sample.coordinate_confidence,
                    },
                    {"label": "Dating basis", "value": sample.dating_basis},
                    {"label": "Genetic ID", "value": sample.genetic_id},
                    {"label": "Locality", "value": sample.locality},
                    {"label": "Country", "value": sample.political_entity},
                    {"label": "Master ID", "value": sample.master_id},
                    {"label": "Group ID", "value": sample.group_id},
                    {"label": "Datasets", "value": ", ".join(sample.datasets)},
                    {"label": "Publication", "value": sample.publication},
                    {"label": "Date", "value": sample.full_date},
                    {"label": "Date mean in BP", "value": sample.date_mean_bp},
                    {
                        "label": "Date standard deviation in BP",
                        "value": sample.date_stddev_bp,
                    },
                    {"label": "BP coverage", "value": bp_coverage},
                    {
                        "label": "Temporal comparison posture",
                        "value": str(
                            temporal_semantics["comparability_posture"]
                        ).replace("_", " "),
                    },
                ],
            }
        )
    return {
        "key": "aadr",
        "label": f"AADR-{version} aDNA samples",
        "count": len(features),
        "description": "Ancient DNA sample locations from AADR.",
        "group": "primary-evidence",
        "atlas_layer_key": "homo_sapiens_direct",
        "species_latin_name": "Homo sapiens",
        "contribution_role": "direct",
        "provenance_posture": "aadr_metadata_only",
        "source_name": "Allen Ancient DNA Resource",
        "coverage_label": "Country assignment follows the AADR political entity field.",
        "geometry_label": "Point records",
        "default_enabled": True,
        "applies_country_filter": True,
        "applies_time_filter": True,
        "circle_enabled": True,
        "traceability_artifact": "",
        "style": {
            "fill": "#2563eb",
            "stroke": "#0f172a",
            "circleStroke": "rgba(37, 99, 235, 0.42)",
            "circleFill": "rgba(37, 99, 235, 0.10)",
        },
        "features": features,
    }


__all__ = ["build_aadr_point_layer"]
