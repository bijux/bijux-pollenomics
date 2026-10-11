"""Reconstruction regional for the LRA engine."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import warnings

import numpy as np
import pandas as pd

from bijux_pollenomics_lra.dispersal.kernels import (
    BASIN_TYPES,
    METHODS,
    DispersalFactorK,
)
from bijux_pollenomics_lra.dispersal.rounding import r_round
from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.models.validation import (
    DEFAULT_FALL_SPEED_PROFILE,
    frame,
    integer,
    matrix,
    normalise_parameters,
    rng_from,
    vector,
)
from bijux_pollenomics_lra.reconstruction.draws import rmultinom_reveals, rnorm_reveals

PPEFunction = Callable[[int, np.ndarray, np.ndarray], np.ndarray]

PollenFunction = Callable[..., np.ndarray]


def reveals_cover(
    pollen: object,
    ppe: object,
    deposition: object,
    *,
    round_digits: int | None = 3,
) -> np.ndarray:
    """Evaluate REVEALS equation B1 for one pollen/PPE realization."""
    pollen_values = vector(pollen, "pollen", nonnegative=True)
    ppe_values = vector(ppe, "ppe", nonnegative=True)
    deposition_values = vector(
        np.asarray(deposition, dtype=float).reshape(-1),
        "deposition",
    )
    if not (pollen_values.shape == ppe_values.shape == deposition_values.shape):
        raise ValidationError(
            "pollen, PPE, and deposition must have the same number of taxa"
        )
    if pollen_values.sum() <= 0:
        raise ValidationError("Pollen total must be positive")
    if np.any(ppe_values <= 0) or np.any(deposition_values <= 0):
        raise ValidationError("PPE and deposition factors must be strictly positive")

    combined = deposition_values * ppe_values
    scale = np.sum(pollen_values / combined)
    cover = 100 * pollen_values / (combined * scale)
    return (
        np.asarray(r_round(cover, round_digits)) if round_digits is not None else cover
    )


def _reveals_cover_batch(
    pollen: object,
    ppe: object,
    deposition: np.ndarray,
) -> np.ndarray:
    """Evaluate equation B1 for an already dimensioned draw batch."""
    pollen_values = matrix(pollen, "pollen draws", nonnegative=True)
    ppe_values = matrix(ppe, "PPE draws")
    if pollen_values.shape != ppe_values.shape:
        raise ValidationError(f"ppe_draws must have shape {pollen_values.shape}")
    if pollen_values.shape[1] != len(deposition):
        raise ValidationError("Deposition and pollen taxon dimensions disagree")
    if np.any(pollen_values.sum(axis=1) <= 0):
        raise ValidationError("Pollen total must be positive")
    if np.any(ppe_values <= 0) or np.any(deposition <= 0):
        raise ValidationError("PPE and deposition factors must be strictly positive")

    combined = ppe_values * deposition[None, :]
    scale = np.sum(pollen_values / combined, axis=1)
    cover = 100 * pollen_values / (combined * scale[:, None])
    return np.asarray(r_round(cover, 3), dtype=float)


def _normalise_ppe_table(ppes: object, taxon_count: int) -> pd.DataFrame:
    if isinstance(ppes, pd.DataFrame):
        table = ppes.copy(deep=True)
        table.columns = [str(column).strip().lower() for column in table.columns]
        if not {"ppe", "ppe.error"} <= set(table.columns):
            raise ValidationError("ppes must contain ppe and ppe.error columns")
        table = table[["ppe", "ppe.error"]]
    else:
        values = matrix(ppes, "ppes")
        if values.shape[1] < 2:
            raise ValidationError("ppes must contain mean and error columns")
        table = pd.DataFrame(values[:, :2], columns=["ppe", "ppe.error"])
    if len(table) != taxon_count:
        raise ValidationError("PPE and pollen taxon dimensions disagree")
    vector(table["ppe"], "ppe", positive=True)
    vector(table["ppe.error"], "ppe.error", nonnegative=True)
    return table


def REVEALS(
    pollen: object,
    n: int = 1000,
    ppes: object | None = None,
    ppefun: PPEFunction | None = None,
    deposition: object | None = None,
    pollenfun: PollenFunction | None = None,
    writeresults: bool = False,
    verbose: bool = False,
    *,
    rng: None | int | np.random.Generator = None,
    stochastic: bool = True,
    ppe_draws: object | None = None,
    pollen_draws: object | None = None,
    return_samples: bool = False,
    output_dir: str | Path = ".",
) -> dict[str, np.ndarray]:
    """Run Python REVEALS for one coordinate-prefixed pollen sample.

    Explicit ``ppe_draws`` and ``pollen_draws`` use shape ``(n, taxa)`` and
    override callbacks and RNG sampling.  They are the paired-parity interface.
    """
    n = integer(n, "n")
    generator = rng_from(rng)
    row = np.asarray(pollen, dtype=float).reshape(-1)
    if len(row) < 2 or not np.isfinite(row).all():
        raise ValidationError(
            "pollen must be a finite coordinate followed by taxon counts"
        )
    counts = vector(row[1:], "pollen counts", nonnegative=True)
    if counts.sum() <= 0:
        raise ValidationError("Pollen total must be positive")
    ppe_table = _normalise_ppe_table(ppes, len(counts))
    deposition_values = vector(
        np.asarray(deposition, dtype=float).reshape(-1),
        "deposition",
        positive=True,
    )
    if deposition_values.shape != counts.shape:
        raise ValidationError("Deposition and pollen taxon dimensions disagree")

    expected_shape = (n, len(counts))
    if ppe_draws is not None and np.asarray(ppe_draws).shape != expected_shape:
        raise ValidationError(f"ppe_draws must have shape {expected_shape}")
    if pollen_draws is not None and np.asarray(pollen_draws).shape != expected_shape:
        raise ValidationError(f"pollen_draws must have shape {expected_shape}")

    means = ppe_table["ppe"].to_numpy(dtype=float)
    errors = ppe_table["ppe.error"].to_numpy(dtype=float)
    sampled_ppe = (
        np.asarray(ppe_draws, dtype=float)
        if ppe_draws is not None
        else np.empty(expected_shape, dtype=float)
    )
    sampled_pollen = (
        np.asarray(pollen_draws, dtype=float)
        if pollen_draws is not None
        else np.empty(expected_shape, dtype=float)
    )

    for iteration in range(n):
        if ppe_draws is None and ppefun is not None:
            alpha = vector(
                np.asarray(
                    ppefun(len(means), means.copy(), errors.copy()), dtype=float
                ).reshape(-1),
                "ppe",
                nonnegative=True,
            )
            if alpha.shape != counts.shape:
                raise ValidationError(
                    "pollen, PPE, and deposition must have the same number of taxa"
                )
            sampled_ppe[iteration] = alpha
        elif ppe_draws is None and stochastic:
            sampled_ppe[iteration] = rnorm_reveals(
                len(means), means, errors, rng=generator
            )
        elif ppe_draws is None:
            sampled_ppe[iteration] = means

        if pollen_draws is None and pollenfun is not None:
            pollen_values = vector(
                np.asarray(pollenfun(n=1, pollen=counts.copy()), dtype=float).reshape(
                    -1
                ),
                "pollen",
                nonnegative=True,
            )
            if pollen_values.shape != counts.shape:
                raise ValidationError(
                    "pollen, PPE, and deposition must have the same number of taxa"
                )
            sampled_pollen[iteration] = pollen_values
        elif pollen_draws is None and stochastic:
            sampled_pollen[iteration] = rmultinom_reveals(
                n=1, pollen=counts, rng=generator
            ).reshape(-1)
        elif pollen_draws is None:
            sampled_pollen[iteration] = counts

    samples = _reveals_cover_batch(
        sampled_pollen,
        sampled_ppe,
        deposition_values,
    )

    result: dict[str, np.ndarray] = {
        "meansim": samples.mean(axis=0),
        "sdsim": (
            samples.std(axis=0, ddof=1) if n > 1 else np.full(len(counts), np.nan)
        ),
        "mediansim": np.median(samples, axis=0),
        "q90sim": np.quantile(samples, 0.9, axis=0, method="linear"),
        "q10sim": np.quantile(samples, 0.1, axis=0, method="linear"),
    }
    if return_samples:
        result["samples"] = samples

    if writeresults:
        raise ValidationError(
            "Numerical functions do not write artifacts; use result.write()"
        )
    if verbose:
        # Kept intentionally minimal; library code does not print each iteration.
        pass
    return result


def checkREVEALS(
    pollen: pd.DataFrame,
    params: pd.DataFrame,
    tBasin: str,
    dBasin: int,
    dwm: str,
    n: int,
    regionCutoff: float,
    writeresults: bool = False,
    verbose: bool = False,
    *,
    fall_speed_profile: str = DEFAULT_FALL_SPEED_PROFILE,
) -> bool:
    """Validate the source wrapper's scientific and dimensional contract."""
    del writeresults
    pollen_table = frame(pollen, "pollen")
    if pollen_table.shape[1] < 2:
        raise ValidationError("pollen requires a coordinate and at least one taxon")
    if pollen_table.shape[1] == 2:
        raise ValidationError(
            "The DISQOVER 0.9.14 REVEALS source wrapper drops the single-taxon "
            "result dimension; this profile requires at least two taxa",
            reason_code="unsupported_source_taxon_dimensions",
        )
    try:
        numeric = pollen_table.apply(pd.to_numeric, errors="raise").to_numpy(float)
    except (TypeError, ValueError) as exc:
        raise ValidationError("pollen must contain only numeric values") from exc
    if not np.isfinite(numeric).all():
        raise ValidationError("pollen must contain only finite values")
    if np.any(numeric[:, 1:] < 0) or np.any(numeric[:, 1:].sum(axis=1) <= 0):
        raise ValidationError(
            "Pollen counts must be nonnegative with positive sample totals"
        )

    normalise_parameters(
        params,
        list(pollen_table.columns[1:]),
        fall_speed_profile=fall_speed_profile,
        distance_weighting=str(dwm).lower(),
    )
    basin_type = str(tBasin).lower()
    method = str(dwm).lower()
    if basin_type not in BASIN_TYPES:
        raise ValidationError(f"tBasin must be one of {BASIN_TYPES}")
    if method not in METHODS:
        raise ValidationError(f"dwm must be one of {METHODS}")
    basin_diameter = integer(dBasin, "dBasin", minimum=10)
    iterations = integer(n, "n")
    cutoff = float(regionCutoff)
    if not np.isfinite(cutoff) or cutoff <= 0:
        raise ValidationError("regionCutoff must be positive and finite")
    if basin_diameter / 2 > cutoff:
        raise ValidationError("Basin radius cannot exceed regionCutoff")
    if verbose and iterations < 1000:
        warnings.warn(
            "n < 1000: uncertainty summaries may be unstable",
            UserWarning,
            stacklevel=2,
        )
    return True


def _reconstruct_frame(
    pollen: pd.DataFrame,
    params: pd.DataFrame,
    tBasin: str,
    dBasin: int,
    dwm: str,
    n: int,
    regionCutoff: float,
    ppefun: PPEFunction | None,
    pollenfun: PollenFunction | None,
    writeresults: bool,
    verbose: bool,
    *,
    rng: None | int | np.random.Generator,
    stochastic: bool,
    ppe_draws: object | None,
    pollen_draws: object | None,
    output_dir: str | Path,
    collect_samples: bool,
    fall_speed_profile: str = DEFAULT_FALL_SPEED_PROFILE,
) -> tuple[pd.DataFrame, pd.Series, np.ndarray | None]:
    pollen_table = frame(pollen, "pollen")
    taxa = list(map(str, pollen_table.columns[1:]))
    parameter_table = normalise_parameters(
        params,
        taxa,
        fall_speed_profile=fall_speed_profile,
        distance_weighting=str(dwm).lower(),
    )
    basin_type = str(tBasin).lower()
    method = str(dwm).lower()
    checkREVEALS(
        pollen_table,
        parameter_table,
        basin_type,
        dBasin,
        method,
        n,
        regionCutoff,
        writeresults,
        verbose,
        fall_speed_profile=fall_speed_profile,
    )

    n = int(n)
    generator = rng_from(rng)
    deposition = np.asarray(
        [
            DispersalFactorK(
                fall_speed,
                basin_type,
                dBasin,
                method,
                regionCutoff,
            )
            for fall_speed in parameter_table["fallspeed"]
        ],
        dtype=float,
    )
    if not np.isfinite(deposition).all() or np.any(deposition <= 0):
        raise ValidationError(
            "Deposition factors are undefined or nonpositive; check model domain, "
            "basin geometry, and regionCutoff"
        )

    full_shape = (len(pollen_table), n, len(taxa))
    if ppe_draws is not None and np.asarray(ppe_draws).shape != full_shape:
        raise ValidationError(f"ppe_draws must have shape {full_shape}")
    if pollen_draws is not None and np.asarray(pollen_draws).shape != full_shape:
        raise ValidationError(f"pollen_draws must have shape {full_shape}")

    rows: list[list[object]] = []
    all_samples = np.empty(full_shape, dtype=float) if collect_samples else None
    statistics = (
        ("mean", "meansim"),
        ("median", "mediansim"),
        ("q90", "q90sim"),
        ("q10", "q10sim"),
        ("sd", "sdsim"),
    )

    for sample_index, row in enumerate(pollen_table.to_numpy(dtype=float)):
        result = REVEALS(
            row,
            n,
            parameter_table[["ppe", "ppe.error"]],
            ppefun,
            deposition,
            pollenfun,
            writeresults,
            verbose,
            rng=generator,
            stochastic=stochastic,
            ppe_draws=(
                None if ppe_draws is None else np.asarray(ppe_draws)[sample_index]
            ),
            pollen_draws=(
                None if pollen_draws is None else np.asarray(pollen_draws)[sample_index]
            ),
            return_samples=collect_samples,
            output_dir=output_dir,
        )
        rows.append(
            [method, basin_type, row[0]]
            + [
                float(value)
                for _, result_key in statistics
                for value in result[result_key]
            ]
        )
        if collect_samples and all_samples is not None:
            all_samples[sample_index] = result["samples"]

    columns = [
        "Distance.weighting",
        "Basin.type",
        str(pollen_table.columns[0]),
    ] + [f"{taxon}.{statistic}" for statistic, _ in statistics for taxon in taxa]
    output = pd.DataFrame(rows, columns=columns, index=pollen_table.index)
    deposition_series = pd.Series(deposition, index=taxa, name="K", dtype=float)
    output.attrs.update(
        {
            "reference_package": "disqover",
            "reference_version": "0.9.14",
            "native": True,
            "stochastic": bool(stochastic),
            "deposition": deposition_series.to_dict(),
        }
    )

    if writeresults:
        raise ValidationError(
            "Numerical functions do not write artifacts; use result.write()"
        )

    return output, deposition_series, all_samples


def REVEALSinR(
    pollen: pd.DataFrame,
    params: pd.DataFrame,
    tBasin: str,
    dBasin: int,
    dwm: str = "lsm unstable",
    n: int = 1000,
    regionCutoff: float = 100_000,
    ppefun: PPEFunction | None = None,
    pollenfun: PollenFunction | None = None,
    writeresults: bool = False,
    verbose: bool = True,
    *,
    rng: None | int | np.random.Generator = None,
    stochastic: bool = True,
    ppe_draws: object | None = None,
    pollen_draws: object | None = None,
    output_dir: str | Path = ".",
) -> pd.DataFrame:
    """Return the source-compatible REVEALS result table."""
    output, _, _ = _reconstruct_frame(
        pollen,
        params,
        tBasin,
        dBasin,
        dwm,
        n,
        regionCutoff,
        ppefun,
        pollenfun,
        writeresults,
        verbose,
        rng=rng,
        stochastic=stochastic,
        ppe_draws=ppe_draws,
        pollen_draws=pollen_draws,
        output_dir=output_dir,
        collect_samples=False,
    )
    return output
