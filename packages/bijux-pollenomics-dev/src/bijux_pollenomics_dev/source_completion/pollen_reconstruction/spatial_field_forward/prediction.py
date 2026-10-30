"""Predict a held place from two other count panels and count-free geometry."""

from __future__ import annotations

from dataclasses import asdict
import math
from typing import Any

import numpy as np

from bijux_pollenomics_lra.reconstruction.fixed_site_covariance import (
    fixed_site_cover_covariance,
)
from bijux_pollenomics_lra.reconstruction.forward import forward_deposition

from .inputs import SourcePanel, TargetGeometry
from .sources import FAMILIES, require


def close(values: list[float]) -> list[float]:
    """Close finite nonnegative deposition without replacing an absent axis."""
    require(
        all(math.isfinite(x) and x >= 0 for x in values) and math.fsum(values) > 0,
        "Invalid deposition composition",
    )
    total = math.fsum(values)
    return [x / total for x in values]


def normalized_bounds(mass: list[list[float]]) -> list[list[float]]:
    """Conservatively normalize independent nonnegative two-axis mass ranges."""
    require(
        len(mass) == 2 and all(0 <= a <= b and math.isfinite(b) for a, b in mass),
        "Invalid mass interval",
    )
    require(
        mass[0][0] + mass[1][1] > 0 and mass[0][1] + mass[1][0] > 0,
        "Undefined normalized interval",
    )
    lo = mass[0][0] / (mass[0][0] + mass[1][1])
    hi = mass[0][1] / (mass[0][1] + mass[1][0])
    return [[lo, hi], [1 - hi, 1 - lo]]


def predict(
    target: TargetGeometry,
    anchors: tuple[SourcePanel, SourcePanel],
    geometry: dict[str, Any],
    homogeneous: dict[str, list[float]],
    ppe: list[float],
) -> dict[str, Any]:
    """The complete prediction boundary has no argument for target outcomes."""
    require(
        target.core == geometry["core"]
        and [a.core for a in anchors] == geometry["anchor_order"],
        "Geometry/anchor identities differ",
    )
    require(
        all(a.site_id != target.site_id and a.window == target.window for a in anchors)
        and len({a.site_id for a in anchors}) == 2,
        "Held place entered its own training set",
    )
    training = []
    pollen = [close(list(a.counts)) for a in anchors]
    for anchor, fraction in zip(anchors, pollen, strict=True):
        training.append({**asdict(anchor), "pollen_fraction": fraction})
    weights = geometry["centre_weights"]
    direct = [math.fsum(weights[s] * pollen[s][i] for s in range(2)) for i in range(2)]
    families: dict[str, Any] = {
        FAMILIES[0]: {
            "status": "predicted",
            "pollen_fraction": direct,
            "prediction_bounds": [[v, v] for v in direct],
        }
    }
    try:
        require(
            target.core in homogeneous and all(a.core in homogeneous for a in anchors),
            "A required homogeneous receiver geometry was refused",
        )
        covers = []
        for anchor, record in zip(anchors, training, strict=True):
            factors = homogeneous[anchor.core]
            cover = fixed_site_cover_covariance(
                np.array([anchor.counts]),
                np.array([factors]),
                np.array(ppe),
                np.zeros((2, 2)),
                taxon_measured=np.ones((1, 2), dtype=bool),
            ).cover.tolist()
            covers.append(cover)
            record.update(cover=cover, homogeneous_factors=factors)
        target_k = homogeneous[target.core]
        centre_cover = [
            math.fsum(weights[s] * covers[s][i] for s in range(2)) for i in range(2)
        ]
        centre = forward_deposition(
            centre_cover, [0.0, 0.0], [target_k], [1.0], ppe
        ).pollen_fraction.tolist()
        families[FAMILIES[1]] = {
            "status": "predicted",
            "pollen_fraction": centre,
            "prediction_bounds": [[v, v] for v in centre],
        }
        require(
            geometry["status"] == "qualified", "Weighted spatial geometry was refused"
        )
        weighted_factors = [t["primary"]["anchor_factors"] for t in geometry["taxa"]]
        deposition = [
            forward_deposition(
                covers[s],
                [0.0, 0.0],
                [[weighted_factors[i][s] for i in range(2)]],
                [1.0],
                ppe,
            ).total_deposition.tolist()
            for s in range(2)
        ]
        spatial = close([math.fsum(d[i] for d in deposition) for i in range(2)])
        intervals = []
        for i, taxon in enumerate(geometry["taxa"]):
            bounds = taxon["step_bounds"]["anchor_factor_bounds"]
            intervals.append(
                [
                    ppe[i] * math.fsum(bounds[s][end] * covers[s][i] for s in range(2))
                    for end in range(2)
                ]
            )
        families[FAMILIES[2]] = {
            "status": "predicted",
            "pollen_fraction": spatial,
            "prediction_bounds": normalized_bounds(intervals),
        }
    except (ValueError, ArithmeticError) as error:
        for family in FAMILIES[1:]:
            families.setdefault(
                family,
                {
                    "status": "refused_prediction",
                    "reason": f"{type(error).__name__}: {error}",
                },
            )
    return {
        "context_id": f"{target.core}:{target.window[0]}:{target.window[1]}",
        "target": asdict(target),
        "training": training,
        "geometry_core": target.core,
        "families": families,
    }
