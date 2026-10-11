"""Conditional multi-site uncertainty for a closed author-example pollen axis."""

from __future__ import annotations

import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path
from typing import cast

import numpy as np

from bijux_pollenomics_lra.api import (
    fixed_site_cover_covariance,
    joint_site_cover_draws,
)
from bijux_pollenomics_lra.dispersal.publication import publication_deposition

GRID = "512"
WINDOW_MIDPOINT_BP = "225"
REPLICATES = 1024
SEED = 630512225


def _csv(path: Path) -> list[list[str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.reader(handle))


def _identity(path: Path, root: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {
        "path": path.relative_to(root).as_posix(),
        "bytes": len(data),
        "sha256": sha256(data).hexdigest(),
    }


def replay(
    source_root: Path, repository: Path
) -> tuple[dict[str, object], dict[str, object], np.ndarray]:
    """Use only positive source-supported taxa in one author example window."""
    author = source_root / "author"
    parameter_path = author / "run.REVEALS.files/av-RPP.all.landclimII.csv"
    covariance_path = author / "run.REVEALS.files/avar-RPP.all.landclimII.csv"
    site_list_path = author / "run.REVEALS.files/site.list.512.csv"
    crosswalk_path = source_root / "reference/taxon-name-crosswalk.csv"
    parameter_rows = _csv(parameter_path)
    covariance_rows = _csv(covariance_path)
    names = [row[0] for row in _csv(site_list_path)]
    if len(names) != 9 or len(set(names)) != 9:
        raise ValueError("Author grid 512 site membership changed")
    crosswalk = dict(_csv(crosswalk_path)[1:])
    files = [parameter_path, covariance_path, site_list_path, crosswalk_path]
    site_data: list[tuple[str, float, dict[str, int]]] = []
    for filename in names:
        site = filename.removeprefix("LRAready_").removesuffix(".csv")
        path = author / "run.REVEALS.files" / filename
        files.append(path)
        rows = _csv(path)
        column = rows[0].index(WINDOW_MIDPOINT_BP)
        radius = float(rows[1][column])
        model = int(float(rows[2][column]))
        if radius == 0:
            continue
        if model != 2 or radius <= 0:
            raise ValueError("Active site has unsupported source geometry")
        site_counts = {row[0]: int(row[column]) for row in rows[3:]}
        if len(site_counts) != 31 or any(value < 0 for value in site_counts.values()):
            raise ValueError("Prepared author count axis changed")
        site_data.append((site, radius, site_counts))
    if len(site_data) != 6 or len({site for site, _, _ in site_data}) != 6:
        raise ValueError("Selected six-site author window changed")
    lineage_path = (
        repository
        / "docs/report/source-relations/landclim/author-example-taxon-support/sites.csv"
    )
    lineage_rows = list(csv.DictReader(lineage_path.open(encoding="utf-8", newline="")))
    lineage_status = {row["site"]: row["byte_equal"] for row in lineage_rows}
    if len(lineage_status) != 17 or any(
        lineage_status.get(site) != "TRUE" for site, _, _ in site_data
    ):
        raise ValueError("Selected source site is not byte-replayed from raw pollen")

    prepared_targets = sorted(
        set.intersection(
            *(
                set(key for key, value in counts.items() if value > 0)
                for _, _, counts in site_data
            )
        )
    )
    if len(prepared_targets) != 10:
        raise ValueError("Common positive taxon axis changed")
    source_targets = [
        next(source for source, prepared in crosswalk.items() if prepared == target)
        for target in prepared_targets
    ]
    parameter_by_name = {row[0]: row for row in parameter_rows[1:]}
    covariance_names = covariance_rows[0][1:]
    covariance_by_name = {row[0]: row[1:] for row in covariance_rows[1:]}
    if set(source_targets) - set(parameter_by_name) or set(source_targets) - set(
        covariance_names
    ):
        raise ValueError("Selected taxa are missing source PPE parameters")
    counts = np.array(
        [[values[target] for target in prepared_targets] for _, _, values in site_data],
        dtype=np.int64,
    )
    if not np.all(counts > 0):
        raise ValueError("Selected source counts are not all positive")
    ppe = np.array([float(parameter_by_name[target][1]) for target in source_targets])
    fall_speed = np.array(
        [float(parameter_by_name[target][2]) for target in source_targets]
    )
    ppe_covariance = np.array(
        [
            [
                float(covariance_by_name[row][covariance_names.index(column)])
                for column in source_targets
            ]
            for row in source_targets
        ]
    )
    deposition = np.stack(
        [
            publication_deposition(fall_speed, radius, "lake", 3.0, 100_000.0)
            for _, radius, _ in site_data
        ]
    )
    measured = np.ones_like(counts, dtype=bool)
    fixed = fixed_site_cover_covariance(
        counts, deposition, ppe, ppe_covariance, taxon_measured=measured
    )

    rng = np.random.default_rng(SEED)
    site_indices = rng.integers(0, len(site_data), size=(REPLICATES, len(site_data)))
    count_draws = np.stack(
        [
            [rng.multinomial(int(site.sum()), site / site.sum()) for site in counts]
            for _ in range(REPLICATES)
        ]
    )
    log_covariance = np.log1p(ppe_covariance / np.outer(ppe, ppe))
    log_mean = np.log(ppe) - np.diag(log_covariance) / 2
    ppe_draws = np.exp(rng.multivariate_normal(log_mean, log_covariance, REPLICATES))
    joint = joint_site_cover_draws(
        counts,
        deposition,
        site_indices,
        count_draws,
        ppe_draws,
        taxon_measured=measured,
    )
    draws = {
        "site_indices": site_indices.tolist(),
        "count_draws_by_original_site": count_draws.tolist(),
        "shared_ppe_draws": ppe_draws.tolist(),
    }
    code_paths = [
        repository
        / "docs/report/method-certification/author-site-uncertainty/replay.py",
        repository
        / "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/fixed_site_covariance.py",
        repository
        / "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/joint_site_draws.py",
        repository
        / "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/dispersal/publication.py",
    ]
    report: dict[str, object] = {
        "schema_version": "landclim-author-site-uncertainty.v1",
        "source_role": "released author example; numerical development only",
        "grid_id": GRID,
        "window_midpoint_bp": int(WINDOW_MIDPOINT_BP),
        "site_ids": [site for site, _, _ in site_data],
        "source_radius_values": [radius for _, radius, _ in site_data],
        "radius_interpretation": "source static radius values passed as metres to lake deposition; age-specific basin geometry unverified",
        "source_model_code": 2,
        "prepared_targets": prepared_targets,
        "source_parameter_targets": source_targets,
        "taxon_axis_rule": "positive prepared count in all six active sites; exploratory selection",
        "denominator": "sum of the ten selected taxon counts within each site/window",
        "selected_counts_by_site": counts.sum(axis=1).tolist(),
        "all_author_target_counts_by_site": [
            sum(values.values()) for _, _, values in site_data
        ],
        "source_counting_absence_claimed": False,
        "taxon_measured_basis": "each selected taxon has a positive prepared source count at every selected site",
        "ppe": ppe.tolist(),
        "ppe_covariance": ppe_covariance.tolist(),
        "fall_speed_m_s": fall_speed.tolist(),
        "wind_speed_m_s": 3.0,
        "regional_extent_m": 100_000.0,
        "deposition": deposition.tolist(),
        "fixed_site_cover": fixed.cover.tolist(),
        "fixed_site_standard_error": fixed.standard_error.tolist(),
        "joint_mean_cover": joint.mean_cover.tolist(),
        "joint_standard_error": joint.standard_error.tolist(),
        "joint_replicate_count": REPLICATES,
        "joint_seed": SEED,
        "ppe_draw_model": "positive multivariate lognormal moment-matched to author mean/covariance",
        "count_draw_model": "one conditional multinomial draw per original site and replicate",
        "site_draw_model": "bootstrap six original site identities with replacement",
        "chronology_geometry_transport_fixed": True,
        "historical_source_r_parity_claimed": False,
        "ecological_accuracy_claimed": False,
        "private_source_inputs": [_identity(path, source_root) for path in files],
        "author_prepared_lineage": _identity(lineage_path, repository),
        "repository_code_inputs": [_identity(path, repository) for path in code_paths],
    }
    return report, draws, joint.cover_draws


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report, draws, covers = replay(
        args.source_root.resolve(), args.repository.resolve()
    )
    args.output.mkdir(parents=True, exist_ok=True)
    draws_path = args.output / "draws.json"
    draws_path.write_text(
        json.dumps(draws, separators=(",", ":")) + "\n", encoding="utf-8"
    )
    report["draws_sha256"] = sha256(draws_path.read_bytes()).hexdigest()
    cover_path = args.output / "cover-draws.csv"
    with cover_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(cast(list[str], report["prepared_targets"]))
        writer.writerows(covers.tolist())
    report["cover_draws_sha256"] = sha256(cover_path.read_bytes()).hexdigest()
    (args.output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("Six author sites and ten positive taxa retain conditional joint draws")


if __name__ == "__main__":
    main()
