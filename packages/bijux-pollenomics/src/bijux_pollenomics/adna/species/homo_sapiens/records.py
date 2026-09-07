"""AADR annotation-row parsing into canonical Homo sapiens records."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
import csv
from pathlib import Path

from bijux_pollenomics.adna.domain.locality import build_locality_identity
from bijux_pollenomics.adna.domain.models import (
    AdnaChronology,
    AdnaCoordinate,
    AdnaSampleIdentity,
    AdnaSampleRecord,
)
from bijux_pollenomics.adna.species.homo_sapiens_schema import (
    resolve_homo_sapiens_schema,
    sample_time_interval,
    sample_time_label,
    sample_time_mean,
    schema_value,
)
from bijux_pollenomics.core.temporal_semantics import admit_bp_interval

from .text import clean_text


def iter_homo_sapiens_samples_from_anno(
    path: Path,
    *,
    dataset_name: str,
    source_release: str,
    source_family: str,
    record_modality: str,
    review_strength: str,
    provenance_quality: str,
) -> Iterable[AdnaSampleRecord]:
    """Yield normalized Homo sapiens sample records from one AADR anno file."""
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        schema = resolve_homo_sapiens_schema(reader.fieldnames or ())
        for row in reader:
            record = _parse_sample_row(
                row,
                schema=schema,
                dataset_name=dataset_name,
                source_release=source_release,
                source_family=source_family,
                record_modality=record_modality,
                review_strength=review_strength,
                provenance_quality=provenance_quality,
            )
            if record is not None:
                yield record


def _parse_sample_row(
    row: Mapping[str, str],
    *,
    schema: Mapping[str, str | None],
    dataset_name: str,
    source_release: str,
    source_family: str,
    record_modality: str,
    review_strength: str,
    provenance_quality: str,
) -> AdnaSampleRecord | None:
    genetic_id = clean_text(schema_value(row, schema, "genetic_id"))
    latitude_text = clean_text(schema_value(row, schema, "latitude"))
    longitude_text = clean_text(schema_value(row, schema, "longitude"))
    if not genetic_id or not latitude_text or not longitude_text:
        return None
    try:
        latitude = float(latitude_text)
        longitude = float(longitude_text)
    except ValueError:
        return None
    source_time_interval = sample_time_interval(row, schema)
    time_admission = admit_bp_interval(
        source_time_interval[0] if source_time_interval is not None else None,
        source_time_interval[1] if source_time_interval is not None else None,
    )
    time_interval = time_admission.as_tuple()
    locality = clean_text(schema_value(row, schema, "locality")) or (
        "Unspecified locality"
    )
    political_entity = clean_text(schema_value(row, schema, "political_entity"))
    return AdnaSampleRecord(
        identity=AdnaSampleIdentity(
            namespace="homo_sapiens:aadr_genetic_id",
            stable_token=genetic_id,
            accession_lineage=(
                "species:Homo sapiens",
                f"source:{source_family}",
                f"release:{source_release}",
                f"dataset:{dataset_name}",
                f"genetic_id:{genetic_id}",
            ),
        ),
        locality_identity=build_locality_identity(
            species_name="Homo sapiens",
            source_family=source_family,
            locality_text=locality,
            political_entity=political_entity,
            latitude_text=latitude_text,
            longitude_text=longitude_text,
        ),
        species_latin_name="Homo sapiens",
        species_common_name="human",
        source_family=source_family,
        source_release=source_release,
        record_modality=record_modality,
        review_strength=review_strength,
        provenance_quality=provenance_quality,
        master_id=clean_text(schema_value(row, schema, "master_id")),
        group_id=clean_text(schema_value(row, schema, "group_id")),
        locality=locality,
        political_entity=political_entity,
        coordinates=AdnaCoordinate(
            latitude=latitude,
            longitude=longitude,
            latitude_text=latitude_text,
            longitude_text=longitude_text,
            confidence="unknown",
        ),
        publication=clean_text(schema_value(row, schema, "publication")),
        year_first_published=clean_text(
            schema_value(row, schema, "year_first_published")
        ),
        full_date=clean_text(schema_value(row, schema, "full_date")),
        chronology=AdnaChronology(
            original_text=sample_time_label(row, schema),
            time_start_bp=time_interval[0] if time_interval is not None else None,
            time_end_bp=time_interval[1] if time_interval is not None else None,
            time_mean_bp=(
                sample_time_mean(row, schema) if time_admission.admitted else None
            ),
            date_stddev_bp=clean_text(schema_value(row, schema, "date_stddev_bp")),
            source_mean_bp_text=clean_text(schema_value(row, schema, "date_mean_bp")),
            dating_basis=_dating_basis(row, schema, source_time_interval),
            evidence_class=(
                "direct_numeric_sample_date"
                if source_time_interval is not None
                else "unresolved"
            ),
            precision_posture=(
                "sample_precise_interval"
                if source_time_interval is not None
                else "unresolved"
            ),
            refusal_reason_code=time_admission.refusal_reason_code,
        ),
        data_type=clean_text(schema_value(row, schema, "data_type")),
        molecular_sex=clean_text(schema_value(row, schema, "molecular_sex")),
        datasets=(dataset_name,),
    )


def dating_basis(
    row: Mapping[str, str],
    schema: Mapping[str, str | None],
    time_interval: tuple[int, int] | None,
) -> str:
    """Classify chronology evidence without coercing absent time to zero."""
    if time_interval is not None and clean_text(
        schema_value(row, schema, "date_stddev_bp")
    ):
        return "bp_mean_and_stddev"
    if time_interval is not None:
        return "bp_window"
    if clean_text(schema_value(row, schema, "full_date")):
        return "archaeological_period"
    return "unknown"


_dating_basis = dating_basis
