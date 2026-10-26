"""Check metadata-only Swedish pollen cohort availability against the retained site graph."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
from typing import Any
import xml.etree.ElementTree as ET

FAMILY = Path("docs/report/source-relations/neotoma/swedish-cohort-availability")
RELATIONAL = Path("data/neotoma/relational")
PANGAEA_NAMESPACE = "{http://www.pangaea.de/MetaData}"
EPD_PROFILE_IDS = {
    "ADRAN": 738941,
    "GARASEL": 739248,
    "HAKULLA5": 711892,
    "LEVEANIE": 739449,
    "NDRAKET": 739584,
    "VUOLEPAL": 889510,
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _source(repository: Path, private_root: Path) -> tuple[dict[str, Any], Path]:
    declared = _read_json(repository / FAMILY / "sources.json")
    if declared["schema_version"] != "swedish-cohort-availability-sources.v1":
        raise ValueError("unexpected source declaration")
    source_root = private_root / declared["private_source_subdir"]
    source_manifest = source_root / "source-manifest.json"
    if _sha(source_manifest) != declared["private_source_manifest_sha256"]:
        raise ValueError("private metadata source manifest changed")
    manifest = _read_json(source_manifest)
    if (
        manifest["schema_version"] != "swedish-cohort-metadata-source.v1"
        or manifest["sources"] != declared["sources"]
        or manifest["captured_at_utc"] != declared["source_capture_utc"]
    ):
        raise ValueError("private metadata source declaration changed")
    for item in declared["sources"]:
        path = source_root / item["file"]
        if path.stat().st_size != item["bytes"] or _sha(path) != item["sha256"]:
            raise ValueError(f"metadata source bytes changed: {item['file']}")
    return declared, source_root


def _site_ids(repository: Path, declared: dict[str, Any]) -> set[int]:
    manifest_path = repository / RELATIONAL / "manifest.json"
    if _sha(manifest_path) != declared["relational_manifest_sha256"]:
        raise ValueError("retained Neotoma relational manifest changed")
    manifest = _read_json(manifest_path)
    parts = manifest["surfaces"]["sites"]["parts"]
    if len(parts) != 1:
        raise ValueError("retained Neotoma site-part count changed")
    part = parts[0]
    if part["sha256"] != declared["relational_sites_part_sha256"]:
        raise ValueError("retained Neotoma site-part declaration changed")
    path = repository / RELATIONAL / part["path"]
    if _sha(path) != part["sha256"]:
        raise ValueError("retained Neotoma site-part bytes changed")
    rows = _read_json(path)["rows"]
    return {row["source_site_id"] for row in rows}


def _neotoma_core(
    source_root: Path, filename: str, *, site: int, core: int, dataset: int, handle: str
) -> tuple[float, float]:
    payload = _read_json(source_root / filename)
    if payload["status"] != "success" or len(payload["data"]) != 1:
        raise ValueError(f"Neotoma site response changed: {filename}")
    row = payload["data"][0]
    if row["siteid"] != site or not any(
        unit["collectionunitid"] == core
        and unit["handle"] == handle
        and any(item["datasetid"] == dataset for item in unit["datasets"])
        for unit in row["collectionunits"]
    ):
        raise ValueError(f"Neotoma core identity changed: {filename}")
    geography = json.loads(row["geography"])
    longitude, latitude = geography["coordinates"]
    return latitude, longitude


def _pangaea_core(
    source_root: Path, filename: str, *, doi: str, handle: str
) -> tuple[dict[str, Any], tuple[float, float]]:
    payload = _read_json(source_root / filename)
    if (
        payload["identifier"] != f"https://doi.org/{doi}"
        or handle not in payload["name"]
    ):
        raise ValueError(f"PANGAEA core identity changed: {filename}")
    geography = payload["spatialCoverage"]["geo"]
    return payload, (geography["latitude"], geography["longitude"])


def _epd_sources(
    declared: dict[str, Any], private_root: Path
) -> tuple[dict[str, Any], Path]:
    root = private_root / declared["epd_private_source_subdir"]
    path = root / "source-manifest.json"
    if _sha(path) != declared["epd_source_manifest_sha256"]:
        raise ValueError("private EPD metadata source manifest changed")
    manifest = _read_json(path)
    if manifest["schema_version"] != "swedish-epd-metadata-source.v1":
        raise ValueError("unexpected private EPD metadata source schema")
    if len(manifest["sources"]) != 17:
        raise ValueError("EPD metadata source count changed")
    for item in manifest["sources"]:
        source = private_root / item["file"]
        if source.stat().st_size != item["bytes"] or _sha(source) != item["sha256"]:
            raise ValueError(f"EPD metadata source bytes changed: {item['file']}")
    return manifest, root


def _retained_core_handles(
    repository: Path, declared: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    manifest = _read_json(repository / RELATIONAL / "manifest.json")
    surfaces: dict[str, list[dict[str, Any]]] = {}
    for name in ("sites", "collection_units", "datasets"):
        parts = manifest["surfaces"][name]["parts"]
        if len(parts) != 1:
            raise ValueError(f"retained {name} part count changed")
        if (
            name == "collection_units"
            and parts[0]["sha256"]
            != declared["relational_collection_units_part_sha256"]
        ):
            raise ValueError("retained collection-unit declaration changed")
        path = repository / RELATIONAL / parts[0]["path"]
        if _sha(path) != parts[0]["sha256"]:
            raise ValueError(f"retained {name} part bytes changed")
        surfaces[name] = _read_json(path)["rows"]
    sites = {row["site_id"]: row for row in surfaces["sites"]}
    datasets: dict[str, list[int]] = {}
    for row in surfaces["datasets"]:
        datasets.setdefault(row["collection_unit_id"], []).append(
            row["source_dataset_id"]
        )
    handles: dict[str, dict[str, Any]] = {}
    for unit in surfaces["collection_units"]:
        handle = unit["source_payload"].get("handle")
        if not handle:
            continue
        handle = handle.upper()
        if handle in handles:
            raise ValueError(f"duplicate retained core handle: {handle}")
        site = sites[unit["site_id"]]
        handles[handle] = {
            "neotoma_site_id": site["source_site_id"],
            "neotoma_core_id": unit["source_collection_unit_id"],
            "neotoma_pollen_dataset_ids": sorted(
                datasets.get(unit["collection_unit_id"], [])
            ),
            "retained_country_code": site["country_code"],
            "source_geopolitical": site["source_payload"]["geopolitical"],
        }
    return handles


def _pangaea_title(hit: dict[str, Any]) -> str:
    title = ET.fromstring(hit["_source"]["xml-thumb"]).find(
        f".//{PANGAEA_NAMESPACE}title"
    )
    if title is None or not title.text:
        raise ValueError("PANGAEA metadata search title missing")
    return title.text


def _garasel_prior_processing(
    repository: Path, declared: dict[str, Any]
) -> dict[str, Any]:
    """Read identity and completed-processing metadata, never a target workbook."""
    evidence = declared["prior_processing_evidence"]
    expected_paths = {
        "crosswalk": "data/landclim/review/rootsi-candidate-inputs/rootsi-crosswalk.csv",
        "census": "reports/science/publication-correspondence/rootsi-feature-census/report.json",
    }
    paths = {}
    for role, expected in expected_paths.items():
        item = evidence[role]
        if item["path"] != expected:
            raise ValueError("prior-processing metadata path changed")
        path = repository / expected
        if path.is_symlink() or not path.is_file() or _sha(path) != item["sha256"]:
            raise ValueError("prior-processing metadata identity changed")
        paths[role] = path
    census = _read_json(paths["census"])
    if census["canonical_crosswalk"] != evidence["crosswalk"]:
        raise ValueError("census and crosswalk source identities differ")
    with paths["crosswalk"].open(encoding="utf-8", newline="") as stream:
        identities = [
            row
            for row in csv.DictReader(stream)
            if row["rootsi_sequence_label_raw"].upper() == "GARASEL"
        ]
    if len(identities) != 1:
        raise ValueError("GARASEL crosswalk identity is missing or duplicated")
    identity = identities[0]
    member = identity["typed_workbook_member"]
    entries = [row for row in census["workbooks"] if row["archive_member"] == member]
    if len(entries) != 1 or member != "rootsi/GARASEL.xls":
        raise ValueError("GARASEL prior-processing workbook identity differs")
    entry = entries[0]
    if (
        entry["sha256"] != identity["typed_workbook_sha256"]
        or entry["bytes"] != int(identity["typed_workbook_bytes"])
        or entry["metadata_source_locator"] != identity["rootsi_source_locator"]
        or entry["status"] != "computed"
        or entry["value_origin"]
        != "decoded cached values; literal/formula origin unavailable"
    ):
        raise ValueError("GARASEL completed numeric-processing evidence differs")
    return {
        "status": "prior_numeric_source_processing_recorded",
        "workbook_member": member,
        "workbook_sha256": entry["sha256"],
        "workbook_bytes": entry["bytes"],
        "sheet": entry["sheet"],
        "metadata_source_locator": identity["rootsi_source_locator"],
        "site_name_raw": identity["rootsi_site_name_raw"],
        "latitude_raw": identity["rootsi_latitude_raw"],
        "longitude_raw": identity["rootsi_longitude_raw"],
        "completed_census_source_commit": census["source_commit"],
        "evidence_inputs": evidence,
        "processing_scope": entry["value_origin"],
        "fitting_or_tuning_exposure": "not_established_by_these_records",
        "target_measurement_values_opened_by_this_check": False,
    }


def _prior_processing_facet(
    lead: dict[str, Any], exposure: dict[str, Any]
) -> dict[str, Any]:
    """Known previous processing cannot become untouched through metadata repair."""
    if lead["core_handle"].upper() != "GARASEL":
        return lead
    if exposure.get("status") != "prior_numeric_source_processing_recorded":
        raise ValueError("GARASEL prior-processing evidence is unavailable")
    return {
        **lead,
        "decision": "refused_as_untouched_prior_numeric_source_processing",
        "prior_source_processing": exposure,
        "untouched_confirmation_eligible": False,
        "untouched_status_restored_by_age_or_rights_repair": False,
    }


def _epd_age_events(path: Path) -> set[str]:
    events: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if line == "*/":
            break
        if "* LOCATION:" in line and "Sweden" in line:
            match = re.match(r"\s*([^\s(]+)", line)
            if match is None:
                raise ValueError("EPD Swedish age-table event label missing")
            events.add(match.group(1))
    return events


def _epd_screen(
    repository: Path, private_root: Path, declared: dict[str, Any]
) -> dict[str, Any]:
    manifest, root = _epd_sources(declared, private_root)
    prior_processing = _garasel_prior_processing(repository, declared)
    retained_handles = _retained_core_handles(repository, declared)
    search = _read_json(root / "pangaea-sweden-pollen-profiles.json")
    if (
        search["timed_out"]
        or search["hits"]["total"] != 66
        or len(search["hits"]["hits"]) != 66
    ):
        raise ValueError("bounded PANGAEA pollen-profile search changed")
    matched = 0
    unmatched: dict[str, int] = {}
    retained_named: dict[str, int] = {}
    unbound: list[int] = []
    for hit in search["hits"]["hits"]:
        title = _pangaea_title(hit)
        match = re.search(
            r"Pollen profile (?:of sediment core )?([A-Z][A-Z0-9_-]+)[, ]", title
        )
        doi_id = int(hit["_id"])
        if match is None:
            unbound.append(doi_id)
        elif match.group(1) in retained_handles:
            matched += 1
            if match.group(1) in EPD_PROFILE_IDS:
                retained_named[match.group(1)] = doi_id
        else:
            unmatched[match.group(1)] = doi_id
    if (
        unmatched
        != {key: EPD_PROFILE_IDS[key] for key in ("ADRAN", "GARASEL", "LEVEANIE")}
        or retained_named
        != {key: EPD_PROFILE_IDS[key] for key in ("HAKULLA5", "NDRAKET", "VUOLEPAL")}
        or unbound != [761854]
        or matched != 62
    ):
        raise ValueError("PANGAEA/Neotoma core-handle screen changed")

    final_ages = _epd_age_events(
        private_root / "epd/pangaea/epd-age-cut-pangaea-804596.tsv"
    )
    if len(final_ages) != 37 or not final_ages <= retained_handles.keys():
        raise ValueError("EPD final-age Swedish event inventory changed")
    if final_ages & EPD_PROFILE_IDS.keys():
        raise ValueError("screened PANGAEA handle appears in final-age event inventory")

    chronology_text = (root / "pangaea-core-chronologies-853943.tsv").read_text(
        encoding="utf-8"
    )
    chronology_rows = list(
        csv.DictReader(chronology_text.split("*/\n", 1)[1].splitlines(), delimiter="\t")
    )
    chronology = [row for row in chronology_rows if row["Event"] == "HAKULLA5"]
    if len(chronology) != 1 or chronology[0]["Reference"] != "EPD chron2":
        raise ValueError("HAKULLA5 published chronology-reference row changed")

    legacy_text = (
        private_root
        / "epd/pangaea/legacyage-site-chronology-metadata-pangaea-933132.tsv"
    ).read_text(encoding="utf-8")
    legacy_rows = list(
        csv.DictReader(legacy_text.split("*/\n", 1)[1].splitlines(), delimiter="\t")
    )
    legacy = [row for row in legacy_rows if row["Event"] == "HAKULLA5"]
    if (
        len(legacy) != 1
        or legacy[0]["ID (Site)"] != "3138"
        or legacy[0]["ID (Dataset)"] != "4082"
        or legacy[0]["Reference (AgeModel)"] != "AWI"
    ):
        raise ValueError("HAKULLA5 LegacyAge cross-archive identity changed")

    leads = []
    for handle, doi_id in sorted(EPD_PROFILE_IDS.items()):
        name = handle.lower()
        profile = _read_json(root / f"pangaea-{name}-pollen-metadata.jsonld")
        if (
            profile["identifier"] != f"https://doi.org/10.1594/PANGAEA.{doi_id}"
            or handle not in profile["name"]
        ):
            raise ValueError(f"PANGAEA profile identity changed: {handle}")
        related = _read_json(root / f"pangaea-{name}-related-metadata.json")
        if related["timed_out"] or related["hits"]["total"] != len(
            related["hits"]["hits"]
        ):
            raise ValueError(f"PANGAEA handle-related metadata is incomplete: {handle}")
        dated_controls = sorted(
            int(hit["_id"])
            for hit in related["hits"]["hits"]
            if _pangaea_title(hit).startswith("Age determination of sediment core ")
            and handle in _pangaea_title(hit)
        )
        retained = retained_handles.get(handle)
        if retained is not None and (
            retained["retained_country_code"] != "UNASSIGNED"
            or "Sweden" not in retained["source_geopolitical"]
        ):
            raise ValueError(f"retained Swedish core country posture changed: {handle}")
        leads.append(
            _prior_processing_facet(
                {
                    "core_handle": handle,
                    "pangaea_pollen_doi": f"10.1594/PANGAEA.{doi_id}",
                    "age_determination_metadata_dois": [
                        f"10.1594/PANGAEA.{item}" for item in dated_controls
                    ],
                    "profile_license": profile.get("license"),
                    "profile_conditions_of_access": profile.get("conditionsOfAccess"),
                    "retained_neotoma_identity": retained,
                    "in_checked_epd_final_age_events": False,
                    "selected_sample_age_sequence_identified": False,
                    "decision": (
                        "refused_as_fresh_retained_core_country_unassigned"
                        if retained is not None
                        else "metadata_lead_only_core_alias_and_selected_age_model_unresolved"
                    ),
                },
                prior_processing,
            )
        )
    generic = _read_json(root / "pangaea-schonen-pollen-metadata.jsonld")
    if generic["identifier"] != "https://doi.org/10.1594/PANGAEA.761854":
        raise ValueError("generic Schonen metadata identity changed")
    return {
        "private_source_manifest_sha256": declared["epd_source_manifest_sha256"],
        "source_capture_utc": manifest["captured_at_utc"],
        "pangaea_metadata_search_hits": 66,
        "retained_neotoma_all_country_core_handles": len(retained_handles),
        "search_hits_matching_retained_handles": matched,
        "screened_retained_country_unassigned_handles": len(retained_named),
        "unmatched_named_core_handles": len(unmatched),
        "generic_unbound_profile_doi": "10.1594/PANGAEA.761854",
        "checked_epd_final_age_swedish_events": len(final_ages),
        "checked_epd_final_age_events_matching_retained_handles": len(final_ages),
        "hakulla5_chronology_reference": {
            "doi": "10.1594/PANGAEA.853943",
            "reference": chronology[0]["Reference"],
            "comment": chronology[0]["Comm"],
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
        "scope": "PANGAEA title metadata search, seven profile metadata records, six handle-related metadata searches, Giesecke final-age event inventory, Fyfe chronology reference and LegacyAge site identity table. All retained Neotoma core handles were checked, including UNASSIGNED country rows. No pollen observation/count table opened; absent exact handle is not proof of distinct physical site.",
    }


def replay(repository: Path, private_root: Path) -> dict[str, Any]:
    repository = repository.resolve()
    declared, source_root = _source(repository, private_root)
    retained_sites = _site_ids(repository, declared)
    inventory = _read_json(source_root / "neotoma-sweden-datasets-current.json")
    if inventory["status"] != "success" or not isinstance(inventory["data"], list):
        raise ValueError("Neotoma metadata inventory response changed")
    records = inventory["data"]
    site_ids = {row["site"]["siteid"] for row in records}
    if not site_ids or any(type(site_id) is not int for site_id in site_ids):
        raise ValueError("Neotoma metadata inventory site IDs changed")
    outside = sorted(site_ids - retained_sites)

    sambotot, sambotot_geo = _pangaea_core(
        source_root,
        "pangaea-sambotot-pollen-metadata.jsonld",
        doi="10.1594/PANGAEA.739778",
        handle="SAMBOTOT",
    )
    age, _ = _pangaea_core(
        source_root,
        "pangaea-sambotot-age-controls-metadata.jsonld",
        doi="10.1594/PANGAEA.740716",
        handle="SAMBOTOT",
    )
    klot, klot_geo = _pangaea_core(
        source_root,
        "pangaea-klot-pollen-metadata.jsonld",
        doi="10.1594/PANGAEA.739382",
        handle="KLOT",
    )
    sambotot_neotoma_geo = _neotoma_core(
        source_root,
        "neotoma-sambosjon-site-metadata.json",
        site=3398,
        core=4262,
        dataset=4403,
        handle="SAMBOTOT",
    )
    klot_neotoma_geo = _neotoma_core(
        source_root,
        "neotoma-klot-site-metadata.json",
        site=13336,
        core=14908,
        dataset=19909,
        handle="KLOT",
    )
    age_fields = [item["name"] for item in age["variableMeasured"]]
    pollen_fields = [item["name"] for item in sambotot["variableMeasured"]]
    if (
        not {"DEPTH, sediment/rock", "Age, dated", "Age, dated, error to older"}
        <= set(age_fields)
        or "DEPTH, sediment/rock" not in pollen_fields
    ):
        raise ValueError("PANGAEA depth/dated-control metadata changed")
    if any("calibrated" in name.lower() for name in age_fields):
        raise ValueError("PANGAEA age-control metadata gained calibrated-age field")

    return {
        "schema_version": "swedish-cohort-availability.v1",
        "source_capture_utc": declared["source_capture_utc"],
        "private_source_manifest_sha256": declared["private_source_manifest_sha256"],
        "relational_manifest_sha256": declared["relational_manifest_sha256"],
        "neotoma_inventory": {
            "url": next(
                item["url"]
                for item in declared["sources"]
                if item["file"] == "neotoma-sweden-datasets-current.json"
            ),
            "source_sha256": next(
                item["sha256"]
                for item in declared["sources"]
                if item["file"] == "neotoma-sweden-datasets-current.json"
            ),
            "records": len(records),
            "unique_site_ids": len(site_ids),
            "site_ids_sha256_newline_utf8": hashlib.sha256(
                ("\n".join(map(str, sorted(site_ids))) + "\n").encode("utf-8")
            ).hexdigest(),
            "retained_site_ids": len(retained_sites),
            "site_ids_outside_retained_snapshot": outside,
        },
        "cross_archive_leads": [
            {
                "core_handle": "SAMBOTOT",
                "pangaea_pollen_doi": "10.1594/PANGAEA.739778",
                "pangaea_dated_control_doi": "10.1594/PANGAEA.740716",
                "neotoma_site_id": 3398,
                "neotoma_core_id": 4262,
                "neotoma_pollen_dataset_id": 4403,
                "pangaea_latitude_longitude": list(sambotot_geo),
                "neotoma_latitude_longitude": list(sambotot_neotoma_geo),
                "selected_calibrated_age_model_in_checked_pangaea_metadata": False,
                "decision": "refused_as_fresh_cohort_core_handle_collides_with_scored_retained_core",
            },
            {
                "core_handle": "KLOT",
                "pangaea_pollen_doi": "10.1594/PANGAEA.739382",
                "neotoma_site_id": 13336,
                "neotoma_core_id": 14908,
                "neotoma_pollen_dataset_id": 19909,
                "pangaea_latitude_longitude": list(klot_geo),
                "neotoma_latitude_longitude": list(klot_neotoma_geo),
                "decision": "refused_as_fresh_cohort_core_handle_collides_with_retained_core",
            },
        ],
        "result": "no_fresh_physical_site_in_checked_metadata_surfaces",
        "scope": "This current availability check reads metadata only, including prior-processing identity metadata; no target pollen measurements are opened. Known previous numeric processing is not erased by a new metadata-only check. A genuinely unexposed physical site must satisfy the original grouping, input and prediction-freeze requirements.",
        "epd_metadata_screen": _epd_screen(repository, private_root, declared),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--private-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = replay(args.repository, args.private_root)
    if args.output.exists():
        raise ValueError("output already exists")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
