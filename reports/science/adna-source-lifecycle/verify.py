"""Independently compare whole exported records and exact retained source partitions."""

from __future__ import annotations

from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import sys
from typing import Any
import zipfile


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def main() -> None:
    source, output, result = map(Path, sys.argv[1:])
    comparisons: list[dict[str, Any]] = []
    totals: Counter[str] = Counter()
    forbidden = {
        "pollen_count",
        "pollen_sum",
        "relative_pollen_percentage",
        "ppe",
        "fall_speed_m_s",
        "whole_pollen",
    }
    animal_ids: set[str] = set()
    human_ids: set[str] = set()
    for country in ("Denmark", "Finland", "Norway", "Sweden"):
        slug = country.lower()
        base = source / "docs/report/countries" / slug
        for kind, suffix in (("aadr", "aadr"), ("animal", "animal_adna")):
            generated = output / f"{slug}_{kind}.csv"
            retained = base / f"{slug}_{suffix}_v66_samples.csv"
            actual_rows = rows(generated)
            original_rows = rows(retained)
            if generated.read_bytes() != retained.read_bytes():
                differing = [
                    i
                    for i, (a, b) in enumerate(
                        zip(actual_rows, original_rows, strict=False)
                    )
                    if a != b
                ]
                raise ValueError(
                    f"Exact {country} {kind} CSV mismatch; rows {differing[:10]}; lengths {len(actual_rows)}/{len(original_rows)}"
                )
            if actual_rows and forbidden.intersection(actual_rows[0]):
                raise ValueError(
                    "Pollen measurement semantics leaked into DNA country contract"
                )
            for row in actual_rows:
                if kind == "aadr":
                    if (
                        row["source_family"] != "AADR"
                        or row["sample_namespace"] != "homo_sapiens:aadr_genetic_id"
                        or row["species_latin_name"] != "Homo sapiens"
                    ):
                        raise ValueError("Human source/species/namespace changed")
                    human_ids.add(row["genetic_id"])
                else:
                    if row["sample_namespace"].startswith("homo_sapiens"):
                        raise ValueError("Animal record entered human namespace")
                    animal_ids.add(row["sample_record_id"])
            totals[kind] += len(actual_rows)
            comparisons.append(
                {
                    "country": country,
                    "kind": kind,
                    "rows": len(actual_rows),
                    "all_fields_and_order_byte_equal": True,
                    "source_sha256": digest(retained),
                    "actual_sha256": digest(generated),
                }
            )
        actual_summary = json.loads((output / f"{slug}_animal.json").read_text())
        original_summary = json.loads(
            (base / f"{slug}_animal_adna_v66_summary.json").read_text()
        )
        if actual_summary != original_summary:
            changed = [
                key
                for key in set(actual_summary) | set(original_summary)
                if actual_summary.get(key) != original_summary.get(key)
            ]
            raise ValueError(f"Complete {country} animal bundle mismatch: {changed}")
        human_summary = json.loads((base / f"{slug}_aadr_v66_summary.json").read_text())
        if human_summary["total_unique_samples"] != sum(
            row["country"] == country and row["kind"] == "aadr" and row["rows"]
            for row in comparisons
        ):
            raise ValueError("Human country denominator mismatch")
    if (
        totals != Counter(aadr=1231, animal=12)
        or len(human_ids) != 1231
        or len(animal_ids) != 12
    ):
        raise ValueError("Current source country populations differ")
    human: dict[str, Any] = json.loads(
        (output.parent / "human-entities/report.json").read_text()
    )
    animal: dict[str, Any] = json.loads(
        (output.parent / "animal-entities/report.json").read_text()
    )
    if (
        human["source_genetic_ids"],
        human["published"],
        human["excluded_missing_coordinates"],
    ) != (1325, 1231, 94):
        raise ValueError("Human raw-source partition mismatch")
    if (
        animal["normalized_sample_ids"],
        animal["mapped_sample_ids"],
        animal["excluded_sample_ids"],
    ) != (1468, 322, 1146):
        raise ValueError("Animal source partition mismatch")
    if (
        human["map_admitted"]
        or human["scientifically_admitted"]
        or animal["country_assignment_admitted"]
        or animal["scientifically_admitted"]
    ):
        raise ValueError("Source qualification promoted scientific admission")
    normalized: list[dict[str, str]] = []
    for path in sorted(
        (source / "data/adna/species").glob("*/normalized/sample_records.csv")
    ):
        normalized.extend(rows(path))
    domain_sources: list[dict[str, Any]] = []
    for path in sorted(
        (source / "data/adna/species").glob("*/normalized/sample_records.json")
    ):
        payload = json.loads(path.read_text())
        if (
            payload["evidence_domain"] != "animal_ancient_dna"
            or payload["pollen_eligible"] is not False
            or payload["pollen_propagation_eligible"] is not False
        ):
            raise ValueError(
                "Actual normalized animal source flags allow pollen admission"
            )
        if len(payload["samples"]) != payload["admitted_sample_count"]:
            raise ValueError("Animal source JSON population differs")
        domain_sources.append(
            {
                "path": str(path.relative_to(source)),
                "sha256": digest(path),
                "samples": len(payload["samples"]),
                "pollen_eligible": False,
                "pollen_propagation_eligible": False,
            }
        )
    if (
        len(domain_sources) != 10
        or sum(row["samples"] for row in domain_sources) != 1468
    ):
        raise ValueError("Actual animal domain source population differs")
    families = Counter(row["source_family"] for row in normalized)
    modalities = Counter(row["record_modality"] for row in normalized)
    if len(normalized) != 1468 or families != Counter(
        ENA=1411, BioProject=22, SRA=20, GenBank=15
    ):
        raise ValueError("Full retained animal source-family population changed")
    if modalities != Counter(archive_reads=1442, mitogenome_only=26):
        raise ValueError("Full animal source modality population changed")
    if any(forbidden.intersection(row) for row in normalized):
        raise ValueError(
            "Pollen measurement fields entered normalized animal source contract"
        )
    backlinks = json.loads(
        (Path(__file__).parent / "source-backlinks.json").read_text()
    )
    for link in backlinks["references"]:
        physical = source / link["path"]
        if digest(physical) != link["sha256"]:
            raise ValueError("Animal provenance source pointer differs")
        if link["kind"] == "zip-member":
            with zipfile.ZipFile(physical) as archive:
                content = archive.read(link["member"])
            if (
                len(content) != link["member_bytes"]
                or hashlib.sha256(content).hexdigest() != link["member_sha256"]
            ):
                raise ValueError("Animal source member pointer differs")
    evidence_counts = {
        "source_families": dict(families),
        "actual_domain_flags": domain_sources,
        "modalities": dict(modalities),
        "actual_source_backlinks": len(backlinks["references"]),
        "historical_metadata_without_declared_hash": sum(
            link.get("historical_metadata_digest_present") is False
            for link in backlinks["references"]
        ),
    }
    evidence = {
        "schema_version": "adna-source-country-lifecycle.v1",
        "countries": comparisons,
        "complete_animal_bundles_equal": 4,
        "normalized_source_contracts": evidence_counts,
        "source_partition": {
            "human_source_ids": 1325,
            "human_published": 1231,
            "human_missing_coordinates": 94,
            "animal_source_ids": 1468,
            "animal_mapped": 322,
            "animal_excluded": 1146,
            "animal_nordic": 12,
        },
        "scope": "Four actual human source loaders/CSV writers and four actual animal source bundle/CSV writers, exact every-cell and source-record partition correspondence. Separate controlled boundary tests do not constitute accepted empirical events or a complete map/publication replay.",
        "scientific_admission": False,
        "accepted_propagation_mapping_count": 0,
    }
    result.write_text(json.dumps(evidence, indent=2) + "\n")
    print(
        json.dumps(
            {
                "csv_comparisons": len(comparisons),
                "complete_animal_bundles": 4,
                "human_records": totals["aadr"],
                "animal_records": totals["animal"],
            }
        )
    )


if __name__ == "__main__":
    main()
