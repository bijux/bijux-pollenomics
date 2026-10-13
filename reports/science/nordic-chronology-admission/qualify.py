"""Account for every declared native source window without filling missing ages."""

from __future__ import annotations

import argparse
from bisect import bisect_right
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
from typing import Any, cast


DOMAIN = Path(__file__).resolve().parent
CAL_BP = "Calibrated radiocarbon years BP"
JsonMap = dict[str, Any]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def finite(value: object) -> float:
    if type(value) not in (int, float):
        raise ValueError("Native age is not finite numeric source evidence")
    number = cast(int | float, value)
    if not math.isfinite(number):
        raise ValueError("Native age is not finite numeric source evidence")
    return float(number)


def window(age: object, edges: list[float]) -> int | None:
    value = finite(age)
    if not edges[0] <= value < edges[-1]:
        return None
    return bisect_right(edges, value) - 1


def bound_support(age: JsonMap, index: int, edges: list[float]) -> str:
    younger, older = age.get("ageyounger"), age.get("ageolder")
    if younger is None or older is None:
        return "reported_bounds_missing"
    lower, upper, point = finite(younger), finite(older), finite(age["age"])
    if not lower <= point <= upper:
        return "reported_bounds_inconsistent_with_point"
    if lower < edges[0] or upper >= edges[-1]:
        return "reported_bounds_extend_outside_point_domain"
    if edges[index] <= lower <= upper < edges[index + 1]:
        return "reported_bounds_wholly_within_point_window"
    return "reported_bounds_cross_point_window_boundary"


def qualify(source_root: Path) -> tuple[JsonMap, JsonMap]:
    source_root = source_root.resolve(strict=True)
    pins = json.loads((DOMAIN / "source-custody.json").read_text())
    for name, pin in pins.items():
        path = source_root / name
        if (
            path.is_symlink()
            or not path.is_file()
            or not path.resolve().is_relative_to(source_root)
            or path.stat().st_size != pin["bytes"]
            or sha(path) != pin["sha256"]
        ):
            raise ValueError("Native source custody differs: " + name)

    def read(name: str) -> JsonMap:
        return cast(JsonMap, json.loads((source_root / name).read_text()))

    protocol, report = read("protocol.json"), read("report.json")
    source, terminal = (
        read("local-native-source-support.json"),
        read("native-terminal.json"),
    )
    if (
        type(terminal["native_exit_code"]) is not int
        or terminal["native_exit_code"] != 0
        or not terminal["custody_after_unchanged"]
        or terminal["native_files"]["local-native-source-support.json"]["sha256"]
        != sha(source_root / "local-native-source-support.json")
        or report["private_actual_source_support_sha256"]
        != sha(source_root / "local-native-source-support.json")
    ):
        raise ValueError("Original source execution identity differs")
    census = read("source-census.json")
    domain = read("source-domain.json")
    edges: list[float] = protocol["age_window_edges_cal_bp"]
    if len(edges) != 26 or any(
        finite(a) >= finite(b) for a, b in zip(edges, edges[1:])
    ):
        raise ValueError("Declared source-window edges differ")
    rows: list[JsonMap] = []
    assignments: list[JsonMap] = []
    exclusions: list[JsonMap] = []
    case_rows: list[JsonMap] = []
    core_rows: list[JsonMap] = []
    bound_counts: Counter[str] = Counter()
    comparisons = 0
    for core in protocol["cores"]:
        did = core["native_dataset_id"]
        native = source[str(did)]
        accepted: dict[str, JsonMap] = native["accepted_native_samples"]
        excluded: list[JsonMap] = native["excluded_native_samples"]
        if (
            len(accepted) + len(excluded) != core["expected_samples"]
            or len(accepted) != core["expected_eligible_samples"]
        ):
            raise ValueError("Source population differs from named protocol")
        ids = [item["native_sample_id"] for item in accepted.values()] + [
            item["native_sample_id"] for item in excluded
        ]
        if len(set(ids)) != len(ids):
            raise ValueError("Native sample identity duplicates")
        bins: list[list[JsonMap]] = [[] for _ in edges[:-1]]
        bounds: Counter[str] = Counter()
        for key, item in accepted.items():
            age = item["selected_age"]
            if (
                age["chronologyid"] != core["named_calibrated_chronology_id"]
                or age["agetype"] != CAL_BP
                or str(item["native_sample_id"]) != key
            ):
                raise ValueError("Native named chronology/sample identity differs")
            index = window(age["age"], edges)
            if index is None or not item["inside_declared_point_domain"]:
                raise ValueError("Included source point lies outside declared domain")
            flag = bound_support(age, index, edges)
            bounds[flag] += 1
            bound_counts[flag] += 1
            bins[index].append(item)
            assignments.append(
                {
                    "dataset_id": did,
                    "sample_id": item["native_sample_id"],
                    "selected_age": age,
                    "window_index": index,
                    "bound_support": flag,
                }
            )
        for item in excluded:
            age = item["source_age"]
            if (
                age["chronologyid"] != core["named_calibrated_chronology_id"]
                or age["agetype"] != CAL_BP
                or window(age["age"], edges) is not None
            ):
                raise ValueError(
                    "Excluded point refusal differs from named source domain"
                )
            exclusions.append({"dataset_id": did, **item})
        cases = [case for case in report["cases"] if case["native_dataset_id"] == did]
        if len(cases) != len(core["geometry_profiles"]):
            raise ValueError("Frozen geometry case inventory differs")
        occupied = 0
        for index, samples in enumerate(bins):
            counts = [
                sum(item["count_labels"][taxon] for item in samples)
                for taxon in core["taxa"]
            ]
            total = sum(item["reported_all_pollen_NISP"] for item in samples)
            for value in counts + [total]:
                if type(value) is not int or value < 0:
                    raise ValueError("Invalid native pooled count")
            if sum(counts) > total:
                raise ValueError("Panel count exceeds reported pollen denominator")
            occupied += bool(samples)
            row: JsonMap = {
                "native_dataset_id": did,
                "native_collection_unit_id": core["native_collection_unit_id"],
                "named_cal_bp_chronology_id": core["named_calibrated_chronology_id"],
                "window_index": index,
                "younger_cal_bp": edges[index],
                "older_cal_bp_exclusive": edges[index + 1],
                "status": "observed_point_support"
                if samples
                else "no_native_point_support",
                "native_samples": len(samples),
                "pooled_panel_counts": counts if samples else None,
                "reported_pollen_NISP": total if samples else None,
                "parameter_taxa": core["taxa"],
                "bound_support_counts": dict(
                    sorted(
                        Counter(
                            bound_support(item["selected_age"], index, edges)
                            for item in samples
                        ).items()
                    )
                ),
                "vegetation_zero_inferred": False,
            }
            rows.append(row)
            for case in cases:
                saved = [
                    result
                    for result in case["results"]
                    if result["younger_cal_bp"] == edges[index]
                    and result["older_cal_bp_exclusive"] == edges[index + 1]
                ]
                if len(saved) != bool(samples):
                    raise ValueError(
                        "Saved numerical occupied-window inventory differs"
                    )
                if saved:
                    old = saved[0]
                    if (
                        old["counts"] != [counts]
                        or old["native_sample_count"] != len(samples)
                        or old["reported_all_pollen_NISP_sum"] != total
                        or old["panel_count_denominator"] != sum(counts)
                    ):
                        raise ValueError(
                            "Native source pool differs from saved reconstruction"
                        )
                    comparisons += len(counts) + 3
                case_rows.append(
                    {
                        "case_id": case["case_id"],
                        "native_dataset_id": did,
                        "window_index": index,
                        "status": row["status"],
                        "saved_numerical_result_retained": bool(saved),
                        "new_reconstruction_performed": False,
                    }
                )
        original = next(
            row for row in domain["cores"] if row["native_dataset_id"] == did
        )
        raw = next(
            row
            for row in census["cores"]
            if row["source_core"]["native_dataset_id"] == did
        )
        accepted_nisp = sum(
            item["reported_all_pollen_NISP"] for item in accepted.values()
        )
        if (
            occupied != original["occupied_windows"]
            or accepted_nisp != original["accepted_all_reported_pollen_NISP"]
            or len(accepted) != original["accepted_point_domain_samples"]
            or len(ids) != raw["source_sample_count"]
        ):
            raise ValueError("Source-domain and full-source census disagree")
        full_nisp = raw["all_reported_pollen_NISP"]
        if type(full_nisp) is not int or full_nisp < accepted_nisp:
            raise ValueError("Full source mass disagrees with accepted point support")
        core_rows.append(
            {
                "native_dataset_id": did,
                "native_collection_unit_id": core["native_collection_unit_id"],
                "named_cal_bp_chronology_id": core["named_calibrated_chronology_id"],
                "source_samples": len(ids),
                "accepted_point_samples": len(accepted),
                "excluded_point_samples": len(excluded),
                "full_source_reported_pollen_NISP": full_nisp,
                "accepted_reported_pollen_NISP": accepted_nisp,
                "excluded_reported_pollen_NISP": full_nisp - accepted_nisp,
                "declared_windows": 25,
                "occupied_windows": occupied,
                "unobserved_windows": 25 - occupied,
                "reported_bound_support_counts": dict(sorted(bounds.items())),
            }
        )
    if (
        len(rows) != 100
        or len(case_rows) != 225
        or sum(row["saved_numerical_result_retained"] for row in case_rows) != 182
    ):
        raise ValueError("Full declared Nordic window universe differs")
    summary: JsonMap = {
        "schema_version": "nordic-complete-source-window-domain.v1",
        "original_reconstruction_candidate": report["candidate"],
        "original_native_status_preserved": terminal["status"],
        "original_native_exit": terminal["native_exit_code"],
        "source_sha256": pins,
        "cores": core_rows,
        "native_source_samples": sum(row["source_samples"] for row in core_rows),
        "accepted_point_samples": len(assignments),
        "excluded_source_points": len(exclusions),
        "declared_core_windows": len(rows),
        "observed_core_windows": sum(
            row["status"] == "observed_point_support" for row in rows
        ),
        "absent_core_windows": sum(
            row["status"] == "no_native_point_support" for row in rows
        ),
        "declared_geometry_case_windows": len(case_rows),
        "retained_actual_case_results": 182,
        "absent_geometry_case_windows": sum(
            not row["saved_numerical_result_retained"] for row in case_rows
        ),
        "saved_count_support_scalar_comparisons": comparisons,
        "reported_bound_support_counts": dict(sorted(bound_counts.items())),
        "source_window_rows": rows,
        "geometry_case_window_rows": case_rows,
        "scope": "Exhaustive source-point support and retained-count reconciliation on four named native CalBP models under their previously declared AD1950 source datum. Bounds are classified by literal numeric containment only, with no confidence interpretation or probability allocation. Absent windows have null counts and no inferred zero vegetation. No sample calibration, chronology fit, model reconstruction, physical quadrature, historical-selection, source-rights broadening or independent vegetation/chronology accuracy claim.",
    }
    private: JsonMap = {
        "sample_window_assignments": assignments,
        "excluded_source_points": exclusions,
        "scope": "Private exact native sample/age associations; no public raw-data redistribution",
    }
    return summary, private


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    summary, private = qualify(args.source_root)
    args.output_root.mkdir(parents=True, exist_ok=False)
    for name, account in [
        ("window-domain.json", summary),
        ("private-sample-support.json", private),
    ]:
        with (args.output_root / name).open("x", encoding="utf-8") as stream:
            json.dump(account, stream, indent=2, ensure_ascii=False, allow_nan=False)
            stream.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
