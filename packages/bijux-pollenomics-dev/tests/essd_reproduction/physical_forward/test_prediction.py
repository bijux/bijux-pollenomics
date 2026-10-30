"""Artificial complete-population controls for training and point predictions."""

from __future__ import annotations

from dataclasses import fields, replace
from typing import Any

import numpy as np
import pytest

from bijux_pollenomics_dev.essd_reproduction.physical_forward import prediction as p
from bijux_pollenomics_dev.essd_reproduction.physical_forward.inputs import (
    Core,
    normalize,
)


@pytest.fixture
def cores(
    artificial_sources: tuple[dict[str, Any], dict[str, Any]], protocol: dict[str, Any]
) -> tuple[Core, ...]:
    return normalize(*artificial_sources, protocol)


def test_all154_contexts_preserve_structural_refusals(
    cores: tuple[Core, ...], protocol: dict[str, Any], fake_points: None
) -> None:
    rows, completed = p.predictions(cores, protocol)
    assert completed and len(rows) == 154
    for core, scopes in protocol["structural_counts"].items():
        for scope, expected in scopes.items():
            selected = [
                row
                for row in rows
                if row["identity"]["core"] == core and row["identity"]["scope"] == scope
            ]
            assert len(selected) == expected["target_windows"]
            assert (
                sum(
                    row["families"]["physical_forward"]["status"] == "predicted"
                    for row in selected
                )
                == expected["structural_candidates"]
            )
            assert all(
                source["physical_site"] != row["identity"]["physical_site"]
                for row in selected
                for source in row["training_sources"]
            )
    assert [f.name for f in fields(p.Target)] == [
        "core",
        "site",
        "dataset",
        "collection_unit",
        "window",
        "axis",
        "ppe",
        "kernels",
    ]


def test_core_order_cannot_change_predictions(
    cores: tuple[Core, ...], protocol: dict[str, Any], fake_points: None
) -> None:
    assert p.predictions(cores, protocol) == p.predictions(
        tuple(reversed(cores)), protocol
    )


def test_own_target_counts_do_not_change_own_predictions(
    cores: tuple[Core, ...], protocol: dict[str, Any], fake_points: None
) -> None:
    original = p.predictions(cores, protocol)[0]
    changed = tuple(
        replace(
            core,
            cells=tuple(
                replace(cell, counts=tuple(n + 100 for n in cell.counts))
                for cell in core.cells
            ),
        )
        if core.id == "BOKE"
        else core
        for core in cores
    )
    actual = p.predictions(changed, protocol)[0]
    assert [row for row in original if row["identity"]["core"] == "BOKE"] == [
        row for row in actual if row["identity"]["core"] == "BOKE"
    ]


def test_removed_fraxinus_does_not_enter_either_panel_denominator(
    cores: tuple[Core, ...], protocol: dict[str, Any], fake_points: None
) -> None:
    changed = tuple(
        replace(
            core,
            cells=tuple(
                replace(cell, counts=(cell.counts[0], 99999, cell.counts[2]))
                for cell in core.cells
            ),
        )
        if core.id == "BOKE"
        else core
        for core in cores
    )
    assert p.predictions(changed, protocol) == p.predictions(cores, protocol)


def test_zero_projected_training_panel_refuses_without_imputation(
    cores: tuple[Core, ...], protocol: dict[str, Any], fake_points: None
) -> None:
    changed = tuple(
        replace(
            core, cells=tuple(replace(cell, counts=(0, 9, 0)) for cell in core.cells)
        )
        if core.id == "BOKE"
        else core
        for core in cores
    )
    rows, completed = p.predictions(changed, protocol)
    assert completed
    row = next(
        row
        for row in rows
        if row["identity"]["core"] == "BUS"
        and row["identity"]["scope"] == "swedish_only"
    )
    assert any(
        r["reason"] == "projected_training_panel_total_zero"
        for r in row["source_refusals"]
    )
    assert all(value["status"] == "refused" for value in row["families"].values())


def test_two_solsoe_cores_never_become_independent_places(
    cores: tuple[Core, ...], protocol: dict[str, Any], fake_points: None
) -> None:
    target_core = next(c for c in cores if c.id == "BOKE")
    target = p.target_geometry(target_core, (2700.0, 3200.0), ("Betula", "Ulmus"))
    sources, refused = p.eligible_sources(target, cores, "pooled_eligible_nordic")
    assert any(
        row["core"] == "SOLSOE81" and "panel" in row["reason"] for row in refused
    )
    solsoe = next(source for source in sources if source.core.id == "SOLSOE83")
    values = p.predict_context(
        target,
        [*sources, replace(solsoe, core=replace(solsoe.core, id="duplicate-core"))],
        {},
    )
    assert all(
        value["reason"] == "ambiguous_multiple_cores_same_physical_place"
        for value in values.values()
    )


def test_known_inverse_refusal_retains_direct_baseline(
    cores: tuple[Core, ...],
    protocol: dict[str, Any],
    fake_points: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from bijux_pollenomics_lra.models.errors import ValidationError

    def refuse(source: p.Source) -> tuple[float, ...]:
        raise ValidationError(
            "Artificial inverse refusal", reason_code="artificial_inverse"
        )

    monkeypatch.setattr(p, "_inverse", refuse)
    rows, completed = p.predictions(cores, protocol)
    assert completed
    row = next(row for row in rows if row["training_sources"])
    assert row["families"]["direct_panel_mean"]["status"] == "predicted"
    assert row["families"]["physical_forward"]["reason"] == "artificial_inverse"
    assert row["families"]["physical_forward"]["operation"] == "source_inverse"
    assert row["families"]["physical_forward"]["core"] in {
        source["core"] for source in row["training_sources"]
    }


def test_unknown_fault_is_fatal_and_retains_prior_direct_value(
    cores: tuple[Core, ...],
    protocol: dict[str, Any],
    fake_points: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def crash(source: p.Source) -> tuple[float, ...]:
        raise RuntimeError("Artificial unexpected failure")

    monkeypatch.setattr(p, "_inverse", crash)
    rows, completed = p.predictions(cores, protocol)
    assert not completed and len(rows) == 154
    index = next(i for i, row in enumerate(rows) if row["status"] == "fatal")
    assert rows[index]["families"]["direct_panel_mean"]["status"] == "predicted"
    assert rows[index]["families"]["physical_forward"]["error_type"] == "RuntimeError"
    assert rows[index]["families"]["physical_forward"]["operation"] == "source_inverse"
    assert all(row["status"] == "not_run_after_fatal" for row in rows[index + 1 :])


def test_real_API_adapters_pass_exact_source_and_target_axes(
    cores: tuple[Core, ...], monkeypatch: pytest.MonkeyPatch
) -> None:
    from types import SimpleNamespace

    from bijux_pollenomics_lra import api

    target_core = next(c for c in cores if c.id == "BUS")
    target = p.target_geometry(
        target_core, target_core.cells[0].window, ("Betula", "Ulmus")
    )
    sources, _ = p.eligible_sources(target, cores, "swedish_only")
    source = sources[0]

    def inverse(
        n: np.ndarray[Any, Any],
        k: np.ndarray[Any, Any],
        e: np.ndarray[Any, Any],
        cov: np.ndarray[Any, Any],
        *,
        taxon_measured: np.ndarray[Any, Any],
    ) -> Any:
        assert n.tolist() == [list(source.counts)]
        assert k.tolist() == [[source.core.kernels[i] for i in source.indices]]
        assert e.tolist() == [source.core.ppe[i] for i in source.indices]
        assert (
            cov.tolist()
            == np.diag([source.core.sd[i] ** 2 for i in source.indices]).tolist()
        )
        assert taxon_measured.tolist() == [[True, True]]
        return SimpleNamespace(cover=np.asarray([0.25, 0.75]))

    def forward(
        cover: object,
        regional: np.ndarray[Any, Any],
        k: np.ndarray[Any, Any],
        fractions: np.ndarray[Any, Any],
        ppe: object,
    ) -> Any:
        assert cover == (0.25, 0.75)
        assert regional.tolist() == [0.0, 0.0]
        assert k.tolist() == [list(target.kernels)] and fractions.tolist() == [1.0]
        assert ppe == target.ppe
        return SimpleNamespace(pollen_fraction=np.asarray([0.4, 0.6]))

    monkeypatch.setattr(api, "fixed_site_cover_covariance", inverse)
    monkeypatch.setattr(api, "forward_deposition", forward)
    assert p._inverse(source) == (0.25, 0.75)
    assert p._forward(target, (0.25, 0.75)) == (0.4, 0.6)
