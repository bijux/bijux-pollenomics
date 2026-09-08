from __future__ import annotations

from bijux_pollenomics.core.text import clean_optional_text

from ..chronology import AgeRangeAggregate, merge_age_ranges
from .merging import (
    dataset_key,
    normalize_chronologies,
    normalize_collection_units,
    normalize_datasets,
    sort_datasets,
)


def populate_neotoma_site_summary_fields(row: dict[str, object]) -> None:
    """Populate denormalized summary fields used by raw artifacts and map popups."""
    collection_units = normalize_collection_units(row.get("collectionunits"))
    datasets = [
        dataset
        for unit in collection_units
        for dataset in normalize_datasets(unit.get("datasets"))
    ]
    row["collectionunits"] = collection_units
    row["dataset_count"] = len({dataset_key(dataset) for dataset in datasets})
    row["dataset_ids"] = [
        clean_optional_text(dataset.get("datasetid"))
        for dataset in sort_datasets(datasets)
        if clean_optional_text(dataset.get("datasetid"))
    ]
    row["dataset_types"] = sorted(
        {
            clean_optional_text(dataset.get("datasettype"))
            for dataset in datasets
            if clean_optional_text(dataset.get("datasettype"))
        }
    )
    row["databases"] = sorted(
        {
            clean_optional_text(dataset.get("database"))
            for dataset in datasets
            if clean_optional_text(dataset.get("database"))
        }
    )

    sample_ids: set[str] = set()
    analysis_unit_ids: set[str] = set()
    chronology_ids: set[str] = set()
    taxon_keys: set[tuple[str, str]] = set()
    age_ranges_by_units: dict[str, AgeRangeAggregate] = {}

    for dataset in datasets:
        for chronology in normalize_chronologies(dataset.get("chronologies")):
            chronology_id = chronology_key(chronology)
            if chronology_id:
                chronology_ids.add(chronology_id)

        merge_age_ranges(age_ranges_by_units, dataset.get("agerange"))

        samples = dataset.get("samples", [])
        if not isinstance(samples, list):
            continue
        for sample in samples:
            if not isinstance(sample, dict):
                continue
            sample_id = clean_optional_text(sample.get("sampleid"))
            if sample_id:
                sample_ids.add(sample_id)
            analysis_unit_id = clean_optional_text(sample.get("analysisunitid"))
            if analysis_unit_id:
                analysis_unit_ids.add(analysis_unit_id)
            merge_age_ranges(age_ranges_by_units, sample.get("ages"))
            datum = sample.get("datum", [])
            if not isinstance(datum, list):
                continue
            for item in datum:
                if not isinstance(item, dict):
                    continue
                taxon_id = clean_optional_text(item.get("taxonid"))
                variable_name = clean_optional_text(item.get("variablename"))
                if taxon_id or variable_name:
                    taxon_keys.add((taxon_id, variable_name))

    row["sample_count"] = len(sample_ids)
    row["analysis_unit_count"] = len(analysis_unit_ids)
    row["chronology_count"] = len(chronology_ids)
    row["taxon_count"] = len(taxon_keys)
    row["age_ranges"] = sorted(
        age_ranges_by_units.values(),
        key=lambda item: clean_optional_text(item.get("units")),
    )


def count_neotoma_dataset_samples(dataset: dict[str, object]) -> int:
    """Count unique samples in one Neotoma dataset payload."""
    samples = dataset.get("samples", [])
    if not isinstance(samples, list):
        return 0
    return len(
        {
            clean_optional_text(sample.get("sampleid"))
            for sample in samples
            if isinstance(sample, dict) and clean_optional_text(sample.get("sampleid"))
        }
    )


def count_neotoma_dataset_analysis_units(dataset: dict[str, object]) -> int:
    """Count unique analysis units in one Neotoma dataset payload."""
    samples = dataset.get("samples", [])
    if not isinstance(samples, list):
        return 0
    return len(
        {
            clean_optional_text(sample.get("analysisunitid"))
            for sample in samples
            if isinstance(sample, dict)
            and clean_optional_text(sample.get("analysisunitid"))
        }
    )


def count_neotoma_dataset_chronologies(dataset: dict[str, object]) -> int:
    """Count unique chronologies in one Neotoma dataset payload."""
    return len(
        {
            chronology_key(chronology)
            for chronology in normalize_chronologies(dataset.get("chronologies"))
            if chronology_key(chronology)
        }
    )


def count_neotoma_dataset_taxa(dataset: dict[str, object]) -> int:
    """Count unique taxa in one Neotoma dataset payload."""
    samples = dataset.get("samples", [])
    if not isinstance(samples, list):
        return 0
    taxon_keys: set[tuple[str, str]] = set()
    for sample in samples:
        if not isinstance(sample, dict):
            continue
        datum = sample.get("datum", [])
        if not isinstance(datum, list):
            continue
        for item in datum:
            if not isinstance(item, dict):
                continue
            taxon_id = clean_optional_text(item.get("taxonid"))
            variable_name = clean_optional_text(item.get("variablename"))
            if taxon_id or variable_name:
                taxon_keys.add((taxon_id, variable_name))
    return len(taxon_keys)


def chronology_key(chronology: dict[str, object]) -> str:
    """Build a stable identity key for one chronology payload."""
    chronology_id = clean_optional_text(chronology.get("chronologyid"))
    if chronology_id:
        return chronology_id
    nested = chronology.get("chronology")
    if isinstance(nested, dict):
        return clean_optional_text(nested.get("chronologyid"))
    return ""
