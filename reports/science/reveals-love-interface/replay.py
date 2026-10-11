"""Replay the source-bound REVEALS to analytical LOVE draw interface."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from bijux_pollenomics_lra.api import (
    LoveConfig,
    MultisiteRevealsInput,
    PublicationRevealsConfig,
    ValidationError,
    run_love,
    run_reveals_multisite,
)
from bijux_pollenomics_lra.provenance.identity import sha256_object


GRID = "512"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    repository = args.repository.resolve()
    source_root = args.source_root.resolve()
    output = args.output.resolve()
    custody = json.loads(
        (
            repository / "docs/report/pollen-reconstruction/author-source-custody.json"
        ).read_text()
    )
    source_manifest = source_root / custody["original_manifest_filename"]
    if sha(source_manifest) != custody["original_manifest_sha256"]:
        raise ValueError("Author source manifest identity differs")
    recorded = json.loads(source_manifest.read_text())["files"]
    author = source_root / "author"
    reference = source_root / "reference"
    working = author / "run.REVEALS.files"
    paths = (working / f"site.list.{GRID}.csv").read_text().splitlines()
    used = [
        f"author/run.REVEALS.files/site.list.{GRID}.csv",
        *(f"author/run.REVEALS.files/{name}" for name in paths),
        "author/run.REVEALS.files/av-RPP.all.landclimII.csv",
        "author/run.REVEALS.files/avar-RPP.all.landclimII.csv",
        "author/run.REVEALS.files/LRA-REVEALS-release.R",
        "author/bins.csv",
        "reference/taxon-name-crosswalk.csv",
        f"reference/{GRID}/bootstrap-bin-1.csv",
    ]
    for relative in used:
        if recorded.get(relative) != sha(source_root / relative):
            raise ValueError(f"Author input identity differs: {relative}")
    tables = [pd.read_csv(working / name, index_col=0) for name in paths]
    source_params = pd.read_csv(working / "av-RPP.all.landclimII.csv", index_col=0)
    source_cov = pd.read_csv(working / "avar-RPP.all.landclimII.csv", index_col=0)
    crosswalk = pd.read_csv(reference / "taxon-name-crosswalk.csv")
    assert crosswalk["source"].tolist() == source_params.index.tolist()
    assert all(
        table.index[2:].tolist() == crosswalk["prepared"].tolist() for table in tables
    )
    assert (
        source_cov.index.tolist()
        == source_cov.columns.tolist()
        == source_params.index.tolist()
    )
    filipendula_speed = float(
        np.asarray(source_params.loc["Filipendula", "vg"], dtype=float)
    )
    if filipendula_speed != 0.006:
        raise AssertionError("author Filipendula fall speed is not 0.006 m/s")
    bin_id = str(tables[0].columns[0])
    counts = np.stack([table.iloc[2:, :1].to_numpy(dtype=float).T for table in tables])
    radii = np.stack([table.iloc[0, :1].to_numpy(dtype=float) for table in tables])
    basin_codes = np.stack(
        [table.iloc[1, :1].to_numpy(dtype=float) for table in tables]
    )
    available = counts.sum(axis=-1) > 0
    assert int(available.sum()) == 5
    counts[~available] = np.nan
    radii[~available] = np.nan
    basin_types = np.full(available.shape, None, dtype=object)
    basin_types[available & (basin_codes == 1)] = "peatland"
    basin_types[available & (basin_codes == 2)] = "lake"
    edges = np.loadtxt(author / "bins.csv")
    inputs = MultisiteRevealsInput(
        site_ids=tuple(Path(path).stem.removeprefix("LRAready_") for path in paths),
        bin_ids=(bin_id,),
        taxon_ids=tuple(source_params.index),
        counts=counts,
        availability=available,
        basin_radius_m=radii,
        basin_type=basin_types,
        bin_bounds_bp=np.array([[edges[0], edges[1]]]),
        ppe=source_params["alpha"].to_numpy(dtype=float),
        ppe_covariance=source_cov.to_numpy(dtype=float),
        fall_speed_m_s=source_params["vg"].to_numpy(dtype=float),
    )
    indices = np.loadtxt(
        reference / GRID / "bootstrap-bin-1.csv", delimiter=",", dtype=int, ndmin=2
    )
    regional = run_reveals_multisite(
        inputs,
        PublicationRevealsConfig("landclimii-author-archive-bins-v1"),
        bootstrap_indices={bin_id: indices},
    )
    if regional.manifest.parameters["source_axes"] != {
        "site_ids": list(inputs.site_ids),
        "bin_ids": list(inputs.bin_ids),
        "taxon_ids": list(inputs.taxon_ids),
    }:
        raise AssertionError("regional source axes do not match author inputs")
    draws = regional.regional_cover_draws[bin_id]
    active = np.flatnonzero(available[:, 0])
    local_site, placeholder_site = map(int, active[:2])
    columns = ["coordinate", *inputs.taxon_ids]
    local = pd.DataFrame([[50.0, *counts[local_site, 0]]], columns=columns)
    placeholder = pd.DataFrame([[50.0, *counts[placeholder_site, 0]]], columns=columns)
    params = pd.DataFrame(
        {
            "fallspeed": inputs.fall_speed_m_s,
            "ppe": inputs.ppe,
            "ppe.error": np.zeros(len(inputs.taxon_ids)),
        },
        index=list(inputs.taxon_ids),
    )
    rings = pd.DataFrame(
        [
            {
                "inner": 200.0,
                "outer": 300.0,
                "mean": 250.0,
                "ring": math.pi * (300.0**2 - 200.0**2),
                "terrestrial": math.pi * (300.0**2 - 200.0**2),
            }
        ]
    )
    config = LoveConfig(
        "analytical",
        "lake",
        300,
        12.9,
        1,
        distance_weighting="gpm neutral",
        fall_speed_profile="landclimii-2016-gpm-neutral-analytical-v1",
        repeats=1000,
        stochastic=False,
        seed=1950,
        retain_samples=True,
        ppe_error=False,
    )
    try:
        run_love(
            local,
            placeholder,
            params,
            rings,
            config,
            regional_cover_draws=draws[:-1],
        )
    except ValidationError as exc:
        shape_refusal = "shape" in str(exc)
    else:
        shape_refusal = False
    if not shape_refusal:
        raise AssertionError("truncated regional draw tensor was not refused")
    love = run_love(
        local,
        placeholder,
        params,
        rings,
        config,
        regional_cover_draws=draws,
    )
    samples = love.samples["cover"]
    if samples.shape != (1000, 1, len(inputs.taxon_ids)):
        raise AssertionError(f"unexpected LOVE sample shape: {samples.shape}")
    if love.manifest.inputs["regional_cover_draws"] != sha256_object(draws):
        raise AssertionError("LOVE did not hash the supplied regional draw tensor")
    if love.manifest.parameters["paired_regional_cover_draws"] is not True:
        raise AssertionError("paired regional draw flag missing")
    if not np.isfinite(samples).all():
        raise AssertionError("Nonfinite local draw cell")
    taxon_summary = pd.DataFrame(
        {
            "taxon": inputs.taxon_ids,
            "mean_cover": samples[:, 0, :].mean(axis=0),
            "sd_cover": samples[:, 0, :].std(axis=0, ddof=1),
            "negative_draws": (samples[:, 0, :] < 0).sum(axis=0),
        }
    )
    output.mkdir(parents=True, exist_ok=False)
    taxon_summary.to_csv(
        output / "taxon-summary.csv", index=False, float_format="%.17g"
    )
    report = {
        "schema_version": "reveals-love-interface.1",
        "love_fall_speed_profile": config.fall_speed_profile,
        "love_distance_weighting": config.distance_weighting,
        "source_fall_speed_min_m_s": float(inputs.fall_speed_m_s.min()),
        "author_filipendula_fall_speed_m_s": filipendula_speed,
        "claim_boundary": "synthetic local/one-ring method control, source author regional draws, local site overlaps regional cohort; no held-out or ecological claim",
        "grid": GRID,
        "bin_id": bin_id,
        "regional_site_count": int(available.sum()),
        "taxa": len(inputs.taxon_ids),
        "draws": len(draws),
        "regional_draws_sha256": hashlib.sha256(draws.tobytes()).hexdigest(),
        "love_manifest_regional_draw_hash": love.manifest.inputs[
            "regional_cover_draws"
        ],
        "shape_refusal": shape_refusal,
        "love_sample_shape": list(samples.shape),
        "finite_local_draw_cells": int(np.isfinite(samples).sum()),
        "negative_local_draw_cells": int((samples < 0).sum()),
        "minimum_local_cover": float(samples.min()),
        "local_site_id": inputs.site_ids[local_site],
        "placeholder_regional_pollen_site_id": inputs.site_ids[placeholder_site],
        "placeholder_counts_role": "taxon-aligned required API argument, not used to reconstruct supplied regional cover draws",
        "source_manifest_sha256": sha(source_manifest),
        "source_inputs_sha256": {relative: recorded[relative] for relative in used},
        "taxon_summary_sha256": sha(output / "taxon-summary.csv"),
    }
    if report["finite_local_draw_cells"] == 0:
        raise AssertionError("no finite local draw cells")
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                "draws": len(draws),
                "taxa": len(inputs.taxon_ids),
                "finite_local_draw_cells": report["finite_local_draw_cells"],
                "shape_refusal": shape_refusal,
            }
        )
    )


if __name__ == "__main__":
    main()
