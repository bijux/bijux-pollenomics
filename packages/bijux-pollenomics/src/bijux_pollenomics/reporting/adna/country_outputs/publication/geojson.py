from __future__ import annotations

import json
from pathlib import Path

from ..models import CountryAnimalOutputBundle


def write_country_animal_localities_geojson(
    path: Path, bundle: CountryAnimalOutputBundle
) -> None:
    """Write one map-ready feature collection for country-resolved animal localities."""
    features: list[dict[str, object]] = []
    for row in bundle.localities:
        latitude = row.get("latitude")
        longitude = row.get("longitude")
        if not isinstance(latitude, (int, float)) or not isinstance(
            longitude, (int, float)
        ):
            continue
        sample_record_ids = row["sample_record_ids"]
        mapped_sample_ids = (
            ", ".join(str(item) for item in sample_record_ids)
            if isinstance(sample_record_ids, list)
            else ""
        )
        popup_rows: list[dict[str, object]] = [
            {"label": "Species", "value": row["species_latin_name"]},
            {
                "label": "Animal scope",
                "value": str(row["animal_scope"]).replace("_", " "),
            },
            {"label": "Project accession", "value": row["project_accession"]},
            {
                "label": "Country assignment",
                "value": row["country_assignment_confidence"],
            },
            {"label": "Assignment note", "value": row["country_assignment_reason"]},
            {"label": "Chronology", "value": row["time_label"]},
            {"label": "Chronology class", "value": row["chronology_evidence_class"]},
            {
                "label": "Chronology posture",
                "value": row["chronology_precision_posture"],
            },
            {"label": "Coordinate basis", "value": row["coordinate_basis"]},
            {"label": "Coordinate confidence", "value": row["coordinate_confidence"]},
            {
                "label": "Mapped sample identifiers",
                "value": mapped_sample_ids,
            },
            {
                "label": "Site evidence locator",
                "value": (
                    f"{row['source_artifact_path']}#{row['source_locator']}"
                    if row["source_artifact_path"] and row["source_locator"]
                    else row["source_artifact_path"] or row["source_locator"]
                ),
            },
            {
                "label": "Coordinate evidence locator",
                "value": (
                    f"{row['coordinate_source_artifact_path']}#{row['coordinate_source_locator']}"
                    if row["coordinate_source_artifact_path"]
                    and row["coordinate_source_locator"]
                    else row["coordinate_source_artifact_path"]
                    or row["coordinate_source_locator"]
                ),
            },
            {"label": "Interpretation", "value": row["interpretation_note"]},
        ]
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [longitude, latitude]},
                "properties": {
                    "name": row["locality"],
                    "country": row["country"],
                    "feature_id": row["feature_id"],
                    "evidence_row_id": row["evidence_row_id"],
                    "site_record_id": row["site_record_id"],
                    "species_latin_name": row["species_latin_name"],
                    "species_common_name": row["species_common_name"],
                    "animal_scope": row["animal_scope"],
                    "project_accession": row["project_accession"],
                    "project_accessions": row["project_accessions"],
                    "support_class": row["support_class"],
                    "country_assignment_confidence": row[
                        "country_assignment_confidence"
                    ],
                    "country_assignment_reason": row["country_assignment_reason"],
                    "coordinate_basis": row["coordinate_basis"],
                    "coordinate_confidence": row["coordinate_confidence"],
                    "sample_count": row["sample_count"],
                    "sample_record_ids": row["sample_record_ids"],
                    "sample_group_ids": row["sample_group_ids"],
                    "sample_namespace": row["sample_namespace"],
                    "source_artifact_path": row["source_artifact_path"],
                    "source_artifact_kind": row["source_artifact_kind"],
                    "source_locator": row["source_locator"],
                    "source_support_status": row["source_support_status"],
                    "coordinate_source_artifact_path": row[
                        "coordinate_source_artifact_path"
                    ],
                    "coordinate_source_locator": row["coordinate_source_locator"],
                    "coordinate_supplementary_source": row[
                        "coordinate_supplementary_source"
                    ],
                    "coordinate_support_gap_note": row["coordinate_support_gap_note"],
                    "time_start_bp": row["time_start_bp"],
                    "time_end_bp": row["time_end_bp"],
                    "time_mean_bp": row["time_mean_bp"],
                    "time_label": row["time_label"],
                    "chronology_evidence_class": row["chronology_evidence_class"],
                    "chronology_precision_posture": row["chronology_precision_posture"],
                    "paper_title": row["paper_title"],
                    "paper_doi": row["paper_doi"],
                    "source_url": row["source_url"],
                    "popup_rows": [item for item in popup_rows if item["value"]],
                },
            }
        )
    path.write_text(
        json.dumps(
            {
                "schema_version": "country-animal-adna-localities.v1",
                "type": "FeatureCollection",
                "country": bundle.country,
                "features": features,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
