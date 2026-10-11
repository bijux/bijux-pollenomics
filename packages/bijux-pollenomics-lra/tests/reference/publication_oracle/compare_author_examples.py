"""Compare two acquired author grids against their independent exact R replay.

No scientific data are downloaded or distributed by this script. Paths point to
immutable separately acquired author inputs and independently produced R output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from bijux_pollenomics_lra.api import (
    MultisiteRevealsInput,
    PublicationRevealsConfig,
    run_reveals_multisite,
)
from bijux_pollenomics_lra.models.publication import PUBLICATION_SOURCE_SHA256


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _compare(
    actual: np.ndarray,
    expected: np.ndarray,
    mask: np.ndarray,
    *,
    standard_error: bool = False,
) -> dict[str, object]:
    first, second = actual[mask], expected[mask]
    # The source computes variance by subtracting two accumulated sums of
    # squares; SE near zero therefore has sqrt(epsilon) cancellation noise.
    # Tolerances are declared here before acquiring the comparison result.
    atol, rtol = (5e-8, 1e-9) if standard_error else (1e-11, 1e-10)
    finite = np.isfinite(first) & np.isfinite(second)
    return {
        "passed": bool(
            np.allclose(first, second, atol=atol, rtol=rtol, equal_nan=True)
        ),
        "values": int(first.size),
        "finite_pairs": int(finite.sum()),
        "max_absolute_error": float(np.max(np.abs(first[finite] - second[finite])))
        if finite.any()
        else None,
        "atol": atol,
        "rtol": rtol,
        "undefined_masks_equal": bool(
            np.array_equal(np.isnan(first), np.isnan(second))
        ),
    }


def compare_grid(
    source: Path, reference: Path, output: Path, grid: str
) -> dict[str, object]:
    working = source / "run.REVEALS.files"
    assert _hash(working / "LRA-REVEALS-release.R") == PUBLICATION_SOURCE_SHA256
    paths = (working / f"site.list.{grid}.csv").read_text().splitlines()
    tables = [pd.read_csv(working / path, index_col=0) for path in paths]
    parameters = pd.read_csv(working / "av-RPP.all.landclimII.csv", index_col=0)
    covariance = pd.read_csv(working / "avar-RPP.all.landclimII.csv", index_col=0)
    crosswalk = pd.read_csv(reference / "taxon-name-crosswalk.csv")
    assert crosswalk["source"].tolist() == parameters.index.tolist()
    assert covariance.index.tolist() == parameters.index.tolist()
    assert covariance.columns.tolist() == parameters.index.tolist()
    for table in tables:
        assert table.index[2:].tolist() == crosswalk["prepared"].tolist()
        assert table.columns.tolist() == tables[0].columns.tolist()
    counts = np.stack([table.iloc[2:].to_numpy(dtype=float).T for table in tables])
    radii = np.stack([table.iloc[0].to_numpy(dtype=float) for table in tables])
    model_codes = np.stack([table.iloc[1].to_numpy(dtype=float) for table in tables])
    availability = counts.sum(axis=-1) > 0
    assert np.all(counts[~availability] == 0)
    # Authored zeros represent unrepresented site/windows in the prepared files.
    # This explicit adapter disposition is recorded; no pollen count is imputed.
    counts[~availability] = np.nan
    radii[~availability] = np.nan
    basin_type = np.full(availability.shape, None, dtype=object)
    assert np.isin(model_codes[availability], [1, 2]).all()
    basin_type[availability & (model_codes == 1)] = "peatland"
    basin_type[availability & (model_codes == 2)] = "lake"
    edges = np.loadtxt(source / "bins.csv")
    assert len(edges) == len(tables[0].columns) + 1
    inputs = MultisiteRevealsInput(
        site_ids=tuple(Path(path).stem.removeprefix("LRAready_") for path in paths),
        bin_ids=tuple(tables[0].columns),
        taxon_ids=tuple(parameters.index),
        counts=counts,
        availability=availability,
        basin_radius_m=radii,
        basin_type=basin_type,
        bin_bounds_bp=np.column_stack([edges[:-1], edges[1:]]),
        ppe=parameters["alpha"].to_numpy(dtype=float),
        ppe_covariance=covariance.to_numpy(dtype=float),
        fall_speed_m_s=parameters["vg"].to_numpy(dtype=float),
    )
    draws = {
        name: np.loadtxt(
            reference / grid / f"bootstrap-bin-{position + 1}.csv",
            delimiter=",",
            dtype=int,
            ndmin=2,
        )
        for position, name in enumerate(inputs.bin_ids)
        if availability[:, position].sum() > 1
    }
    result = run_reveals_multisite(
        inputs,
        PublicationRevealsConfig("landclimii-author-archive-bins-v1"),
        bootstrap_indices=draws,
    )
    result.write(output / grid)
    supported = availability.any(axis=0)
    expected_mean = pd.read_csv(reference / grid / "regional-cover.csv", index_col=0).T
    expected_se = pd.read_csv(reference / grid / "regional-se.csv", index_col=0).T
    expected_count = (
        pd.read_csv(reference / grid / "site-count.csv", index_col=0)
        .to_numpy(dtype=int)
        .ravel()
    )
    checks: dict[str, object] = {
        "regional_cover": _compare(
            result.cover.to_numpy(), expected_mean.to_numpy(), supported
        ),
        "regional_se": _compare(
            result.standard_error.to_numpy(),
            expected_se.to_numpy(),
            supported,
            standard_error=True,
        ),
        "site_counts_equal": bool(
            np.array_equal(result.site_count.to_numpy(), expected_count)
        ),
    }
    site_checks = []
    for position, name in enumerate(inputs.site_ids):
        expected = pd.read_csv(
            reference / grid / f"site-{position + 1}-cover.csv", index_col=0
        ).T
        expected_error = pd.read_csv(
            reference / grid / f"site-{position + 1}-se.csv", index_col=0
        ).T
        site_checks.append(
            {
                "site_id": name,
                "cover": _compare(
                    result.site_cover[name].to_numpy(),
                    expected.to_numpy(),
                    availability[position],
                ),
                "se": _compare(
                    result.site_standard_error[name].to_numpy(),
                    expected_error.to_numpy(),
                    availability[position],
                    standard_error=True,
                ),
            }
        )
    checks["sites"] = site_checks
    raw_paths = [working / path for path in paths] + [
        working / "av-RPP.all.landclimII.csv",
        working / "avar-RPP.all.landclimII.csv",
        source / "bins.csv",
        source / "TWlookup.csv",
        working / f"site.list.{grid}.csv",
    ]
    return {
        "passed": bool(
            checks["regional_cover"]["passed"]
            and checks["regional_se"]["passed"]
            and checks["site_counts_equal"]
            and all(
                check["cover"]["passed"] and check["se"]["passed"]
                for check in site_checks
            )
        ),
        "grid_id": grid,
        "sites": len(paths),
        "bins": len(inputs.bin_ids),
        "taxa": len(inputs.taxon_ids),
        "available_site_bins": int(availability.sum()),
        "missing_site_bins": int((~availability).sum()),
        "supported_bins": int(supported.sum()),
        "checks": checks,
        "source_files": {
            str(path.relative_to(source)): _hash(path) for path in raw_paths
        },
        "reference_files": {
            str(path.relative_to(reference)): _hash(path)
            for path in sorted((reference / grid).glob("*.csv"))
        },
        "crosswalk_sha256": _hash(reference / "taxon-name-crosswalk.csv"),
        "transformations": [
            "exact_R_make_names_crosswalk_checked_before_positional_arrays",
            "source_zero_no_count_windows_to_explicit_unavailable_nan",
            "source_bins_retained_despite_50BP_difference_from_paper",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = json.loads((args.reference / "receipt.json").read_text())
    if (
        receipt.get("exit_code") != 0
        or receipt.get("source_sha256") != PUBLICATION_SOURCE_SHA256
        or receipt.get("input_files_unchanged") is not True
    ):
        raise ValueError(
            "Reference receipt does not establish a successful immutable exact-source run"
        )
    for name, digest in receipt["input_files"].items():
        if _hash(args.source / name) != digest:
            raise ValueError(f"Reference input hash mismatch: {name}")
    for name, digest in receipt["output_files"].items():
        if _hash(args.reference / name) != digest:
            raise ValueError(f"Reference output hash mismatch: {name}")
    args.output.mkdir(parents=True, exist_ok=False)
    grids = [
        compare_grid(args.source, args.reference, args.output, grid)
        for grid in ("512", "562")
    ]
    report = {
        "reference_receipt_sha256": _hash(args.reference / "receipt.json"),
        "schema_version": "1.0.0",
        "profile": "landclimii-2016-release-source-v1",
        "coverage": "two_author_example_grids_only_not_full_1128_record_study",
        "independent_measured_vegetation_accuracy": "not_evaluated",
        "grids": grids,
    }
    (args.output / "report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    passed = all(bool(grid["passed"]) for grid in grids)
    print(
        json.dumps(
            {"passed": passed, "grids": 2, "report": str(args.output / "report.json")}
        )
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
