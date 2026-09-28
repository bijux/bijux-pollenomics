"""Compare historical and reviewed REVEALS summaries on paired author-site draws."""

from __future__ import annotations

import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from bijux_pollenomics_lra.api import joint_site_cover_draws
from bijux_pollenomics_lra.reconstruction.publication import (
    bootstrap_cover_variance_with_draws,
)

DRAW_COUNT = 1000


def identity(path: Path, root: Path) -> dict[str, object]:
    content = path.read_bytes()
    return {
        "path": path.relative_to(root).as_posix(),
        "bytes": len(content),
        "sha256": sha256(content).hexdigest(),
    }


def replay(repository: Path, source_root: Path) -> dict[str, object]:
    prior_dir = repository / "docs/report/method-certification/author-site-uncertainty"
    prior_report_path = prior_dir / "report.json"
    draws_path = prior_dir / "draws.json"
    prior = json.loads(prior_report_path.read_text())
    if prior["grid_id"] != "512" or prior["window_midpoint_bp"] != 225:
        raise ValueError("Author site window changed")
    if sha256(draws_path.read_bytes()).hexdigest() != prior["draws_sha256"]:
        raise ValueError("Author draw identity changed")
    source_identities = {row["path"]: row for row in prior["private_source_inputs"]}
    targets = prior["prepared_targets"]
    counts = []
    source_paths = []
    for site in prior["site_ids"]:
        path = source_root / "author/run.REVEALS.files" / f"LRAready_{site}.csv"
        observed = identity(path, source_root)
        if observed != source_identities.get(observed["path"]):
            raise ValueError(f"Author source bytes changed: {site}")
        source_paths.append(observed)
        with path.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.reader(handle))
        column = rows[0].index("225")
        by_name = {row[0]: int(row[column]) for row in rows[3:]}
        counts.append([by_name[name] for name in targets])
    counts_array = np.asarray(counts, dtype=np.int64)
    if counts_array.sum(axis=1).tolist() != prior["selected_counts_by_site"]:
        raise ValueError("Selected author count denominators changed")
    deposition = np.asarray(prior["deposition"], dtype=float)
    ppe = np.asarray(prior["ppe"], dtype=float)
    draws = json.loads(draws_path.read_text())
    site_indices = np.asarray(draws["site_indices"][:DRAW_COUNT], dtype=np.int64)
    if site_indices.shape != (DRAW_COUNT, len(prior["site_ids"])):
        raise ValueError("Paired source site-draw dimensions changed")

    historical_mean, historical_variance, historical_closed = (
        bootstrap_cover_variance_with_draws(counts_array, deposition, ppe, site_indices)
    )
    site_only = joint_site_cover_draws(
        counts_array,
        deposition,
        site_indices,
        np.broadcast_to(counts_array, (DRAW_COUNT, *counts_array.shape)),
        np.broadcast_to(ppe, (DRAW_COUNT, len(ppe))),
        taxon_measured=np.ones_like(counts_array, dtype=bool),
    )
    paired = joint_site_cover_draws(
        counts_array,
        deposition,
        site_indices,
        np.asarray(draws["count_draws_by_original_site"][:DRAW_COUNT], dtype=np.int64),
        np.asarray(draws["shared_ppe_draws"][:DRAW_COUNT], dtype=float),
        taxon_measured=np.ones_like(counts_array, dtype=bool),
    )
    if not np.allclose(historical_closed, site_only.cover_draws, rtol=0, atol=1e-14):
        raise ValueError("Historical and reviewed site-only draw covers differ")
    historical_se = np.sqrt(historical_variance)
    if not np.allclose(historical_se, site_only.standard_error, rtol=0, atol=1e-12):
        raise ValueError("Matched site-only draw standard errors differ")
    comparison_rows = [
        {
            "taxon": taxon,
            "historical_ratio_mean": float(historical_mean[i]),
            "reviewed_site_only_mean": float(site_only.mean_cover[i]),
            "historical_site_only_se": float(historical_se[i]),
            "reviewed_site_only_se": float(site_only.standard_error[i]),
            "reviewed_joint_mean": float(paired.mean_cover[i]),
            "reviewed_joint_se": float(paired.standard_error[i]),
        }
        for i, taxon in enumerate(targets)
    ]
    code_paths = [
        repository
        / "docs/report/method-certification/author-site-profile-comparison/replay.py",
        repository
        / "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/publication.py",
        repository
        / "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/joint_site_draws.py",
    ]
    return {
        "schema_version": "author-site-profile-comparison.v1",
        "source_role": "released author example; restricted ten-taxon numerical development",
        "grid_id": prior["grid_id"],
        "window_midpoint_bp": prior["window_midpoint_bp"],
        "site_ids": prior["site_ids"],
        "taxon_axis": targets,
        "selected_counts_by_site": prior["selected_counts_by_site"],
        "paired_site_draw_count": DRAW_COUNT,
        "paired_draw_rule": "first 1000 retained joint author draw identities",
        "historical_profile": "landclimii-2016-release-source-v1 fixed-count/PPE site bootstrap",
        "reviewed_profile": "closed-draw arithmetic mean with original-site bootstrap, conditional multinomial counts and shared correlated PPE",
        "historical_source_r_parity_basis": "separate tagged-R full-grid comparison; no new R run on this selected ten-taxon case",
        "same_site_only_closed_draws": True,
        "max_historical_vs_reviewed_site_only_mean_gap": float(
            np.max(np.abs(historical_mean - site_only.mean_cover))
        ),
        "max_historical_vs_reviewed_site_only_se_gap": float(
            np.max(np.abs(historical_se - site_only.standard_error))
        ),
        "rows": comparison_rows,
        "input_identities": [
            identity(prior_report_path, repository),
            identity(draws_path, repository),
            *source_paths,
            *(identity(path, repository) for path in code_paths),
        ],
        "chronology_geometry_transport_fixed": True,
        "ecological_accuracy_claimed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = replay(args.repository.resolve(), args.source_root.resolve())
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print("Paired historical and reviewed author-site draw comparison complete")


if __name__ == "__main__":
    main()
