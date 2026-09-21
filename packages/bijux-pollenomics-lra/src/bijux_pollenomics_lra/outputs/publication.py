"""Persistence of historical publication-profile numerical bundles."""

from __future__ import annotations

import json
from pathlib import Path

from bijux_pollenomics_lra.models.results import MultisiteRevealsResult
from bijux_pollenomics_lra.outputs.checksums import _write_checksum_manifest


def write_multisite_result(
    result: MultisiteRevealsResult, directory: str | Path
) -> Path:
    """Persist site/bin support and uncertainties with opaque positional paths."""
    destination = Path(directory)
    destination.mkdir(parents=True, exist_ok=True)
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
    (destination / "diagnostics.json").write_text(
        json.dumps(result.diagnostics, indent=2) + "\n", encoding="utf-8"
    )
    result.manifest.write(destination / "run-manifest.json")
    _write_checksum_manifest(destination)
    return destination
