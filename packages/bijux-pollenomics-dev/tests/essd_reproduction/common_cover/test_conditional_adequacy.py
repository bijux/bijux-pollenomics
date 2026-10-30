"""Exact conditional arithmetic, independent null coverage and source boundaries."""

from __future__ import annotations

from copy import deepcopy
import csv
from decimal import Decimal
from fractions import Fraction
import io
from math import comb
from pathlib import Path
import subprocess
import sys
from typing import Any

import numpy as np
import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.essd_reproduction.common_cover import cohort
from bijux_pollenomics_dev.essd_reproduction.common_cover import (
    conditional_adequacy as subject,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.swedish_static_basin import (
    sources,
)
from bijux_pollenomics_lra.models.errors import ValidationError

from .test_measured_panel_counting import admit_fixture

MASK = [[True, True], [True, True]]
UNIT = [[1.0, 1.0], [1.0, 1.0]]


@pytest.mark.parametrize(
    ("counts", "responses", "left", "right", "p_value"),
    [
        ([[0, 2], [2, 0]], UNIT, Fraction(1, 6), Fraction(1), Fraction(1, 3)),
        ([[1, 1], [1, 1]], UNIT, Fraction(5, 6), Fraction(5, 6), Fraction(1)),
        (
            [[0, 1], [1, 0]],
            [[4.0, 1.0], [1.0, 1.0]],
            Fraction(1, 5),
            Fraction(1),
            Fraction(2, 5),
        ),
        (
            [[0, 2], [2, 0]],
            [[4.0, 1.0], [1.0, 1.0]],
            Fraction(1, 33),
            Fraction(1),
            Fraction(2, 33),
        ),
    ],
)
def test_manual_central_and_noncentral_conditionals(
    counts: list[list[int]],
    responses: list[list[float]],
    left: Fraction,
    right: Fraction,
    p_value: Fraction,
) -> None:
    result = subject.conditional_test(counts, responses, taxon_measured=MASK)
    assert (result.left_tail, result.right_tail, result.p_value) == (
        left,
        right,
        p_value,
    )
    assert result.status == "computed"


def test_independent_joint_binomial_enumeration_and_exact_null_coverage() -> None:
    # Construct joint binomial probabilities from rational common cover;
    # neither the production weight recurrence nor its odds formula is reused.
    for n1 in range(1, 5):
        for n2 in range(1, 5):
            for theta in (Fraction(1, 3), Fraction(2, 5)):
                probabilities = (theta, 2 * theta / (1 + theta))
                joint = {
                    (x, y): comb(n1, x)
                    * probabilities[0] ** x
                    * (1 - probabilities[0]) ** (n1 - x)
                    * comb(n2, y)
                    * probabilities[1] ** y
                    * (1 - probabilities[1]) ** (n2 - y)
                    for x in range(n1 + 1)
                    for y in range(n2 + 1)
                }
                for total in range(n1 + n2 + 1):
                    compatible = {xy: p for xy, p in joint.items() if sum(xy) == total}
                    mass = sum(compatible.values(), Fraction())
                    conditional = {xy: p / mass for xy, p in compatible.items()}
                    p_values = {}
                    for (x, y), observed_mass in conditional.items():
                        result = subject.conditional_test(
                            [[x, n1 - x], [y, n2 - y]],
                            [[1.0, 1.0], [2.0, 1.0]],
                            taxon_measured=MASK,
                        )
                        left = sum(
                            (p for (a, _), p in conditional.items() if a <= x),
                            Fraction(),
                        )
                        right = sum(
                            (p for (a, _), p in conditional.items() if a >= x),
                            Fraction(),
                        )
                        assert result.left_tail == left and result.right_tail == right
                        assert left + right == 1 + observed_mass
                        assert result.p_value == min(1, 2 * min(left, right))
                        p_values[(x, y)] = result.p_value
                    for alpha in (Fraction(1, 20), Fraction(1, 4), Fraction(1, 2)):
                        rejected = sum(
                            (
                                p
                                for xy, p in conditional.items()
                                if p_values[xy] <= alpha
                            ),
                            Fraction(),
                        )
                        assert rejected <= alpha


def test_site_taxon_and_site_scale_symmetries_preserve_exact_result() -> None:
    n, a = [[1, 4], [3, 2]], [[4.0, 2.0], [3.0, 8.0]]
    original = subject.conditional_test(n, a, taxon_measured=MASK)
    for counts, responses in (
        (n[::-1], a[::-1]),
        ([row[::-1] for row in n], [row[::-1] for row in a]),
    ):
        changed = subject.conditional_test(counts, responses, taxon_measured=MASK)
        assert changed.p_value == original.p_value
        assert changed.left_tail == original.right_tail
        assert changed.right_tail == original.left_tail
        assert changed.odds == 1 / original.odds
    scaled = subject.conditional_test(n, [[8.0, 4.0], [0.75, 2.0]], taxon_measured=MASK)
    assert scaled == original


def test_supplied_binary64_responses_are_exact_before_odds_products() -> None:
    responses = [[0.1, 0.2], [0.3, 0.4]]
    result = subject.conditional_test([[0, 1], [1, 0]], responses, taxon_measured=MASK)
    a, b, c, d = (Fraction.from_float(x) for row in responses for x in row)
    assert result.odds == a * d / (b * c)
    assert result.left_tail == 1 / (1 + result.odds)


@pytest.mark.parametrize(
    "counts", [[[0, 0], [1, 3]], [[2, 3], [0, 0]], [[0, 5], [0, 6]], [[5, 0], [6, 0]]]
)
def test_uninformative_support_is_explicit_not_confirmation(
    counts: list[list[int]],
) -> None:
    result = subject.conditional_test(counts, UNIT, taxon_measured=MASK)
    assert result.status == "uninformative" and result.reason
    assert result.left_tail == result.right_tail == result.p_value == 1


@pytest.mark.parametrize(
    "defect",
    [
        "both_zero",
        "negative",
        "fractional",
        "bool",
        "missing",
        "masked",
        "shape",
        "count_limit",
        "response_zero",
        "response_flag",
        "response_inf",
        "response_mask",
        "mask_false",
        "mask_integer",
        "mask_masked",
    ],
)
def test_malformed_or_unmeasured_inputs_refuse(defect: str) -> None:
    n: Any = [[1, 2], [3, 4]]
    a: Any = deepcopy(UNIT)
    mask: Any = deepcopy(MASK)
    if defect == "both_zero":
        n = [[0, 0], [0, 0]]
    elif defect == "negative":
        n[0][0] = -1
    elif defect == "fractional":
        n[0][0] = 1.5
    elif defect == "bool":
        n[0][0] = False
    elif defect == "missing":
        n[0][0] = None
    elif defect == "masked":
        n = np.ma.array(n, mask=[[True, False], [False, False]])
    elif defect == "shape":
        n = [[1, 2]]
    elif defect == "count_limit":
        n[0][0] = 10001
    elif defect == "response_zero":
        a[0][0] = 0
    elif defect == "response_flag":
        a[0][0] = True
    elif defect == "response_inf":
        a[0][0] = float("inf")
    elif defect == "response_mask":
        a = np.ma.array(a, mask=[[False, True], [False, False]])
    elif defect == "mask_false":
        mask[0][0] = False
    elif defect == "mask_integer":
        mask[0][0] = 1
    else:
        mask = np.ma.array(mask, mask=[[True, False], [False, False]])
    with pytest.raises(ValidationError):
        subject.conditional_test(n, a, taxon_measured=mask)


def test_fixed_bit_budget_refuses_before_any_combinatorial_allocation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*args: Any) -> int:
        pytest.fail("Resource guard must precede comb/pow")

    monkeypatch.setattr(subject, "comb", forbidden)
    with pytest.raises(ValidationError) as caught:
        subject.conditional_test(
            [[5000, 5000], [5000, 5000]],
            [[1e300, 1e-300], [1e-300, 1e300]],
            taxon_measured=MASK,
        )
    assert caught.value.reason_code == "conditional_integer_budget"


def test_directed_displays_keep_tiny_positive_tails_and_exact_decisions() -> None:
    result = subject.conditional_test(
        [[0, 1], [1, 0]], [[1e300, 1e-300], [1e-300, 1e300]], taxon_measured=MASK
    )
    assert 0 < result.p_value < Fraction(1, 10**1000)
    lower, upper = subject.decimal_bounds(result.p_value)
    assert 0 < Fraction(Decimal(lower)) <= result.p_value <= Fraction(Decimal(upper))
    assert result.p_value <= subject.ALPHA / subject.WINDOW_COUNT
    assert subject.decimal_bounds(Fraction(1)) == ("1", "1")


def loaded_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    loaded = deepcopy(admit_fixture(tmp_path, monkeypatch))
    for group in loaded["groups"]:
        for key in ("status", "solver", "common_cover_fit"):
            group.pop(key, None)
    for index, site in enumerate(loaded["unmatched"]):
        site["projected_counts"] = list(site["original_counts"])
        site["sample_ids"] = [100 + index]
    return loaded


def test_nineteen_windows_preserve_native_panels_and_do_not_consume_fits(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    loaded = loaded_fixture(tmp_path, monkeypatch)
    before = deepcopy(loaded)
    rows = subject.evaluate(loaded)
    assert loaded == before
    assert len(rows) == 19 and sum(r["status"] == "unmatched" for r in rows) == 6
    for row in rows[:13]:
        assert row["status"] in {"computed", "uninformative"}
        assert row["bus_Fraxinus_measured"] is False and row["boke_Fraxinus"] == 6
        assert Fraction(Decimal(row["p_value_lower"])) <= Fraction(
            Decimal(row["p_value_upper"])
        )
        assert type(row["p_le_0_05"]) is type(row["p_le_0_05_div_13"]) is bool
    for row in rows[13:]:
        assert row["p_value_lower"] == row["p_value_upper"] == ""
        assert row["boke_Betula"] == "" and row["bus_Betula"] == 4


@pytest.mark.parametrize(
    "defect",
    ["axis", "mask", "fraxinus", "denominator", "duplicate_window", "population"],
)
def test_changed_source_semantics_refuse(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, defect: str
) -> None:
    loaded = loaded_fixture(tmp_path, monkeypatch)
    site = loaded["groups"][0]["sites"][0]
    if defect == "axis":
        site["original_axis"].reverse()
    elif defect == "mask":
        site["taxon_measured_on_common_axis"][0] = 1
    elif defect == "fraxinus":
        site["Fraxinus_original_panel_count"] += 1
    elif defect == "denominator":
        site["original_panel_N"] += 1
    elif defect == "duplicate_window":
        loaded["groups"][1]["window_cal_bp"] = loaded["groups"][0]["window_cal_bp"]
    else:
        loaded["groups"].pop()
    with pytest.raises(ValidationError):
        subject.evaluate(loaded)


def test_fraxinus_only_boke_window_is_kept_as_uninformative(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    loaded = loaded_fixture(tmp_path, monkeypatch)
    site = loaded["groups"][0]["sites"][0]
    site.update(
        original_counts=[0, 6, 0],
        original_panel_N=6,
        projected_counts=[0, 0],
        projected_panel_N=0,
    )
    rows = subject.evaluate(loaded)
    assert len(rows) == 19 and rows[0]["status"] == "uninformative"
    assert rows[0]["reason"] == "zero_effort_site"
    assert rows[0]["p_value_lower"] == rows[0]["p_value_upper"] == "1"
    assert rows[0]["p_le_0_05"] is rows[0]["p_le_0_05_div_13"] is False


@pytest.mark.parametrize("change", ["none", "raw_changed", "source_changed"])
def test_cli_saved_csv_and_terminal_integrity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    change: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    loaded = loaded_fixture(tmp_path, monkeypatch)
    output = tmp_path / "artifacts" / "adequacy.csv"
    output.parent.mkdir()
    monkeypatch.setattr(cohort, "load_count_groups", lambda repository: loaded)
    calls = []

    def revision(repository: Path) -> str:
        calls.append(repository)
        return "2" * 40 if change == "source_changed" and len(calls) > 1 else "1" * 40

    monkeypatch.setattr(subject, "_revision", revision)
    if change == "raw_changed":

        def read(*args: Any) -> bytes:
            raise ValueError("Changed original raw source")

        monkeypatch.setattr(sources, "read_bound", read)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "conditional_adequacy",
            "--repository",
            str(tmp_path),
            "--output",
            str(output),
        ],
    )
    if change != "none":
        with pytest.raises(ValueError):
            subject.main()
        assert not output.exists()
        return
    with pytest.raises(SystemExit) as caught:
        subject.main()
    assert caught.value.code == 0
    rows = list(csv.DictReader(io.StringIO(output.read_text())))
    assert len(rows) == 19 and len(rows[0]) == len(subject.CSV_FIELDS)
    assert output.stat().st_size <= 128 * 1024
    assert "source_commit=" + "1" * 40 in capsys.readouterr().out
    with pytest.raises(ReportRebuildError, match="must be absent"):
        subject.main()


def test_source_gate_refuses_wrong_module_origin(tmp_path: Path) -> None:
    with pytest.raises(ValidationError, match="Canonical consumed source"):
        subject._revision(tmp_path)


def test_source_gate_checks_current_tracked_blobs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = Path(__file__).resolve().parents[5]
    calls = []

    def git(argv: list[str], **kwargs: Any) -> bytes:
        calls.append(argv)
        if argv[3] == "diff":
            raise subprocess.CalledProcessError(1, argv)
        return b"1" * 40 if argv[3] == "rev-parse" else b""

    monkeypatch.setattr(subprocess, "check_output", git)
    with pytest.raises(subprocess.CalledProcessError):
        subject._revision(root)
    assert [c[3] for c in calls] == ["rev-parse", "ls-files", "diff"]
