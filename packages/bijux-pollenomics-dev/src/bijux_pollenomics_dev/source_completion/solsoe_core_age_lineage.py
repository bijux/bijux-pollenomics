"""Match a primary Solsø core age table to retained Neotoma controls."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
from typing import Any


SOURCE = Path("landclim/pangaea/solsoe/solsoe81-age-740759.txt")
SOURCE_SHA256 = "9934dd802fa7b7094c2a6cc08fff90ef29c1c630a092787c4f4a3aac96be6be0"
DOI = "10.1594/PANGAEA.740759"
CONTROL = Path("data/neotoma/relational/surfaces/chronology_controls/part-00001.json")
CHRONOLOGIES = Path("data/neotoma/relational/surfaces/chronologies/part-00001.json")
MANIFEST = Path("data/neotoma/relational/manifest.json")
SOLSOE = Path("docs/report/countries/denmark/solsoe-source-lineage/report.json")
UNIT = "neotoma:collection-unit:4303"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _integer(value: str, multiplier: int) -> int:
    try:
        number = Decimal(value) * multiplier
    except InvalidOperation as exc:
        raise ValueError(f"Invalid PANGAEA core control value: {value}") from exc
    if not number.is_finite() or number != int(number):
        raise ValueError(f"Nonintegral PANGAEA core control value: {value}")
    return int(number)


def _primary_rows(data: bytes) -> list[dict[str, str]]:
    text = data.decode("utf-8")
    if (
        DOI not in text
        or "Event(s):\tSOLSOE81" not in text
        or "Area: 2.5 ha." not in text
        or "Creative Commons Attribution-NonCommercial 3.0 Unported" not in text
        or "*/\n" not in text
    ):
        raise ValueError("Primary Solsø core citation, event or rights changed")
    with_header = text.split("*/\n", 1)[1].splitlines()
    rows = list(csv.DictReader(with_header, delimiter="\t"))
    expected_columns = {
        "Depth sed [m]",
        "Age dated [ka BP]",
        "Age e + [ka +]",
        "Age e - [ka -]",
        "Lab no",
        "δ13C [‰ PDB]",
    }
    if not rows or not expected_columns <= rows[0].keys():
        raise ValueError("Primary Solsø age-table columns changed")
    labels = [row["Lab no"] for row in rows]
    if len(labels) != len(set(labels)):
        raise ValueError("Primary Solsø radiocarbon lab labels are duplicated")
    return rows


def publish(repository: Path, source_root: Path, output: Path) -> dict[str, Any]:
    repository = repository.resolve()
    source_path = source_root.resolve() / SOURCE
    source_data = source_path.read_bytes()
    if _sha(source_data) != SOURCE_SHA256:
        raise ValueError("Primary PANGAEA Solsø age source changed")
    primary = _primary_rows(source_data)
    manifest_path = repository / MANIFEST
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    declared = manifest["surfaces"]["chronology_controls"]["parts"]
    if (
        len(declared) != 1
        or declared[0]["path"] != "surfaces/chronology_controls/part-00001.json"
    ):
        raise ValueError("Neotoma chronology control surface changed")
    controls_path = repository / CONTROL
    raw_controls = controls_path.read_bytes()
    if _sha(raw_controls) != declared[0]["sha256"]:
        raise ValueError("Neotoma chronology control source changed")
    part = json.loads(raw_controls)
    if len(part["rows"]) != declared[0]["row_count"]:
        raise ValueError("Neotoma chronology control count changed")
    controls = [row for row in part["rows"] if row["collection_unit_id"] == UNIT]
    if not controls or {row["site_id"] for row in controls} != {"neotoma:site:3432"}:
        raise ValueError("Neotoma SOLSOE81 core control identity changed")
    chronology_parts = manifest["surfaces"]["chronologies"]["parts"]
    if (
        len(chronology_parts) != 1
        or chronology_parts[0]["path"] != "surfaces/chronologies/part-00001.json"
    ):
        raise ValueError("Neotoma chronology surface changed")
    raw_chronologies = (repository / CHRONOLOGIES).read_bytes()
    if _sha(raw_chronologies) != chronology_parts[0]["sha256"]:
        raise ValueError("Neotoma chronology source changed")
    chronology_rows = json.loads(raw_chronologies)["rows"]
    if len(chronology_rows) != chronology_parts[0]["row_count"]:
        raise ValueError("Neotoma chronology count changed")
    profiles = []
    for row in chronology_rows:
        if row["collection_unit_id"] != UNIT:
            continue
        if row["site_id"] != "neotoma:site:3432":
            raise ValueError("Neotoma SOLSOE81 chronology site changed")
        payload = row["source_payload"]["chronology"]
        profiles.append(
            {
                "chronology_id": row["chronology_id"],
                "name": payload["chronologyname"],
                "model": payload["agemodel"],
                "age_type": payload["modelagetype"],
                "age_range_bp": payload["agerange"],
                "selected_by_collection_unit_reference": row[
                    "selected_by_collection_unit_reference"
                ],
            }
        )
    profiles.sort(key=lambda profile: profile["chronology_id"])
    by_lab: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in controls:
        geo = row["source_payload"].get("geochron")
        if geo and geo.get("labnumber"):
            by_lab[geo["labnumber"]].append(row)
    matched_primary = 0
    matched_control_ids: set[str] = set()
    matched_chronologies: Counter[str] = Counter()
    missing_labels: list[str] = []
    partial_or_conflicting: list[str] = []
    for row in primary:
        label = row["Lab no"]
        expected = (
            _integer(row["Depth sed [m]"], 100),
            _integer(row["Age dated [ka BP]"], 1000),
            _integer(row["Age e + [ka +]"], 1000),
            _integer(row["Age e - [ka -]"], 1000),
            Decimal(row["δ13C [‰ PDB]"]),
        )
        candidates = by_lab.get(label, [])
        if not candidates:
            missing_labels.append(label)
            continue
        exact: list[dict[str, Any]] = []
        for candidate in candidates:
            payload = candidate["source_payload"]
            geo = payload["geochron"]
            value = (
                payload["depth"],
                geo["geochronage"],
                geo["geochronerrorolder"],
                geo["geochronerroryounger"],
                Decimal(str(geo["delta13c"])),
            )
            if value == expected:
                exact.append(candidate)
        if not exact:
            partial_or_conflicting.append(label)
            continue
        matched_primary += 1
        for candidate in exact:
            control_id = candidate["chronology_control_id"]
            if control_id in matched_control_ids:
                raise ValueError("Neotoma control matched more than one PANGAEA row")
            matched_control_ids.add(control_id)
            matched_chronologies[candidate["chronology_id"]] += 1
    if matched_primary + len(missing_labels) + len(partial_or_conflicting) != len(
        primary
    ):
        raise ValueError("Solsø primary control denominator does not close")
    if {profile["chronology_id"] for profile in profiles} != set(matched_chronologies):
        raise ValueError("Solsø matched-control chronology identity changed")
    prior_path = repository / SOLSOE
    prior = json.loads(prior_path.read_text(encoding="utf-8"))
    if (
        prior["landclim_i"]["reported_site_area_ha"] != 2.5
        or prior["neotoma"]["cores"][0]["collection_unit_id"] != UNIT
    ):
        raise ValueError("Published Solsø source lineage changed")
    report: dict[str, Any] = {
        "schema_version": "solsoe-primary-core-age-lineage.v1",
        "primary_doi": DOI,
        "primary_event": "SOLSOE81",
        "primary_core_area_ha": 2.5,
        "landclim_i_site_area_ha": 2.5,
        "primary_radiocarbon_control_rows": len(primary),
        "neotoma_core_control_rows": len(controls),
        "matched_primary_rows": matched_primary,
        "matched_neotoma_control_rows": len(matched_control_ids),
        "matched_neotoma_rows_by_chronology": dict(
            sorted(matched_chronologies.items())
        ),
        "neotoma_1981_chronologies": profiles,
        "primary_labels_absent_from_neotoma_controls": sorted(missing_labels),
        "primary_labels_with_nonmatching_neotoma_controls": sorted(
            partial_or_conflicting
        ),
        "inputs": [
            {
                "role": "external_pangaea_age_table",
                "path": SOURCE.as_posix(),
                "sha256": SOURCE_SHA256,
            },
            {"path": MANIFEST.as_posix(), "sha256": _sha(manifest_path.read_bytes())},
            {"path": CONTROL.as_posix(), "sha256": _sha(raw_controls)},
            {"path": CHRONOLOGIES.as_posix(), "sha256": _sha(raw_chronologies)},
            {"path": SOLSOE.as_posix(), "sha256": _sha(prior_path.read_bytes())},
        ],
        "interpretation": "The PANGAEA EPD event binds 2.5 ha and 30 exact radiocarbon controls to the 1981 Solsø core; 24 matched controls recur in both Neotoma chronologies. The selected EPD default is a radiocarbon linear-interpolation model, whereas the later MADCAP record is a calibrated-radiocarbon clam model. Shared dated material does not identify the LandClim II author chronology. Four primary lab labels have no retained Neotoma control. The event area is not an age-specific historical basin outline, and this join does not identify the 79 LandClim II samples.",
        "source_rights": "PANGAEA EPD CC BY-NC 3.0; source table retained only in the external data store, not redistributed here.",
        "lra_admitted_samples": 0,
    }
    output.mkdir(parents=True, exist_ok=False)
    (output / "report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(publish(args.repository, args.source_root, args.output), indent=2))


if __name__ == "__main__":
    main()
