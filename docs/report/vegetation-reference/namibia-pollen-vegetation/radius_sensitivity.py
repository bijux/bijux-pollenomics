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


def _site_distances(
    paired_bytes: bytes,
) -> tuple[bytes, list[dict[str, object]], dict[str, object]]:
    rows = list(csv.DictReader(io.StringIO(paired_bytes.decode("utf-8"))))
    if len(rows) != 750 or tuple(rows[0]) != replay.PAIRED_COLUMNS:
        raise ValueError("Joined source columns or row count differ")
    groups: dict[tuple[str, int], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[row["event"], int(row["ring_sector_radius_m"])].append(row)
    events = sorted({event for event, _ in groups})
    if len(events) != 10 or set(groups) != {
        (event, radius) for event in events for radius in RADII
    }:
        raise ValueError("Expected ten sites at each of 15 publisher radius labels")

    site_rows: list[dict[str, str]] = []
    by_radius: dict[int, list[float]] = defaultdict(list)
    area_by_series: dict[tuple[str, str], dict[int, float]] = defaultdict(dict)
    full_annulus_ratios: list[dict[str, object]] = []
    for event in events:
        pollen_by_radius: list[tuple[str, ...]] = []
        for radius in RADII:
            group = groups[event, radius]
            if tuple(row["taxon"] for row in group) != TAXA:
                raise ValueError(f"Taxon order differs for {event} at {radius} m")
            pollen_by_radius.append(tuple(row["pollen_count"] for row in group))
            pollen_total = sum(int(row["pollen_count"]) for row in group)
            areas = [float(row["vegetation_area_m2"]) for row in group]
            if any(not math.isfinite(area) or area < 0 for area in areas):
                raise ValueError("Vegetation area must be finite and nonnegative")
            vegetation_total = sum(areas)
            if (
                pollen_total <= 0
                or not math.isfinite(vegetation_total)
                or vegetation_total <= 0
            ):
                raise ValueError("Five-taxon composition requires positive finite mass")
            if any(int(row["five_taxon_pollen_sum"]) != pollen_total for row in group):
                raise ValueError("Pollen denominator differs from source counts")
            for row, area in zip(group, areas, strict=True):
                area_by_series[event, row["taxon"]][radius] = area
            full_annulus_area = math.pi * (radius**2 - (radius - 100) ** 2)
            full_annulus_ratios.append(
                {
                    "event": event,
                    "ring_sector_radius_m": radius,
                    "five_taxon_area_to_full_annulus_ratio": round(
                        vegetation_total / full_annulus_area, 12
                    ),
                }
            )
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
    decreases = 0
    affected_series = 0
    for event in events:
        for taxon in TAXA:
            series_areas = area_by_series[event, taxon]
            if set(series_areas) != set(RADII):
                raise ValueError("Vegetation radius coverage differs")
            series_decreases = sum(
                series_areas[radius] < series_areas[radius - 100]
                for radius in RADII[1:]
            )
            decreases += series_decreases
            affected_series += series_decreases > 0
    if len(full_annulus_ratios) != len(events) * len(RADII):
        raise ValueError("Full-annulus diagnostic population differs")
    ring_geometry: dict[str, object] = {
        "source_description_url": "https://doi.pangaea.de/10.1594/PANGAEA.931037",
        "publisher_description": "Mean cover of the studied taxa was calculated by 100 m rings.",
        "adjacent_site_taxon_comparisons": len(events) * len(TAXA) * (len(RADII) - 1),
        "adjacent_area_decreases": decreases,
        "site_taxon_series_with_decrease": affected_series,
        "full_annulus_width_m": 100,
        "full_annulus_area_formula": "pi * (outer_radius_m^2 - (outer_radius_m - 100)^2)",
        "full_annulus_ratio_interpretation": "The publisher radius label is assumed to be the outer radius of a hypothetical complete circular 100 m annulus. The five listed vegetation areas are divided by that full-annulus area. This is a geometric diagnostic, not measured whole-cover fraction or proof of the publisher's exact ring-sector mask.",
        "full_annulus_ratios": full_annulus_ratios,
    }
    return buffer.getvalue().encode("utf-8"), summary, ring_geometry


def build(source_dir: Path) -> tuple[bytes, dict[str, object]]:
    """Return site-level descriptive distances and a source-bound summary."""
    paired_bytes, source_join = replay.build(source_dir)
    site_bytes, summary, ring_geometry = _site_distances(paired_bytes)
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
        "ring_geometry": ring_geometry,
        "independence": "Ten pollen sites are independent units for this description; each site's one pollen sample repeats across 15 radius labels.",
        "ring_semantics": "The publisher describes mean cover by 100 m rings, and the retained area series include decreases incompatible with cumulative nonnegative-area disks on a fixed map. Full-annulus ratios assume radius labels are outer radii and complete circles; exact ring-sector geometry and masks are not supplied by these tables. No ecological source radius is selected.",
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
