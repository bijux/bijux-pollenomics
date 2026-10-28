"""Rejoin metadata identities independently of the maintained report producer."""

from __future__ import annotations

import csv
import hashlib
import io
from pathlib import Path
import re
from typing import Any
import xml.etree.ElementTree as ET

from contracts import exact, load, require, sha

PROFILES = {
    "ADRAN": 738941,
    "GARASEL": 739248,
    "HAKULLA5": 711892,
    "LEVEANIE": 739449,
    "NDRAKET": 739584,
    "VUOLEPAL": 889510,
}
RELATIONAL = Path("data/neotoma/relational")
FAMILY = Path("docs/report/source-relations/neotoma/swedish-cohort-availability")
TOP_SCOPE = "Metadata-only current Neotoma Sweden query and two PANGAEA leads; no pollen observation or count table opened. A different EPD-only core and its selected calibrated sample ages may exist outside these checked metadata surfaces."
EPD_SCOPE = "PANGAEA title metadata search, seven profile metadata records, six handle-related metadata searches, Giesecke final-age event inventory, Fyfe chronology reference and LegacyAge site identity table. All retained Neotoma core handles were checked, including UNASSIGNED country rows. No pollen observation/count table opened; absent exact handle is not proof of distinct physical site."


def title(hit: dict[str, Any]) -> str:
    root = ET.fromstring(hit["_source"]["xml-thumb"])
    values = [
        element.text
        for element in root.iter()
        if element.tag == "{http://www.pangaea.de/MetaData}title"
    ]
    require(
        len(values) >= 1 and isinstance(values[0], str) and bool(values[0]),
        "Metadata title required",
    )
    assert isinstance(values[0], str)
    return values[0]


def profile_handle(text: str) -> str | None:
    prefix = "Pollen profile "
    if not text.startswith(prefix):
        return None
    remainder = text[len(prefix) :].removeprefix("of sediment core ")
    token = re.split(r"[, ]", remainder, maxsplit=1)
    if len(token) != 2 or re.fullmatch(r"[A-Z][A-Z0-9_-]+", token[0]) is None:
        return None
    return token[0]


def title_screen(
    search: dict[str, Any], handles: dict[str, dict[str, Any]]
) -> tuple[int, dict[str, int], dict[str, int], list[int]]:
    hits = search["hits"]["hits"]
    require(
        search["timed_out"] is False
        and type(search["hits"]["total"]) is int
        and search["hits"]["total"] == len(hits) == 66,
        "Complete metadata title population required",
    )
    ids = [int(hit["_id"]) for hit in hits]
    require(len(ids) == len(set(ids)), "Duplicate metadata search DOI")
    retained = 0
    unmatched: dict[str, int] = {}
    named: dict[str, int] = {}
    generic = []
    for hit, doi in zip(hits, ids, strict=True):
        handle = profile_handle(title(hit))
        if handle is None:
            generic.append(doi)
        elif handle in handles:
            retained += 1
            if handle in PROFILES:
                named[handle] = doi
        else:
            require(handle not in unmatched, "Duplicate unmatched profile handle")
            unmatched[handle] = doi
    require(
        retained == 62
        and unmatched
        == {name: PROFILES[name] for name in ("ADRAN", "GARASEL", "LEVEANIE")}
        and named
        == {name: PROFILES[name] for name in ("HAKULLA5", "NDRAKET", "VUOLEPAL")}
        and generic == [761854],
        "Named/retained/generic metadata split differs",
    )
    return retained, unmatched, named, generic


def dataset_sites(records: list[dict[str, Any]]) -> set[int]:
    require(len(records) == 102, "Complete current dataset inventory required")
    datasets = [row["datasetid"] for row in records]
    sites = [row["site"]["siteid"] for row in records]
    require(
        all(type(value) is int for value in [*datasets, *sites])
        and len(set(datasets)) == 102
        and len(set(sites)) == 99,
        "Unique dataset/native site identities differ",
    )
    return set(sites)


def retained_identities(
    sites: list[dict[str, Any]],
    units: list[dict[str, Any]],
    datasets: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    site_lookup = {row["site_id"]: row for row in sites}
    require(len(site_lookup) == len(sites), "Duplicate retained site key")
    ds: dict[str, list[int]] = {}
    for row in datasets:
        require(
            type(row["source_dataset_id"]) is int, "Dataset native ID must be integer"
        )
        ds.setdefault(row["collection_unit_id"], []).append(row["source_dataset_id"])
    result = {}
    for unit in units:
        label = unit["source_payload"].get("handle")
        if not label:
            continue
        require(isinstance(label, str), "Core handle is not text")
        normalized = label.upper()
        require(normalized not in result, "Duplicate all-country core handle")
        site = site_lookup[unit["site_id"]]
        result[normalized] = {
            "neotoma_site_id": site["source_site_id"],
            "neotoma_core_id": unit["source_collection_unit_id"],
            "neotoma_pollen_dataset_ids": sorted(
                ds.get(unit["collection_unit_id"], [])
            ),
            "retained_country_code": site["country_code"],
            "source_geopolitical": site["source_payload"]["geopolitical"],
        }
    return result


def age_events(text: str) -> set[str]:
    header = text.split("*/", 1)[0]
    result = set()
    for line in header.splitlines():
        if "* LOCATION:" in line and "Sweden" in line:
            label = re.split(r"[\s(]", line.lstrip(), maxsplit=1)[0]
            require(bool(label), "Age metadata event label missing")
            result.add(label)
    return result


def table(text: str) -> list[dict[str, str]]:
    _, marker, body = text.partition("*/\n")
    require(bool(marker), "Metadata table header terminator missing")
    return list(csv.DictReader(io.StringIO(body), delimiter="\t"))


def report(repository: Path, private: Path) -> dict[str, Any]:
    declared = load(repository / FAMILY / "sources.json")
    primary = private / declared["private_source_subdir"]
    epd = private / declared["epd_private_source_subdir"]
    first, second = (
        load(primary / "source-manifest.json"),
        load(epd / "source-manifest.json"),
    )
    require(
        sha(primary / "source-manifest.json")
        == declared["private_source_manifest_sha256"]
        and sha(epd / "source-manifest.json") == declared["epd_source_manifest_sha256"],
        "Original metadata manifests differ",
    )
    require(
        first["schema_version"] == "swedish-cohort-metadata-source.v1"
        and exact(first["sources"], declared["sources"])
        and first["captured_at_utc"] == declared["source_capture_utc"]
        and second["schema_version"] == "swedish-epd-metadata-source.v1"
        and len(second["sources"]) == 17,
        "Complete source declaration/epoch differs",
    )
    for root, rows in ((primary, declared["sources"]), (private, second["sources"])):
        for row in rows:
            path = root / row["file"]
            require(
                path.stat().st_size == row["bytes"] and sha(path) == row["sha256"],
                "Metadata source identity differs",
            )
    rel = repository / RELATIONAL
    require(
        sha(rel / "manifest.json") == declared["relational_manifest_sha256"],
        "Relational source manifest differs",
    )
    registry = load(rel / "manifest.json")
    surfaces = {}
    for name in ("sites", "collection_units", "datasets"):
        (part,) = registry["surfaces"][name]["parts"]
        path = rel / part["path"]
        require(sha(path) == part["sha256"], "Relational part changed")
        surfaces[name] = load(path)["rows"]
    handles = retained_identities(
        surfaces["sites"], surfaces["collection_units"], surfaces["datasets"]
    )
    require(len(handles) == 206, "Complete all-country handle population differs")
    retained_sites = {row["source_site_id"] for row in surfaces["sites"]}
    inventory = load(primary / "neotoma-sweden-datasets-current.json")
    require(
        inventory["status"] == "success" and isinstance(inventory["data"], list),
        "Dataset metadata status differs",
    )
    site_ids = dataset_sites(inventory["data"])
    require(
        all(type(x) is int for x in site_ids)
        and len(inventory["data"]) == 102
        and len(site_ids) == 99,
        "Current102dataset/99site census differs",
    )
    retained, unmatched, named, generic = title_screen(
        load(epd / "pangaea-sweden-pollen-profiles.json"), handles
    )
    events = age_events(
        (private / "epd/pangaea/epd-age-cut-pangaea-804596.tsv").read_text()
    )
    require(
        len(events) == 37
        and events <= handles.keys()
        and not events.intersection(PROFILES),
        "Final-age37 event support differs",
    )
    chronological = [
        row
        for row in table((epd / "pangaea-core-chronologies-853943.tsv").read_text())
        if row["Event"] == "HAKULLA5"
    ]
    legacy = [
        row
        for row in table(
            (
                private
                / "epd/pangaea/legacyage-site-chronology-metadata-pangaea-933132.tsv"
            ).read_text()
        )
        if row["Event"] == "HAKULLA5"
    ]
    require(
        len(chronological) == len(legacy) == 1
        and chronological[0]["Reference"] == "EPD chron2"
        and legacy[0]["ID (Site)"] == "3138"
        and legacy[0]["ID (Dataset)"] == "4082"
        and legacy[0]["Reference (AgeModel)"] == "AWI",
        "Exact HAKULLA5 chronology-reference/native-ID join differs",
    )
    leads = []
    for handle, doi in sorted(PROFILES.items()):
        profile = load(epd / ("pangaea-" + handle.lower() + "-pollen-metadata.jsonld"))
        require(
            profile["identifier"] == f"https://doi.org/10.1594/PANGAEA.{doi}"
            and handle in profile["name"],
            "Profile handle/DOI differs",
        )
        related = load(epd / ("pangaea-" + handle.lower() + "-related-metadata.json"))
        require(
            related["timed_out"] is False
            and related["hits"]["total"] == len(related["hits"]["hits"]),
            "Related metadata search incomplete",
        )
        dated = sorted(
            int(hit["_id"])
            for hit in related["hits"]["hits"]
            if title(hit).startswith("Age determination of sediment core ")
            and handle in title(hit)
        )
        identity = handles.get(handle)
        require(
            identity is None
            or (
                identity["retained_country_code"] == "UNASSIGNED"
                and "Sweden" in identity["source_geopolitical"]
            ),
            "Swedish UNASSIGNED retained collision was dropped",
        )
        leads.append(
            {
                "core_handle": handle,
                "pangaea_pollen_doi": f"10.1594/PANGAEA.{doi}",
                "age_determination_metadata_dois": [
                    f"10.1594/PANGAEA.{x}" for x in dated
                ],
                "profile_license": profile.get("license"),
                "profile_conditions_of_access": profile.get("conditionsOfAccess"),
                "retained_neotoma_identity": identity,
                "in_checked_epd_final_age_events": False,
                "selected_sample_age_sequence_identified": False,
                "decision": "refused_as_fresh_retained_core_country_unassigned"
                if identity is not None
                else "metadata_lead_only_core_alias_and_selected_age_model_unresolved",
            }
        )
    require(
        load(epd / "pangaea-schonen-pollen-metadata.jsonld")["identifier"]
        == "https://doi.org/10.1594/PANGAEA.761854",
        "Generic unbound DOI differs",
    )
    cross = []
    for handle, doi, site, core, dataset, filename in (
        ("SAMBOTOT", 739778, 3398, 4262, 4403, "neotoma-sambosjon-site-metadata.json"),
        ("KLOT", 739382, 13336, 14908, 19909, "neotoma-klot-site-metadata.json"),
    ):
        profile = load(
            primary / ("pangaea-" + handle.lower() + "-pollen-metadata.jsonld")
        )
        require(
            profile["identifier"] == f"https://doi.org/10.1594/PANGAEA.{doi}"
            and handle in profile["name"],
            "Cross-archive metadata DOI/handle differs",
        )
        native = load(primary / filename)
        require(
            native["status"] == "success" and len(native["data"]) == 1,
            "Native site metadata response differs",
        )
        entry = native["data"][0]
        require(
            entry["siteid"] == site
            and any(
                unit["collectionunitid"] == core
                and unit["handle"] == handle
                and any(item["datasetid"] == dataset for item in unit["datasets"])
                for unit in entry["collectionunits"]
            ),
            "Complete site/core/dataset identity join differs",
        )
        geography = load_geo(entry["geography"])
        geo = profile["spatialCoverage"]["geo"]
        row = {
            "core_handle": handle,
            "pangaea_pollen_doi": f"10.1594/PANGAEA.{doi}",
            "neotoma_site_id": site,
            "neotoma_core_id": core,
            "neotoma_pollen_dataset_id": dataset,
            "pangaea_latitude_longitude": [geo["latitude"], geo["longitude"]],
            "neotoma_latitude_longitude": [geography[1], geography[0]],
            "decision": "refused_as_fresh_cohort_core_handle_collides_with_scored_retained_core"
            if handle == "SAMBOTOT"
            else "refused_as_fresh_cohort_core_handle_collides_with_retained_core",
        }
        if handle == "SAMBOTOT":
            dated = load(primary / "pangaea-sambotot-age-controls-metadata.jsonld")
            require(
                dated["identifier"] == "https://doi.org/10.1594/PANGAEA.740716"
                and handle in dated["name"],
                "Dated-control DOI differs",
            )
            fields = {x["name"] for x in dated["variableMeasured"]}
            require(
                {"DEPTH, sediment/rock", "Age, dated", "Age, dated, error to older"}
                <= fields
                and not any("calibrated" in x.lower() for x in fields)
                and "DEPTH, sediment/rock"
                in {x["name"] for x in profile["variableMeasured"]},
                "Dated-control metadata incorrectly promoted to selected calibrated ages",
            )
            row["pangaea_dated_control_doi"] = "10.1594/PANGAEA.740716"
            row["selected_calibrated_age_model_in_checked_pangaea_metadata"] = False
        cross.append(row)
    inventory_source = next(
        row
        for row in declared["sources"]
        if row["file"] == "neotoma-sweden-datasets-current.json"
    )
    return {
        "schema_version": "swedish-cohort-availability.v1",
        "source_capture_utc": first["captured_at_utc"],
        "private_source_manifest_sha256": declared["private_source_manifest_sha256"],
        "relational_manifest_sha256": declared["relational_manifest_sha256"],
        "neotoma_inventory": {
            "url": inventory_source["url"],
            "source_sha256": inventory_source["sha256"],
            "records": len(inventory["data"]),
            "unique_site_ids": len(site_ids),
            "site_ids_sha256_newline_utf8": hashlib.sha256(
                ("\n".join(map(str, sorted(site_ids))) + "\n").encode()
            ).hexdigest(),
            "retained_site_ids": len(retained_sites),
            "site_ids_outside_retained_snapshot": sorted(site_ids - retained_sites),
        },
        "cross_archive_leads": cross,
        "result": "no_fresh_physical_site_in_checked_metadata_surfaces",
        "scope": TOP_SCOPE,
        "epd_metadata_screen": {
            "private_source_manifest_sha256": declared["epd_source_manifest_sha256"],
            "source_capture_utc": second["captured_at_utc"],
            "pangaea_metadata_search_hits": 66,
            "retained_neotoma_all_country_core_handles": len(handles),
            "search_hits_matching_retained_handles": retained,
            "screened_retained_country_unassigned_handles": len(named),
            "unmatched_named_core_handles": len(unmatched),
            "generic_unbound_profile_doi": f"10.1594/PANGAEA.{generic[0]}",
            "checked_epd_final_age_swedish_events": len(events),
            "checked_epd_final_age_events_matching_retained_handles": len(events),
            "hakulla5_chronology_reference": {
                "doi": "10.1594/PANGAEA.853943",
                "reference": chronological[0]["Reference"],
                "comment": chronological[0]["Comm"],
                "selected_sample_age_sequence_in_table": False,
            },
            "hakulla5_legacyage_cross_archive_identity": {
                "doi": "10.1594/PANGAEA.933132",
                "neotoma_site_id": 3138,
                "neotoma_pollen_dataset_id": 4082,
                "legacyage_age_model": legacy[0]["Reference (AgeModel)"],
            },
            "named_leads": leads,
            "result": "three_unmatched_handles_three_retained_unassigned_cores_no_fresh_cohort_qualified",
            "scope": EPD_SCOPE,
        },
    }


def load_geo(text: str) -> list[int | float]:
    import json

    value = json.loads(text)
    points = value["coordinates"]
    require(
        value.get("type") == "Point"
        and len(points) == 2
        and all(type(x) in (float, int) for x in points),
        "Metadata point geometry differs",
    )
    return list(points)
