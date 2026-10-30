"""Analytical controls and refusal accounting for independent numerical verification."""

from decimal import Decimal, localcontext
from pathlib import Path

import pytest

from bijux_pollenomics_dev.source_completion.vegetation.namibia_pollen_prediction import (
    verification,
)
from bijux_pollenomics_dev.source_completion.vegetation.namibia_pollen_prediction.verification_math import (
    losses,
)
from bijux_pollenomics_dev.source_completion.vegetation.namibia_pollen_prediction.verification_sources import (
    GROUPS,
    read_sources,
)
from bijux_pollenomics_dev.source_completion.vegetation.namibia_pollen_prediction.verification_summary import (
    Scores,
    summarize_verification,
)


def test_analytical_cli_controls_need_no_scientific_source(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        verification,
        "verify",
        lambda *_args: pytest.fail("analytical controls must not read study data"),
    )
    assert verification.main(["--self-test"]) == 0
    assert "PASS controlled" in capsys.readouterr().out


def test_scores_match_two_taxon_closed_form() -> None:
    with localcontext() as context:
        context.prec = 160
        nll, mae, h2 = losses((Decimal("0.5"), Decimal("0.5")), (1, 3))
        assert nll == Decimal(2).ln()
        assert mae == Decimal("0.25")
        expected = 1 - (Decimal(1) / 8).sqrt() - (Decimal(3) / 8).sqrt()
        assert abs(h2 - expected) < Decimal("1e-150")


def test_independent_source_reader_refuses_changed_original_bytes(
    tmp_path: Path,
) -> None:
    (tmp_path / "PANGAEA.931033.tab").write_bytes(b"changed source table")
    with pytest.raises(AssertionError, match="original source identity"):
        read_sources(tmp_path)


def test_ledger_refuses_unknown_columns_before_fitting(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(verification, "read_sources", lambda _root: ({}, {}, {}, {}))
    monkeypatch.setattr(
        verification, "solve", lambda *_args: pytest.fail("unexpected fit")
    )
    report = tmp_path / "predictions.csv"
    report.write_text("unknown,column\n1,2\n")
    with pytest.raises(AssertionError, match="exact declared prediction CSV fields"):
        verification.verify(tmp_path, report)


def test_missing_site_does_not_create_partial_full_support_means() -> None:
    scores: Scores = {
        (100, "empirical", "mean_nll"): [
            (site, "|".join(group), Decimal(1), Decimal(1))
            for group in GROUPS
            for site in group
            if site != "Namibia_T7"
        ]
    }

    def compare(*_args: object) -> Decimal:
        pytest.fail("no complete method population is available for averaging")

    summaries, compared = summarize_verification(scores, {}, None, compare)
    selected = [
        row
        for row in summaries
        if row["radius"] == 100
        and row["method"] == "empirical"
        and row["metric"] == "mean_nll"
    ]
    assert len(selected) == 2 and compared == 0
    assert all(row["sites"] == 9 and row["groups"] == 8 for row in selected)
    assert all(
        row["value"] is None and row["full_support"] is False for row in selected
    )
