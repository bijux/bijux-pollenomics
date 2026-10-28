"""Contrast retained same-core native chronology profiles without fitting models."""

from __future__ import annotations

import argparse
from bisect import bisect_right
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
from typing import Any, cast


JsonMap = dict[str, Any]
DOMAIN = Path(__file__).resolve().parent
CAL_BP = "Calibrated radiocarbon years BP"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def point_window(value: object, edges: list[float]) -> int | None:
    if type(value) not in (int, float):
        raise ValueError("Source age is not a finite native number")
    number = cast(int | float, value)
    if not math.isfinite(number):
        raise ValueError("Source age is not a finite native number")
    if not edges[0] <= number < edges[-1]:
        return None
    return bisect_right(edges, number) - 1


def select(
    sample: JsonMap, cid: int, edges: list[float]
) -> tuple[int | None, JsonMap | None, str | None]:
    ages = [
        age
        for age in sample["typed_calibrated_source_ages"]
        if age["native_chronology_id"] == cid
    ]
    if len(ages) != 1:
        return None, None, "named_calibrated_age_missing_or_ambiguous"
    age: JsonMap = ages[0]
    if age["source_age_type"] != CAL_BP:
        raise ValueError("Named profile age scale differs")
    index = point_window(age["source_point_age"], edges)
    if age["window_index"] != index:
        raise ValueError("Native source age/window witness differs")
    if index is None:
        return None, age, "source_point_outside_declared_windows"
    panel = sample["strict_unique_literal_parameter_counts"]
    if not all(taxon in panel for taxon in ("Betula", "Poaceae")):
        return None, age, "literal_panel_missing_or_ambiguous"
    counts = [panel[taxon]["count"] for taxon in ("Betula", "Poaceae")]
    if any(type(count) is not int or count < 0 for count in counts):
        raise ValueError("Native panel counts are not nonnegative integers")
    if not sum(counts):
        return None, age, "explicit_allzero_panel"
    return index, age, None


def qualify(source_root: Path) -> tuple[JsonMap, JsonMap]:
    source_root = source_root.resolve(strict=True)
    custody: JsonMap = json.loads((DOMAIN / "source-custody.json").read_text())
    protocol: JsonMap = json.loads((DOMAIN / "protocol.json").read_text())
    for name, pin in custody.items():
        path = source_root / name
        if (
            path.is_symlink()
            or not path.is_file()
            or not path.resolve().is_relative_to(source_root)
            or path.stat().st_size != pin["bytes"]
            or sha(path) != pin["sha256"]
        ):
            raise ValueError("Retained source custody differs: " + name)

    def read(name: str) -> Any:
        return json.loads((source_root / name).read_text())

    native, original, eligibility = (
        read("native-results.json"),
        read("protocol.json"),
        read("source-eligibility.json"),
    )
    for name in ("native-terminal.json", "source-terminal.json"):
        receipt = read(name)
        if (
            receipt["status"] != "PASS"
            or type(receipt["native_exit_code"]) is not int
            or receipt["native_exit_code"] != 0
            or not receipt["custody_after_unchanged"]
        ):
            raise ValueError("Original native terminal is unqualified")
    native_terminal, source_terminal = (
        read("native-terminal.json"),
        read("source-terminal.json"),
    )
    if (
        native_terminal["product_files"]["physical-results.json"]["sha256"]
        != sha(source_root / "native-results.json")
        or source_terminal["product_files"]["eligibility-report.json"]["sha256"]
        != sha(source_root / "source-eligibility.json")
        or native["frozen_protocol_sha256"] != sha(source_root / "protocol.json")
        or original["source_eligibility_report_sha256"]
        != sha(source_root / "source-eligibility.json")
    ):
        raise ValueError("Original source/result/protocol identity differs")
    edges: list[float] = original["age_window_edges_cal_bp"]
    if len(edges) != 26 or native["literal_axis"] != protocol["literal_panel"]:
        raise ValueError("Original declared window/taxon universe differs")
    rows: list[JsonMap] = []
    summaries: list[JsonMap] = []
    private: list[JsonMap] = []
    verified_cells = 0
    for did, ref, alt in protocol["dataset_chronology_pairs"]:
        source = next(
            core for core in eligibility["cores"] if core["native_dataset_id"] == did
        )
        observations: list[JsonMap] = read(f"dataset-{did}-sample-eligibility.json")
        if (
            source_terminal["product_files"][f"dataset-{did}-sample-eligibility.json"][
                "sha256"
            ]
            != sha(source_root / f"dataset-{did}-sample-eligibility.json")
            or len(observations) != source["native_samples"]
        ):
            raise ValueError("Exact native sample authority differs")
        if len({sample["native_sample_id"] for sample in observations}) != len(
            observations
        ):
            raise ValueError("Native sample identity repeats")
        bins: dict[int, list[list[JsonMap]]] = {
            cid: [[] for _ in edges[:-1]] for cid in (ref, alt)
        }
        selected: dict[int, set[int]] = {ref: set(), alt: set()}
        migrations = Counter[str]()
        refusals: dict[int, Counter[str]] = {ref: Counter(), alt: Counter()}
        profiles: dict[int, JsonMap] = {}
        saved: dict[int, dict[int, JsonMap]] = {}
        for cid in (ref, alt):
            profile = next(
                p
                for p in native["single_dataset_profiles"]
                if p["selected_source_profile"]["native_dataset_id"] == did
                and p["selected_source_profile"]["native_chronology_id"] == cid
            )
            profile_record = profile["selected_source_profile"]
            if (
                profile_record["native_collection_unit_id"]
                != source["native_collection_unit_id"]
                or profile_record["literal_panel"] != protocol["literal_panel"]
                or source["native_chronologies"][str(cid)]["modelagetype"] != CAL_BP
            ):
                raise ValueError("Same-core native chronology/axis identity differs")
            profiles[cid] = profile
            baseline = [
                row
                for row in profile["conditional_results"]
                if row["physical_profile"] == protocol["physical_profile"]
            ]
            saved[cid] = {row["window_index"]: row for row in baseline}
            if len(saved[cid]) != len(baseline):
                raise ValueError("Baseline window identity repeats")
        for sample in observations:
            record: JsonMap = {
                "native_dataset_id": did,
                "native_sample_id": sample["native_sample_id"],
                "native_analysis_unit_id": sample["native_analysis_unit_id"],
                "source_depth": sample["source_depth"],
                "chronology_sides": {},
            }
            indices: list[int | None] = []
            for cid in (ref, alt):
                index, age, refusal = select(sample, cid, edges)
                indices.append(index)
                record["chronology_sides"][str(cid)] = {
                    "window_index": index,
                    "source_age": age,
                    "refusal": refusal,
                }
                if refusal:
                    refusals[cid][refusal] += 1
                else:
                    assert index is not None
                    selected[cid].add(sample["native_sample_id"])
                    bins[cid][index].append(sample)
            kind = (
                "both_refused"
                if indices == [None, None]
                else "reference_only"
                if indices[1] is None
                else "alternative_only"
                if indices[0] is None
                else "same_window"
                if indices[0] == indices[1]
                else "changed_window"
            )
            record["migration_status"] = kind
            migrations[kind] += 1
            private.append(record)
        for cid in (ref, alt):
            if len(selected[cid]) != profiles[cid]["selected_native_samples"]:
                raise ValueError("Selected native sample population differs")
            if {i for i, samples in enumerate(bins[cid]) if samples} != set(saved[cid]):
                raise ValueError("Occupied native window population differs")
            for index, row in saved[cid].items():
                support = row["source_support"]
                samples = bins[cid][index]
                counts = [
                    sum(
                        sample["strict_unique_literal_parameter_counts"][taxon]["count"]
                        for sample in samples
                    )
                    for taxon in protocol["literal_panel"]
                ]
                if (
                    set(support["native_sample_ids"])
                    != {sample["native_sample_id"] for sample in samples}
                    or set(support["native_analysis_unit_ids"])
                    != {sample["native_analysis_unit_id"] for sample in samples}
                    or support["counts"] != counts
                    or support["reported_source_pollen_NISP_sum"]
                    != sum(sample["reported_pollen_NISP"] for sample in samples)
                    or support["selected_panel_count_denominator"] != sum(counts)
                ):
                    raise ValueError(
                        "Saved numerical support differs from native source"
                    )
                verified_cells += 4
        deltas: list[float] = []
        for index in range(25):
            a, b = saved[ref].get(index), saved[alt].get(index)
            if a is not None and b is not None and a["deposition"] != b["deposition"]:
                raise ValueError("Paired physical factors differ")
            matched = a is not None and b is not None
            delta = (
                [
                    y - x
                    for x, y in zip(
                        a["conditional_panel_cover"], b["conditional_panel_cover"]
                    )
                ]
                if a is not None and b is not None
                else None
            )
            if delta is not None:
                deltas.append(delta[0])
            rows.append(
                {
                    "native_dataset_id": did,
                    "native_collection_unit_id": source["native_collection_unit_id"],
                    "reference_chronology_id": ref,
                    "alternative_chronology_id": alt,
                    "window_index": index,
                    "younger_cal_bp": edges[index],
                    "older_cal_bp_exclusive": edges[index + 1],
                    "status": "matched_saved_outputs"
                    if matched
                    else "reference_only"
                    if a is not None
                    else "alternative_only"
                    if b is not None
                    else "neither_source_supported",
                    "reference_samples": len(bins[ref][index]),
                    "alternative_samples": len(bins[alt][index]),
                    "shared_sample_count": len(
                        {s["native_sample_id"] for s in bins[ref][index]}
                        & {s["native_sample_id"] for s in bins[alt][index]}
                    ),
                    "reference_cover": a["conditional_panel_cover"]
                    if a is not None
                    else None,
                    "alternative_cover": b["conditional_panel_cover"]
                    if b is not None
                    else None,
                    "alternative_minus_reference_cover": delta,
                    "paired_standard_error": None,
                    "paired_standard_error_refusal": (
                        "Cross-chronology count and shared-PPE covariance not supplied; marginal errors cannot be assumed independent"
                        if matched
                        else "Two source-supported window outputs are required for a paired contrast"
                    ),
                    "vegetation_zero_inferred": False,
                }
            )
        summaries.append(
            {
                "native_dataset_id": did,
                "native_collection_unit_id": source["native_collection_unit_id"],
                "source_site_name": source["source_site_name"],
                "reference_chronology_id": ref,
                "alternative_chronology_id": alt,
                "reference_model": {
                    k: source["native_chronologies"][str(ref)][k]
                    for k in (
                        "chronologyname",
                        "agemodel",
                        "modelagetype",
                        "dateprepared",
                        "notes",
                    )
                },
                "alternative_model": {
                    k: source["native_chronologies"][str(alt)][k]
                    for k in (
                        "chronologyname",
                        "agemodel",
                        "modelagetype",
                        "dateprepared",
                        "notes",
                    )
                },
                "source_default_chronology": source["source_default_chronology"],
                "source_samples": len(observations),
                "selected_reference_samples": len(selected[ref]),
                "selected_alternative_samples": len(selected[alt]),
                "shared_selected_samples": len(selected[ref] & selected[alt]),
                "selected_cohort_symmetric_difference": len(
                    selected[ref] ^ selected[alt]
                ),
                "sample_migrations": dict(sorted(migrations.items())),
                "reference_refusals": dict(sorted(refusals[ref].items())),
                "alternative_refusals": dict(sorted(refusals[alt].items())),
                "matched_windows": len(deltas),
                "max_absolute_Betula_panel_share_change": max(map(abs, deltas)),
                "signed_Betula_change_at_max": max(deltas, key=abs),
                "current_native_rights_scope": source["local_rights_scope"],
            }
        )
    summary: JsonMap = {
        "schema_version": "swedish-native-chronology-contrast.v1",
        "source_custody": custody,
        "protocol": protocol,
        "original_numerical_candidate": native_terminal["candidate"],
        "original_source_candidate": source_terminal["candidate"],
        "literal_panel": protocol["literal_panel"],
        "original_PPE": native["ppe"],
        "original_PPE_SD": native["ppe_SD"],
        "original_physical_profile": protocol["physical_profile"],
        "pair_count": len(summaries),
        "full_declared_pair_windows": len(rows),
        "saved_support_scalar_comparisons": verified_cells,
        "pairs": summaries,
        "window_rows": rows,
        "age_epoch_and_scale_scope": original["age_support"],
        "uncertainty_scope": "Deterministic retained-output sensitivity at fixed parameter/physical inputs. Raw sample age bounds remain private unchanged; no age distribution or probability allocation. Paired SE withheld without cross-chronology count/PPE covariance.",
        "publication_scope": "Only aggregate derived source-qualified comparisons. Private exact native sample/depth/age/count records and original archives are not redistributed. Existing current public analytical-use and historical/private-source rights scopes remain distinct.",
        "scientific_limits": protocol["scope"],
    }
    return summary, {
        "sample_migrations": private,
        "scope": "Private original native sample/depth/raw-age witnesses; no redistribution",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    summary, private = qualify(args.source_root)
    args.output_root.mkdir(parents=True, exist_ok=False)
    for name, account in [
        ("chronology-contrasts.json", summary),
        ("private-sample-migrations.json", private),
    ]:
        with (args.output_root / name).open("x", encoding="utf-8") as stream:
            json.dump(account, stream, indent=2, ensure_ascii=False, allow_nan=False)
            stream.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
