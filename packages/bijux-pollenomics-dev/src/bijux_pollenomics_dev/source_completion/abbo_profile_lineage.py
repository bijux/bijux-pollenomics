"""Compare the Abborrtjärnen Neotoma sequence with its PANGAEA EPD profile."""

from __future__ import annotations

import argparse
import csv
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path
import re

PROFILE_SHA256 = "ee4671277fc4120c65f6fe4fa19fb1d302167e419d5419a55287d09c226ab154"
DATASET_ID = "19913"
SITE_ID = "13338"
TAXA = {
    "Alnus": "Aln [#]",
    "Betula": "Bet [#]",
    "Cyperaceae": "Cypae [#]",
    "Picea abies": "Pic.a [#]",
    "Poaceae": "Poac [#]",
}


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def build(repository: Path, profile: Path, output: Path) -> dict[str, object]:
    """Retain only matched lineage and source metadata, not source count rows."""
    repository, profile, output = (
        repository.resolve(),
        profile.resolve(),
        output.resolve(),
    )
    if output.exists() or output.is_symlink():
        raise ValueError("Absent output destination required")
    if profile.is_symlink() or not profile.is_file():
        raise ValueError("PANGAEA profile missing or linked")
    profile_bytes = profile.read_bytes()
    if _sha(profile_bytes) != PROFILE_SHA256:
        raise ValueError("PANGAEA profile digest changed")
    lines = profile_bytes.decode("utf-8").splitlines()
    if lines.count("*/") != 1:
        raise ValueError("PANGAEA profile metadata boundary changed")
    metadata = lines[: lines.index("*/")]
    event = next(line for line in metadata if line.startswith("Event(s):\tABBO *"))
    if "Area: 3 ha." not in event or "DATE/TIME: 2002-06-15T00:00:00" not in event:
        raise ValueError("PANGAEA core area or collection date changed")
    license_row = next(line for line in metadata if line.startswith("License:\t"))
    if "CC-BY-NC-3.0" not in license_row:
        raise ValueError("PANGAEA source license changed")
    reader = csv.DictReader(
        io.StringIO("\n".join(lines[lines.index("*/") + 1 :])), delimiter="\t"
    )
    if reader.fieldnames is None or not {"Depth sed [m]", *TAXA.values()}.issubset(
        reader.fieldnames
    ):
        raise ValueError("PANGAEA profile columns changed")
    source_rows = list(reader)
    if len(source_rows) != 107:
        raise ValueError("PANGAEA ABBO sample count changed")
    source_by_depth = {Decimal(row["Depth sed [m]"]): row for row in source_rows}
    if len(source_by_depth) != len(source_rows):
        raise ValueError("PANGAEA ABBO depth identity is ambiguous")

    sequence = repository / "docs/report/pollen-reconstruction/swedish-native-sequences"
    manifest_bytes = (sequence / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    authenticated = {}
    for filename in ("sites.json", "samples.json", "observations.json"):
        content = (sequence / filename).read_bytes()
        if _sha(content) != manifest["files_sha256"][filename]:
            raise ValueError(f"Governed Neotoma sequence digest changed: {filename}")
        authenticated[filename] = json.loads(content)
    sites = [
        row for row in authenticated["sites.json"] if row["dataset_id"] == DATASET_ID
    ]
    samples = [
        row for row in authenticated["samples.json"] if row["dataset_id"] == DATASET_ID
    ]
    observations = [
        row
        for row in authenticated["observations.json"]
        if row["dataset_id"] == DATASET_ID
    ]
    if (
        len(sites) != 1
        or sites[0]["site_id"] != SITE_ID
        or sites[0]["collection_unit_handle"] != "ABBO"
    ):
        raise ValueError("Neotoma ABBO source identity changed")
    neotoma_depths = {Decimal(row["depth"]) / 100 for row in samples}
    if len(samples) != 107 or neotoma_depths != set(source_by_depth):
        raise ValueError("Neotoma/PANGAEA ABBO depth series differs")
    observed = {}
    for row in observations:
        key = Decimal(row["depth"]) / 100, row["taxon_native"]
        if key in observed:
            raise ValueError("Neotoma ABBO repeats a taxon/depth cell")
        observed[key] = row["count"]
    taxon_results = []
    for taxon, column in TAXA.items():
        positive = 0
        for depth, row in source_by_depth.items():
            count = int(row[column])
            if count < 0 or observed.get((depth, taxon), 0) != count:
                raise ValueError(
                    f"PANGAEA/Neotoma ABBO {taxon} counts differ at {depth}"
                )
            positive += count > 0
        taxon_results.append(
            {
                "native_taxon": taxon,
                "pangaea_column": column,
                "matched_depths": 107,
                "positive_count_depths": positive,
            }
        )
    source_date = re.search(r"DATE/TIME: ([0-9-]+)T", event)
    if source_date is None:
        raise ValueError("PANGAEA ABBO date missing")
    report: dict[str, object] = {
        "schema_version": "neotoma-abbo-pangaea-lineage.v1",
        "source_profile_doi": "10.1594/PANGAEA.738429",
        "source_profile_url": "https://doi.pangaea.de/10.1594/PANGAEA.738429",
        "source_profile_sha256": PROFILE_SHA256,
        "source_profile_license": "CC-BY-NC-3.0",
        "governed_sequence_manifest_sha256": _sha(manifest_bytes),
        "dataset_id": DATASET_ID,
        "site_id": SITE_ID,
        "source_core_handle": "ABBO",
        "matched_sample_depths": len(source_by_depth),
        "source_depth_unit": "m",
        "neotoma_depth_source_unit": None,
        "depth_relation": "pangaea_m_equals_neotoma_native_divided_by_100_for_all_107_samples",
        "taxon_count_comparisons": len(taxon_results) * len(source_rows),
        "taxon_results": taxon_results,
        "pangaea_core_date": source_date.group(1),
        "neotoma_collection_date": sites[0]["collection_date"],
        "collection_date_agreement": source_date.group(1)
        == sites[0]["collection_date"],
        "pangaea_reported_lake_area_ha": 3,
        "pangaea_area_temporal_support": "source_event_metadata_only",
        "historical_basin_geometry_admitted": False,
        "lra_input_admitted": False,
    }
    output.mkdir(parents=True)
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    build(args.repository, args.profile, args.output)


if __name__ == "__main__":
    main()
