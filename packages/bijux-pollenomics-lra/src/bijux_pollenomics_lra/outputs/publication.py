"""Persistence of historical publication-profile numerical bundles."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd

from bijux_pollenomics_lra.models.results import MultisiteRevealsResult
from bijux_pollenomics_lra.outputs.checksums import _write_checksum_manifest


def _validated_result_axes(result: MultisiteRevealsResult) -> None:
    """Refuse relabelled result tables before any numerical file is written."""
    bins, taxa = result.bin_ids, result.taxon_ids
    source_axes = {
        "site_ids": list(result.site_ids),
        "bin_ids": list(bins),
        "taxon_ids": list(taxa),
    }
    if result.manifest.parameters.get("source_axes") != source_axes:
        raise ValueError(
            "Result axes must match source axes in the scientific manifest"
        )
    if tuple(result.cover.index) != bins or tuple(result.cover.columns) != taxa:
        raise ValueError("Regional cover axes must match the input bin and taxon IDs")
    if (
        tuple(result.standard_error.index) != bins
        or tuple(result.standard_error.columns) != taxa
    ):
        raise ValueError("Regional standard-error axes must match the input IDs")
    if tuple(result.site_count.index) != bins:
        raise ValueError("Site-count bins must match the input bin IDs")
    sites = result.site_ids
    if (
        tuple(result.availability.index) != bins
        or tuple(result.availability.columns) != sites
    ):
        raise ValueError("Availability axes must match the input bin and site IDs")
    for name in ("site_cover", "site_standard_error", "deposition"):
        tables = getattr(result, name)
        if tuple(tables) != sites:
            raise ValueError(f"{name} sites must match availability sites in order")
        if any(
            tuple(table.index) != bins or tuple(table.columns) != taxa
            for table in tables.values()
        ):
            raise ValueError(f"{name} axes must match the input bin and taxon IDs")


def _validated_draw_bins(
    result: MultisiteRevealsResult,
) -> list[tuple[int, str, np.ndarray]]:
    """Refuse malformed draw support before writing any bundle files."""
    if set(result.regional_cover_draws) != set(result.bootstrap_indices):
        raise ValueError("Regional cover draws must match multi-site bootstrap bins")
    bins = []
    for bin_position, bin_id in enumerate(result.cover.index):
        if bin_id not in result.regional_cover_draws:
            continue
        values = result.regional_cover_draws[bin_id]
        if (
            values.shape != (1000, len(result.cover.columns))
            or not np.isfinite(values).all()
            or (values < 0).any()
            or not np.allclose(values.sum(axis=1), 1, rtol=0, atol=1e-12)
        ):
            raise ValueError("Regional cover draws must be 1000 closed finite rows")
        bins.append((bin_position, str(bin_id), values))
    if len(bins) != len(result.regional_cover_draws):
        raise ValueError("Regional cover draws contain an unknown bin")
    return bins


def _write_multisite_files(
    result: MultisiteRevealsResult,
    destination: Path,
    draw_bins: list[tuple[int, str, np.ndarray]],
) -> None:
    """Build a complete bundle only inside a fresh staging directory."""
    result.cover.to_csv(destination / "regional-cover.csv", index_label="bin_id")
    result.standard_error.to_csv(
        destination / "regional-standard-error.csv", index_label="bin_id"
    )
    result.site_count.to_csv(destination / "site-count.csv", index_label="bin_id")
    result.availability.to_csv(destination / "availability.csv", index_label="bin_id")
    site_index = []
    for position, (site_id, cover) in enumerate(result.site_cover.items()):
        relative = f"site-{position}"
        path = destination / relative
        path.mkdir(exist_ok=True)
        cover.to_csv(path / "cover.csv", index_label="bin_id")
        result.site_standard_error[site_id].to_csv(
            path / "standard-error.csv", index_label="bin_id"
        )
        result.deposition[site_id].to_csv(path / "deposition.csv", index_label="bin_id")
        site_index.append({"site_id": site_id, "path": relative})
    (destination / "site-index.json").write_text(
        json.dumps(site_index, indent=2) + "\n", encoding="utf-8"
    )
    (destination / "bootstrap-indices.json").write_text(
        json.dumps(
            {
                name: values.tolist()
                for name, values in result.bootstrap_indices.items()
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    draw_root = destination / "regional-cover-draws"
    draw_root.mkdir(exist_ok=True)
    draw_index = []
    for bin_position, bin_id, values in draw_bins:
        relative = f"bin-{bin_position}.csv"
        pd.DataFrame(values, columns=result.cover.columns).to_csv(
            draw_root / relative, index_label="draw_index"
        )
        draw_index.append(
            {
                "bin_id": bin_id,
                "path": relative,
                "draw_index_base": 0,
                "draw_count": 1000,
                "taxon_ids": list(result.cover.columns),
            }
        )
    (draw_root / "index.json").write_text(
        json.dumps(draw_index, indent=2) + "\n", encoding="utf-8"
    )
    (destination / "diagnostics.json").write_text(
        json.dumps(result.diagnostics, indent=2) + "\n", encoding="utf-8"
    )
    result.manifest.write(destination / "run-manifest.json")
    _write_checksum_manifest(destination)


def write_multisite_result(
    result: MultisiteRevealsResult, directory: str | Path
) -> Path:
    """Publish a complete immutable bundle without stale files from prior runs."""
    _validated_result_axes(result)
    draw_bins = _validated_draw_bins(result)
    destination = Path(directory)
    if destination.is_symlink() or (
        destination.exists()
        and (not destination.is_dir() or any(destination.iterdir()))
    ):
        raise FileExistsError(f"Refusing to replace an existing bundle: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(
        prefix=f".{destination.name}.staging-", dir=destination.parent
    ) as staging:
        staged = Path(staging) / "bundle"
        staged.mkdir()
        _write_multisite_files(result, staged, draw_bins)
        if destination.exists():
            # A concurrent new file makes this fail without touching its contents.
            destination.rmdir()
        staged.replace(destination)
    return destination
