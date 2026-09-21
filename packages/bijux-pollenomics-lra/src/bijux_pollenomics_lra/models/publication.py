"""Explicit input and method contracts for historical multi-site REVEALS."""

from __future__ import annotations

from dataclasses import dataclass
from numbers import Real

import numpy as np

from bijux_pollenomics_lra.models.errors import ValidationError

PUBLICATION_PROFILE = "landclimii-2016-release-source-v1"
PUBLICATION_REVISION = "57ead2e2fcc493d099be4e5a3092fc396e1c3d3a"
PUBLICATION_LIMITATIONS = (
    "single_site_ppe_diagonal_preserves_source_operator_order",
    "single_site_se_depends_on_taxon_order_in_source",
    "multisite_bootstrap_does_not_propagate_ppe_covariance",
    "bootstrap_mean_is_ratio_of_accumulated_unclosed_productivity_adjusted_cover",
    "lake_gamma_expression_has_unresolved_author_source_comment",
    "source_agreement_does_not_certify_independent_vegetation_accuracy",
)


@dataclass(frozen=True, slots=True)
class PublicationRevealsConfig:
    """One historical GPM profile; time support must be named explicitly.

    This profile always uses 1000 explicit site-bootstrap draws, matching the
    release. The caller supplies BP bin edges and their preprocessing identity;
    an author-archive bin label is not evidence of the paper's time support.
    """

    time_bin_profile: str
    wind_speed_m_s: float = 3.0
    regional_extent_m: float = 100_000.0
    profile: str = PUBLICATION_PROFILE

    def __post_init__(self) -> None:
        if self.profile != PUBLICATION_PROFILE:
            raise ValidationError("Unsupported publication REVEALS profile")
        if (
            not isinstance(self.time_bin_profile, str)
            or not self.time_bin_profile.strip()
        ):
            raise ValidationError(
                "A nonempty time-bin preprocessing profile is required"
            )
        for name in ("wind_speed_m_s", "regional_extent_m"):
            value = getattr(self, name)
            if (
                isinstance(value, (bool, np.bool_))
                or not isinstance(value, Real)
                or not np.isfinite(float(value))
                or value <= 0
            ):
                raise ValidationError(f"{name} must be positive and finite")


def _identifiers(values: tuple[str, ...], name: str) -> tuple[str, ...]:
    result = tuple(values)
    if not result or any(
        not isinstance(value, str) or not value.strip() for value in result
    ):
        raise ValidationError(f"{name} must contain nonempty string identifiers")
    if len(set(result)) != len(result):
        raise ValidationError(f"{name} must be unique")
    return result


def _array(value: object, name: str, shape: tuple[int, ...]) -> np.ndarray:
    original = np.asarray(value)
    if original.dtype.kind not in "iuf":
        raise ValidationError(
            f"{name} must contain numeric values, not coerced strings or booleans"
        )
    if original.dtype.kind in "iu" and np.any(
        np.abs(original.astype(object)) > 2**53 - 1
    ):
        raise ValidationError(
            f"{name} integer values exceed exact count/radius conversion support"
        )
    result = np.array(original, dtype=float, copy=True)
    if result.shape != shape:
        raise ValidationError(f"{name} must have shape {shape}")
    result.setflags(write=False)
    return result


@dataclass(frozen=True, slots=True)
class MultisiteRevealsInput:
    """Owned arrays with site/bin/taxon axes and explicit missing support.

    Counts use counts, radii use metres, fall speeds use metres/second and PPEs
    are dimensionless ratios. Bin bounds are [younger, older] calendar years BP
    (1950 CE). Unavailable site/bin cells must contain NaN counts and radius plus
    None basin type; they cannot silently become zero-count observations.
    """

    site_ids: tuple[str, ...]
    bin_ids: tuple[str, ...]
    taxon_ids: tuple[str, ...]
    counts: np.ndarray
    availability: np.ndarray
    basin_radius_m: np.ndarray
    basin_type: np.ndarray
    bin_bounds_bp: np.ndarray
    ppe: np.ndarray
    ppe_covariance: np.ndarray
    fall_speed_m_s: np.ndarray

    def __post_init__(self) -> None:
        for name in ("site_ids", "bin_ids", "taxon_ids"):
            object.__setattr__(self, name, _identifiers(getattr(self, name), name))
        sites, bins, taxa = len(self.site_ids), len(self.bin_ids), len(self.taxon_ids)
        for name, shape in (
            ("counts", (sites, bins, taxa)),
            ("basin_radius_m", (sites, bins)),
            ("bin_bounds_bp", (bins, 2)),
            ("ppe", (taxa,)),
            ("ppe_covariance", (taxa, taxa)),
            ("fall_speed_m_s", (taxa,)),
        ):
            object.__setattr__(self, name, _array(getattr(self, name), name, shape))
        available = np.array(self.availability, copy=True)
        if available.dtype != bool or available.shape != (sites, bins):
            raise ValidationError("availability must be a boolean [sites,bins] matrix")
        types = np.array(self.basin_type, dtype=object, copy=True)
        if types.shape != (sites, bins):
            raise ValidationError("basin_type must have shape [sites,bins]")
        if any(value not in ("lake", "peatland") for value in types[available]):
            raise ValidationError(
                "Available basin_type values must be lake or peatland"
            )
        if any(value is not None for value in types[~available]):
            raise ValidationError("Unavailable basin_type values must be None")
        available.setflags(write=False)
        types.setflags(write=False)
        object.__setattr__(self, "availability", available)
        object.__setattr__(self, "basin_type", types)
        observed = self.counts[available]
        if (
            not np.isfinite(observed).all()
            or np.any(observed < 0)
            or np.any(observed != np.floor(observed))
            or np.any(observed.sum(axis=-1) <= 0)
        ):
            raise ValidationError(
                "Available pollen observations require nonnegative integer counts with positive totals"
            )
        if not np.isnan(self.counts[~available]).all():
            raise ValidationError(
                "Unavailable pollen observations must be NaN, not zeros"
            )
        if not np.isnan(self.basin_radius_m[~available]).all():
            raise ValidationError("Unavailable basin radii must be NaN")
        if not np.isfinite(self.basin_radius_m[available]).all() or np.any(
            self.basin_radius_m[available] <= 0
        ):
            raise ValidationError("Available basin radii must be positive and finite")
        for name in ("ppe", "fall_speed_m_s"):
            values = getattr(self, name)
            if not np.isfinite(values).all() or np.any(values <= 0):
                raise ValidationError(f"{name} must be positive and finite")
        covariance = self.ppe_covariance
        if not np.isfinite(covariance).all() or not np.allclose(
            covariance, covariance.T, rtol=0, atol=1e-12
        ):
            raise ValidationError("PPE covariance must be finite and symmetric")
        if (
            np.any(np.diag(covariance) < 0)
            or np.linalg.eigvalsh(covariance).min() < -1e-12
        ):
            raise ValidationError("PPE covariance must be positive semidefinite")
        bounds = self.bin_bounds_bp
        if not np.isfinite(bounds).all() or np.any(bounds[:, 0] >= bounds[:, 1]):
            raise ValidationError("BP bin bounds need finite younger < older")
        if np.any(bounds[1:, 0] < bounds[:-1, 1]):
            raise ValidationError("BP bins must be ordered without overlap")


PUBLICATION_ARCHIVE_SHA256 = (
    "cd6cc688e6c44dd61d0ed038f53d118f4aade0696c37dc6174d613a38097bb38"
)
PUBLICATION_SOURCE_SHA256 = (
    "7675b6e615cddba328bad506692b3a6a31e00d9273cef5ad4641a1737fddfd87"
)
