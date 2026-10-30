"""Independent finite-table nulls, exact Pearson ties and original sample intake."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import csv
from fractions import Fraction
import io
from itertools import permutations, product
from math import factorial, prod
from pathlib import Path
import sys
from typing import Any

import numpy as np
import pytest

from bijux_pollenomics_dev.essd_reproduction.common_cover import cohort
from bijux_pollenomics_dev.essd_reproduction.common_cover import (
    within_site_homogeneity as subject,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.swedish_static_basin import (
    sources,
)
from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.reconstruction.uncertainty import two_taxon_counting

from .test_producer import native_fixture


def finite_tables(
    rows: tuple[int, ...], columns: tuple[int, ...]
) -> list[tuple[tuple[int, ...], ...]]:
    """Independent exhaustive cell enumeration, not the production row sampler."""
    candidates = [product(range(r + 1), repeat=len(columns)) for r in rows]
    return [
        tuple(table)
        for table in product(*candidates)
        if tuple(map(sum, table)) == rows
        and tuple(sum(row[j] for row in table) for j in range(len(columns))) == columns
    ]


def probability(table: tuple[tuple[int, ...], ...]) -> Fraction:
    rows = tuple(map(sum, table))
    columns = tuple(map(sum, zip(*table, strict=True)))
    return Fraction(
        prod(factorial(n) for n in (*rows, *columns)),
        factorial(sum(rows)) * prod(factorial(n) for row in table for n in row),
    )


def pearson(table: tuple[tuple[int, ...], ...]) -> Fraction:
    total = sum(map(sum, table))
    columns = tuple(map(sum, zip(*table, strict=True)))
    result = Fraction()
    for row in table:
        for value, column in zip(row, columns, strict=True):
            expected = Fraction(sum(row) * column, total) if total else Fraction()
            if expected:
                result += (value - expected) ** 2 / expected
    return result


@pytest.mark.parametrize(
    "rows,columns",
    [
        ((2, 2), (2, 2)),
        ((1, 1, 2), (2, 2)),
        ((2, 2), (1, 1, 2)),
        ((0, 2, 2), (0, 2, 2)),
    ],
)
def test_all_small_fixed_margin_tables_have_exact_pearson_order_and_nonuniform_mass(
    rows: tuple[int, ...], columns: tuple[int, ...]
) -> None:
    tables = finite_tables(rows, columns)
    assert sum(map(probability, tables)) == 1
    for table in tables:
        _, actual_rows, actual_columns, denominator, weights = subject.prepare(table)
        score = subject.integer_score(table, weights)
        assert actual_rows == rows and actual_columns == columns
        assert Fraction(sum(rows) * score, denominator) - sum(rows) == pearson(table)
    if rows == columns == (2, 2):
        assert sorted(map(probability, tables)) == [
            Fraction(1, 6),
            Fraction(1, 6),
            Fraction(2, 3),
        ]


def test_sequential_sampler_preserves_all_margins_and_its_nonuniform_distribution() -> (
    None
):
    rows, columns = (2, 2), (2, 2)
    tables = finite_tables(rows, columns)
    rng = np.random.Generator(np.random.PCG64(70319))
    sampled = Counter(subject.draw_table(rows, columns, rng) for _ in range(6000))
    assert set(sampled) == set(tables)
    for table in tables:
        assert abs(Fraction(sampled[table], 6000) - probability(table)) < Fraction(
            1, 40
        )
    rng = np.random.Generator(np.random.PCG64(1))
    for _ in range(30):
        table = subject.draw_table((0, 2, 1, 1, 0), (0, 1, 1, 2), rng)
        assert tuple(map(sum, table)) == (0, 2, 1, 1, 0)
        assert tuple(map(sum, zip(*table, strict=True))) == (0, 1, 1, 2)


def test_plus_one_inclusive_tails_have_exact_conservative_small_null_coverage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tables = finite_tables((2, 2), (2, 2))
    rejected = Fraction()
    for observed in tables:
        for simulations in product(tables, repeat=3):
            iterator = iter(simulations)
            monkeypatch.setattr(
                subject, "draw_table", lambda *_, iterator=iterator: next(iterator)
            )
            result = subject.conditional_homogeneity(observed, seed=7, draws=3)
            count = sum(pearson(t) >= pearson(observed) for t in simulations)
            assert result.extreme_count == count and result.p_value == Fraction(
                count + 1, 4
            )
            if result.p_value <= Fraction(1, 4):
                rejected += probability(observed) * prod(map(probability, simulations))
    assert rejected <= Fraction(1, 4)


def test_tied_statistics_are_inclusive_and_simulation_interval_is_separate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    table = ((1, 1), (1, 1))
    monkeypatch.setattr(subject, "draw_table", lambda *_: table)
    result = subject.conditional_homogeneity(table, seed=5, draws=19)
    assert result.p_value == 1 and result.extreme_count == 19
    assert result.mc_tail_interval is not None
    assert 0 < result.mc_tail_interval[0] < result.mc_tail_interval[1] == 1


@pytest.mark.parametrize(
    "table,reason",
    [
        ([[0, 0], [0, 0]], "zero_total_effort"),
        ([[1, 2], [0, 0]], "one_positive_sample"),
        ([[4, 0], [2, 0]], "one_positive_taxon"),
    ],
)
def test_uninformative_native_rows_are_not_dropped_or_simulated(
    table: Any, reason: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        subject, "draw_table", lambda *_: pytest.fail("uninformative sampling")
    )
    result = subject.conditional_homogeneity(table, seed=1)
    assert result.status == "uninformative" and result.reason == reason
    assert result.p_value == 1 and result.draws_completed == 0
    assert result.extreme_count is None and result.mc_tail_interval is None


@pytest.mark.parametrize(
    "value", [None, True, -1, 0.5, "2", float("inf"), float("nan"), 10**2000, 10001]
)
def test_missing_flags_invalid_and_unbounded_cells_refuse(value: Any) -> None:
    with pytest.raises(ValidationError):
        subject.conditional_homogeneity([[value, 1], [1, 1]], seed=1)


@pytest.mark.parametrize(
    "table",
    [
        [],
        [[1, 2], [3]],
        [[1, 1, 1, 1]],
        [[1, 2]] * 129,
        np.ma.array([[0, 1], [1, 1]], mask=[[True, False], [False, False]]),
    ],
)
def test_shape_and_masked_missingness_refuse_before_sampling(table: Any) -> None:
    with pytest.raises(ValidationError):
        subject.conditional_homogeneity(table, seed=1)


@pytest.mark.parametrize(
    "field,value",
    [
        ("draws", True),
        ("draws", 10000),
        ("draws", 0),
        ("seed", True),
        ("seed", -1),
        ("seed", 2**64),
    ],
)
def test_rng_and_work_contracts_are_bounded(field: str, value: Any) -> None:
    options = {"seed": 1, "draws": 19, field: value}
    with pytest.raises(ValidationError):
        subject.conditional_homogeneity([[2, 1], [1, 2]], **options)


def test_preflight_resources_and_elapsed_deadline_refuse_without_partial_p(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(subject, "MAX_DRAW_CELLS", 1)
    with pytest.raises(ValidationError, match="work"):
        subject.conditional_homogeneity([[2, 1], [1, 2]], seed=1)
    monkeypatch.setattr(subject, "MAX_DRAW_CELLS", 4_000_000)
    monkeypatch.setattr(subject, "MAX_DENOMINATOR_BITS", 1)
    with pytest.raises(ValidationError, match="denominator"):
        subject.conditional_homogeneity([[2, 1], [1, 2]], seed=1)
    monkeypatch.setattr(subject, "MAX_DENOMINATOR_BITS", 4096)
    result = subject.conditional_homogeneity([[2, 1], [1, 2]], seed=1, deadline=0)
    assert result.status == "refused" and result.draws_completed == 0
    assert (
        result.p_value is None
        and result.extreme_count is None
        and result.mc_tail_interval is None
    )


def test_original_projection_collector_is_lossless_and_does_not_alter_prior_outputs() -> (
    None
):
    native, saved, core = native_fixture()
    before = deepcopy((native, saved, core))
    ordinary = cohort.project_count_core(native, saved, core, [0, 100, 350])
    collected: list[dict[str, Any]] = []
    counted = cohort.project_count_core(
        native, saved, core, [0, 100, 350], sample_rows=collected
    )
    assert ordinary == counted and (native, saved, core) == before
    assert len(collected) == sum(len(row["sample_ids"]) for row in counted)
    for row in counted:
        members = [s for s in collected if s["window_cal_bp"] == row["window_cal_bp"]]
        assert [s["sample_id"] for s in members] == row["sample_ids"]
        assert all(
            s["source_unit"] == "NISP" and s["taxa"] == list(core.axis) for s in members
        )
        assert (
            list(map(sum, zip(*(s["counts"] for s in members), strict=True)))
            == row["original_counts"]
        )


def loaded_fixture() -> dict[str, Any]:
    sites: dict[tuple[str, int], dict[str, Any]] = {}
    samples: list[dict[str, Any]] = []
    for name, length in (("BOKE", 13), ("BUS", 19)):
        axis = list(cohort.FULL_TAXA if name == "BOKE" else cohort.TAXA)
        for index in range(length):
            number = (
                4
                if (name == "BOKE" and index < 11) or (name == "BUS" and index < 3)
                else 3
            )
            members = []
            for _ in range(number):
                sample = {
                    "core": name,
                    "window_cal_bp": [100 * index, 100 * (index + 1)],
                    "sample_id": len(samples) + 1,
                    "taxa": axis.copy(),
                    "counts": [2, 1, 3] if name == "BOKE" else [3, 2],
                    "source_unit": "NISP",
                }
                samples.append(sample)
                members.append(sample)
            totals = list(map(sum, zip(*(s["counts"] for s in members), strict=True)))
            sites[name, index] = {
                "core": name,
                "window_cal_bp": members[0]["window_cal_bp"],
                "original_axis": axis,
                "original_counts": totals,
                "original_panel_N": sum(totals),
                "sample_ids": [s["sample_id"] for s in members],
            }
    return {
        "groups": [
            {
                "window_cal_bp": sites["BOKE", i]["window_cal_bp"],
                "sites": [sites[n, i] for n in cohort.CORES],
            }
            for i in range(13)
        ],
        "unmatched": [sites["BUS", i] for i in range(13, 19)],
        "sample_panels": samples,
        "scientific_inputs": [],
    }


def test_all_original_windows_and_samples_reconcile_with_unmatched_and_missing_frax_retained() -> (
    None
):
    loaded = loaded_fixture()
    before = deepcopy(loaded)
    rows = subject.evaluate(loaded, draws=19)
    assert loaded == before and len(rows) == 32
    assert sum(row["sample_count"] for row in rows) == 110
    assert sum(not row["matched_window"] for row in rows) == 6
    assert Counter(row["core"] for row in rows) == {"BOKE": 13, "BUS": 19}
    for row in rows:
        assert row["status"] == "computed" and row["draws_completed"] == 19
        assert row["seed"] == subject.BASE_SEED + rows.index(row)
        assert (row["Fraxinus"] == "") is (row["core"] == "BUS")
        assert row["Fraxinus_measured"] is (row["core"] == "BOKE")
        assert Fraction(row["p_mc_exact"]) == Fraction(row["extreme_count"] + 1, 20)
        assert row["p_le_0_05_div_32"] is False


@pytest.mark.parametrize(
    "defect",
    [
        "duplicate_sample",
        "missing_sample",
        "axis",
        "unit",
        "total",
        "window",
        "support",
    ],
)
def test_source_sample_and_parent_conservation_tampers_refuse(defect: str) -> None:
    loaded = loaded_fixture()
    sample = loaded["sample_panels"][0]
    if defect == "duplicate_sample":
        loaded["sample_panels"][1]["sample_id"] = sample["sample_id"]
    elif defect == "missing_sample":
        loaded["sample_panels"].pop()
    elif defect == "axis":
        sample["taxa"].reverse()
    elif defect == "unit":
        sample["source_unit"] = "percent"
    elif defect == "total":
        sample["counts"][0] += 1
    elif defect == "window":
        sample["window_cal_bp"] = [5, 10]
    else:
        loaded["groups"][0]["sites"][0]["sample_ids"].reverse()
    with pytest.raises(ValidationError):
        subject.sample_tables(loaded)


@pytest.mark.parametrize("changed", ["none", "raw", "source"])
def test_cli_protocol_csv_and_terminal_source_authentication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    changed: str,
) -> None:
    loaded = loaded_fixture()
    output = tmp_path / "artifacts/homogeneity.csv"
    output.parent.mkdir()
    calls = []

    def revision(repository: Path) -> str:
        calls.append(repository)
        return "2" * 40 if changed == "source" and len(calls) > 1 else "1" * 40

    monkeypatch.setattr(subject, "_revision", revision)
    monkeypatch.setattr(cohort, "load_sample_count_groups", lambda _: loaded)
    rows = [dict.fromkeys(subject.CSV_FIELDS, "") for _ in range(32)]
    for row in rows:
        row["status"] = "uninformative"
    monkeypatch.setattr(subject, "evaluate", lambda *args, **kwargs: rows)
    if changed == "raw":
        loaded["scientific_inputs"] = [{"path": "raw.json"}]
        monkeypatch.setattr(
            sources,
            "read_bound",
            lambda *_: (_ for _ in ()).throw(ValueError("raw changed")),
        )
    monkeypatch.setattr(
        sys,
        "argv",
        ["homogeneity", "--repository", str(tmp_path), "--output", str(output)],
    )
    if changed != "none":
        with pytest.raises((ValueError, ValidationError)):
            subject.main()
        assert not output.exists()
    else:
        with pytest.raises(SystemExit) as terminal:
            subject.main()
        assert terminal.value.code == 0
        assert len(list(csv.DictReader(io.StringIO(output.read_text())))) == 32
        assert "PCG64" in capsys.readouterr().out


@pytest.mark.parametrize("failure", ["certifier", "deadline"])
def test_post_simulation_refusal_preserves_actual_draw_and_extreme_counts(
    monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    monkeypatch.setattr(subject, "draw_table", lambda *_: ((1, 1), (1, 1)))
    if failure == "certifier":
        monkeypatch.setattr(subject, "monotonic", lambda: 0.0)

        def refuse(*args: Any, **kwargs: Any) -> Any:
            raise ValidationError(
                "certification failed", reason_code="counting_interval_certification"
            )

        monkeypatch.setattr(
            two_taxon_counting, "fixed_two_taxon_counting_interval", refuse
        )
    else:
        clock = iter([0.0, 100.0])
        monkeypatch.setattr(subject, "monotonic", lambda: next(clock))
    result = subject.conditional_homogeneity(
        [[1, 1], [1, 1]], seed=1, draws=19, deadline=50
    )
    assert (
        result.status == "refused"
        and result.draws_completed == result.extreme_count == 19
    )
    assert result.p_value is None and result.mc_tail_interval is None
    assert result.reason == (
        "counting_interval_certification"
        if failure == "certifier"
        else "homogeneity_runtime_budget"
    )


def test_sample_entry_reads_once_without_response_or_point_report_work(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    native, saved, core = native_fixture()
    calls = []

    def load(repository: Path, project: Any) -> dict[str, Any]:
        calls.append(repository)
        return {"groups": project(native, saved, core, [0, 100, 350])}

    monkeypatch.setattr(cohort, "_load_groups", load)
    monkeypatch.setattr(
        cohort, "read_full_response", lambda *_: pytest.fail("unneeded response read")
    )
    result = cohort.load_sample_count_groups(tmp_path)
    assert calls == [tmp_path] and len(result["sample_panels"]) == 2
    assert result["groups"] == cohort.project_count_core(
        native, saved, core, [0, 100, 350]
    )


def test_joint_taxon_and_sample_permutations_preserve_exact_statistic_and_mass() -> (
    None
):
    original = ((0, 1, 1), (2, 0, 0), (1, 1, 0))
    for rows in permutations(range(3)):
        for columns in permutations(range(3)):
            table = tuple(tuple(original[i][j] for j in columns) for i in rows)
            _, r, _, denominator, weights = subject.prepare(table)
            assert Fraction(
                sum(r) * subject.integer_score(table, weights), denominator
            ) - sum(r) == pearson(original)
            assert probability(table) == probability(original)
