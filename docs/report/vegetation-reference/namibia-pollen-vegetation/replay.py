"""Join authenticated Namibian soil-pollen and vegetation source rows."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from decimal import Decimal
from pathlib import Path


SOURCES = {
    "PANGAEA.931033.tab": "73c62c335a227283c27a224304b52fd21d1c674f95551d58a2e42dffa325a2e1",
    "PANGAEA.931035.tab": "b2460910d5f72e234fef50a24c4ade08e57ab714bf482ba4afb3b4ed8e7b4f2a",
}
TAXA = (
    ("Acacia", "Aca [#]", "Acacia [m**2]"),
    ("Dichrostachys", "Dichrostachys [#]", "Dichrostachys [m**2]"),
    ("Grewia", "Grewia [#]", "Grewia [m**2]"),
    ("Poaceae", "Poac [#]", "Poaceae [m**2]"),
    ("Combretaceae", "Comeae [#]", "Combretaceae [m**2]"),
)
POLLEN_COLUMNS = ("Event", "Latitude", "Longitude", *(item[1] for item in TAXA))
VEGETATION_COLUMNS = (
    "Event",
    "Latitude",
    "Longitude",
    "Ring sect radius [m]",
    *(item[2] for item in TAXA),
)
PAIRED_COLUMNS = (
    "event",
    "latitude_display",
    "longitude_display",
    "ring_sector_radius_m",
    "taxon",
    "pollen_count",
    "five_taxon_pollen_sum",
    "pollen_fraction_conditional_five_taxa",
    "vegetation_area_m2",
    "five_taxon_area_sum_m2",
    "area_fraction_conditional_five_taxa",
)
FRACTION_PRECISION = Decimal("0.000000000001")


def _read_source(path: Path, expected_columns: tuple[str, ...]) -> list[dict[str, str]]:
    source = path.read_bytes()
    if hashlib.sha256(source).hexdigest() != SOURCES[path.name]:
        raise ValueError(f"Source checksum differs: {path.name}")
    content = source.decode("utf-8")
    if "Creative Commons Attribution 4.0 International (CC-BY-4.0)" not in content:
        raise ValueError(f"Source license declaration absent: {path.name}")
    if "*/\n" not in content:
        raise ValueError(f"Source table delimiter absent: {path.name}")
    reader = csv.DictReader(io.StringIO(content.split("*/\n", 1)[1]), delimiter="\t")
    if tuple(reader.fieldnames or ()) != expected_columns:
        raise ValueError(f"Source table columns differ: {path.name}")
    rows = list(reader)
    if any(None in row or any(value == "" for value in row.values()) for row in rows):
        raise ValueError(f"Source table has incomplete rows: {path.name}")
    return rows


def _fraction(numerator: Decimal, denominator: Decimal) -> str:
    if denominator <= 0:
        raise ValueError("Five-taxon denominator must be positive")
    return str((numerator / denominator).quantize(FRACTION_PRECISION))


def build(source_dir: Path) -> tuple[bytes, dict[str, object]]:
    """Return deterministic source-row pairs and a descriptive report."""
    pollen = _read_source(source_dir / "PANGAEA.931033.tab", POLLEN_COLUMNS)
    vegetation = _read_source(source_dir / "PANGAEA.931035.tab", VEGETATION_COLUMNS)
    if len(pollen) != 10 or len(vegetation) != 150:
        raise ValueError("Expected ten pollen sites and 150 vegetation site-rings")
    pollen_by_event = {row["Event"]: row for row in pollen}
    if len(pollen_by_event) != len(pollen):
        raise ValueError("Duplicate pollen event")
    vegetation_keys = [(row["Event"], row["Ring sect radius [m]"]) for row in vegetation]
    if len(set(vegetation_keys)) != len(vegetation_keys):
        raise ValueError("Duplicate vegetation event and radius")
    radii = tuple(range(100, 1501, 100))
    if {Decimal(row["Ring sect radius [m]"]) for row in vegetation} != {
        Decimal(radius) for radius in radii
    }:
        raise ValueError("Vegetation radius support differs")
    if {row["Event"] for row in vegetation} != set(pollen_by_event):
        raise ValueError("Pollen and vegetation events differ")
    for event in pollen_by_event:
        observed = {int(row["Ring sect radius [m]"]) for row in vegetation if row["Event"] == event}
        if observed != set(radii):
            raise ValueError(f"Vegetation ring support differs: {event}")

    paired: list[dict[str, str]] = []
    event_order = {row["Event"]: index for index, row in enumerate(pollen)}
    for row in sorted(
        vegetation,
        key=lambda item: (event_order[item["Event"]], int(item["Ring sect radius [m]"])),
    ):
        site = pollen_by_event[row["Event"]]
        if (site["Latitude"], site["Longitude"]) != (row["Latitude"], row["Longitude"]):
            raise ValueError(f"Source coordinates differ: {row['Event']}")
        counts = [int(site[pollen_col]) for _, pollen_col, _ in TAXA]
        areas = [Decimal(row[area_col]) for _, _, area_col in TAXA]
        if any(value < 0 for value in counts) or any(value < 0 for value in areas):
            raise ValueError("Negative pollen or vegetation value")
        count_sum = sum(counts)
        area_sum = sum(areas, Decimal(0))
        for (taxon, _, area_col), count, area in zip(TAXA, counts, areas, strict=True):
            paired.append(
                {
                    "event": row["Event"],
                    "latitude_display": site["Latitude"],
                    "longitude_display": site["Longitude"],
                    "ring_sector_radius_m": row["Ring sect radius [m]"],
                    "taxon": taxon,
                    "pollen_count": str(count),
                    "five_taxon_pollen_sum": str(count_sum),
                    "pollen_fraction_conditional_five_taxa": _fraction(Decimal(count), Decimal(count_sum)),
                    "vegetation_area_m2": row[area_col],
                    "five_taxon_area_sum_m2": str(area_sum),
                    "area_fraction_conditional_five_taxa": _fraction(area, area_sum),
                }
            )

    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=PAIRED_COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(paired)
    pairs_bytes = buffer.getvalue().encode("utf-8")
    report: dict[str, object] = {
        "schema_version": "namibia-modern-pollen-vegetation-source-join.v1",
        "status": "source_rows_joined",
        "source": {
            "citation": "Tabares et al. (2021), PANGAEA dataset series 10.1594/PANGAEA.931037",
            "rights": "CC BY 4.0; cite both source datasets and parent series",
            "pollen": {"doi": "10.1594/PANGAEA.931033", "sha256": SOURCES["PANGAEA.931033.tab"]},
            "vegetation": {"doi": "10.1594/PANGAEA.931035", "sha256": SOURCES["PANGAEA.931035.tab"]},
        },
        "join": {
            "event_count": len(pollen),
            "pollen_row_count": len(pollen),
            "vegetation_row_count": len(vegetation),
            "site_radius_pair_count": len(vegetation),
            "taxon_pair_count": len(paired),
            "taxa": [item[0] for item in TAXA],
            "radius_values_m": list(radii),
            "radius_100m_site_count": sum(row["Ring sect radius [m]"] == "100" for row in vegetation),
            "radius_100m_taxon_pair_count": sum(row["ring_sector_radius_m"] == "100" for row in paired),
            "five_taxon_pollen_mass_once_per_site": sum(sum(int(row[col]) for _, col, _ in TAXA) for row in pollen),
            "coordinates": "exact match at displayed four-decimal source precision",
            "denominators": "five listed taxa only; neither total terrestrial pollen nor total vegetation cover",
            "paired_csv_sha256": hashlib.sha256(pairs_bytes).hexdigest(),
        },
        "interpretation": "Source-row pairing for an out-of-domain modern soil-pollen development cohort; no model fit, score, Nordic vegetation validation, or selected pollen-source radius.",
        "temporal_support": "Exact soil-sampling and satellite-image dates are not stated in these source tables.",
        "ring_semantics": "Publisher labels radius in 100 m steps; paired rows preserve that label without reinterpreting ring area or selecting an ecological source radius.",
    }
    return pairs_bytes, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists() or args.output_dir.is_symlink():
        raise ValueError(f"output directory must be absent: {args.output_dir}")
    pairs_bytes, report = build(args.source_dir)
    args.output_dir.mkdir(parents=True)
    (args.output_dir / "paired.csv").write_bytes(pairs_bytes)
    (args.output_dir / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
