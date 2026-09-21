"""Governed orchestration of the historical multi-site REVEALS profile."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, replace

import numpy as np
import pandas as pd

from bijux_pollenomics_lra.dispersal.publication import publication_deposition
from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.models.publication import (
    PUBLICATION_ARCHIVE_SHA256,
    PUBLICATION_LIMITATIONS,
    PUBLICATION_REVISION,
    PUBLICATION_SOURCE_SHA256,
    MultisiteRevealsInput,
    PublicationRevealsConfig,
)
from bijux_pollenomics_lra.models.results import MultisiteRevealsResult
from bijux_pollenomics_lra.provenance.manifest import build_manifest
from bijux_pollenomics_lra.reconstruction.publication import (
    bootstrap_cover_variance_with_draws,
    individual_cover_variance,
)


def _bootstrap_draws(
    inputs: MultisiteRevealsInput, supplied: Mapping[str, object]
) -> dict[str, np.ndarray]:
    """Validate and own explicit 1000-row site resamples for supported bins.

    Each column draws an original site index available in that bin. Only bins
    with multiple available sites may have a supplied bootstrap matrix.
    """
    required = {
        name
        for position, name in enumerate(inputs.bin_ids)
        if inputs.availability[:, position].sum() > 1
    }
    if set(supplied) != required:
        raise ValidationError(
            "Bootstrap indices must cover exactly the bins with multiple available sites"
        )
    draws: dict[str, np.ndarray] = {}
    for position, name in enumerate(inputs.bin_ids):
        if name not in required:
            continue
        eligible = np.flatnonzero(inputs.availability[:, position])
        values = np.asarray(supplied[name])
        if values.dtype.kind not in "iu" or values.shape != (1000, len(eligible)):
            raise ValidationError(
                "Bootstrap indices must be integer [1000,eligible_sites] matrices"
            )
        if not np.isin(values, eligible).all():
            raise ValidationError(
                "Bootstrap draw references an unavailable or unknown site"
            )
        owned = np.array(values, dtype=np.intp, copy=True)
        owned.setflags(write=False)
        draws[name] = owned
    return draws


def run_reveals_multisite(
    inputs: MultisiteRevealsInput,
    config: PublicationRevealsConfig,
    *,
    bootstrap_indices: Mapping[str, object],
) -> MultisiteRevealsResult:
    """Replay a named historical profile with explicitly supplied site draws.

    Indices are zero-based original site positions, not positions in a filtered
    eligible-site list. No random stream is inferred and no sites are pooled
    before individual geometry correction. This profile preserves known source
    uncertainty defects; it is unsuitable for claiming corrected uncertainty.
    """
    if not inputs.availability.any():
        raise ValidationError(
            "No site/bin has pollen support", reason_code="no_supported_bins"
        )
    if np.any(inputs.basin_radius_m[inputs.availability] >= config.regional_extent_m):
        raise ValidationError(
            "Every available basin radius must be below regional extent"
        )
    draws = _bootstrap_draws(inputs, bootstrap_indices)
    sites, bins, taxa = inputs.counts.shape
    site_cover = np.full((sites, bins, taxa), np.nan)
    site_variance = np.full_like(site_cover, np.nan)
    deposition = np.full_like(site_cover, np.nan)
    regional_cover = np.full((bins, taxa), np.nan)
    regional_variance = np.full_like(regional_cover, np.nan)
    regional_cover_draws: dict[str, np.ndarray] = {}
    diagnostics: list[dict[str, object]] = []
    for time_index, bin_id in enumerate(inputs.bin_ids):
        eligible = np.flatnonzero(inputs.availability[:, time_index])
        if not len(eligible):
            diagnostics.append({"bin_id": bin_id, "reason_code": "no_site_support"})
            continue
        for site_index in eligible:
            k = publication_deposition(
                inputs.fall_speed_m_s,
                float(inputs.basin_radius_m[site_index, time_index]),
                str(inputs.basin_type[site_index, time_index]),
                config.wind_speed_m_s,
                config.regional_extent_m,
            )
            deposition[site_index, time_index] = k
            cover, variance = individual_cover_variance(
                inputs.counts[site_index, time_index],
                inputs.ppe,
                inputs.ppe_covariance,
                k,
            )
            site_cover[site_index, time_index] = cover
            site_variance[site_index, time_index] = variance
            negative = np.flatnonzero(variance < 0)
            if len(negative):
                diagnostics.append(
                    {
                        "bin_id": bin_id,
                        "site_id": inputs.site_ids[site_index],
                        "reason_code": "negative_variance_in_historical_source",
                        "taxon_ids": [inputs.taxon_ids[index] for index in negative],
                    }
                )
        if len(eligible) == 1:
            regional_cover[time_index] = site_cover[eligible[0], time_index]
            regional_variance[time_index] = site_variance[eligible[0], time_index]
        else:
            cover, variance, cover_draws = bootstrap_cover_variance_with_draws(
                inputs.counts[:, time_index],
                deposition[:, time_index],
                inputs.ppe,
                draws[bin_id],
            )
            regional_cover[time_index], regional_variance[time_index] = cover, variance
            regional_cover_draws[bin_id] = cover_draws
    with np.errstate(invalid="ignore"):
        site_se = np.sqrt(site_variance)
        regional_se = np.sqrt(regional_variance)
    manifest = replace(
        build_manifest(
            "REVEALS-multisite-publication-source",
            {
                **asdict(config),
                "bootstrap_replicates": 1000,
                "bootstrap_sampling": "explicit_original_site_indices_uniform_resampling_reference",
                "known_source_limitations": list(PUBLICATION_LIMITATIONS),
                "source_revision": PUBLICATION_REVISION,
                "source_file_sha256": PUBLICATION_SOURCE_SHA256,
                "units": {
                    "cover": "fraction",
                    "standard_error": "fraction",
                    "counts": "count",
                    "radius": "metre",
                },
                "missing_support": "masked_nan_instead_of_source_zero",
                "single_site_regional_output": "same_individual_cover_and_se",
                "regional_cover_draws": "closed_Vx_rows_for_multisite_bins_only",
                "regional_cover_draw_index_base": 0,
                "time_bins": "explicit_calendar_years_bp_1950CE_younger_older",
            },
            {"inputs": inputs, "bootstrap_indices": draws},
            stochastic=False,
            seed=None,
        ),
        reference_package="LRA-REVEALS-release.R",
        reference_version="2016-10-30",
        reference_archive_sha256=PUBLICATION_ARCHIVE_SHA256,
        compatibility_mode=config.profile,
    )

    def table(values: np.ndarray) -> pd.DataFrame:
        """Label a bin-by-taxon result matrix with declared identities."""
        return pd.DataFrame(values, index=inputs.bin_ids, columns=inputs.taxon_ids)

    return MultisiteRevealsResult(
        cover=table(regional_cover),
        standard_error=table(regional_se),
        site_cover={
            name: table(site_cover[index]) for index, name in enumerate(inputs.site_ids)
        },
        site_standard_error={
            name: table(site_se[index]) for index, name in enumerate(inputs.site_ids)
        },
        site_count=pd.Series(
            inputs.availability.sum(axis=0), index=inputs.bin_ids, name="site_count"
        ),
        availability=pd.DataFrame(
            inputs.availability.T, index=inputs.bin_ids, columns=inputs.site_ids
        ),
        deposition={
            name: table(deposition[index]) for index, name in enumerate(inputs.site_ids)
        },
        bootstrap_indices=draws,
        regional_cover_draws=regional_cover_draws,
        site_ids=inputs.site_ids,
        bin_ids=inputs.bin_ids,
        taxon_ids=inputs.taxon_ids,
        diagnostics=diagnostics,
        manifest=manifest,
    )
