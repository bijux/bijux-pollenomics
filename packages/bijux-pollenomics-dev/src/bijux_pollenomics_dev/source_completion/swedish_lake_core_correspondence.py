"""Compare two Swedish lake core leads across retained Neotoma and LandClim sources."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from math import isfinite
from pathlib import Path
from typing import Any

from .abborrtjarne_core import _distance_m, _workbook_row

LEADS = (
    (28869, 53995, 552101, 978, "BUS"),
    (28872, 54001, 552389, 977, "BOKE"),
)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _raw_count_summary(datums: list[dict[str, Any]]) -> dict[str, Any]:
    """Preserve pure pollen and every other native NISP label separately."""
    pollen_count = 0
    pollen_observations = 0
    other_count = 0
    other_observations = 0
    non_nisp = 0
    label_observations: Counter[str] = Counter()
    label_mass: Counter[str] = Counter()
    non_nisp_units: Counter[str] = Counter()
    for datum in datums:
        if datum["units"] != "NISP":
            non_nisp += 1
            non_nisp_units[str(datum["units"])] += 1
            continue
        value = datum["value"]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError("Native NISP must be an exact nonnegative integer")
        label = f"{datum['element']!s}/{datum['elementtype']!s}"
        label_observations[label] += 1
        label_mass[label] += value
        if datum["element"] == datum["elementtype"] == "pollen":
            pollen_count += value
            pollen_observations += 1
        else:
            other_count += value
            other_observations += 1
    return {
        "pollen_observations": pollen_observations,
        "pollen_count": pollen_count,
        "other_nisp_observations": other_observations,
        "other_nisp_count": other_count,
        "non_nisp_observations": non_nisp,
        "original_nisp_element_labels": {
            label: {
                "observations": label_observations[label],
                "count_sum": label_mass[label],
            }
            for label in sorted(label_observations)
        },
        "non_nisp_unit_counts": dict(sorted(non_nisp_units.items())),
    }


def _native_series_summary(samples: list[dict[str, Any]]) -> dict[str, Any]:
    """Audit native count mass and age claims without choosing an LRA denominator."""
    seen: set[int] = set()
    totals: Counter[str] = Counter()
    chronology_names: Counter[str] = Counter()
    age_units: Counter[str] = Counter()
    single_ages: list[float] = []
    for sample in samples:
        sample_id = sample["sampleid"]
        if sample_id in seen:
            raise ValueError("Native series repeats a sample ID")
        seen.add(sample_id)
        counts = _raw_count_summary(sample["datum"])
        totals["pollen_nisp"] += counts["pollen_count"]
        totals["other_nisp"] += counts["other_nisp_count"]
        totals["non_nisp_observations"] += counts["non_nisp_observations"]
        totals["samples_with_pollen"] += counts["pollen_count"] > 0
        claims = sample["ages"]
        totals["samples_without_age_claim"] += not claims
        totals["samples_with_multiple_age_claims"] += len(claims) > 1
        if len(claims) == 1:
            claim = claims[0]
            chronology_names[str(claim["chronologyname"])] += 1
            age_units[str(claim["agetype"])] += 1
            age = claim["age"]
            if (
                isinstance(age, bool)
                or not isinstance(age, (int, float))
                or not isfinite(age)
            ):
                raise ValueError("Native single age claim is not finite and numeric")
            single_ages.append(float(age))
    return {
        "native_samples": len(samples),
        "samples_with_pollen_nisp": totals["samples_with_pollen"],
        "pure_pollen_nisp": totals["pollen_nisp"],
        "other_nisp": totals["other_nisp"],
        "non_nisp_observations": totals["non_nisp_observations"],
        "samples_without_age_claim": totals["samples_without_age_claim"],
        "samples_with_multiple_age_claims": totals["samples_with_multiple_age_claims"],
        "samples_with_single_age_claim": len(single_ages),
        "single_age_claim_range": [min(single_ages), max(single_ages)]
        if single_ages and len(age_units) == 1
        else None,
        "single_age_chronology_names": dict(sorted(chronology_names.items())),
        "single_age_units": dict(sorted(age_units.items())),
        "chronology_selection": "not_evaluated",
        "pollen_denominator_selection": "not_evaluated",
    }


def compare_lakes(
    raw_part: Path,
    raw_manifest: Path,
    workbook: Path,
    workbook_receipt: Path,
    count_mass: Path,
    projection: Path,
) -> dict[str, object]:
    """Retain agreements and discrepancies without promoting a cross-source join."""
    manifest = json.loads(raw_manifest.read_text())
    selected_part = next(
        part for part in manifest["parts"] if part["filename"] == raw_part.name
    )
    if selected_part["part_number"] != 8 or not all(
        dataset in selected_part["downloaded_dataset_ids"]
        for _, dataset, _, _, _ in LEADS
    ):
        raise ValueError("Selected Neotoma datasets are outside raw part 008")
    raw = json.loads(raw_part.read_text())
    if (
        raw["part_number"] != 8
        or raw["downloaded_dataset_ids"] != selected_part["downloaded_dataset_ids"]
    ):
        raise ValueError("Raw part and manifest dataset axes differ")
    receipt = json.loads(workbook_receipt.read_text())
    asset = next(
        item
        for item in receipt["assets"]
        if item["filename"] == workbook.name and item["dataset_id"] == "937075"
    )
    if _digest(workbook) != asset["sha256"]:
        raise ValueError("Pinned LandClim metadata workbook differs")
    mass = json.loads(count_mass.read_text())
    prerequisite = json.loads(projection.read_text())
    if (
        mass["schema_version"] != "neotoma-swedish-lake-count-mass-crosscheck.v1"
        or mass["lra_accepted_samples"] != 0
        or prerequisite["denominators"]["accepted_samples"] != 0
        or mass["source_snapshot_id"]
        != prerequisite["source_identities"]["source_snapshot_id"]
        or prerequisite["source_identities"]["raw_manifest_sha256"]
        != _digest(raw_manifest)
        or {row["sample_id"] for row in mass["sample_rows"]}
        != {f"neotoma:sample:{sample_id}" for _, _, sample_id, _, _ in LEADS}
    ):
        raise ValueError("Retained source admission or snapshot differs")
    results: list[dict[str, Any]] = []
    for site_id, dataset_id, sample_id, workbook_row, handle in LEADS:
        sites = [
            row["site"]
            for row in raw["rows"]
            if row["site"]["dataset"]["datasetid"] == dataset_id
        ]
        if len(sites) != 1 or sites[0]["siteid"] != site_id:
            raise ValueError("Selected Neotoma site/dataset identity differs")
        site = sites[0]
        core = site["collectionunit"]
        dataset = core["dataset"]
        samples = dataset["samples"]
        selected_samples = [row for row in samples if row["sampleid"] == sample_id]
        if len(selected_samples) != 1 or core["handle"] != handle:
            raise ValueError("Selected sample or native core handle differs")
        sample = selected_samples[0]
        header, published = _workbook_row(workbook, workbook_row)
        if (
            [header.get(key) for key in ("A", "B", "C", "D", "L", "N", "O", "Q")]
            != [
                "SiteName",
                "csvfilename",
                "siteType",
                "siteradius",
                "nPollenSamples",
                "TopBP",
                "BotBP",
                "chronologySource",
            ]
            or published["A"] != site["sitename"]
            or published["B"] != handle
            or published["C"] != "lake"
            or published["I"] != "Sweden"
            or int(published["L"]) != len(samples)
            or int(published["D"]) <= 0
        ):
            raise ValueError("Published and native lake axes differ")
        geometry = json.loads(site["geography"])
        if (
            geometry["type"] != "Point"
            or geometry["crs"]["properties"]["name"] != "EPSG:4326"
            or len(geometry["coordinates"]) != 2
        ):
            raise ValueError("Native point geometry or CRS differs")
        point = (
            float(geometry["coordinates"][0]),
            float(geometry["coordinates"][1]),
        )
        distance = _distance_m(point, (float(published["E"]), float(published["F"])))
        if distance > 1:
            raise ValueError("Published and native points differ beyond one metre")
        basin_rows = [
            row
            for row in prerequisite["basin_rows"]
            if row["site_id"] == f"neotoma:site:{site_id}"
        ]
        ages = [
            row
            for row in prerequisite["chronology_rows"]
            if row["sample_id"] == f"neotoma:sample:{sample_id}"
        ]
        if (
            len(basin_rows) != 1
            or basin_rows[0]["basin_disposition"] != "not_evaluated"
            or basin_rows[0]["candidate_basin_evidence"]
            or len(ages) != 1
            or ages[0]["site_id"] != f"neotoma:site:{site_id}"
            or ages[0]["chronology_disposition"] != "not_evaluated"
            or len(ages[0]["candidate_age_claims"]) != 1
        ):
            raise ValueError("Retained basin or chronology selection differs")
        age = ages[0]["candidate_age_claims"][0]["source_claim"]
        if len(sample["ages"]) != 1 or sample["ages"][0] != age["source_payload"]:
            raise ValueError("Raw and projected sample age claims differ")
        count_rows = [
            row
            for row in mass["sample_rows"]
            if row["sample_id"] == f"neotoma:sample:{sample_id}"
        ]
        counts = _raw_count_summary(sample["datum"])
        if (
            len(count_rows) != 1
            or count_rows[0]["known_compatible_pollen_denominator_status"]
            != "not_evaluated"
            or len(count_rows[0]["source_unit_partitions"]) != 1
        ):
            raise ValueError("Retained count-mass row differs")
        mass_row = count_rows[0]
        partition = mass_row["source_unit_partitions"][0]
        if (
            partition["source_unit"] != "NISP"
            or mass_row["observations"] != len(sample["datum"])
            or mass_row["count_candidate_observations"]
            != counts["pollen_observations"] + counts["other_nisp_observations"]
            or mass_row["refused_count_observations"] != counts["non_nisp_observations"]
            or partition["pollen_count_observations"] != counts["pollen_observations"]
            or partition["pollen_exact_count_sum"] != counts["pollen_count"]
            or partition["nonpollen_count_observations"]
            + partition["unresolved_label_count_observations"]
            != counts["other_nisp_observations"]
            or partition["nonpollen_exact_count_sum"]
            + partition["unresolved_label_exact_count_sum"]
            != counts["other_nisp_count"]
        ):
            raise ValueError("Raw first-sample mass and retained receipt differ")
        age_range = dataset["agerange"]
        if (
            len(age_range) != 1
            or age_range[0]["units"] != "Calibrated radiocarbon years BP"
        ):
            raise ValueError("Native dataset age-range units differ")
        series = _native_series_summary(samples)
        native_endpoints = series["single_age_claim_range"]
        if (
            series["single_age_units"]
            != {"Calibrated radiocarbon years BP": len(samples)}
            or native_endpoints is None
        ):
            raise ValueError("Native series lacks a common calibrated age axis")
        if native_endpoints != [age_range[0]["ageyoung"], age_range[0]["ageold"]]:
            raise ValueError("Native sample and dataset age endpoints differ")
        published_endpoints = [float(published["N"]), float(published["O"])]
        results.append(
            {
                "neotoma_site_id": f"neotoma:site:{site_id}",
                "neotoma_dataset_id": f"neotoma:dataset:{dataset_id}",
                "neotoma_sample_id": f"neotoma:sample:{sample_id}",
                "site_name": site["sitename"],
                "shared_core_handle": handle,
                "point_distance_m": distance,
                "neotoma_elevation_m": site["altitude"],
                "landclim_elevation_m": int(published["G"]),
                "neotoma_downloaded_sample_count": len(samples),
                "landclim_metadata_sample_count": int(published["L"]),
                "prerequisite_candidate_sample_count": basin_rows[0][
                    "candidate_sample_count"
                ],
                "neotoma_dataset_age_range": age_range[0],
                "first_sample_age_claim": age["source_payload"],
                "first_sample_counts": counts,
                "native_series_summary": series,
                "native_minus_published_age_end_labels_bp": [
                    native - published_age
                    for native, published_age in zip(
                        native_endpoints, published_endpoints, strict=True
                    )
                ],
                "retained_first_sample_nisp_partition": partition,
                "landclim_metadata_row": workbook_row,
                "landclim_site_radius_m": int(published["D"]),
                "landclim_top_bp_label": published["N"],
                "landclim_bottom_bp_label": published["O"],
                "landclim_chronology_source": published["Q"],
                "landclim_restriction_label": published["K"],
                "cross_source_core_identity": "not_established",
                "radius_transfer": "refused",
                "pollen_denominator_status": "not_evaluated",
                "rights_status": "not_evaluated",
                "lra_admitted_samples": 0,
            }
        )
    return {
        "schema_version": "swedish-lake-core-correspondence.v1",
        "source": "pinned_neotoma_and_landclim_ii_metadata",
        "lakes": results,
        "lra_admitted_samples": 0,
        "input_sha256": {
            "raw_part": _digest(raw_part),
            "raw_manifest": _digest(raw_manifest),
            "workbook": asset["sha256"],
            "workbook_receipt": _digest(workbook_receipt),
            "count_mass": _digest(count_mass),
            "projection": _digest(projection),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "raw_part",
        "raw_manifest",
        "workbook",
        "workbook_receipt",
        "count_mass",
        "projection",
        "output",
    ):
        parser.add_argument(f"--{name.replace('_', '-')}", type=Path, required=True)
    args = parser.parse_args()
    result = compare_lakes(
        args.raw_part,
        args.raw_manifest,
        args.workbook,
        args.workbook_receipt,
        args.count_mass,
        args.projection,
    )
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "report.json").write_text(json.dumps(result, indent=2) + "\n")
    lakes = result["lakes"]
    if not isinstance(lakes, list):
        raise ValueError("Lake comparison report lacks its two source rows")
    lines = [
        "# Swedish lake core correspondence leads",
        "",
        "Pinned Neotoma and LandClim II metadata agree on names, core handles, "
        "downloaded sample counts and points within one metre for these two "
        "lakes. The smaller prerequisite counts are candidate-filter counts, "
        "not the native dataset sample denominators.",
        "",
        "| Lake | Native / published / prerequisite samples | Point gap (m) | Native / published elevation (m) | Published radius (m) | First-sample pure pollen NISP / other NISP |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for lake in lakes:
        if not isinstance(lake, dict):
            raise ValueError("Lake comparison row is not an object")
        counts = lake["first_sample_counts"]
        assert isinstance(counts, dict)
        lines.append(
            f"| {lake['site_name']} | {lake['neotoma_downloaded_sample_count']} / "
            f"{lake['landclim_metadata_sample_count']} / "
            f"{lake['prerequisite_candidate_sample_count']} | "
            f"{lake['point_distance_m']:.3f} | "
            f"{lake['neotoma_elevation_m']} / {lake['landclim_elevation_m']} | "
            f"{lake['landclim_site_radius_m']} | "
            f"{counts['pollen_count']} / {counts['other_nisp_count']} |"
        )
    lines.extend(
        [
            "",
            "## Native series coverage",
            "",
            "These are source NISP partitions and unselected age claims, not LRA "
            "pollen denominators or a selected chronology.",
            "",
            "| Lake | Samples | Pure pollen NISP | Other NISP | Single age claims | Native age range (calibrated BP) | Native − published end labels (years) |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for lake in lakes:
        series = lake["native_series_summary"]
        age_range = series["single_age_claim_range"]
        age_text = (
            f"{age_range[0]:g}–{age_range[1]:g}" if age_range is not None else "none"
        )
        lines.append(
            f"| {lake['site_name']} | {series['native_samples']} | "
            f"{series['pure_pollen_nisp']} | {series['other_nisp']} | "
            f"{series['samples_with_single_age_claim']} | {age_text} | "
            f"{lake['native_minus_published_age_end_labels_bp'][0]:+.1f} / "
            f"{lake['native_minus_published_age_end_labels_bp'][1]:+.1f} |"
        )
    lines.extend(
        [
            "",
            "Source NISP categories, age claims, series-end labels, elevations "
            "and exact input hashes are retained in report.json. The different "
            "elevations and chronology labels still need source resolution. "
            "The published radii are not transferred to Neotoma; original "
            "pollen denominator, taxon/PPE mapping and analytical-use rights "
            "remain unreviewed. Zero Swedish LRA samples are admitted.",
        ]
    )
    (args.output / "REPORT.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({"lakes": len(lakes), "admitted_samples": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
