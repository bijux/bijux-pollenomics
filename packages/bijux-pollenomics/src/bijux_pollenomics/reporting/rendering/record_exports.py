from __future__ import annotations

from collections.abc import Iterable
import csv
import json
from pathlib import Path

from ...adna.domain.models.localities import AdnaSampleChronologySupport
from ..models import LocalitySummary, SampleRecord

__all__ = [
    "build_sample_geojson_feature",
    "build_samples_geojson",
    "serialize_locality_summary",
    "serialize_sample_record",
    "write_localities_csv",
    "write_samples_csv",
    "write_samples_geojson",
]


LEGACY_SAMPLE_EXPORT_FIELDS = (
    "schema_version",
    "species_latin_name",
    "species_common_name",
    "source_family",
    "sample_namespace",
    "genetic_id",
    "master_id",
    "group_id",
    "locality",
    "political_entity",
    "latitude",
    "longitude",
    "publication",
    "year_first_published",
    "full_date",
    "date_mean_bp",
    "date_stddev_bp",
    "time_start_bp",
    "time_end_bp",
    "time_mean_bp",
    "time_label",
    "dating_basis",
    "coordinate_confidence",
    "data_type",
    "molecular_sex",
    "datasets",
    "accession_lineage",
)
SAMPLE_EXPORT_FIELDS = (
    *LEGACY_SAMPLE_EXPORT_FIELDS,
    "sample_chronology",
    "sample_identity",
)
SAMPLE_RECORD_SCHEMA = "adna-sample-record-export.v2"
LEGACY_SAMPLE_RECORD_SCHEMA = "adna-sample-record-export.v1"


LOCALITY_EXPORT_FIELDS = (
    "schema_version",
    "species_latin_name",
    "species_common_name",
    "source_family",
    "sample_namespace",
    "locality",
    "latitude",
    "longitude",
    "sample_count",
    "time_start_bp",
    "time_end_bp",
    "time_mean_bp",
    "time_label",
    "dating_basis",
    "coordinate_confidence",
    "datasets",
    "sample_ids",
    "chronology_role",
    "sample_chronologies",
    "locality_identity",
    "political_entity",
)


def serialize_sample_record(
    sample: SampleRecord, *, schema_version: str = SAMPLE_RECORD_SCHEMA
) -> dict[str, object]:
    """Export owned chronology and identity; v1 is an explicit lossy legacy view."""
    _sample_export_fields(schema_version)
    payload: dict[str, object] = {
        "schema_version": schema_version,
        "species_latin_name": sample.species_latin_name,
        "species_common_name": sample.species_common_name,
        "source_family": sample.source_family,
        "sample_namespace": sample.sample_namespace,
        "genetic_id": sample.genetic_id,
        "master_id": sample.master_id,
        "group_id": sample.group_id,
        "locality": sample.locality,
        "political_entity": sample.political_entity,
        "latitude": sample.latitude_text,
        "longitude": sample.longitude_text,
        "publication": sample.publication,
        "year_first_published": sample.year_first_published,
        "full_date": sample.full_date,
        "date_mean_bp": sample.date_mean_bp,
        "date_stddev_bp": sample.date_stddev_bp,
        "time_start_bp": sample.time_start_bp,
        "time_end_bp": sample.time_end_bp,
        "time_mean_bp": sample.time_mean_bp,
        "time_label": sample.time_label,
        "dating_basis": sample.dating_basis,
        "coordinate_confidence": sample.coordinate_confidence,
        "data_type": sample.data_type,
        "molecular_sex": sample.molecular_sex,
        "datasets": list(sample.datasets),
        "accession_lineage": list(sample.accession_lineage),
    }
    if schema_version == LEGACY_SAMPLE_RECORD_SCHEMA:
        return payload
    payload["sample_chronology"] = AdnaSampleChronologySupport(
        sample_id=sample.genetic_id,
        chronology=sample.chronology,
        source_release=sample.source_release,
        provenance_path=sample.chronology_provenance_path,
        provenance_locator=sample.chronology_provenance_locator,
        provenance_excerpt=sample.chronology_provenance_text,
        provenance_kind=sample.chronology_provenance_kind,
        chronology_strength=sample.chronology_strength,
        normalization_status=sample.chronology_normalization_status,
        conflict_note=sample.chronology_conflict_note,
    ).as_dict()
    payload["sample_identity"] = {
        "namespace": sample.sample_namespace,
        "stable_token": sample.genetic_id,
        "accession_lineage": list(sample.accession_lineage),
        "master_id": sample.master_id,
        "group_id": sample.group_id,
        "archive_native_sample_id": sample.archive_native_sample_id,
        "archive_native_experiment_id": sample.archive_native_experiment_id,
        "paper_native_sample_label": sample.paper_native_sample_label,
        "supplementary_table_sample_label": sample.supplementary_table_sample_label,
        "source_native_identity_kind": sample.source_native_identity_kind,
        "source_native_tax_id": sample.source_native_tax_id,
        "source_native_scientific_name": sample.source_native_scientific_name,
        "project_accession": sample.project_accession,
        "sample_basis": sample.sample_basis,
        "sample_evidence_status": sample.sample_evidence_status,
        "sample_identity_resolution": sample.sample_identity_resolution,
        "sample_ambiguity_note": sample.sample_ambiguity_note,
        "sample_lineage_path": sample.sample_lineage_path,
        "sample_lineage_locator": sample.sample_lineage_locator,
        "sample_lineage_excerpt": sample.sample_lineage_excerpt,
    }
    return payload


def _sample_export_fields(schema_version: str) -> tuple[str, ...]:
    if schema_version == SAMPLE_RECORD_SCHEMA:
        return SAMPLE_EXPORT_FIELDS
    if schema_version == LEGACY_SAMPLE_RECORD_SCHEMA:
        return LEGACY_SAMPLE_EXPORT_FIELDS
    raise ValueError("Unsupported sample export schema")


def serialize_locality_summary(locality: LocalitySummary) -> dict[str, object]:
    """Serialize one locality summary into the shared export contract."""
    return {
        "schema_version": "adna-locality-summary-export.v2",
        "locality_identity": locality.identity.as_dict(),
        "political_entity": locality.identity.political_entity,
        "species_latin_name": locality.species_latin_name,
        "species_common_name": locality.species_common_name,
        "source_family": locality.source_family,
        "sample_namespace": locality.sample_namespace,
        "locality": locality.locality,
        "latitude": locality.latitude_text,
        "longitude": locality.longitude_text,
        "sample_count": locality.sample_count,
        "time_start_bp": locality.time_start_bp,
        "time_end_bp": locality.time_end_bp,
        "time_mean_bp": locality.time_mean_bp,
        "time_label": locality.time_label,
        "dating_basis": locality.dating_basis,
        "coordinate_confidence": locality.coordinate_confidence,
        "datasets": list(locality.datasets),
        "sample_ids": list(locality.sample_ids),
        "chronology_role": "locality_sample_coverage_hull",
        "sample_chronologies": [row.as_dict() for row in locality.sample_chronologies],
    }


def build_sample_geojson_feature(
    sample: SampleRecord, *, schema_version: str = "adna-sample-geojson.v2"
) -> dict[str, object]:
    """Build one GeoJSON feature with an explicitly versioned sample contract."""
    if schema_version not in {"adna-sample-geojson.v1", "adna-sample-geojson.v2"}:
        raise ValueError("Unsupported sample GeoJSON schema")
    record_schema = (
        LEGACY_SAMPLE_RECORD_SCHEMA
        if schema_version == "adna-sample-geojson.v1"
        else SAMPLE_RECORD_SCHEMA
    )
    properties = serialize_sample_record(sample, schema_version=record_schema)
    properties["datasets"] = list(sample.datasets)
    return {
        "schema_version": schema_version,
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [sample.longitude, sample.latitude],
        },
        "properties": properties,
    }


def build_samples_geojson(
    samples: Iterable[SampleRecord],
    *,
    schema_version: str = "adna-sample-geojson-collection.v2",
) -> dict[str, object]:
    """Build a GeoJSON collection with matching feature/property schema versions."""
    if schema_version not in {
        "adna-sample-geojson-collection.v1",
        "adna-sample-geojson-collection.v2",
    }:
        raise ValueError("Unsupported sample GeoJSON collection schema")
    feature_schema = (
        "adna-sample-geojson.v1"
        if schema_version == "adna-sample-geojson-collection.v1"
        else "adna-sample-geojson.v2"
    )
    features = []
    for sample in samples:
        features.append(
            build_sample_geojson_feature(sample, schema_version=feature_schema)
        )
    return {
        "schema_version": schema_version,
        "type": "FeatureCollection",
        "features": features,
    }


def write_samples_csv(
    path: Path,
    samples: Iterable[SampleRecord],
    *,
    schema_version: str = SAMPLE_RECORD_SCHEMA,
) -> None:
    """Write v2 metadata as JSON-valued cells; preserve explicit legacy v1 rows."""
    fields = _sample_export_fields(schema_version)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(fields),
            lineterminator="\n",
        )
        writer.writeheader()
        for sample in samples:
            payload = serialize_sample_record(sample, schema_version=schema_version)
            if schema_version == SAMPLE_RECORD_SCHEMA:
                for key in ("sample_chronology", "sample_identity"):
                    payload[key] = json.dumps(
                        payload[key],
                        ensure_ascii=False,
                        allow_nan=False,
                        separators=(",", ":"),
                    )
            payload["datasets"] = ",".join(sample.datasets)
            payload["accession_lineage"] = ";".join(sample.accession_lineage)
            writer.writerow(payload)


def write_localities_csv(path: Path, localities: Iterable[LocalitySummary]) -> None:
    """Write the locality-level aggregation as CSV."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(LOCALITY_EXPORT_FIELDS),
            lineterminator="\n",
        )
        writer.writeheader()
        for locality in localities:
            payload = serialize_locality_summary(locality)
            payload["datasets"] = ",".join(locality.datasets)
            payload["sample_ids"] = ";".join(locality.sample_ids)
            for key in ("sample_chronologies", "locality_identity"):
                payload[key] = json.dumps(
                    payload[key],
                    ensure_ascii=False,
                    allow_nan=False,
                    separators=(",", ":"),
                )
            writer.writerow(payload)


def write_samples_geojson(
    path: Path,
    samples: Iterable[SampleRecord],
    *,
    schema_version: str = "adna-sample-geojson-collection.v2",
) -> None:
    """Write matching versioned map-ready sample chronology and identity."""
    path.write_text(
        json.dumps(
            build_samples_geojson(samples, schema_version=schema_version),
            indent=2,
            ensure_ascii=schema_version == "adna-sample-geojson-collection.v1",
            allow_nan=False,
        ),
        encoding="utf-8",
    )
