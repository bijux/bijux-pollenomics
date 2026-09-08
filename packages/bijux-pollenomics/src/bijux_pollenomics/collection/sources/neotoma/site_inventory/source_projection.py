from __future__ import annotations

import copy


def build_neotoma_site_row_from_download(
    download_row: object,
) -> dict[str, object] | None:
    """Project one full dataset download into the site structure used downstream."""
    if not isinstance(download_row, dict):
        return None
    site = download_row.get("site")
    if not isinstance(site, dict):
        return None

    row = {
        key: copy.deepcopy(value)
        for key, value in site.items()
        if key not in {"dataset", "collectionunit", "chronologies", "defaultchronology"}
    }
    dataset = build_neotoma_dataset_from_download(site)
    collection_unit = build_neotoma_collection_unit_from_download(site, dataset)
    row["collectionunits"] = [collection_unit] if collection_unit is not None else []
    return row


def build_neotoma_collection_unit_from_download(
    site: dict[str, object],
    dataset: dict[str, object] | None,
) -> dict[str, object] | None:
    """Normalize one collection unit from the full dataset download response."""
    collection_unit = site.get("collectionunit")
    if not isinstance(collection_unit, dict):
        return None
    row = {
        "collectionunitid": copy.deepcopy(collection_unit.get("collectionunitid")),
        "collectionunit": copy.deepcopy(collection_unit.get("collectionunit")),
        "handle": copy.deepcopy(collection_unit.get("handle")),
        "collectionunittype": copy.deepcopy(collection_unit.get("collunittype")),
        "collectiondevice": copy.deepcopy(collection_unit.get("collectiondevice")),
        "depositionalenvironment": copy.deepcopy(
            collection_unit.get("depositionalenvironment")
        ),
        "location": copy.deepcopy(collection_unit.get("location")),
        "notes": copy.deepcopy(collection_unit.get("notes")),
        "waterdepth": copy.deepcopy(collection_unit.get("waterdepth")),
        "datasets": [dataset] if dataset is not None else [],
    }
    gps_location = collection_unit.get("gpslocation")
    if isinstance(gps_location, dict):
        row["gpslocation"] = copy.deepcopy(gps_location)
    return row


def build_neotoma_dataset_from_download(
    site: dict[str, object],
) -> dict[str, object] | None:
    """Normalize one dataset record from the full dataset download response."""
    collection_unit = site.get("collectionunit")
    if isinstance(collection_unit, dict) and isinstance(
        collection_unit.get("dataset"), dict
    ):
        dataset = {
            key: copy.deepcopy(value)
            for key, value in collection_unit["dataset"].items()
        }
    elif isinstance(site.get("dataset"), dict):
        site_dataset = site.get("dataset")
        if not isinstance(site_dataset, dict):
            return None
        dataset = {key: copy.deepcopy(value) for key, value in site_dataset.items()}
    else:
        return None
    chronology_owner = collection_unit if isinstance(collection_unit, dict) else site
    chronologies = chronology_owner.get("chronologies")
    default_chronology = chronology_owner.get("defaultchronology")
    if chronologies is None:
        chronologies = site.get("chronologies", [])
    if default_chronology is None:
        default_chronology = site.get("defaultchronology")
    dataset["chronologies"] = copy.deepcopy(chronologies)
    dataset["defaultchronology"] = copy.deepcopy(default_chronology)
    return dataset
