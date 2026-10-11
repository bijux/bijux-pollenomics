"""Bind native pollen observations, typed chronology and basin metadata to bytes."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
from pathlib import Path
from typing import Any

NativeSourceRecord = dict[str, Any]
NativeDatasets = dict[int, NativeSourceRecord]

FAMILY = Path("docs/report/pollen-reconstruction/swedish-static-basin-scenarios")
RAW = Path("data/neotoma/raw/neotoma_pollen_dataset_downloads")
CALIBRATED_BP = "Calibrated radiocarbon years BP"


def sha256(path: Path) -> str:
    """Hash the exact retained source bytes without decoding or normalization."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_bound(repository: Path, relative: str, identity: dict[str, Any]) -> bytes:
    """Refuse changed bytes and symlink traversal before interpreting a source."""
    locator = Path(relative)
    if locator.is_absolute() or ".." in locator.parts:
        raise ValueError("source locator must be repository relative")
    path = repository / locator
    if path.resolve() != path or not path.is_file():
        raise ValueError(f"source is not a regular contained file: {relative}")
    body = path.read_bytes()
    if (
        hashlib.sha256(body).hexdigest() != identity["sha256"]
        or len(body) != identity["bytes"]
    ):
        raise ValueError(f"source identity mismatch: {relative}")
    return body


def pollen_counts(sample: dict[str, Any]) -> dict[str, Any]:
    """Retain reported integer NISP only; absence remains absent, never zero."""
    counts: Counter[str] = Counter()
    rows = []
    rejected: Counter[str] = Counter()
    seen: set[tuple[int, str]] = set()
    for ordinal, datum in enumerate(sample["datum"]):
        if datum.get("element") != "pollen" or datum.get("elementtype") != "pollen":
            rejected["non_pollen"] += 1
            continue
        if datum.get("units") != "NISP":
            raise ValueError("native pollen unit is not NISP")
        value = datum.get("value")
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value < 0
            or value != math.floor(value)
        ):
            raise ValueError("native pollen value is not a finite nonnegative integer")
        name, taxon_id = datum["variablename"], datum["taxonid"]
        if not isinstance(name, str) or not name or type(taxon_id) is not int:
            raise ValueError("native pollen taxon identity is missing")
        key = (taxon_id, name)
        if key in seen:
            raise ValueError(
                "duplicate native pollen taxon row needs an aggregation decision"
            )
        seen.add(key)
        counts[name] += int(value)
        rows.append(
            {
                "ordinal": ordinal,
                "taxon_id": taxon_id,
                "name": name,
                "count": int(value),
            }
        )
    return {
        "sample_id": sample["sampleid"],
        "analysis_unit_id": sample["analysisunitid"],
        "depth": sample["depth"],
        "ages": sample["ages"],
        "counts": dict(counts),
        "reported_all_pollen_NISP_sum": sum(counts.values()),
        "datum_rows": rows,
        "excluded_non_pollen_rows": dict(rejected),
    }


def selected_age(
    sample: dict[str, Any], chronology_id: int
) -> tuple[dict[str, Any] | None, str | None]:
    """Select exactly one finite age from the named native chronology."""
    ages = [age for age in sample["ages"] if age.get("chronologyid") == chronology_id]
    if len(ages) != 1 or ages[0].get("agetype") != CALIBRATED_BP:
        return None, "named_calibrated_chronology_missing_or_ambiguous"
    value = ages[0].get("age")
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
    ):
        return None, "named_chronology_point_age_nonfinite"
    return ages[0], None


def explicit_panel(
    sample: dict[str, Any], taxa: list[str]
) -> tuple[list[int] | None, str | None]:
    """Require explicit nonnegative integer counts for every selected panel taxon."""
    if any(name not in sample["counts"] for name in taxa):
        return None, "panel_taxon_not_explicitly_reported"
    counts = [sample["counts"][name] for name in taxa]
    if sum(counts) == 0:
        return None, "reported_panel_total_zero"
    return counts, None


def load_inputs(
    repository: Path,
) -> tuple[NativeSourceRecord, NativeDatasets, NativeSourceRecord, NativeSourceRecord]:
    """Read only the declared two raw parts, and reconcile their retained authority."""
    family = repository / FAMILY
    identity_path = family / "inputs/source-identities.json"
    protocol_path = family / "assumptions/protocol.json"
    for declaration in (identity_path, protocol_path):
        if declaration.resolve() != declaration or not declaration.is_file():
            raise ValueError("source declaration must be a contained regular file")
    identities = json.loads(identity_path.read_bytes())["source_files"]
    bound = {
        name: read_bound(repository, name, identity)
        for name, identity in identities.items()
    }
    baseline = json.loads(bound["data/neotoma/review/relational_baseline.json"])
    archive = baseline["input_artifacts"]["raw_archive"]
    manifest_name = str(RAW / "manifest.json")
    if identities[manifest_name]["sha256"] != archive["manifest_sha256"]:
        raise ValueError("retained Neotoma manifest authority differs")
    manifest = json.loads(bound[manifest_name])
    protocol = json.loads((family / "assumptions/protocol.json").read_bytes())
    cores = protocol["cores"]
    if len({core["native_dataset_id"] for core in cores}) != len(cores):
        raise ValueError("native dataset selected more than once")
    requested = {core["native_dataset_id"]: core for core in cores}
    datasets = {}
    for part in manifest["parts"]:
        relative = str(RAW / part["filename"])
        if relative not in bound:
            continue
        if identities[relative]["sha256"] != archive["part_sha256"][part["filename"]]:
            raise ValueError("raw part authority differs from retained baseline")
        payload = json.loads(bound[relative])
        if len(payload["rows"]) != part["row_count"]:
            raise ValueError("raw part row count differs from source manifest")
        for row in payload["rows"]:
            site = row["site"]
            unit = site["collectionunit"]
            dataset = unit["dataset"]
            did = dataset["datasetid"]
            if did not in requested:
                continue
            if did in datasets:
                raise ValueError("native dataset appears in multiple source rows")
            selected = requested[did]["chronology_id"]
            chronologies = [
                value["chronology"]
                for value in unit["chronologies"]
                if value["chronology"]["chronologyid"] == selected
            ]
            if (
                len(chronologies) != 1
                or chronologies[0]["chronology"]["modelagetype"] != CALIBRATED_BP
            ):
                raise ValueError(
                    "named chronology is not a unique calibrated BP source model"
                )
            samples = [pollen_counts(sample) for sample in dataset["samples"]]
            if len({sample["sample_id"] for sample in samples}) != len(samples):
                raise ValueError("duplicate native sample identity")
            datasets[did] = {
                "samples": samples,
                "native_site_id": site["siteid"],
                "native_collection_unit_id": unit["collectionunitid"],
                "source_core_handle": unit["handle"],
                "source_site_name": site["sitename"],
                "source_dataset": {k: v for k, v in dataset.items() if k != "samples"},
                "source_default_chronology": unit.get("defaultchronology"),
                "selected_chronology": {
                    "chronology_id": selected,
                    "model": chronologies[0]["chronology"],
                    "raw_control_count": len(chronologies[0]["chroncontrols"]),
                    "raw_control_sha256": hashlib.sha256(
                        json.dumps(
                            chronologies[0]["chroncontrols"],
                            sort_keys=True,
                            separators=(",", ":"),
                            ensure_ascii=False,
                        ).encode()
                    ).hexdigest(),
                },
                "source_locator": relative,
            }
    if set(datasets) != set(requested):
        raise ValueError(
            "a named native dataset is absent from the declared source parts"
        )
    metadata = {}
    for line in bound[
        "docs/report/publication-replay/landclim-study-inputs/records.jsonl"
    ].splitlines():
        record = json.loads(line)
        fields = {field["column"]: field["raw"] for field in record["values"]}
        code = fields.get("csvfilename")
        if isinstance(code, str) and code in {core["metadata_code"] for core in cores}:
            if (
                code in metadata
                or fields["Country"] != "Sweden"
                or fields["siteType"] != "lake"
            ):
                raise ValueError(
                    "basin metadata selection is ambiguous or not a Swedish lake"
                )
            radius = float(fields["siteradius"])
            if not math.isfinite(radius) or radius <= 0:
                raise ValueError("static metadata radius must be positive and finite")
            metadata[code] = {
                "fields": fields,
                "publication_row": record["worksheet_row"],
                "radius_m": radius,
            }
    if set(metadata) != {core["metadata_code"] for core in cores}:
        raise ValueError("a selected basin lacks publication metadata")
    return protocol, datasets, metadata, identities
