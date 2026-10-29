"""The exact saved R diagnostic boundary needs no live numerical runtime."""

from __future__ import annotations

import csv
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import pytest

from . import compare_reference as reference

pytestmark = pytest.mark.reference


@dataclass(frozen=True)
class MiniatureResponse:
    factor: float
    estimated_absolute_error: float = 1e-12


def diagnostic_rows() -> list[dict[str, Any]]:
    return [
        {
            "factor": value,
            "raw_factor": value,
            "estimated_absolute_error": 1e-12,
            "tail_mass_bound": 0,
            "method": "displacement_circle_overlap_one_dimensional",
            "coefficient_from_parameters": 4
            * 0.03
            / (0.25 * 3 * math.sqrt(math.pi) * 0.12),
            "exponent": 0.125,
            "absolute_tolerance": 1e-11,
            "relative_tolerance": 1e-10,
            "quadrature_limit": 1000,
            "subdivisions_used": 3,
            "case": case,
        }
        for (case, _, _), value in zip(reference.CASES, (0.2, 0.3, 0.5), strict=True)
    ]


def write(path: Path, rows: list[dict[str, Any]]) -> str:
    with path.open("w", newline="") as target:
        writer = csv.DictWriter(
            target, reference.COLUMNS, delimiter="\t", quoting=csv.QUOTE_ALL
        )
        writer.writeheader()
        writer.writerows(rows)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def argv(path: Path, checksum: str, output: Path) -> list[str]:
    return [
        "--diagnostics",
        str(path),
        "--diagnostics-sha256",
        checksum,
        "--r-source-epoch",
        "1" * 40,
        "--python-source-epoch",
        "2" * 40,
        "--output-root",
        str(output.parent),
        "--output",
        str(output),
    ]


def test_actual_tsv_reader_and_cli_call_exact_three_tuples(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path, output = tmp_path / "r.tsv", tmp_path / "comparison.json"
    checksum = write(path, diagnostic_rows())
    calls: list[dict[str, float]] = []

    def evaluate(**parameters: float) -> MiniatureResponse:
        calls.append(parameters)
        return MiniatureResponse((0.2, 0.3, 0.5)[len(calls) - 1])

    monkeypatch.setattr(
        reference,
        "_load_evaluator",
        lambda: (evaluate, [{"kind": "synthetic_test_only"}]),
    )
    assert reference.main(argv(path, checksum, output)) == 0
    report = json.loads(output.read_bytes())
    assert report["comparison_count"] == 3 and report["all_within_absolute_tolerance"]
    assert report["r_source_epoch"] == "1" * 40
    assert report["python_source_epoch"] == "2" * 40
    assert [(call["inner_radius_m"], call["outer_radius_m"]) for call in calls] == [
        (81, 500),
        (500, 1000),
        (81, 1000),
    ]
    assert all(
        call["receiver_radius_m"] == 80 and call["quadrature_limit"] == 100
        for call in calls
    )
    assert all(
        row["r"]["estimated_absolute_error"] == 1e-12 for row in report["comparisons"]
    )
    assert output.stat().st_size < reference.MAX_REPORT_BYTES


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "duplicate",
        "reordered",
        "foreign",
        "nan",
        "infinite",
        "negative_error",
        "tail",
        "method",
        "coefficient",
        "tolerance",
        "budget",
        "subdivisions",
        "raw_range",
    ],
)
def test_invalid_saved_population_refuses_before_any_evaluator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    path, output = tmp_path / "r.tsv", tmp_path / "comparison.json"
    rows = diagnostic_rows()
    if mutation == "missing":
        rows.pop()
    elif mutation == "duplicate":
        rows[1] = dict(rows[0])
    elif mutation == "reordered":
        rows.reverse()
    else:
        field, value = {
            "foreign": ("case", "unregistered"),
            "nan": ("factor", "NaN"),
            "infinite": ("raw_factor", "Inf"),
            "negative_error": ("estimated_absolute_error", -1),
            "tail": ("tail_mass_bound", -1),
            "method": ("method", "different"),
            "coefficient": ("coefficient_from_parameters", 9),
            "tolerance": ("absolute_tolerance", 0.1),
            "budget": ("quadrature_limit", 1),
            "subdivisions": ("subdivisions_used", 1.5),
            "raw_range": ("raw_factor", 2),
        }[mutation]
        rows[0][field] = value
    checksum = write(path, rows)

    def forbidden() -> None:
        pytest.fail("Malformed R diagnostics must fail before engine import/call")

    monkeypatch.setattr(reference, "_load_evaluator", forbidden)
    with pytest.raises(ValueError):
        reference.main(argv(path, checksum, output))
    assert not output.exists()


def test_hash_columns_size_symlink_and_existing_output_refuse(tmp_path: Path) -> None:
    path = tmp_path / "r.tsv"
    checksum = write(path, diagnostic_rows())
    with pytest.raises(ValueError, match="identity changed"):
        reference.read_diagnostics(path, "0" * 64)
    path.write_text(path.read_text().replace('"factor"', '"other"', 1))
    with pytest.raises(ValueError, match="columns"):
        reference.read_diagnostics(path, hashlib.sha256(path.read_bytes()).hexdigest())
    path.write_bytes(b"x" * (reference.MAX_DIAGNOSTIC_BYTES + 1))
    with pytest.raises(ValueError, match="bounded"):
        reference.read_diagnostics(path, hashlib.sha256(path.read_bytes()).hexdigest())
    link = tmp_path / "linked.tsv"
    link.symlink_to(path)
    with pytest.raises(OSError):
        reference.read_diagnostics(link, checksum)
    output = tmp_path / "comparison.json"
    output.write_text("retained")
    with pytest.raises(ValueError, match="absent"):
        reference.main(argv(path, checksum, output))
    assert output.read_text() == "retained"


def test_mismatch_retains_all_three_and_unknown_failure_is_fatal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path, output = tmp_path / "r.tsv", tmp_path / "comparison.json"
    checksum = write(path, diagnostic_rows())
    monkeypatch.setattr(
        reference, "_load_evaluator", lambda: (lambda **_: MiniatureResponse(0.4), [])
    )
    assert reference.main(argv(path, checksum, output)) == 1
    report = json.loads(output.read_bytes())
    assert (
        report["comparison_count"] == 3 and not report["all_within_absolute_tolerance"]
    )
    failure = RuntimeError(
        "implementation fault must not become a refused or skipped row"
    )

    def broken(**_: float) -> MiniatureResponse:
        raise failure

    monkeypatch.setattr(reference, "_load_evaluator", lambda: (broken, []))
    with pytest.raises(RuntimeError) as caught:
        reference.main(argv(path, checksum, tmp_path / "failed.json"))
    assert caught.value is failure
    assert not (tmp_path / "failed.json").exists()


@pytest.mark.parametrize("token", ["1_000", " 1000", "1000 ", "1000\n"])
def test_resealed_nonproducer_numeric_tokens_refuse(tmp_path: Path, token: str) -> None:
    path = tmp_path / "r.tsv"
    rows = diagnostic_rows()
    rows[0]["quadrature_limit"] = token
    checksum = write(path, rows)
    with pytest.raises(ValueError, match="numeric"):
        reference.read_diagnostics(path, checksum)


def test_linked_ancestors_traversal_and_output_escape_refuse(tmp_path: Path) -> None:
    real = tmp_path / "physical"
    real.mkdir()
    path = real / "r.tsv"
    checksum = write(path, diagnostic_rows())
    linked = tmp_path / "linked"
    linked.symlink_to(real, target_is_directory=True)
    with pytest.raises(ValueError, match="physical"):
        reference.read_diagnostics(linked / "r.tsv", checksum)
    with pytest.raises(ValueError, match="traverse"):
        reference.read_diagnostics(real / ".." / "physical" / "r.tsv", checksum)
    with pytest.raises(ValueError, match="physical"):
        reference._output_path(tmp_path, linked / "comparison.json")
    with pytest.raises(ValueError, match="traverse"):
        reference._output_path(real, real / ".." / "comparison.json")
    with pytest.raises(ValueError, match="inside"):
        reference._output_path(real, tmp_path / "escaped.json")
    assert not (tmp_path / "escaped.json").exists()
