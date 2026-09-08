"""LandClim point evidence for governed boundary review."""

from __future__ import annotations

from pathlib import Path

from ......core.geospatial.geojson import feature_list
from ..models import JsonObject, PointEvidence
from ..serialization import _optional_text, _read_json_object, _required_text
from .records import _artifact_records, _lineage, _point_feature, _popup_value


def _load_landclim_points(
    root: Path,
) -> tuple[str, list[PointEvidence], list[JsonObject]]:
    normalized_path = Path(
        "data/landclim/normalized/nordic_pollen_site_sequences.geojson"
    )
    raw_path = Path("data/landclim/raw/landclim_i_land_cover_types.xlsx")
    normalized = _read_json_object(root / normalized_path)
    points: list[PointEvidence] = []
    for index, feature in enumerate(feature_list(normalized)):
        properties, longitude, latitude = _point_feature(feature, "LandClim")
        record_id = _required_text(properties.get("record_id"), "LandClim record ID")
        raw_country = _popup_value(properties, "Reported country")
        points.append(
            PointEvidence(
                source_family="landclim",
                source_scope="four_country_expected",
                source_record_id=f"landclim:site-sequence:{record_id}",
                longitude=longitude,
                latitude=latitude,
                raw_country=raw_country,
                published_country=_optional_text(properties.get("country")),
                lineage=(
                    _lineage(normalized_path, f"features[{index}]", "point_record"),
                    _lineage(
                        raw_path,
                        f"SiteData[record_id={record_id}]",
                        "source_native_workbook",
                    ),
                ),
            )
        )
    return (
        "landclim",
        points,
        _artifact_records(root, (normalized_path, raw_path)),
    )
