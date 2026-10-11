"""Describe pollen and vegetation composition distance at publisher radius labels."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

import replay


TAXA = tuple(item[0] for item in replay.TAXA)
RADII = tuple(range(100, 1501, 100))
SITE_COLUMNS = ("event", "ring_sector_radius_m", "hellinger_distance")


def _site_distances(paired_bytes: bytes) -> tuple[bytes, list[dict[str, object]]]:
    rows = list(csv.DictReader(io.StringIO(paired_bytes.decode("utf-8"))))
    if len(rows) != 750 or tuple(rows[0]) != replay.PAIRED_COLUMNS:
        raise ValueError("Joined source columns or row count differ")
    groups: dict[tuple[str, int], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[row["event"], int(row["ring_sector_radius_m"])].append(row)
    events = sorted({event for event, _ in groups})
    if len(events) != 10 or set(groups) != {(event, radius) for event in events for radius in RADII}:
        raise ValueError("Expected ten sites at each of 15 publisher radius labels")

    site_rows: list[dict[str, str]] = []
    by_radius: dict[int, list[float]] = defaultdict(list)
    for event in events:
        pollen_by_radius: list[tuple[str, ...]] = []
        for radius in RADII:
            group = groups[event, radius]
            if tuple(row["taxon"] for row in group) != TAXA:
                raise ValueError(f"Taxon order differs for {event} at {radius} m")
            pollen_by_radius.append(tuple(row["pollen_count"] for row in group))
            pollen_total = sum(int(row["pollen_count"]) for row in group)
            vegetation_total = sum(float(row["vegetation_area_m2"]) for row in group)
            if pollen_total <= 0 or vegetation_total <= 0:
                raise ValueError("Five-taxon composition requires positive mass")
            if any(int(row["five_taxon_pollen_sum"]) != pollen_total for row in group):
                raise ValueError("Pollen denominator differs from source counts")
            distance = math.sqrt(
                sum(
                    (
                        math.sqrt(int(row["pollen_count"]) / pollen_total)
                        - math.sqrt(float(row["vegetation_area_m2"]) / vegetation_total)
                    )
                    ** 2
                    for row in group
                )
                / 2
            )
            if not 0 <= distance <= 1:
                raise ValueError("Hellinger distance outside [0, 1]")
            site_rows.append(
                {
                    "event": event,
                    "ring_sector_radius_m": str(radius),
                    "hellinger_distance": f"{distance:.12f}",
                }
            )
            by_radius[radius].append(distance)
        if len(set(pollen_by_radius)) != 1:
            raise ValueError(f"Pollen sample differs across radius labels: {event}")

    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=SITE_COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(site_rows)
    summary: list[dict[str, object]] = []
    for radius in RADII:
        distances = by_radius[radius]
        summary.append(
            {
                "ring_sector_radius_m": radius,
                "independent_site_count": len(distances),
                "mean_hellinger_distance": round(statistics.mean(distances), 12),
                "median_hellinger_distance": round(statistics.median(distances), 12),
                "minimum_hellinger_distance": round(min(distances), 12),
                "maximum_hellinger_distance": round(max(distances), 12),
            }
        )
    return buffer.getvalue().encode("utf-8"), summary


def build(source_dir: Path) -> tuple[bytes, dict[str, object]]:
    """Return site-level descriptive distances and a source-bound summary."""
    paired_bytes, source_join = replay.build(source_dir)
    site_bytes, summary = _site_distances(paired_bytes)
    report: dict[str, object] = {
        "schema_version": "namibia-five-taxon-radius-sensitivity.v1",
        "question": "How does five-taxon pollen-to-vegetation composition distance vary across the publisher's radius labels at the same ten sites?",
        "source": source_join["source"],
        "input": {
            "joined_source_sha256": hashlib.sha256(paired_bytes).hexdigest(),
            "site_distances_sha256": hashlib.sha256(site_bytes).hexdigest(),
            "pollen_event_count": 10,
            "vegetation_site_radius_count": 150,
            "five_taxon_pair_count": 750,
        },
        "metric": {
            "name": "Hellinger composition distance",
            "formula": "sqrt(sum((sqrt(p_i)-sqrt(v_i))^2 for five taxa)/2)",
            "p_i": "pollen count for taxon i divided by the five named pollen counts at one site",
            "v_i": "calculated vegetation area for taxon i divided by the five named areas at one site and publisher radius label",
            "range": [0, 1],
            "interpretation": "descriptive conditional-composition mismatch; not a prediction or model score",
        },
        "radius_summary": summary,
        "independence": "Ten pollen sites are independent units for this description; each site's one pollen sample repeats across 15 radius labels.",
        "ring_semantics": "Radius is the publisher's 'Ring sect radius [m]' label. These source tables do not establish whether areas describe cumulative disks or disjoint rings; this analysis does not reinterpret them.",
        "limitations": [
            "Five listed taxa only; neither total terrestrial pollen nor total vegetation cover.",
            "Exact soil-sampling and satellite-image dates are not stated in these tables.",
            "Pollen productivity and dispersal differ by taxon, so descriptive distance does not select an ecological pollen-source radius.",
            "Out-of-domain Namibian soil samples do not validate Nordic lake predictions or establish an untouched confirmation cohort.",
        ],
    }
    return site_bytes, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists() or args.output_dir.is_symlink():
        raise ValueError(f"output directory must be absent: {args.output_dir}")
    site_bytes, report = build(args.source_dir)
    args.output_dir.mkdir(parents=True)
    (args.output_dir / "radius-sensitivity.csv").write_bytes(site_bytes)
    (args.output_dir / "radius-sensitivity.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
