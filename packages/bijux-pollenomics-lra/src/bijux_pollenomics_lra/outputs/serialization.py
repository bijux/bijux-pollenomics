"""Outputs serialization for the LRA engine."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any, Protocol, cast

import numpy as np
import pandas as pd

from bijux_pollenomics_lra.models.results import (
    LoveResult,
    LRAResult,
    LRASeriesResult,
    RevealsResult,
)
from bijux_pollenomics_lra.outputs.checksums import _write_checksum_manifest


class _ArrayArchiveWriter(Protocol):
    """NumPy archive call shared by the supported 1.x and 2.x versions."""

    def __call__(self, file: Path, **arrays: np.ndarray) -> None: ...


def _safe_name(value: object) -> str:
    name = re.sub(r"[^0-9A-Za-z_.-]+", "_", str(value)).strip("_")
    return name or "sample"


def _write_frame(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path, index=True, index_label=str(frame.index.name or "index"))


def _write_series(series: pd.Series, path: Path) -> None:
    series.to_frame(name=series.name or "value").to_csv(
        path, index=True, index_label=str(series.index.name or "index")
    )


def write_reveals_result(result: RevealsResult, directory: str | Path) -> Path:
    """Write REVEALS table, K factors, samples, provenance, and checksums."""
    destination = Path(directory)
    destination.mkdir(parents=True, exist_ok=True)
    result.table.to_csv(destination / "reconstruction.csv", index=False)
    _write_series(result.deposition, destination / "deposition_factors.csv")
    if result.samples is not None:
        np.savez_compressed(
            destination / "monte_carlo_samples.npz", cover=result.samples
        )
    result.manifest.write(destination / "run_manifest.json")
    (destination / "result_contract.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "result_type": "reveals",
                "primary_artifact": "reconstruction.csv",
                "units": {"cover": "percent", "distance": "metre"},
                "taxon_statistic_column_pattern": "<taxon>.<mean|median|q90|q10|sd>",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _write_checksum_manifest(destination)
    return destination


def write_love_result(result: LoveResult, directory: str | Path) -> Path:
    """Write all local reconstruction summaries and diagnostics."""
    destination = Path(directory)
    destination.mkdir(parents=True, exist_ok=True)
    for statistic, frame in result.cover.items():
        _write_frame(frame, destination / f"cover_{_safe_name(statistic)}.csv")
    for statistic, frame in result.pollen_percentages.items():
        _write_frame(
            frame,
            destination / f"pollen_percentages_{_safe_name(statistic)}.csv",
        )
    if result.outlier is not None:
        _write_series(
            result.outlier.rename("mean_outlier_taxa"), destination / "outliers.csv"
        )
    if result.outlier_quantile is not None:
        _write_series(
            result.outlier_quantile.rename("outlier_taxa_by_quantiles"),
            destination / "outliers_quantiles.csv",
        )
    if result.objective_values is not None:
        _write_frame(result.objective_values, destination / "objective_values.csv")
    if result.diagnostics:
        (destination / "optimizer_diagnostics.json").write_text(
            json.dumps(
                [diagnostic.as_dict() for diagnostic in result.diagnostics], indent=2
            )
            + "\n",
            encoding="utf-8",
        )
    for name, value in result.auxiliary.items():
        if isinstance(value, pd.DataFrame):
            _write_frame(value, destination / f"aux_{_safe_name(name)}.csv")
        elif isinstance(value, pd.Series):
            _write_series(value, destination / f"aux_{_safe_name(name)}.csv")
        else:
            (destination / f"aux_{_safe_name(name)}.json").write_text(
                json.dumps(value, indent=2, default=str) + "\n",
                encoding="utf-8",
            )
    if result.samples:
        # NumPy 2.2 added a reserved allow_pickle keyword. Engine sample names
        # are array entries and this call also supports NumPy 1.26, where that
        # keyword would silently create an unwanted array in the archive.
        archive_writer = cast(_ArrayArchiveWriter, np.savez_compressed)
        archive_writer(destination / "monte_carlo_samples.npz", **result.samples)
    result.manifest.write(destination / "run_manifest.json")
    (destination / "result_contract.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "result_type": "love",
                "method": result.method,
                "primary_artifact": "cover_mean.csv",
                "units": {
                    "cover": "fraction",
                    "pollen_percentages": "percent",
                    "distance": "metre",
                },
                "cover_is_not_clipped": result.method == "analytical",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _write_checksum_manifest(destination)
    return destination


def write_lra_result(result: LRAResult, directory: str | Path) -> Path:
    """Write one complete two-stage LRA result tree."""
    destination = Path(directory)
    destination.mkdir(parents=True, exist_ok=True)
    write_reveals_result(result.regional, destination / "regional_reveals")
    write_love_result(result.local, destination / "local_love")
    result.manifest.write(destination / "run_manifest.json")
    (destination / "product_manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "product_type": "bijux-pollenomics-lra",
                "stages": [
                    {
                        "name": "regional_reveals",
                        "path": "regional_reveals",
                        "primary": "regional_reveals/reconstruction.csv",
                    },
                    {
                        "name": "local_love",
                        "path": "local_love",
                        "primary": "local_love/cover_mean.csv",
                    },
                ],
                "producer": {
                    "distribution": "bijux-pollenomics-lra",
                    "version": result.manifest.package_version,
                },
                "reference": {
                    "package": result.manifest.reference_package,
                    "version": result.manifest.reference_version,
                    "source_sha256": result.manifest.reference_archive_sha256,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _write_checksum_manifest(destination)
    return destination


def write_lra_series_result(result: LRASeriesResult, directory: str | Path) -> Path:
    """Write one directory per coordinate plus a series index."""
    destination = Path(directory)
    destination.mkdir(parents=True, exist_ok=True)
    index: list[dict[str, Any]] = []
    for coordinate, run in result.runs.items():
        relative = Path("samples") / _safe_name(coordinate)
        write_lra_result(run, destination / relative)
        index.append(
            {
                "coordinate": coordinate,
                "path": str(relative),
                "manifest": str(relative / "run_manifest.json"),
            }
        )
    (destination / "series_index.json").write_text(
        json.dumps(index, indent=2) + "\n", encoding="utf-8"
    )
    result.manifest.write(destination / "run_manifest.json")
    _write_checksum_manifest(destination)
    return destination
