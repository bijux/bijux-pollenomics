"""Compare two observed-pollen series with independent dated site context."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

PREPARED = Path("docs/report/pollen-reconstruction/swedish-direct-pollen/prepared")
SEAD = Path("data/sead/derived/sweden_archaeology_site_discovery.geojson")
LINEAGE = Path("docs/report/countries/sweden/pollen-model-lineage/report.json")
SITES = {"BUS": 53995, "BOKE": 54001}
TAXA = ("Alnus", "Plantago lanceolata")
BUS_INVENTORY_POINT = (55.44559, 13.80172)


def _identity(path: Path, repository: Path) -> dict[str, str]:
    return {
        "path": str(path.relative_to(repository)),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def _distance_km(lat_a: float, lon_a: float, lat_b: float, lon_b: float) -> float:
    a = (
        math.sin(math.radians(lat_b - lat_a) / 2) ** 2
        + math.cos(math.radians(lat_a))
        * math.cos(math.radians(lat_b))
        * math.sin(math.radians(lon_b - lon_a) / 2) ** 2
    )
    return 2 * 6371.0088 * math.asin(math.sqrt(a))


def _overlaps(start: float | None, end: float | None, lower: int, upper: int) -> bool:
    if start is None or end is None or start > end:
        return False
    if start == end:
        return lower <= start < upper
    return start < upper and end > lower


def _direction(before: float, after: float, minimum: float) -> int:
    delta = after - before
    return 1 if delta >= minimum else -1 if delta <= -minimum else 0


def _pollen_status(
    previous: dict[str, dict[str, Any]],
    current: dict[str, dict[str, Any]],
    taxon: str,
    minimum: float,
) -> str:
    signs: list[int] = []
    for site in SITES:
        cell_before, cell_after = previous[site], current[site]
        denominator_signs = [
            _direction(
                cell_before["taxa"][taxon][denominator],
                cell_after["taxa"][taxon][denominator],
                minimum,
            )
            for denominator in ("native_fraction", "closed_16_fraction")
        ]
        if 0 in denominator_signs or denominator_signs[0] != denominator_signs[1]:
            return "cannot_conclude_denominator_or_effect_threshold"
        signs.append(denominator_signs[0])
    return (
        "descriptive_agreement" if signs[0] == signs[1] else "descriptive_contradiction"
    )


def publish(repository: Path, output: Path) -> dict[str, Any]:
    """Retain source-supported counts, overlap context and qualified outcomes."""
    repository = repository.resolve()
    paths = [
        repository / PREPARED / f"dataset-{number}.json" for number in SITES.values()
    ]
    paths.extend((repository / SEAD, repository / LINEAGE))
    prepared = {
        site: json.loads((repository / PREPARED / f"dataset-{number}.json").read_text())
        for site, number in SITES.items()
    }
    if any(data["sample_age_bounds_present"] for data in prepared.values()):
        raise ValueError("Sample-age uncertainty contract changed")
    lineage = json.loads((repository / LINEAGE).read_text())
    if lineage["targets_sharing_bus_boke_grid"] != 5:
        raise ValueError("Modeled cover lineage requires new review")
    features = json.loads((repository / SEAD).read_text())["features"]
    centres = {
        site: (data["latitude"], data["longitude"]) for site, data in prepared.items()
    }
    centres["BUS_inventory"] = BUS_INVENTORY_POINT
    nearby: dict[str, dict[int, list[dict[str, Any]]]] = {
        centre: {10: [], 20: []} for centre in centres
    }
    for feature in features:
        geometry = feature.get("geometry")
        if not geometry or geometry["type"] != "Point":
            continue
        lon, lat = geometry["coordinates"]
        for centre, (centre_lat, centre_lon) in centres.items():
            distance = _distance_km(centre_lat, centre_lon, lat, lon)
            if distance <= 20:
                nearby[centre][20].append(feature["properties"])
                if distance <= 10:
                    nearby[centre][10].append(feature["properties"])
    common = set.intersection(*(set(data["bins"]) for data in prepared.values()))
    if common != {str(index) for index in range(-1, 12)}:
        raise ValueError("Common 500-cal-BP bin set changed")
    windows: list[dict[str, Any]] = []
    for index in sorted(map(int, common)):
        lower, upper = index * 500, (index + 1) * 500
        observations: dict[str, dict[str, Any]] = {}
        for site, data in prepared.items():
            cell = data["bins"][str(index)]
            taxa = {
                taxon: {
                    "count": cell["counts"][taxon],
                    "native_fraction": cell["counts"][taxon] / cell["all_nisp_count"],
                    "closed_16_fraction": cell["counts"][taxon]
                    / cell["closed_nisp_count"],
                }
                for taxon in TAXA
            }
            context = {}
            for centre_key, centre_label in (
                (site, "neotoma_point"),
                ("BUS_inventory", "inventory_point"),
            ):
                if centre_key != site and site != "BUS":
                    continue
                for radius in (10, 20):
                    overlapping = [
                        record
                        for record in nearby[centre_key][radius]
                        if _overlaps(
                            record.get("time_start_bp"),
                            record.get("time_end_bp"),
                            lower,
                            upper,
                        )
                    ]
                    context[f"{radius}km_{centre_label}"] = {
                        "dated_feature_count": len(overlapping),
                        "distinct_site_count": len(
                            {record["site_uuid"] for record in overlapping}
                        ),
                    }
            observations[site] = {
                "sample_count": cell["sample_count"],
                "all_native_nisp": cell["all_nisp_count"],
                "closed_16_nisp": cell["closed_nisp_count"],
                "taxa": taxa,
                "sead_chronology_context": context,
            }
        windows.append(
            {
                "bin_index": index,
                "lower_cal_bp": lower,
                "upper_cal_bp_exclusive": upper,
                "observations": observations,
                "sead_to_pollen_outcome": "incomparable_no_qualified_ecological_proxy",
                "land_use_outcome": "cannot_conclude_no_independent_vegetation_measurement",
            }
        )
    transitions = [
        {
            "older_bin_index": older["bin_index"],
            "younger_bin_index": younger["bin_index"],
            "taxon": taxon,
            "minimum_change_fraction": minimum,
            "pollen_site_direction_outcome": _pollen_status(
                older["observations"], younger["observations"], taxon, minimum
            ),
            "inference_scope": "descriptive_two_site_pollen_only_no_age_bounds",
        }
        for minimum in (0.005, 0.01)
        for younger, older in zip(windows, windows[1:], strict=False)
        for taxon in TAXA
    ]
    broad_windows: list[dict[str, Any]] = []
    for pair_start in range(0, 12, 2):
        pair = (windows[pair_start + 1], windows[pair_start + 2])
        broad_observations: dict[str, dict[str, Any]] = {}
        for site in SITES:
            native = sum(cell["observations"][site]["all_native_nisp"] for cell in pair)
            closed = sum(cell["observations"][site]["closed_16_nisp"] for cell in pair)
            broad_taxa: dict[str, dict[str, float | int]] = {}
            for taxon in TAXA:
                count = sum(
                    cell["observations"][site]["taxa"][taxon]["count"] for cell in pair
                )
                broad_taxa[taxon] = {
                    "count": count,
                    "native_fraction": count / native,
                    "closed_16_fraction": count / closed,
                }
            broad_observations[site] = {
                "all_native_nisp": native,
                "closed_16_nisp": closed,
                "taxa": broad_taxa,
            }
        broad_windows.append(
            {
                "lower_cal_bp": pair_start * 500,
                "upper_cal_bp_exclusive": (pair_start + 2) * 500,
                "observations": broad_observations,
            }
        )
    broad_transitions = [
        {
            "older_lower_cal_bp": older["lower_cal_bp"],
            "younger_lower_cal_bp": younger["lower_cal_bp"],
            "taxon": taxon,
            "minimum_change_fraction": minimum,
            "pollen_site_direction_outcome": _pollen_status(
                older["observations"], younger["observations"], taxon, minimum
            ),
        }
        for minimum in (0.005, 0.01)
        for younger, older in zip(broad_windows, broad_windows[1:], strict=False)
        for taxon in TAXA
    ]
    report: dict[str, Any] = {
        "schema_version": "swedish-two-lake-observed-pollen-trajectory.v1",
        "question": "Do BUS and BOKE observed pollen fractions move together across common 500-cal-BP bins, and can dated independent context support a land-use conclusion?",
        "answer": "Some source-local pollen changes may agree or contradict descriptively; dated SEAD site context lacks a qualified comparable ecological measurement, and LandClim grid 779 shares these input sites. No independent land-use or vegetation conclusion follows.",
        "bin_count": len(windows),
        "transition_count": len(transitions),
        "taxa": list(TAXA),
        "country_scope": {
            "SE": "two named Swedish sites; descriptive within-country question only",
            "DK": "not evaluated for this named two-site question",
            "NO": "not evaluated for this named two-site question",
            "FI": "not evaluated for this named two-site question",
        },
        "source_roles": {
            "neotoma": "two independent observed-pollen site series, same exact taxon labels",
            "sead": "independent dated site-location context only, not land-use magnitude",
            "landclim": "model grid 779 with BUS/BOKE input-lineage overlap, excluded from validation outcome",
        },
        "uncertainty": {
            "pollen_sample_age_bounds": "absent in both prepared cohorts",
            "bin_width_years": 500,
            "alternate_aggregation_width_years": 1000,
            "direction_thresholds_fraction": [0.005, 0.01],
            "denominators": ["all_native_nisp", "closed_16_nisp"],
            "sead_radii_km": [10, 20],
            "bus_alternate_centre": {
                "latitude": BUS_INVENTORY_POINT[0],
                "longitude": BUS_INVENTORY_POINT[1],
                "source": "Jenny et al. 2016 supplement Table S2; lake point, not BUS core",
                "url": "https://pure.mpg.de/rest/items/item_2354057/component/file_2357941/content",
            },
            "thresholds_are_sign_sensitivity_not_sampling_confidence_intervals": True,
        },
        "windows": windows,
        "transitions": transitions,
        "alternate_1000_year_windows": broad_windows,
        "alternate_1000_year_transitions": broad_transitions,
        "inputs": [_identity(path, repository) for path in paths],
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    with (output / "transitions.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=list(transitions[0]), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(transitions)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = publish(args.repository, args.output)
    print(
        json.dumps(
            {"bins": report["bin_count"], "transitions": report["transition_count"]}
        )
    )


if __name__ == "__main__":
    main()
