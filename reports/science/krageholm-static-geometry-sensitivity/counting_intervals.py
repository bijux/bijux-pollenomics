"""Fixed counting intervals for individual measured native Krageholm pairs."""

from __future__ import annotations

import argparse
from bisect import bisect_right
from dataclasses import asdict
from fractions import Fraction
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from typing import Any, cast

from bijux_pollenomics_lra import api

JsonMap = dict[str, Any]
DOMAIN = Path(__file__).resolve().parent
AXIS = ("Betula", "Poaceae")


def require(condition: object, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_object(path: Path) -> JsonMap:
    value: object = json.loads(path.read_text())
    require(isinstance(value, dict), "Expected source object")
    return cast(JsonMap, value)


def read_rows(path: Path) -> list[JsonMap]:
    value: object = json.loads(path.read_text())
    require(isinstance(value, list), "Expected source rows")
    result = cast(list[object], value)
    require(all(isinstance(row, dict) for row in result), "Expected source row objects")
    return cast(list[JsonMap], result)


def integer(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"Nonnegative source integer required: {label}")
    return value


def select(
    rows: list[JsonMap], edges: list[float]
) -> tuple[list[JsonMap], list[JsonMap]]:
    selected: list[JsonMap] = []
    refused: list[JsonMap] = []
    keys: set[int] = set()
    units: set[int] = set()
    for row in rows:
        key = integer(row["native_sample_id"], "sample ID")
        unit = integer(row["native_analysis_unit_id"], "analysis unit")
        require(
            key not in keys and unit not in units, "Duplicate native aliquot identity"
        )
        keys.add(key)
        units.add(unit)
        fields: JsonMap = row["strict_unique_literal_parameter_counts"]
        require(
            all(taxon in fields for taxon in AXIS),
            "Missing measured pair: never zero-fill",
        )
        require(
            not any(taxon in row["duplicate_literal_source_rows"] for taxon in AXIS),
            "Duplicated literal pair datum",
        )
        for taxon, code in zip(AXIS, (29, 417), strict=True):
            require(
                fields[taxon]["native_taxon_id"] == code,
                "Native literal taxon code differs",
            )
            integer(fields[taxon]["native_datum_ordinal"], "datum ordinal")
        counts = tuple(integer(fields[taxon]["count"], "grain count") for taxon in AXIS)
        require(
            1 <= sum(counts) <= 10000,
            "Pair counting denominator outside supported domain",
        )
        ages = [
            age
            for age in row["typed_calibrated_source_ages"]
            if age["native_chronology_id"] == 13366
        ]
        require(len(ages) == 1, "Named chronology is missing or duplicated")
        age = ages[0]
        require(
            age["source_age_type"] == "Calibrated radiocarbon years BP",
            "Source age scale differs",
        )
        require(
            type(age["source_point_age"]) in (int, float), "Source age is not numeric"
        )
        point = float(age["source_point_age"])
        require(math.isfinite(point), "Source point age is not finite")
        index = (
            bisect_right(edges, point) - 1 if edges[0] <= point < edges[-1] else None
        )
        require(age["window_index"] == index, "Source point-window assignment differs")
        record = {
            "native_sample_id": key,
            "native_analysis_unit_id": unit,
            "counts": counts,
            "window_index": index,
            "source_fields": fields,
            "native_age": age,
        }
        if index is None:
            refused.append(
                {**record, "reason": "source_point_outside_declared_windows"}
            )
        else:
            selected.append(record)
    return selected, refused


def qualify(source_root: Path, output: Path, repository: Path) -> JsonMap:
    require(
        ".." not in source_root.parts and ".." not in output.parts,
        "Ambiguous lexical path",
    )
    require(
        not any(
            p.is_symlink()
            for p in (source_root, *source_root.parents, output, *output.parents)
        ),
        "Symlink source/output ancestor",
    )
    require(
        not output.exists()
        and output.resolve().is_relative_to(repository.resolve() / "artifacts"),
        "Choose absent artifact output",
    )
    require(
        not output.resolve().is_relative_to(source_root.resolve())
        and not source_root.resolve().is_relative_to(output.resolve()),
        "Output overlaps immutable source capture",
    )
    protocol = read_object(DOMAIN / "counting-protocol.json")
    custody: JsonMap = protocol["source_custody"]
    for name, pin in custody.items():
        p = source_root / name
        require(p.is_file() and not p.is_symlink(), "Source file absent or aliased")
        body = p.read_bytes()
        require(
            len(body) == pin["bytes"]
            and hashlib.sha256(body).hexdigest() == pin["sha256"],
            "Source bytes changed",
        )
    source_terminal = read_object(source_root / "source-terminal.json")
    native_terminal = read_object(source_root / "native-terminal.json")
    require(
        all(
            t["native_exit_code"] == 0 and t["status"] == "PASS"
            for t in (source_terminal, native_terminal)
        ),
        "Original native source/science capture did not pass",
    )
    require(
        source_terminal["product_files"]["dataset-23013-sample-eligibility.json"]
        == custody["dataset-23013-sample-eligibility.json"],
        "Source count capture output binding differs",
    )
    require(
        native_terminal["product_files"]["physical-results.json"]
        == custody["native-results.json"],
        "Native physical result output binding differs",
    )
    native = read_object(source_root / "native-results.json")
    original = read_object(source_root / "protocol.json")
    require(
        native["literal_axis"] == list(AXIS) and native["ppe"] == [5.106, 1.0],
        "Fixed native parameter panel differs",
    )
    profile = next(
        row
        for row in native["single_dataset_profiles"]
        if row["selected_source_profile"]["native_dataset_id"] == 23013
    )
    require(
        profile["selected_source_profile"]["native_chronology_id"] == 13366,
        "Native profile identity differs",
    )
    results = [
        row
        for row in profile["conditional_results"]
        if row["physical_profile"] == "metadata_radius_wind_3"
    ]
    deposition = tuple(float(x) for x in protocol["fixed_response"]["deposition"])
    require(
        len(deposition) == 2
        and all(row["deposition"] == [list(deposition)] for row in results),
        "Saved fixed response differs",
    )
    selected, refused = select(
        read_rows(source_root / "dataset-23013-sample-eligibility.json"),
        [float(x) for x in original["age_window_edges_cal_bp"]],
    )
    require(
        (len(selected), len(refused), len(results)) == (95, 1, 24),
        "Frozen cohort or window population differs",
    )
    require(
        sum(0 in row["counts"] for row in selected) == 0, "Unexpected native zero axis"
    )
    require(
        tuple(native["ppe"]) == tuple(protocol["fixed_response"]["ppe"]),
        "Fixed PPE identity differs",
    )
    spec = importlib.util.spec_from_file_location(
        "native_pair_oracle", DOMAIN / "counting_oracle.py"
    )
    require(
        spec is not None and spec.loader is not None, "Independent observer unavailable"
    )
    assert spec is not None and spec.loader is not None
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)
    dep = cast(tuple[float, float], deposition)
    ppe = (5.106, 1.0)
    private: list[JsonMap] = []
    for row in selected:
        counts = cast(tuple[int, int], row["counts"])
        interval = api.fixed_two_taxon_counting_interval(
            counts, dep, ppe, taxon_measured=[True, True], confidence_level=0.95
        )
        check = oracle.verify_interval(
            counts,
            dep,
            ppe,
            0.95,
            interval.pollen_probability_interval,
            interval.cover,
            interval.cover_lower,
            interval.cover_upper,
            interval.tail_target_lower_bound,
            interval.pollen_tail_upper_bounds,
        )
        private.append({**row, "interval": asdict(interval), "independent": check})
    point_errors: list[float] = []
    for result in results:
        members = [
            row for row in selected if row["window_index"] == result["window_index"]
        ]
        support = result["source_support"]
        require(
            [row["native_sample_id"] for row in members]
            == support["native_sample_ids"],
            "Original pooled point membership differs",
        )
        require(
            [row["native_analysis_unit_id"] for row in members]
            == support["native_analysis_unit_ids"],
            "Original pooled analysis units differ",
        )
        pooled = tuple(sum(row["counts"][i] for row in members) for i in range(2))
        require(
            list(pooled) == support["counts"]
            and sum(pooled) == support["selected_panel_count_denominator"],
            "Original pooled count support differs",
        )
        exact = oracle.transformed_pair(Fraction(pooled[0], sum(pooled)), dep, ppe)
        for i in range(2):
            expected = float(result["conditional_panel_cover"][i])
            error = abs(float(exact[i]) - expected)
            require(
                error <= 2e-13 and error <= 2e-12 * max(abs(expected), 1e-12),
                "Original point-only quotient differs",
            )
            point_errors.append(error)
    widths = [
        row["interval"]["cover_upper"][0] - row["interval"]["cover_lower"][0]
        for row in private
    ]
    report: JsonMap = {
        "schema_version": "source-native-fixed-pair-counting-intervals.v1",
        "source_custody": custody,
        "site": protocol["native_source"],
        "fixed_response": protocol["fixed_response"],
        "counting_model": protocol["counting_model"],
        "native_input_samples": 96,
        "interval_requests": 95,
        "outside_domain_refusals": 1,
        "native_zero_axis_requests": 0,
        "counts_denominator": "Individual measured Betula + Poaceae grains only; never full reported pollen NISP or pooled-window count mass",
        "pair_total_range": [
            min(sum(row["counts"]) for row in selected),
            max(sum(row["counts"]) for row in selected),
        ],
        "conditional_cover_interval_width": {
            "minimum": min(widths),
            "maximum": max(widths),
            "mean": math.fsum(widths) / len(widths),
        },
        "independent": {
            "exact_binomial_tail_inequalities": 190,
            "exact_complementary_cover_enclosures": 380,
            "individual_point_checks": 190,
            "original_occupied_window_point_checks": len(point_errors),
            "maximum_individual_point_absolute_error": max(
                row["independent"]["maximum_point_absolute_error"] for row in private
            ),
            "maximum_original_point_absolute_error": max(point_errors),
            "certificate_tails_enclose_exact_polynomials": True,
        },
        "scientific_admission": False,
        "empirical_coverage_verified": False,
        "full_vegetation_interval": False,
        "old_marginal_errors_replaced": False,
        "joint_or_simultaneous_intervals": False,
    }
    output.mkdir(parents=True)
    (output / "private-intervals.json").write_text(
        json.dumps(
            {"intervals": private, "refusals": refused}, indent=2, allow_nan=False
        )
        + "\n"
    )
    (output / "report.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = qualify(args.source_root, args.output, args.repository)
    print(
        json.dumps(
            {
                "interval_requests": report["interval_requests"],
                "exact_binomial_tail_inequalities": report["independent"][
                    "exact_binomial_tail_inequalities"
                ],
            }
        )
    )


if __name__ == "__main__":
    main()
