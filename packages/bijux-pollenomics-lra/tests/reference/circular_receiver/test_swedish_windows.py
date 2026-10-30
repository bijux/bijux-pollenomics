"""Artificial full-population handoff tests; no R, physical kernels or LRA calls."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest

from . import swedish_population as population
from . import swedish_windows as reference

pytestmark = pytest.mark.reference


def fixture_report() -> dict[str, Any]:
    """Complete artificial shapes; expected arrays test transport, not numerical truth."""
    report: dict[str, Any] = {
        "schema_version": "swedish-static-basin-maintained-producer.v1",
        "producer_candidate": "1" * 40,
        "protocol": {
            "profiles": copy.deepcopy(population.PROFILES),
            "diffusion_coefficient": 0.12,
            "turbulence_parameter": 0.25,
            "regional_extent_m": 100000,
            "age_window_edges_cal_bp": list(range(26)),
            "age_support": "Artificial fixed point-age window fixture",
        },
        "cores": [],
    }
    for key in (
        "historical_reproduction_claimed",
        "full_31_target_reconstruction_claimed",
        "vegetation_accuracy_claimed",
        "chronology_or_geometry_uncertainty_quantified",
        "source_lake_algorithm_parity_claimed",
        "distribution_of_raw_source_counts_authorized",
    ):
        report[key] = False
    for ci, (code, spec) in enumerate(population.CORES.items()):
        n, count = len(spec["taxa"]), spec["windows"]
        core: dict[str, Any] = {
            "metadata_code": code,
            "parameter_taxa": spec["taxa"][:],
            "native_dataset_id": spec["dataset"],
            "chronology_id": spec["chronology"],
            "metadata_static_radius_m": spec["radius"],
            "included_sample_count": spec["included"],
            "native_sample_count": spec["native"],
            "occupied_window_count": count,
            "ppe": [1.0] * n,
            "ppe_standard_deviation": [0.0] * n,
            "ppe_covariance": [[0.0] * n for _ in range(n)],
            "fall_speed_m_s": [0.01 + 0.001 * (3 * ci + j) for j in range(n)],
            "quadrature": [
                {
                    "profile": p["id"],
                    "factors": [[0.5] * n],
                    "estimated_absolute_error": [0.0] * n,
                    "rigorous_error_bound": False,
                }
                for p in population.PROFILES
            ],
            "results": [],
        }
        for profile in population.PROFILE_IDS:
            for wi in range(count):
                samples = spec["included"] - count + 1 if wi == 0 else 1
                row = {
                    "profile": profile,
                    "younger_cal_bp": wi,
                    "older_cal_bp_exclusive": wi + 1,
                    "native_sample_count": samples,
                    "raw_age_bounds_missing": samples,
                    "local_native_sample_support_sha256": "a" * 64,
                    "counts": [[1] * n],
                    "panel_count_denominator": n,
                    "reported_all_pollen_NISP_sum": n + 1,
                    "cover": [1 / n] * n,
                    "direct_pollen_panel_fraction": [1 / n] * n,
                    "standard_error": [0.0] * n,
                    "counting_covariance": [[0.0] * n for _ in range(n)],
                    "ppe_covariance": [[0.0] * n for _ in range(n)],
                    "total_covariance": [[0.0] * n for _ in range(n)],
                }
                if profile == population.PROFILE_IDS[-1]:
                    row = {
                        key: row[key]
                        for key in (
                            "profile",
                            "younger_cal_bp",
                            "older_cal_bp_exclusive",
                            "cover",
                            "standard_error",
                        )
                    }
                core["results"].append(row)
        core["results"] = [
            core["results"][pi * count + wi] for wi in range(count) for pi in range(6)
        ]
        report["cores"].append(core)
    return report


def saved_rows(data: dict[str, Any]) -> tuple[bytes, bytes]:
    factors = [[tid, value, value, 0, 0, 21] for tid, value in data["factors"].items()]
    cells = [
        [cid, wid, track, q, i, j, value]
        for track in population.TRACKS
        for (cid, wid, q, i, j), value in data["expected"].items()
    ]
    for cid, wid, q, i, j in data["r_only"]:
        baseline = cid.split(".", 1)[0] + ".metadata_radius_wind_3"
        target_q = "counting_covariance" if q == "total_conditional_covariance" else q
        value = (
            0.0
            if q == "assumed_ppe_covariance"
            else data["expected"][baseline, wid, target_q, i, j]
        )
        cells.extend([[cid, wid, track, q, i, j, value] for track in population.TRACKS])
    return population._tsv(population.FACTOR_COLUMNS, factors), population._tsv(
        population.VALUE_COLUMNS, cells
    )


def args(root: Path) -> argparse.Namespace:
    report = root / "report.json"
    report.write_text(json.dumps(fixture_report()))
    return argparse.Namespace(
        report=report,
        report_sha256=hashlib.sha256(report.read_bytes()).hexdigest(),
        execution_epoch="2" * 40,
        output_root=root,
        output=root / "export",
        input_directory=root / "export",
        r_directory=root / "r",
    )


def bind_export(a: argparse.Namespace, source: Path | None = None) -> None:
    """Bind the separately retained source and epoch before fresh comparison."""
    a.input_export_manifest_sha256 = hashlib.sha256(
        (a.input_directory / "manifest.json").read_bytes()
    ).hexdigest()
    a.input_exporter_source = Path(reference.__file__) if source is None else source
    a.input_exporter_source_sha256 = hashlib.sha256(
        a.input_exporter_source.read_bytes()
    ).hexdigest()
    a.input_export_execution_epoch = a.execution_epoch


def test_complete_population_and_saved_handoff(tmp_path: Path) -> None:
    a = args(tmp_path)
    data = population.population(fixture_report())
    assert (len(data["factors"]), len(data["windows"]), len(data["expected"])) == (
        45,
        462,
        8434,
    )
    assert reference.export(a) == 0
    bind_export(a)
    a.r_directory.mkdir()
    fb, vb = saved_rows(data)
    (a.r_directory / "factors.tsv").write_bytes(fb)
    (a.r_directory / "values.tsv").write_bytes(vb)
    a.output = tmp_path / "comparison.json"
    assert reference.compare(a) == 0
    result = json.loads(a.output.read_bytes())
    assert (
        result["passed"]
        and len(result["windows"]) == 462
        and result["values_per_track"] == 9720
    )
    assert all(s["tracks"]["saved_factor"]["passed"] for s in result["windows"])


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_core",
        "core_order",
        "taxon_axis",
        "profile_missing",
        "profile_duplicate",
        "fractional_count",
        "count_denominator",
        "profile_count_changed",
        "missing_covariance",
        "correlated_ppe",
        "zero_ppe_variance",
        "zero_ppe_total",
        "native_count",
        "nonfinite_factor",
    ],
)
def test_population_refusals(mutation: str) -> None:
    d = fixture_report()
    c = d["cores"][0]
    r = c["results"][0]
    if mutation == "missing_core":
        d["cores"].pop()
    elif mutation == "core_order":
        d["cores"].reverse()
    elif mutation == "taxon_axis":
        c["parameter_taxa"].reverse()
    elif mutation == "profile_missing":
        c["quadrature"].pop()
    elif mutation == "profile_duplicate":
        c["quadrature"][1]["profile"] = c["quadrature"][0]["profile"]
    elif mutation == "fractional_count":
        r["counts"][0][0] = 0.5
    elif mutation == "count_denominator":
        r["panel_count_denominator"] += 1
    elif mutation == "profile_count_changed":
        c["results"][c["occupied_window_count"]]["counts"] = [[0, 2]]
    elif mutation == "missing_covariance":
        r.pop("total_covariance")
    elif mutation == "correlated_ppe":
        c["ppe_covariance"][0][1] = 0.1
    elif mutation == "zero_ppe_variance":
        c["results"][-1]["ppe_covariance"] = [[0.1, 0.0], [0.0, 0.0]]
    elif mutation == "zero_ppe_total":
        c["results"][-1]["total_covariance"] = [[0.1, 0.0], [0.0, 0.0]]
    elif mutation == "native_count":
        c["included_sample_count"] += 1
    elif mutation == "nonfinite_factor":
        c["quadrature"][0]["factors"][0][0] = float("nan")
    with pytest.raises((ValueError, KeyError)):
        population.population(d)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "duplicate",
        "foreign",
        "numeric",
        "mismatch",
        "report_hash",
        "extra_role",
        "r_only_mismatch",
    ],
)
def test_result_boundaries(tmp_path: Path, mutation: str) -> None:
    a = args(tmp_path)
    data = population.population(fixture_report())
    reference.export(a)
    bind_export(a)
    a.r_directory.mkdir()
    fb, vb = saved_rows(data)
    lines = vb.splitlines(keepends=True)
    if mutation == "missing":
        lines.pop()
    elif mutation == "duplicate":
        lines.append(lines[1])
    elif mutation == "foreign":
        lines[1] = lines[1].replace(b"ABB.", b"OTHER.", 1)
    elif mutation == "numeric":
        lines[1] = lines[1].rsplit(b"\t", 1)[0] + b"\t1_000\n"
    elif mutation == "mismatch":
        lines[1] = lines[1].rsplit(b"\t", 1)[0] + b"\t0.9\n"
    elif mutation == "r_only_mismatch":
        lines[-1] = lines[-1].rsplit(b"\t", 1)[0] + b"\t0.9\n"
    elif mutation == "report_hash":
        a.report_sha256 = "0" * 64
    elif mutation == "extra_role":
        (a.r_directory / "unowned.tsv").write_bytes(b"foreign")
    (a.r_directory / "factors.tsv").write_bytes(fb)
    (a.r_directory / "values.tsv").write_bytes(b"".join(lines))
    a.output = tmp_path / "comparison.json"
    if mutation in ("mismatch", "r_only_mismatch"):
        assert reference.compare(a) == 1
        assert json.loads(a.output.read_bytes())["mismatches"]
    else:
        with pytest.raises(ValueError):
            reference.compare(a)
        assert not a.output.exists()


def test_isolated_script_helper_entry(tmp_path: Path) -> None:
    a = args(tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-S",
            "-B",
            str(Path(reference.__file__)),
            "export",
            "--report",
            str(a.report),
            "--report-sha256",
            a.report_sha256,
            "--execution-epoch",
            a.execution_epoch,
            "--output-root",
            str(tmp_path),
            "--output",
            str(a.output),
        ],
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert {p.name for p in a.output.iterdir()} == {
        "tuples.tsv",
        "scenarios.tsv",
        "windows.tsv",
        "manifest.json",
    }


def retained_export(a: argparse.Namespace) -> None:
    """Artificial historical source authority; not executed or field evidence."""
    reference.export(a)
    source = a.output_root / "retained-exporter.py"
    source.write_text("# Artificial old exporter identity only; never executed.\n")
    manifest_path = a.input_directory / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["python_source_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
    manifest_path.write_bytes(reference._json_bytes(manifest))
    bind_export(a, source)
    a.execution_epoch = "3" * 40
    a.output = a.output_root / "comparison.json"


def test_retained_export_mixed_source_and_epoch_handoff(tmp_path: Path) -> None:
    a = args(tmp_path)
    retained_export(a)
    manifest_before = (a.input_directory / "manifest.json").read_bytes()
    a.r_directory.mkdir()
    fb, vb = saved_rows(population.population(fixture_report()))
    (a.r_directory / "factors.tsv").write_bytes(fb)
    (a.r_directory / "values.tsv").write_bytes(vb)
    assert reference.compare(a) == 0
    result = json.loads(a.output.read_bytes())
    assert result["source_epoch"] == "1" * 40
    assert result["input_export_execution_epoch"] == "2" * 40
    assert result["execution_epoch"] == "3" * 40
    assert result["input_exporter_source"]["sha256"] == a.input_exporter_source_sha256
    assert result["input_exporter_source"]["sha256"] != result["python_source_sha256"]
    assert (a.input_directory / "manifest.json").read_bytes() == manifest_before


@pytest.mark.parametrize(
    "binding",
    [
        "manifest",
        "source",
        "epoch",
        "source_body",
        "relabel_manifest",
        "resealed_source",
        "resealed_epoch",
    ],
)
def test_retained_export_binding_refusals(tmp_path: Path, binding: str) -> None:
    a = args(tmp_path)
    retained_export(a)
    if binding == "manifest":
        a.input_export_manifest_sha256 = "0" * 64
    elif binding == "source":
        a.input_exporter_source_sha256 = "0" * 64
    elif binding == "epoch":
        a.input_export_execution_epoch = "4" * 40
    elif binding == "source_body":
        a.input_exporter_source.write_bytes(a.input_exporter_source.read_bytes() + b" ")
    else:
        path = a.input_directory / "manifest.json"
        manifest = json.loads(path.read_bytes())
        if binding == "resealed_source":
            manifest["python_source_sha256"] = "4" * 64
        else:
            manifest["execution_epoch"] = a.execution_epoch
        path.write_bytes(reference._json_bytes(manifest))
        if binding.startswith("resealed"):
            a.input_export_manifest_sha256 = hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
    with pytest.raises(ValueError):
        reference.compare(a)
    assert not a.output.exists()


def test_retained_export_compare_cli_requires_explicit_bindings(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as refused:
        reference.main(
            [
                "compare",
                "--report",
                str(tmp_path / "report.json"),
                "--report-sha256",
                "0" * 64,
                "--execution-epoch",
                "3" * 40,
                "--output-root",
                str(tmp_path),
                "--output",
                str(tmp_path / "out.json"),
                "--input-directory",
                str(tmp_path / "input"),
                "--r-directory",
                str(tmp_path / "r"),
            ]
        )
    assert refused.value.code == 2


def test_documented_helper_identity_is_current_with_historical_basis(
    tmp_path: Path,
) -> None:
    a = args(tmp_path)
    assert reference.export(a) == 0
    manifest = json.loads((a.output / "manifest.json").read_bytes())
    current = Path(population.__file__).read_bytes()
    identity = manifest["execution_helpers"]["population"]
    assert identity["sha256"] == hashlib.sha256(current).hexdigest()
    assert identity["bytes"] == len(current)
    assert identity["historical_basis"] == {
        "sha256": "3d1769d49d07fc65c3b67a68eca99c89560383111958fe15a2f5f641cd841c12",
        "bytes": 15203,
    }
    assert len(reference._population_helper_historical_basis(current)) == 15203


@pytest.mark.parametrize(
    "mutation",
    [
        "comment",
        "import",
        "doc-text",
        "doc-scope",
        "inline-comment",
        "header",
        "partial-docs",
        "export",
        "number-or-type",
    ],
)
def test_only_exact_named_helper_documentation_is_admitted(mutation: str) -> None:
    current = Path(population.__file__).read_bytes()
    _, header, documentation = reference._POPULATION_HELPER_DOCUMENTATION[0]
    if mutation == "comment":
        changed = current + b"\n# unknown comment\n"
    elif mutation == "import":
        changed = current + b"\nimport math as unrelated\n"
    elif mutation == "doc-text":
        changed = current.replace(
            documentation, documentation.replace(b'"""', b'"""Altered ', 1), 1
        )
    elif mutation == "doc-scope":
        changed = current.replace(header + documentation, header, 1) + documentation
    elif mutation == "inline-comment":
        changed = current.replace(
            documentation, documentation.rstrip(b"\n") + b" # unknown\n", 1
        )
    elif mutation == "header":
        changed = current.replace(header, header.replace(b":", b" : ", 1), 1)
    elif mutation == "partial-docs":
        changed = current.replace(header + documentation, header, 1)
    elif mutation == "export":
        changed = current + b'\n__all__ = ["unknown"]\n'
    else:
        changed = current + b"\nUNKNOWN_NUMBER = 2\n"
    assert changed != current
    with pytest.raises(ValueError):
        reference._population_helper_historical_basis(changed)
