from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
import csv
from pathlib import Path

from ...adna import (
    AdnaChronology,
    AdnaCoordinate,
    AdnaSampleIdentity,
    AdnaSampleRecord,
    resolve_species_definition,
)
from ...core.bp_time import build_bp_interval_label, midpoint_bp_year
from ..shared.merge import pick_value
from ..shared.text import clean_text
from .schema import (
    resolve_schema,
    sample_time_interval,
    sample_time_label,
    sample_time_mean,
)

__all__ = [
    "discover_anno_files",
    "iter_samples_from_anno",
    "load_country_samples",
]

HOMO_SAPIENS_SPECIES = resolve_species_definition("Homo sapiens")


def load_country_samples(
    version_dir: Path, country: str
) -> tuple[list[AdnaSampleRecord], Counter[str]]:
    """Load and deduplicate all samples for a country across every anno file in a version directory."""
    combined: dict[str, AdnaSampleRecord] = {}
    dataset_counts: Counter[str] = Counter()
    country_key = country.strip().casefold()

    for anno_path in discover_anno_files(version_dir):
        dataset_name = anno_path.parent.name
        for sample in iter_samples_from_anno(anno_path, dataset_name):
            if sample.political_entity.casefold() != country_key:
                continue
            dataset_counts[dataset_name] += 1
            existing = combined.get(sample.genetic_id)
            if existing is None:
                combined[sample.genetic_id] = sample
                continue
            combined[sample.genetic_id] = merge_duplicate_samples(existing, sample)

    samples = sorted(
        combined.values(),
        key=lambda sample: (
            sample.locality.casefold(),
            sample.master_id.casefold(),
            sample.genetic_id.casefold(),
        ),
    )
    return samples, dataset_counts


def discover_anno_files(version_dir: Path) -> list[Path]:
    """Find all public anno files for a given AADR version directory."""
    files = sorted(path for path in version_dir.glob("*/*.anno") if path.is_file())
    if not files:
        raise FileNotFoundError(f"No .anno files found under {version_dir}")
    return files


def iter_samples_from_anno(path: Path, dataset_name: str) -> Iterable[AdnaSampleRecord]:
    """Yield normalized sample records from a single AADR anno file."""
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        schema = resolve_schema(reader.fieldnames or ())
        for row in reader:
            genetic_id = clean_text(schema_value(row, schema, "genetic_id"))
            latitude_text = clean_text(schema_value(row, schema, "latitude"))
            longitude_text = clean_text(schema_value(row, schema, "longitude"))
            if not genetic_id or not latitude_text or not longitude_text:
                continue
            try:
                latitude = float(latitude_text)
                longitude = float(longitude_text)
            except ValueError:
                continue
            time_interval = sample_time_interval(row, schema)
            yield AdnaSampleRecord(
                identity=AdnaSampleIdentity(
                    namespace="homo_sapiens:aadr_genetic_id",
                    stable_token=genetic_id,
                    accession_lineage=(
                        "species:Homo sapiens",
                        "source:AADR",
                        f"dataset:{dataset_name}",
                        f"genetic_id:{genetic_id}",
                    ),
                ),
                species_latin_name=HOMO_SAPIENS_SPECIES.latin_name,
                species_common_name=HOMO_SAPIENS_SPECIES.common_name,
                source_family="AADR",
                master_id=clean_text(schema_value(row, schema, "master_id")),
                group_id=clean_text(schema_value(row, schema, "group_id")),
                locality=clean_text(schema_value(row, schema, "locality"))
                or "Unspecified locality",
                political_entity=clean_text(
                    schema_value(row, schema, "political_entity")
                ),
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
                    time_mean_bp=sample_time_mean(row, schema),
                    date_stddev_bp=clean_text(
                        schema_value(row, schema, "date_stddev_bp")
                    ),
                    dating_basis=_dating_basis(row, schema, time_interval),
                ),
                data_type=clean_text(schema_value(row, schema, "data_type")),
                molecular_sex=clean_text(schema_value(row, schema, "molecular_sex")),
                datasets=(dataset_name,),
            )


def merge_duplicate_samples(
    existing: AdnaSampleRecord, sample: AdnaSampleRecord
) -> AdnaSampleRecord:
    """Merge duplicate AADR sample rows across datasets."""
    merged_datasets = tuple(sorted(set(existing.datasets) | set(sample.datasets)))
    merged_interval = merge_sample_time_interval(existing, sample)
    return AdnaSampleRecord(
        identity=AdnaSampleIdentity(
            namespace=existing.sample_namespace,
            stable_token=existing.genetic_id,
            accession_lineage=tuple(
                dict.fromkeys(existing.accession_lineage + sample.accession_lineage)
            ),
        ),
        species_latin_name=existing.species_latin_name,
        species_common_name=existing.species_common_name,
        source_family=existing.source_family,
        master_id=pick_value(existing.master_id, sample.master_id),
        group_id=pick_value(existing.group_id, sample.group_id),
        locality=pick_value(existing.locality, sample.locality),
        political_entity=pick_value(existing.political_entity, sample.political_entity),
        coordinates=AdnaCoordinate(
            latitude=existing.latitude,
            longitude=existing.longitude,
            latitude_text=pick_value(existing.latitude_text, sample.latitude_text),
            longitude_text=pick_value(existing.longitude_text, sample.longitude_text),
            confidence=pick_value(
                existing.coordinate_confidence, sample.coordinate_confidence
            )
            or "unknown",
        ),
        publication=pick_value(existing.publication, sample.publication),
        year_first_published=pick_value(
            existing.year_first_published, sample.year_first_published
        ),
        full_date=pick_value(existing.full_date, sample.full_date),
        chronology=AdnaChronology(
            original_text=pick_time_label(existing, sample, merged_interval),
            time_start_bp=merged_interval[0] if merged_interval is not None else None,
            time_end_bp=merged_interval[1] if merged_interval is not None else None,
            time_mean_bp=mean_bp_from_samples(existing, sample, merged_interval),
            date_stddev_bp=pick_value(existing.date_stddev_bp, sample.date_stddev_bp),
            dating_basis=pick_value(existing.dating_basis, sample.dating_basis)
            or "unknown",
        ),
        data_type=pick_value(existing.data_type, sample.data_type),
        molecular_sex=pick_value(existing.molecular_sex, sample.molecular_sex),
        datasets=merged_datasets,
    )


def merge_sample_time_interval(
    left: AdnaSampleRecord, right: AdnaSampleRecord
) -> tuple[int, int] | None:
    """Merge two sample intervals into a single BP span."""
    intervals = [
        interval
        for interval in (
            (left.time_start_bp, left.time_end_bp)
            if left.time_start_bp is not None and left.time_end_bp is not None
            else None,
            (right.time_start_bp, right.time_end_bp)
            if right.time_start_bp is not None and right.time_end_bp is not None
            else None,
        )
        if interval is not None
    ]
    if not intervals:
        return None
    return (min(start for start, _ in intervals), max(end for _, end in intervals))


def mean_bp_from_samples(
    left: AdnaSampleRecord,
    right: AdnaSampleRecord,
    merged_interval: tuple[int, int] | None,
) -> int | None:
    """Choose the best AADR midpoint for merged duplicate samples."""
    for value in (left.time_mean_bp, right.time_mean_bp):
        if value is not None:
            return value
    if merged_interval is None:
        return None
    return midpoint_bp_year(merged_interval[0], merged_interval[1])


def pick_time_label(
    left: AdnaSampleRecord,
    right: AdnaSampleRecord,
    merged_interval: tuple[int, int] | None,
) -> str:
    """Prefer explicit AADR date labels before falling back to a BP interval label."""
    for value in (left.time_label, right.time_label, left.full_date, right.full_date):
        if clean_text(value):
            return clean_text(value)
    if merged_interval is None:
        return ""
    return build_bp_interval_label(merged_interval[0], merged_interval[1])


def _dating_basis(
    row: Mapping[str, str],
    schema: Mapping[str, str | None],
    time_interval: tuple[int, int] | None,
) -> str:
    """Infer the strongest dating basis available from one AADR row."""
    if time_interval is not None and clean_text(schema_value(row, schema, "date_stddev_bp")):
        return "bp_mean_and_stddev"
    if time_interval is not None:
        return "bp_window"
    return "unknown"


def schema_value(
    row: Mapping[str, str], schema: Mapping[str, str | None], key: str
) -> str:
    """Read one row value via a schema key while handling optional schema columns."""
    column_name = schema.get(key)
    if not column_name:
        return ""
    return row.get(column_name, "")
