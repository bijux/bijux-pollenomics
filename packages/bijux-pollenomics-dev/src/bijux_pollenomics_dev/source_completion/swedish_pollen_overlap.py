"""Detect Swedish source-site overlap before any independence claim."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from math import asin, cos, radians, sin, sqrt
from pathlib import Path
from typing import Any


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _distance_m(first: tuple[float, float], second: tuple[float, float]) -> float:
    latitude_delta = radians(second[1] - first[1])
    longitude_delta = radians(second[0] - first[0])
    arc = (
        sin(latitude_delta / 2) ** 2
        + cos(radians(first[1]))
        * cos(radians(second[1]))
        * sin(longitude_delta / 2) ** 2
    )
    return 12_742_000 * asin(min(1, sqrt(arc)))


def build(sites_path: Path, landclim_path: Path, output: Path) -> dict[str, Any]:
    """Retain exact-name spatial leads without asserting identical source cores."""
    if output.exists() or output.is_symlink():
        raise ValueError("absent overlap output required")
    sites = json.loads(sites_path.read_text(encoding="utf-8"))
    if len(sites) != 3 or {site["dataset_id"] for site in sites} != {
        "19913",
        "53995",
        "54001",
    }:
        raise ValueError("Swedish native sequence cohort changed")
    with landclim_path.open(newline="", encoding="utf-8") as stream:
        landclim = list(csv.DictReader(stream))
    matches = []
    for site in sites:
        candidates = [
            row
            for row in landclim
            if row["country"] == "Sweden"
            and row["name"].casefold() == site["site_name"].casefold()
        ]
        if not candidates:
            raise ValueError(f"missing LandClim name lead: {site['site_name']}")
        for row in candidates:
            distance = _distance_m(
                (float(site["longitude"]), float(site["latitude"])),
                (float(row["longitude"]), float(row["latitude"])),
            )
            if distance > 100:
                raise ValueError(
                    f"same-name coordinate lead exceeds 100 m: {row['record_id']}"
                )
            matches.append(
                {
                    "neotoma_dataset_id": site["dataset_id"],
                    "neotoma_site_id": site["site_id"],
                    "neotoma_site_name": site["site_name"],
                    "landclim_record_id": row["record_id"],
                    "landclim_source_url": row["source_url"],
                    "landclim_provenance": json.loads(row["temporal_semantics_json"])[
                        "provenance_locator"
                    ],
                    "point_distance_m": distance,
                    "name_match": "casefold_exact",
                    "lineage_status": "possible_shared_source; not_independent_corroboration",
                }
            )
    matches.sort(key=lambda row: (row["neotoma_dataset_id"], row["landclim_record_id"]))
    report = {
        "schema_version": "swedish-pollen-source-overlap.v1",
        "inputs_sha256": {
            str(sites_path): _sha(sites_path),
            str(landclim_path): _sha(landclim_path),
        },
        "neotoma_site_count": len(sites),
        "landclim_site_metadata_lead_count": len(matches),
        "matches": matches,
        "independent_corroboration_admitted": False,
        "same_core_or_sample_identity_admitted": False,
        "interpretation": "Exact-name, near-coordinate LandClim site metadata are lineage leads, not separate pollen observations; original source-core identity requires review.",
    }
    output.mkdir(parents=True)
    (output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sites", type=Path, required=True)
    parser.add_argument("--landclim", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.sites, args.landclim, args.output), indent=2))


if __name__ == "__main__":
    main()
