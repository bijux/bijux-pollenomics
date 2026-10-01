"""Check metadata-only Swedish pollen cohort availability against the retained site graph."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


FAMILY = Path("docs/report/source-relations/neotoma/swedish-cohort-availability")
RELATIONAL = Path("data/neotoma/relational")


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
        "scope": "Metadata-only current Neotoma Sweden query and two PANGAEA leads; no pollen observation or count table opened. A different EPD-only core and its selected calibrated sample ages may exist outside these checked metadata surfaces.",
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
