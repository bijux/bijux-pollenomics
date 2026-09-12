"""Dispersal loess for the LRA engine."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

import numpy as np
from scipy.interpolate import CubicHermiteSpline
from scipy.linalg import lstsq

from bijux_pollenomics_lra.models.errors import ValidationError


@dataclass(frozen=True, slots=True)
class Loess1D:
    """Cubic-Hermite representation of R's one-predictor local quadratic fit."""

    vertices: np.ndarray
    values: np.ndarray
    derivatives: np.ndarray
    domain: tuple[float, float]
    _spline: CubicHermiteSpline = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        for name in ("vertices", "values", "derivatives"):
            value = np.array(getattr(self, name), dtype=float, copy=True)
            if value.ndim != 1 or value.size < 2 or not np.isfinite(value).all():
                raise ValidationError(f"Invalid LOESS {name}")
            value.setflags(write=False)
            object.__setattr__(self, name, value)
        if not (
            len(self.vertices) == len(self.values) == len(self.derivatives)
            and np.all(np.diff(self.vertices) > 0)
        ):
            raise ValidationError("LOESS vertices, values, and derivatives disagree")
        domain = (float(self.domain[0]), float(self.domain[1]))
        if not np.isfinite(domain).all() or domain[0] >= domain[1]:
            raise ValidationError("Invalid LOESS domain")
        object.__setattr__(self, "domain", domain)
        object.__setattr__(
            self,
            "_spline",
            CubicHermiteSpline(self.vertices, self.values, self.derivatives),
        )

    def predict(self, x: object) -> float | np.ndarray:
        """Evaluate within the fitted R model domain; return NaN outside it."""
        values = np.asarray(x, dtype=float)
        result = np.asarray(self._spline(values), dtype=float)
        result = np.where(
            (values < self.domain[0]) | (values > self.domain[1]),
            np.nan,
            result,
        )
        return float(result) if result.ndim == 0 else result

    __call__ = predict

    @classmethod
    def fit(
        cls,
        x: object,
        y: object,
        *,
        span: float = 0.015,
        degree: int = 2,
        cell: float = 0.2,
    ) -> Loess1D:
        """Fit the one-dimensional local quadratic used by the source models.

        This implementation is intentionally limited to the exact one-predictor,
        degree-two use case needed by LRA.  It uses split vertices, tricube
        weights, column-equilibrated least squares, and local first derivatives.
        """
        x_values = np.asarray(x, dtype=float)
        y_values = np.asarray(y, dtype=float)
        if (
            x_values.ndim != 1
            or x_values.shape != y_values.shape
            or len(x_values) < 4
            or not np.isfinite(x_values).all()
            or not np.isfinite(y_values).all()
        ):
            raise ValidationError("LOESS requires equal finite one-dimensional data")
        if degree != 2 or not (0 < span <= 1) or not (0 < cell <= 1):
            raise ValidationError(
                "Python LOESS supports degree=2 and 0 < span, cell <= 1"
            )

        order = np.argsort(x_values)
        x_values = x_values[order]
        y_values = y_values[order]
        if np.any(np.diff(x_values) <= 0):
            raise ValidationError("LOESS predictor values must be distinct")

        count = len(x_values)
        neighbourhood = max(3, int(count * span))
        split_tolerance = max(1, int(count * span * cell))
        width = x_values[-1] - x_values[0]
        pad = 0.005 * max(
            width,
            1e-10 * max(abs(x_values[0]), abs(x_values[-1])) + 1e-30,
        )
        vertices: list[float] = [x_values[0] - pad, x_values[-1] + pad]
        queue: deque[tuple[int, int]] = deque([(0, count - 1)])
        # R simpleLoess allocates max(200, n) kd-tree nodes. Each split
        # consumes two nodes; respecting that cap matters for dense 1/d fits.
        maximum_vertices = (max(200, count) + 1) // 2 + 1
        while queue:
            lower, upper = queue.popleft()
            if upper - lower + 1 > split_tolerance and len(vertices) < maximum_vertices:
                middle = (lower + upper) // 2
                vertices.append(float(x_values[middle]))
                queue.extend(((lower, middle), (middle + 1, upper)))

        vertex_values = np.unique(np.asarray(vertices, dtype=float))
        fits: list[np.ndarray] = []
        for query in vertex_values:
            squared_distance = (x_values - query) ** 2
            selected = np.argsort(squared_distance, kind="stable")[:neighbourhood]
            radius = squared_distance[selected[-1]]
            if radius <= 0:
                raise ValidationError("Degenerate LOESS neighbourhood")
            square_root_weights = np.sqrt(
                np.maximum(0, 1 - np.sqrt(squared_distance[selected] / radius) ** 3)
                ** 3
            )
            delta = x_values[selected] - query
            design = np.column_stack(
                (
                    square_root_weights,
                    square_root_weights * delta,
                    square_root_weights * delta**2,
                )
            )
            norms = np.sqrt(np.sum(design**2, axis=0))
            norms[norms == 0] = 1
            beta = (
                lstsq(
                    design / norms,
                    square_root_weights * y_values[selected],
                    cond=100 * np.finfo(float).eps,
                    lapack_driver="gelsd",
                )[0]
                / norms
            )
            fits.append(beta[:2])

        fitted = np.asarray(fits)
        return cls(
            vertex_values,
            fitted[:, 0],
            fitted[:, 1],
            (float(x_values[0]), float(x_values[-1])),
        )
