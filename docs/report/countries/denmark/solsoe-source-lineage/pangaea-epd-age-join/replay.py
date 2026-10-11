"""Join published EPD calibrated ages to both Solsø Neotoma cores."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
from typing import Any


PUBLISHED_SHA256 = "d332d5c7921b914e84da689c918607befdb162f5c68bbcce9cd3534d1f5e58e0"
RELATIONAL_MANIFEST_SHA256 = (
    "6f6777a40b67bd0704eb1a982f19e6d451cad0d6e4a41dfebf5e3f28be33105b"
)
CORES = {"SOLSOE81", "SOLSOE83"}
OTHER_DANISH_HANDLES = {"VEJLBYE4", "VEJLBYG5", "TRELDKLA", "HOLLERUP", "HARRESK"}


def _surface(
    repository: Path, manifest: dict[str, Any], name: str
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for part in manifest["surfaces"][name]["parts"]:
        data = (repository / "data/neotoma/relational" / part["path"]).read_bytes()
        if sha256(data).hexdigest() != part["sha256"]:
            raise ValueError(f"Relational {name} part differs from manifest")
        rows.extend(json.loads(data)["rows"])
    return rows


def run(repository: Path, published_path: Path) -> dict[str, Any]:
    published_bytes = published_path.read_bytes()
    if sha256(published_bytes).hexdigest() != PUBLISHED_SHA256:
        raise ValueError("Published EPD age table bytes changed")
    with published_path.open(encoding="utf-8", newline="") as stream:
        metadata: list[str] = []
        for line in stream:
            if line.startswith("Event\t"):
                header = line.rstrip("\n").split("\t")
                break
            metadata.append(line)
        else:
            raise ValueError("Published EPD age table has no header")
        if "https://doi.org/10.1594/PANGAEA.804596" not in "".join(metadata):
            raise ValueError("Published EPD age table DOI changed")
        all_rows = list(csv.DictReader(stream, fieldnames=header, delimiter="\t"))
    source_rows = [row for row in all_rows if row["Event"] in CORES]
    other_rows = [row for row in all_rows if row["Event"] in OTHER_DANISH_HANDLES]
    if other_rows or len(source_rows) != 92:
        raise ValueError("Published Danish event membership changed")
    source: dict[tuple[str, Decimal], dict[str, str]] = {}
    for row in source_rows:
        key = (row["Event"], Decimal(row["Depth sed [m]"]) * 100)
        if key in source:
            raise ValueError("Repeated published core-depth pair")
        source[key] = row

    manifest_bytes = (repository / "data/neotoma/relational/manifest.json").read_bytes()
    if sha256(manifest_bytes).hexdigest() != RELATIONAL_MANIFEST_SHA256:
        raise ValueError("Relational manifest identity changed")
    manifest = json.loads(manifest_bytes)
    units = {
        row["collection_unit_id"]: row["source_payload"]["handle"]
        for row in _surface(repository, manifest, "collection_units")
    }
    samples = {
        row["sample_id"]: row
        for row in _surface(repository, manifest, "samples")
        if row["site_id"] == "neotoma:site:3432"
    }
    ages = [
        row
        for row in _surface(repository, manifest, "age_claims")
        if row["site_id"] == "neotoma:site:3432"
        and row["source_age_type"] == "Calibrated radiocarbon years BP"
    ]
    if len(ages) != 92 or set(samples) != {row["subject_id"] for row in ages}:
        raise ValueError("Neotoma calibrated Solsø sample denominator changed")

    matched: set[tuple[str, Decimal]] = set()
    by_core: Counter[str] = Counter()
    absolute_residuals: dict[str, list[Decimal]] = {
        "age_bp": [],
        "younger_bp": [],
        "older_bp": [],
    }
    negative_bound_samples: list[str] = []
    for age in ages:
        sample = samples[age["subject_id"]]
        core = units[age["collection_unit_id"]]
        key = (core, Decimal(str(sample["source_depth"])))
        published = source.get(key)
        if published is None or key in matched:
            raise ValueError("Published and Neotoma core-depth identity differs")
        matched.add(key)
        by_core[core] += 1
        for field, published_field, neotoma_field in (
            ("age_bp", "Age dated [ka BP]", "source_age_value"),
            ("younger_bp", "Age min [ka]", "source_age_younger"),
            ("older_bp", "Age max [ka]", "source_age_older"),
        ):
            residual = abs(
                Decimal(published[published_field]) * 1000 - Decimal(age[neotoma_field])
            )
            absolute_residuals[field].append(residual)
            if residual > Decimal("0.5"):
                raise ValueError(f"Published {field} differs from Neotoma at {key}")
        if Decimal(published["Age min [ka]"]) < 0:
            negative_bound_samples.append(age["subject_id"])
            if age["admission_reason"] != "negative_bp":
                raise ValueError("Negative published bound lost its Neotoma refusal")
    if matched != set(source) or by_core != {"SOLSOE81": 66, "SOLSOE83": 26}:
        raise ValueError("Published Solsø core coverage changed")
    if len(negative_bound_samples) != 1:
        raise ValueError("Published negative-bound denominator changed")

    return {
        "schema_version": "solsoe-published-epd-age-join.v1",
        "published_source": {
            "doi": "10.1594/PANGAEA.804596",
            "sha256": PUBLISHED_SHA256,
            "bytes": len(published_bytes),
            "table_rows": len(all_rows),
            "age_unit": "ka BP",
            "depth_unit": "m",
            "license": "CC-BY-3.0",
        },
        "neotoma_source": {
            "relational_manifest_sha256": RELATIONAL_MANIFEST_SHA256,
            "source_snapshot_id": manifest["source_snapshot_id"],
            "build_id": manifest["build_id"],
        },
        "core_depth_matches": dict(sorted(by_core.items())),
        "calibrated_sample_matches": len(matched),
        "largest_absolute_residual_bp": {
            field: float(max(residuals))
            for field, residuals in absolute_residuals.items()
        },
        "published_negative_younger_bound_sample_ids": sorted(negative_bound_samples),
        "other_danish_source_handles_absent": sorted(OTHER_DANISH_HANDLES),
        "lra_admitted_samples": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--published", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.repository.resolve(), args.published.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print("Solsø published EPD ages: 92/92 core-depth and three-field matches")


if __name__ == "__main__":
    main()
