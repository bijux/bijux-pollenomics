"""Replay a heterogeneous-basin conditional REVEALS covariance example."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from bijux_pollenomics_lra.api import fixed_site_cover_covariance
from bijux_pollenomics_lra.dispersal.publication import publication_deposition

SOURCE_FILES = (
    Path(
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/"
        "reconstruction/fixed_site_covariance.py"
    ),
    Path(
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/"
        "dispersal/publication.py"
    ),
)


def replay(repository: Path) -> dict[str, object]:
    """Run one fixed-site example with distinct lake and peatland geometry."""
    counts = np.array([[30, 20, 50], [20, 65, 15]])
    taxon_measured = np.ones_like(counts, dtype=bool)
    ppe = np.array([1.0, 1.5, 0.75])
    covariance = np.array(
        [[0.04, 0.015, -0.005], [0.015, 0.09, 0.01], [-0.005, 0.01, 0.0225]]
    )
    fall_speed = np.array([0.03, 0.035, 0.045])
    basins = (("peatland", 75.0), ("lake", 300.0))
    deposition = np.stack(
        [
            publication_deposition(fall_speed, radius, kind, 3.0, 100_000.0)
            for kind, radius in basins
        ]
    )
    result = fixed_site_cover_covariance(
        counts, deposition, ppe, covariance, taxon_measured=taxon_measured
    )
    no_ppe_covariance = fixed_site_cover_covariance(
        counts,
        deposition,
        ppe,
        np.zeros_like(covariance),
        taxon_measured=taxon_measured,
    )
    inputs = []
    for relative in SOURCE_FILES:
        content = (repository / relative).read_bytes()
        inputs.append(
            {
                "path": relative.as_posix(),
                "bytes": len(content),
                "sha256": sha256(content).hexdigest(),
            }
        )
    return {
        "schema_version": "reveals-fixed-site-covariance-example.v1",
        "profile": result.profile,
        "site_ids": ["small_peatland", "larger_lake"],
        "taxon_ids": ["A", "B", "C"],
        "count_unit": "integer pollen count",
        "basins": [
            {"site_id": site, "type": kind, "radius_m": radius}
            for site, (kind, radius) in zip(
                ("small_peatland", "larger_lake"), basins, strict=True
            )
        ],
        "wind_speed_m_s": 3.0,
        "regional_extent_m": 100_000.0,
        "counts": counts.tolist(),
        "taxon_measured": taxon_measured.tolist(),
        "ppe": ppe.tolist(),
        "ppe_covariance": covariance.tolist(),
        "fall_speed_m_s": fall_speed.tolist(),
        "deposition": deposition.tolist(),
        "cover": result.cover.tolist(),
        "standard_error": result.standard_error.tolist(),
        "counting_covariance": result.counting_covariance.tolist(),
        "ppe_component_covariance": result.ppe_covariance.tolist(),
        "total_covariance": result.total_covariance.tolist(),
        "standard_error_without_ppe_uncertainty": no_ppe_covariance.standard_error.tolist(),
        "counting_model": "independent fixed-total multinomial within each fixed site",
        "parameter_model": "shared full PPE covariance independent of site counts",
        "site_selection_uncertainty_included": False,
        "chronology_uncertainty_included": False,
        "geometry_uncertainty_included": False,
        "transport_uncertainty_included": False,
        "source_r_parity_claimed": False,
        "ecological_accuracy_claimed": False,
        "source_files": inputs,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = replay(args.repository.resolve())
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("Fixed-site cover and covariance retained for two distinct basins")


if __name__ == "__main__":
    main()
