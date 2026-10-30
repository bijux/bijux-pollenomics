"""Predict from whole-site-excluded sources; target geometry carries no counts."""

from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Real
from typing import Any

from .inputs import Cell, Core, Window, require

FAMILIES = ("physical_forward", "direct_panel_mean")


@dataclass(frozen=True)
class Target:
    core: str
    site: int
    dataset: int
    collection_unit: int
    window: Window
    axis: tuple[str, ...]
    ppe: tuple[float, ...]
    kernels: tuple[float, ...]


@dataclass(frozen=True)
class Source:
    core: Core
    cell: Cell
    indices: tuple[int, ...]
    counts: tuple[int, ...]


def target_geometry(core: Core, window: Window, axis: tuple[str, ...]) -> Target:
    indices = tuple(core.axis.index(name) for name in axis)
    return Target(
        core.id,
        core.site,
        core.dataset,
        core.collection_unit,
        window,
        axis,
        tuple(core.ppe[i] for i in indices),
        tuple(core.kernels[i] for i in indices),
    )


def eligible_sources(
    target: Target, cores: tuple[Core, ...], scope: str
) -> tuple[list[Source], list[dict[str, Any]]]:
    require(
        scope in {"swedish_only", "pooled_eligible_nordic"}, "Unknown training scope"
    )
    accepted, rejected = [], []
    for core in sorted(cores, key=lambda item: item.id):
        reason = None
        if core.site == target.site:
            reason = "whole_target_physical_site_excluded"
        elif scope == "swedish_only" and core.country != "SE":
            reason = "outside_declared_training_scope"
        elif not set(target.axis) <= set(core.axis):
            reason = "target_panel_not_fully_explicit_in_saved_source_axis"
        else:
            cells = [cell for cell in core.cells if cell.window == target.window]
            if not cells:
                reason = "no_same_declared_calBP_window"
            else:
                require(len(cells) == 1, "Ambiguous source window")
                indices = tuple(core.axis.index(name) for name in target.axis)
                counts = tuple(cells[0].counts[i] for i in indices)
                if sum(counts) == 0:
                    reason = "projected_training_panel_total_zero"
                elif tuple(core.ppe[i] for i in indices) != target.ppe:
                    reason = "source_target_PPE_transfer_differs"
                else:
                    accepted.append(Source(core, cells[0], indices, counts))
        if reason is not None:
            rejected.append(
                {
                    "core": core.id,
                    "physical_site": core.site,
                    "dataset": core.dataset,
                    "reason": reason,
                }
            )
    return accepted, rejected


def _closed(values: Any, size: int) -> tuple[float, ...]:
    require(len(values) == size, "Prediction taxon axis differs")
    require(
        all(isinstance(v, Real) and not isinstance(v, bool) for v in values),
        "Prediction values must be numeric, not coerced",
    )
    numbers = tuple(float(value) for value in values)
    require(
        all(math.isfinite(v) and 0 <= v <= 1 for v in numbers)
        and abs(math.fsum(numbers) - 1) <= 1e-12,
        "Finite closed prediction required",
    )
    return numbers


def _inverse(source: Source) -> tuple[float, ...]:
    import numpy as np

    from bijux_pollenomics_lra.api import fixed_site_cover_covariance

    indices = source.indices
    sd = np.asarray([source.core.sd[i] for i in indices])
    value = fixed_site_cover_covariance(
        np.asarray([source.counts], dtype=np.int64),
        np.asarray([[source.core.kernels[i] for i in indices]]),
        np.asarray([source.core.ppe[i] for i in indices]),
        np.diag(sd**2),
        taxon_measured=np.ones((1, len(indices)), dtype=bool),
    )
    # This consumer uses the point composition only, never its conditional SE.
    return _closed(value.cover, len(indices))


def _forward(target: Target, cover: tuple[float, ...]) -> tuple[float, ...]:
    import numpy as np

    from bijux_pollenomics_lra.api import forward_deposition

    result = forward_deposition(
        cover,
        np.zeros(len(cover)),
        np.asarray([target.kernels]),
        np.ones(1),
        target.ppe,
    )
    return _closed(result.pollen_fraction, len(cover))


def _mean(values: list[tuple[float, ...]]) -> tuple[float, ...]:
    require(bool(values), "No eligible physical training source")
    size = len(values[0])
    return _closed(
        [math.fsum(row[i] for row in values) / len(values) for i in range(size)], size
    )


def predict_context(
    target: Target,
    sources: list[Source],
    cache: dict[tuple[str, tuple[str, ...], Window], tuple[float, ...]],
) -> dict[str, Any]:
    from bijux_pollenomics_lra.models.errors import ValidationError

    predictions: dict[str, Any] = {
        name: {
            "status": "refused",
            "reason": "no_eligible_training_source",
            "pollen_fraction": None,
        }
        for name in FAMILIES
    }
    if not sources:
        return predictions
    if len({source.core.site for source in sources}) != len(sources):
        return {
            name: {
                "status": "refused",
                "reason": "ambiguous_multiple_cores_same_physical_place",
                "pollen_fraction": None,
            }
            for name in FAMILIES
        }
    direct = _mean(
        [tuple(n / sum(source.counts) for n in source.counts) for source in sources]
    )
    predictions["direct_panel_mean"] = {
        "status": "predicted",
        "pollen_fraction": list(direct),
    }
    operation: dict[str, Any] = {}
    try:
        covers = []
        for source in sources:
            operation = {
                "operation": "source_inverse",
                "core": source.core.id,
                "physical_site": source.core.site,
            }
            key = (source.core.id, target.axis, target.window)
            if key not in cache:
                cache[key] = _inverse(source)
            covers.append(cache[key])
        cover = _mean(covers)
        operation = {
            "operation": "target_forward",
            "core": target.core,
            "physical_site": target.site,
        }
        pollen = _forward(target, cover)
        predictions["physical_forward"] = {
            "status": "predicted",
            "pollen_fraction": list(pollen),
            "training_mean_conditional_cover": list(cover),
        }
    except ValidationError as error:
        predictions["physical_forward"] = {
            **operation,
            "status": "refused",
            "reason": error.reason_code,
            "message": str(error),
            "pollen_fraction": None,
        }
    except Exception as error:
        predictions["physical_forward"] = {
            **operation,
            "status": "fatal",
            "error_type": type(error).__name__,
            "message": str(error),
            "pollen_fraction": None,
        }
    return predictions


def predictions(
    cores: tuple[Core, ...], protocol: dict[str, Any]
) -> tuple[list[dict[str, Any]], bool]:
    rows = []
    cache: dict[tuple[str, tuple[str, ...], Window], tuple[float, ...]] = {}
    fatal = False
    for core in sorted(
        (c for c in cores if c.country == "SE"), key=lambda item: item.id
    ):
        axis = tuple(protocol["target_axes"][core.id])
        for cell in core.cells:
            target = target_geometry(core, cell.window, axis)
            for scope in protocol["scopes"]:
                identity = {
                    "core": core.id,
                    "physical_site": core.site,
                    "dataset": core.dataset,
                    "collection_unit": core.collection_unit,
                    "window_cal_bp": list(cell.window),
                    "axis": list(axis),
                    "scope": scope,
                }
                row: dict[str, Any] = {
                    "identity": identity,
                    "status": "not_run_after_fatal",
                    "training_sources": [],
                    "source_refusals": [],
                    "families": {
                        name: {"status": "not_run_after_fatal", "pollen_fraction": None}
                        for name in FAMILIES
                    },
                }
                if not fatal:
                    try:
                        sources, rejected = eligible_sources(target, cores, scope)
                        row.update(
                            training_sources=[
                                {
                                    "core": s.core.id,
                                    "physical_site": s.core.site,
                                    "dataset": s.core.dataset,
                                    "collection_unit": s.core.collection_unit,
                                    "window_cal_bp": list(s.cell.window),
                                    "source_support_sha256": s.cell.source_support_sha256,
                                    "projected_panel_N": sum(s.counts),
                                }
                                for s in sources
                            ],
                            source_refusals=rejected,
                        )
                        row["families"] = predict_context(target, sources, cache)
                        fatal = any(
                            value["status"] == "fatal"
                            for value in row["families"].values()
                        )
                        row["status"] = "fatal" if fatal else "completed"
                    except Exception as error:
                        fatal = True
                        row.update(
                            status="fatal",
                            error_type=type(error).__name__,
                            message=str(error),
                        )
                rows.append(row)
    require(
        len(rows) == protocol["expected_contexts"] == 154,
        "All154prediction contexts required",
    )
    return rows, not fatal
