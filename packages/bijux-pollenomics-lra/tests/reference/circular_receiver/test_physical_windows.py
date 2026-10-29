"""Controlled full-population reference handoff without R or model evaluation."""

from __future__ import annotations

import copy
import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any

import pytest

from . import physical_windows as reference

pytestmark = pytest.mark.reference


def fixture_population() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Construct complete artificial axes; no real source counts are decoded."""
    tuples: list[dict[str, Any]] = []
    for index in range(23):
        tuples.append(
            dict(
                zip(
                    reference.TUPLE_COLUMNS[1:],
                    (10, 10, 1000, 0.01 + index / 1000, 0.12, 0.25, 3),
                    strict=True,
                )
            )
        )
        tuples[-1].update(
            factor=0.4 + index / 1000,
            estimated_absolute_error=1e-12,
            rigorous_error_bound=False,
            uses=[],
        )
    cases = []
    component = 0
    for cid, (size, occupied) in reference.CASE_SIZES.items():
        selected = [tuples[(component + j) % 23] for j in range(size)]
        component += size
        taxa = [f"taxon{j}" for j in range(size)]
        for taxon, item in zip(taxa, selected, strict=True):
            item["uses"].append({"case_id": cid, "parameter_taxon": taxon})
        counts = list(range(1, size + 1))
        total = sum(counts)
        cover = [x / total for x in counts]
        zero = [[0.0] * size for _ in counts]
        results = []
        for index in range(occupied):
            results.append(
                {
                    "younger_cal_bp": index,
                    "older_cal_bp_exclusive": index + 1,
                    "counts": [counts],
                    "panel_count_denominator": total,
                    "actual_source_panel_presence": True,
                    "conditional_cover": cover,
                    "direct_pollen_panel_fraction": cover,
                    "conditional_standard_error": [0.0] * size,
                    "counting_covariance": zero,
                    "assumed_ppe_covariance": zero,
                    "total_conditional_covariance": zero,
                }
            )
        cases.append(
            {
                "case_id": cid,
                "parameter_taxa": taxa,
                "PPE": [1.0] * size,
                "PPE_SD": [0.0] * size,
                "fall_speed_m_s": [x["fall_speed_m_s"] for x in selected],
                "panel_N_not_full_NISP": True,
                "source_present_not_hypothesized_zero": True,
                "physical_response": {"factors": [[x["factor"] for x in selected]]},
                "static_geometry": {"radius_m": 10},
                "results": results,
                "occupied_windows": occupied,
            }
        )
    report = {
        "candidate": "1" * 40,
        "cases": cases,
        "unique_physical_tuples": 23,
        "physical_tuple_case_uses": 29,
        "scope": "Artificial population only",
        "protocol": {
            "age_window_edges_cal_bp": list(range(26)),
            "regional_extent_m": 1000,
            "diffusion_coefficient": 0.12,
            "turbulence_parameter": 0.25,
            "wind_speed_m_s": 3,
            "chronology_scope": "Synthetic fixed windows",
        },
    }
    return report, tuples


def write_json(path: Path, value: Any) -> str:
    body = json.dumps(value, allow_nan=False).encode()
    path.write_bytes(body)
    return hashlib.sha256(body).hexdigest()


def inputs(root: Path) -> tuple[list[str], dict[str, Any]]:
    report, tuples = fixture_population()
    tuple_sha = write_json(root / "tuples.json", tuples)
    report["physical_response_tuples_sha256"] = tuple_sha
    report_sha = write_json(root / "report.json", report)
    args = [
        "--report",
        str(root / "report.json"),
        "--report-sha256",
        report_sha,
        "--tuples",
        str(root / "tuples.json"),
        "--tuples-sha256",
        tuple_sha,
        "--execution-epoch",
        "2" * 40,
        "--output-root",
        str(root),
    ]
    return args, reference.population(report, tuples)


def outputs(root: Path, data: dict[str, Any]) -> None:
    root.mkdir()
    factor_rows = [
        [tid, factor, factor, 1e-12, 0, 3] for tid, factor in data["factors"].items()
    ]
    (root / "factors.tsv").write_bytes(
        reference._tsv(reference.FACTOR_COLUMNS, factor_rows)
    )
    rows: list[list[Any]] = []
    for track in reference.TRACKS:
        rows.extend(
            [cid, wid, track, quantity, i, j, value]
            for (cid, wid, quantity, i, j), value in data["expected"].items()
        )
    (root / "values.tsv").write_bytes(reference._tsv(reference.VALUE_COLUMNS, rows))


def compare_args(root: Path, args: list[str]) -> list[str]:
    return [
        "compare",
        *args,
        "--input-directory",
        str(root / "export"),
        "--r-directory",
        str(root / "r"),
        "--output",
        str(root / "comparison.json"),
    ]


def test_complete_export_compare_cli_preserves_every_window(tmp_path: Path) -> None:
    args, data = inputs(tmp_path)
    assert reference.main(["export", *args, "--output", str(tmp_path / "export")]) == 0
    assert {p.name for p in (tmp_path / "export").iterdir()} == {
        "tuples.tsv",
        "scenarios.tsv",
        "windows.tsv",
        "manifest.json",
    }
    assert [
        len(list(csv.DictReader(io.StringIO(body.decode()), delimiter="\t")))
        for body in data["files"].values()
    ] == [23, 29, 518]
    assert (
        b"conditional_cover" not in (tmp_path / "export" / "windows.tsv").read_bytes()
    )
    outputs(tmp_path / "r", data)
    assert reference.main(compare_args(tmp_path, args)) == 0
    result = json.loads((tmp_path / "comparison.json").read_bytes())
    assert result["passed"] and len(result["windows"]) == 182
    assert all(
        sum(w["tracks"][track]["cells"] for w in result["windows"]) == 6840
        for track in reference.TRACKS
    )
    assert result["source_epoch"] == "1" * 40 and result["execution_epoch"] == "2" * 40


@pytest.mark.parametrize(
    "mutation",
    [
        "case",
        "tuple",
        "use",
        "geometry",
        "factor",
        "boolean_count",
        "fractional_count",
        "panel",
        "shape",
        "window",
        "nonfinite",
        "taxon",
        "unmeasured",
    ],
)
def test_population_rejects_semantic_mutations(mutation: str) -> None:
    report, tuples = fixture_population()
    case, row = report["cases"][0], report["cases"][0]["results"][0]
    if mutation == "case":
        report["cases"][0]["case_id"] = "foreign"
    elif mutation == "tuple":
        tuples.pop()
    elif mutation == "use":
        tuples[0]["uses"].append(copy.deepcopy(tuples[0]["uses"][0]))
    elif mutation == "geometry":
        case["static_geometry"]["radius_m"] = 11
    elif mutation == "factor":
        case["physical_response"]["factors"][0][0] += 0.01
    elif mutation == "boolean_count":
        row["counts"][0][0] = True
    elif mutation == "fractional_count":
        row["counts"][0][0] = 1.5
    elif mutation == "panel":
        row["panel_count_denominator"] += 1
    elif mutation == "shape":
        row["total_conditional_covariance"] = [[0.0]]
    elif mutation == "window":
        row["older_cal_bp_exclusive"] = 0.5
    elif mutation == "nonfinite":
        case["PPE"][0] = float("nan")
    elif mutation == "taxon":
        case["parameter_taxa"][1] = case["parameter_taxa"][0]
    else:
        row["actual_source_panel_presence"] = False
    with pytest.raises(ValueError):
        reference.population(report, tuples)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "duplicate",
        "foreign",
        "numeric",
        "factor_missing",
        "input",
        "manifest",
        "hash",
        "escape",
        "symlink",
    ],
)
def test_reader_boundary_refuses_without_comparison_output(
    tmp_path: Path, mutation: str
) -> None:
    args, data = inputs(tmp_path)
    reference.main(["export", *args, "--output", str(tmp_path / "export")])
    outputs(tmp_path / "r", data)
    argv = compare_args(tmp_path, args)
    p = tmp_path / "r" / "values.tsv"
    lines = p.read_text().splitlines(keepends=True)
    if mutation == "missing":
        p.write_text("".join(lines[:-1]))
    elif mutation == "duplicate":
        p.write_text("".join(lines + [lines[1]]))
    elif mutation == "foreign":
        p.write_text("".join(lines).replace("fresh_factor", "foreign", 1))
    elif mutation == "numeric":
        fields = lines[1].rstrip("\n").split("\t")
        fields[-1] = "1_000"
        p.write_text(lines[0] + "\t".join(fields) + "\n" + "".join(lines[2:]))
    elif mutation == "factor_missing":
        p = tmp_path / "r" / "factors.tsv"
        p.write_text("\n".join(p.read_text().splitlines()[:-1]) + "\n")
    elif mutation == "input":
        (tmp_path / "export" / "windows.tsv").write_text("corrupted")
    elif mutation == "manifest":
        p = tmp_path / "export" / "manifest.json"
        value = json.loads(p.read_bytes())
        value["execution_epoch"] = "3" * 40
        p.write_text(json.dumps(value))
    elif mutation == "hash":
        (tmp_path / "report.json").write_text("{}")
    elif mutation == "escape":
        argv[-1] = str(tmp_path / ".." / "escape.json")
    else:
        parent = tmp_path / "linked"
        parent.symlink_to(tmp_path, target_is_directory=True)
        argv[-1] = str(parent / "comparison.json")
    with pytest.raises(SystemExit) as caught:
        reference.main(argv)
    assert caught.value.code == 2 and not (tmp_path / "comparison.json").exists()


def test_numerical_failure_retains_all_windows_and_diagnostics(tmp_path: Path) -> None:
    args, data = inputs(tmp_path)
    reference.main(["export", *args, "--output", str(tmp_path / "export")])
    outputs(tmp_path / "r", data)
    p = tmp_path / "r" / "values.tsv"
    lines = p.read_text().splitlines(keepends=True)
    fields = lines[1].rstrip("\n").split("\t")
    fields[-1] = "0.9"
    p.write_text(lines[0] + "\t".join(fields) + "\n" + "".join(lines[2:]))
    assert reference.main(compare_args(tmp_path, args)) == 1
    value = json.loads((tmp_path / "comparison.json").read_bytes())
    assert not value["passed"] and len(value["mismatches"]) == 1
    assert len(value["windows"]) == 182 and len(value["physical_factors"]) == 23
    with pytest.raises(SystemExit) as caught:
        reference.main(compare_args(tmp_path, args))
    assert caught.value.code == 2
