from __future__ import annotations

from collections.abc import Iterable
import copy

from .merging import (
    collection_unit_sort_key,
    normalize_collection_units,
    normalize_datasets,
    sort_datasets,
)
from .summaries import (
    count_neotoma_dataset_analysis_units,
    count_neotoma_dataset_chronologies,
    count_neotoma_dataset_samples,
    count_neotoma_dataset_taxa,
)


def build_neotoma_site_snapshot_rows(
    rows: Iterable[dict[str, object]],
) -> list[dict[str, object]]:
    """Build compact site-summary rows without duplicating full sample payloads."""
    snapshot_rows: list[dict[str, object]] = []
    for row in rows:
        snapshot = copy.deepcopy(row)
        snapshot_units = []
        for unit in normalize_collection_units(snapshot.get("collectionunits")):
            snapshot_unit: dict[str, object] = {
                key: copy.deepcopy(value)
                for key, value in unit.items()
                if key != "datasets"
            }
            snapshot_datasets = [
                build_neotoma_dataset_snapshot(dataset)
                for dataset in normalize_datasets(unit.get("datasets"))
            ]
            snapshot_unit["datasets"] = sort_datasets(snapshot_datasets)
            snapshot_units.append(snapshot_unit)
        snapshot["collectionunits"] = sorted(
            snapshot_units, key=collection_unit_sort_key
        )
        snapshot_rows.append(snapshot)
    return snapshot_rows


def build_neotoma_dataset_snapshot(dataset: dict[str, object]) -> dict[str, object]:
    """Build a compact dataset summary without nested samples or chronologies."""
    snapshot = {
        key: copy.deepcopy(value)
        for key, value in dataset.items()
        if key not in {"samples", "chronologies", "defaultchronology"}
    }
    snapshot["sample_count"] = count_neotoma_dataset_samples(dataset)
    snapshot["analysis_unit_count"] = count_neotoma_dataset_analysis_units(dataset)
    snapshot["chronology_count"] = count_neotoma_dataset_chronologies(dataset)
    snapshot["taxon_count"] = count_neotoma_dataset_taxa(dataset)
    return snapshot
