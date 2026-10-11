"""Compare the native historical REVEALS profile to pinned tagged-R draws."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import pandas as pd

from bijux_pollenomics_lra.api import (
    MultisiteRevealsInput,
    PublicationRevealsConfig,
    run_reveals_multisite,
)

RESULT = Path("docs/report/method-certification/petrkunes-r-comparison")
CODE = (
    Path(
        "docs/report/method-certification/petrkunes-r-comparison/native_comparison.py"
    ),
    Path("docs/report/method-certification/petrkunes-r-comparison/replay.R"),
    Path(
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/workflows/multisite.py"
    ),
    Path(
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/publication.py"
    ),
    Path(
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/dispersal/publication.py"
    ),
)


def _identity(path: Path, root: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {
        "path": path.relative_to(root).as_posix(),
        "bytes": len(data),
        "sha256": sha256(data).hexdigest(),
    }


def _comparison(
    actual: np.ndarray, expected: np.ndarray, *, se: bool
) -> dict[str, object]:
    tolerance = 5e-8 if se else 1e-11
    relative = 1e-9 if se else 1e-10
    finite = np.isfinite(actual) & np.isfinite(expected)
    return {
        "pairs": len(actual),
        "finite_pairs": int(finite.sum()),
        "undefined_masks_equal": bool(
            np.array_equal(np.isnan(actual), np.isnan(expected))
        ),
        "max_absolute_error": float(np.max(np.abs(actual[finite] - expected[finite]))),
        "atol": tolerance,
        "rtol": relative,
        "passed": bool(
            np.allclose(actual, expected, atol=tolerance, rtol=relative, equal_nan=True)
        ),
    }


def compare(repository: Path, private_root: Path) -> dict[str, object]:
    """Evaluate one full author grid window using the tagged R site draws."""
    repository = repository.resolve()
    private_root = private_root.resolve()
    source = private_root / "author/run.REVEALS.files"
    files = [source / "site.list.512.csv"]
    site_paths = (source / "site.list.512.csv").read_text().splitlines()
    if len(site_paths) != 9 or len(set(site_paths)) != 9:
        raise ValueError("Author grid 512 membership changed")
    tables = [pd.read_csv(source / path, index_col=0) for path in site_paths]
    files.extend(source / path for path in site_paths)
    parameter_path = source / "av-RPP.all.landclimII.csv"
    covariance_path = source / "avar-RPP.all.landclimII.csv"
    crosswalk_path = private_root / "reference/taxon-name-crosswalk.csv"
    bins_path = private_root / "author/bins.csv"
    files.extend((parameter_path, covariance_path, crosswalk_path, bins_path))
    parameters = pd.read_csv(parameter_path, index_col=0)
    covariance = pd.read_csv(covariance_path, index_col=0)
    crosswalk = pd.read_csv(crosswalk_path)
    if (
        len(parameters) != 31
        or parameters.index.tolist() != covariance.index.tolist()
        or parameters.index.tolist() != covariance.columns.tolist()
        or parameters.index.tolist() != crosswalk["source"].tolist()
        or any(
            table.index[2:].tolist() != crosswalk["prepared"].tolist()
            for table in tables
        )
        or any("225" not in table.columns for table in tables)
        or any(table.columns.tolist() != tables[0].columns.tolist() for table in tables)
    ):
        raise ValueError("Author taxon or window axes changed")
    position = tables[0].columns.tolist().index("225")
    counts = np.stack(
        [table.iloc[2:].to_numpy(dtype=float)[:, position][None, :] for table in tables]
    )
    radii = np.stack(
        [
            table.iloc[0].to_numpy(dtype=float)[position : position + 1]
            for table in tables
        ]
    )
    models = np.stack(
        [
            table.iloc[1].to_numpy(dtype=float)[position : position + 1]
            for table in tables
        ]
    )
    availability = counts.sum(axis=-1) > 0
    if int(availability.sum()) != 6 or np.any(counts[~availability] != 0):
        raise ValueError("Author active-site support changed")
    counts[~availability] = np.nan
    radii[~availability] = np.nan
    basin_type = np.full(availability.shape, None, dtype=object)
    if np.any(models[availability] != 2):
        raise ValueError("Author active lake models changed")
    basin_type[availability] = "lake"
    edges = np.loadtxt(bins_path)
    if not np.array_equal(edges[:3], [-65, 100, 350]):
        raise ValueError("Author 225 BP window bounds changed")
    inputs = MultisiteRevealsInput(
        site_ids=tuple(
            Path(path).stem.removeprefix("LRAready_") for path in site_paths
        ),
        bin_ids=("225",),
        taxon_ids=tuple(parameters.index),
        counts=counts,
        availability=availability,
        basin_radius_m=radii,
        basin_type=basin_type,
        bin_bounds_bp=np.array([[100, 350]]),
        ppe=parameters["alpha"].to_numpy(dtype=float),
        ppe_covariance=covariance.to_numpy(dtype=float),
        fall_speed_m_s=parameters["vg"].to_numpy(dtype=float),
    )
    draws_path = repository / RESULT / "bootstrap-full-grid.csv"
    taxa_path = repository / RESULT / "taxa.csv"
    draws = np.loadtxt(draws_path, delimiter=",", dtype=int, ndmin=2)
    result = run_reveals_multisite(
        inputs,
        PublicationRevealsConfig("landclimii-author-archive-bins-v1"),
        bootstrap_indices={"225": draws},
    )
    reference = pd.read_csv(taxa_path)
    reference = reference[reference["scenario"] == "full_grid"]
    if reference["taxon"].tolist() != parameters.index.tolist():
        raise ValueError("Tagged R comparison taxon axis changed")
    actual_cover = result.cover.to_numpy(dtype=float)[0]
    actual_se = result.standard_error.to_numpy(dtype=float)[0]
    cover_check = _comparison(
        actual_cover, reference["secondary_cover"].to_numpy(), se=False
    )
    se_check = _comparison(actual_se, reference["secondary_se"].to_numpy(), se=True)
    if (
        not cover_check["passed"]
        or not se_check["passed"]
        or int(result.site_count.to_numpy(dtype=int)[0]) != 6
    ):
        raise ValueError(
            "Native historical profile differs from tagged-R full-grid result"
        )
    return {
        "schema_version": "petrkunes-tagged-r-native-parity.v1",
        "profile": "landclimii-2016-release-source-v1",
        "source_r_release": "Petr Kunes LRA v0.1.2 commit d29075692ed730e3934bc461eb9081c404aef59b",
        "grid_id": "512",
        "window_midpoint_bp": 225,
        "source_window_bounds_bp": [100, 350],
        "supplied_sites": len(site_paths),
        "active_sites": int(availability.sum()),
        "taxa": len(parameters),
        "site_bootstrap_draws": len(draws),
        "cover": cover_check,
        "standard_error": se_check,
        "source_faithful_not_corrected_uncertainty": True,
        "independent_model_validation_claimed": False,
        "private_inputs": [_identity(path, private_root) for path in files],
        "reference_inputs": [
            _identity(path, repository) for path in (draws_path, taxa_path)
        ],
        "code_inputs": [_identity(repository / path, repository) for path in CODE],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--private-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = compare(args.repository, args.private_root)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "native-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        "Native historical profile matches tagged R on the full nine-site grid window"
    )


if __name__ == "__main__":
    main()
