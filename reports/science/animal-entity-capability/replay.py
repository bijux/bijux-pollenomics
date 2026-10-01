"""Check animal sample ownership across normalized records and map decisions."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
from hashlib import sha256
import json
from pathlib import Path


def _identity(path: Path, root: Path) -> dict[str, object]:
    content = path.read_bytes()
    return {
        "path": path.relative_to(root).as_posix(),
        "bytes": len(content),
        "sha256": sha256(content).hexdigest(),
    }


def run(root: Path, output: Path) -> None:
    if output.exists():
        raise ValueError(f"Output directory already exists: {output}")
    foundation_path = root / "data/adna/governance/animal_sample_foundation_truth.json"
    candidates_path = root / "data/adna/final/atlas/animal_atlas_point_candidates.json"
    exclusions_path = root / "docs/report/animal_atlas_exclusion_report.json"
    foundation = json.loads(foundation_path.read_text(encoding="utf-8"))
    candidates = json.loads(candidates_path.read_text(encoding="utf-8"))
    exclusions = json.loads(exclusions_path.read_text(encoding="utf-8"))
    if (
        foundation["schema_version"] != "animal-sample-foundation-truth.v1"
        or candidates["schema_version"] != "animal-atlas-point-candidates.v1"
        or exclusions["schema_version"] != "animal-atlas-exclusion-report.v1"
    ):
        raise ValueError("Animal source or map decision schema changed")

    sample_files = sorted(
        (root / "data/adna/species").glob("*/normalized/sample_records.csv")
    )
    samples = {}
    for path in sample_files:
        with path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                sample_id = row["stable_sample_id"]
                if sample_id in samples:
                    raise ValueError(f"Duplicate normalized animal sample: {sample_id}")
                samples[sample_id] = row
    if (
        len(sample_files) != foundation["summary"]["tracked_species_count"]
        or len(samples) != foundation["summary"]["sample_row_count"]
    ):
        raise ValueError("Animal normalized sample population differs from foundation")

    mapped = {}
    nordic = {}
    for feature in candidates["rows"]:
        for sample_id in feature["sample_record_ids"]:
            if sample_id in mapped:
                raise ValueError(
                    f"Animal sample appears in two map features: {sample_id}"
                )
            mapped[sample_id] = feature["feature_id"]
            if feature["nordic_inclusion"] is True:
                nordic[sample_id] = feature["political_entity"]
    excluded = {}
    for row in exclusions["rows"]:
        sample_id = row["sample_record_id"]
        if sample_id in excluded:
            raise ValueError(f"Duplicate animal map exclusion: {sample_id}")
        excluded[sample_id] = row
    if set(mapped) & set(excluded) or set(mapped) | set(excluded) != set(samples):
        raise ValueError(
            "Mapped and excluded animal samples do not partition foundation"
        )
    if (
        len(candidates["rows"]) != candidates["row_count"]
        or len(excluded) != exclusions["row_count"]
    ):
        raise ValueError("Animal map output row count changed")
    for sample_id, row in excluded.items():
        source = samples[sample_id]
        if (
            row["species_latin_name"] != source["species_latin_name"]
            or row["project_accession"] != source["project_accession"]
        ):
            raise ValueError(f"Animal exclusion lineage differs: {sample_id}")

    nordic_counts = dict(sorted(Counter(nordic.values()).items()))
    if set(nordic_counts) - {"Denmark", "Finland", "Norway", "Sweden"}:
        raise ValueError("Nordic animal feature uses unexpected country label")
    report = {
        "schema_version": "animal-entity-capability.v1",
        "inputs": [
            _identity(path, root)
            for path in (
                *sample_files,
                foundation_path,
                candidates_path,
                exclusions_path,
            )
        ],
        "normalized_sample_ids": len(samples),
        "map_feature_count": len(candidates["rows"]),
        "mapped_sample_ids": len(mapped),
        "excluded_sample_ids": len(excluded),
        "map_exclusion_reasons": dict(
            sorted(
                Counter(row["exclusion_reason"] for row in excluded.values()).items()
            )
        ),
        "nordic_map_feature_count": sum(
            feature["nordic_inclusion"] is True for feature in candidates["rows"]
        ),
        "nordic_mapped_sample_ids": len(nordic),
        "nordic_mapped_country_labels": nordic_counts,
        "country_assignment_admitted": False,
        "scientifically_admitted": False,
        "decision_sources": {
            "mapped_sample_ids": candidates_path.relative_to(root).as_posix(),
            "excluded_sample_ids": exclusions_path.relative_to(root).as_posix(),
        },
    }
    output.mkdir(parents=True)
    (output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"reconciled {len(samples)} animal sample IDs: "
        f"{len(mapped)} mapped, {len(excluded)} map-excluded, "
        f"{len(nordic)} mapped with Nordic labels"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()
    run(arguments.repository.resolve(), arguments.output.resolve())
