"""Retain explicit paired site, count and PPE REVEALS draws."""

from __future__ import annotations

import argparse
import csv
from hashlib import sha256
import io
import json
from pathlib import Path

import numpy as np

from bijux_pollenomics_lra.api import joint_site_cover_draws

SOURCE = Path("docs/report/method-certification/fixed-site-covariance/report.json")
SOURCE_SHA256 = "6f80a5f7bc7db086334cd089b2412d1520ad76e5b2bc0f9b2ff7c99f9cd9a953"
SOURCE_FILES = (
    Path("docs/report/method-certification/joint-site-draws/replay.py"),
    Path(
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/"
        "reconstruction/joint_site_draws.py"
    ),
)
REPEATS = 2048
SEED = 20260928


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _identity(repository: Path, relative: Path) -> dict[str, object]:
    content = (repository / relative).read_bytes()
    return {
        "path": relative.as_posix(),
        "bytes": len(content),
        "sha256": sha256(content).hexdigest(),
    }


def _cover_csv(taxa: list[str], values: np.ndarray) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["draw_index", *taxa])
    for index, row in enumerate(values):
        writer.writerow([index, *row])
    return buffer.getvalue().encode("utf-8")


def publish(repository: Path, output: Path) -> dict[str, object]:
    """Run one bounded synthetic joint uncertainty study on frozen geometry."""
    source_path = repository / SOURCE
    source_bytes = source_path.read_bytes()
    if sha256(source_bytes).hexdigest() != SOURCE_SHA256:
        raise ValueError("Fixed-site geometry or PPE example changed")
    source = json.loads(source_bytes)
    counts = np.asarray(source["counts"], dtype=int)
    deposition = np.asarray(source["deposition"], dtype=float)
    ppe = np.asarray(source["ppe"], dtype=float)
    covariance = np.asarray(source["ppe_covariance"], dtype=float)
    if counts.shape != (2, 3) or len(source["taxon_ids"]) != 3:
        raise ValueError("Heterogeneous-basin example axes changed")
    generator = np.random.default_rng(SEED)
    site_indices = generator.integers(0, 2, size=(REPEATS, 2), dtype=np.int64)
    count_draws = np.empty((REPEATS, 2, 3), dtype=np.int64)
    for site in range(2):
        count_draws[:, site] = generator.multinomial(
            int(counts[site].sum()), counts[site] / counts[site].sum(), size=REPEATS
        )
    ppe_draws = np.empty((REPEATS, 3), dtype=float)
    rejected_ppe_vectors = 0
    for index in range(REPEATS):
        while True:
            draw = generator.multivariate_normal(ppe, covariance)
            if np.all(draw > 0):
                ppe_draws[index] = draw
                break
            rejected_ppe_vectors += 1
            if rejected_ppe_vectors > REPEATS * 100:
                raise ValueError("Positive PPE draw budget exhausted")

    fixed_indices = np.broadcast_to(np.arange(2), site_indices.shape).copy()
    fixed_counts = np.broadcast_to(counts, count_draws.shape).copy()
    fixed_ppe = np.broadcast_to(ppe, ppe_draws.shape).copy()
    scenarios = {
        "joint": (site_indices, count_draws, ppe_draws),
        "fixed_sites_count_and_ppe": (fixed_indices, count_draws, ppe_draws),
        "site_only": (site_indices, fixed_counts, fixed_ppe),
        "count_only": (fixed_indices, count_draws, fixed_ppe),
        "ppe_only": (fixed_indices, fixed_counts, ppe_draws),
    }
    outcomes = {
        name: joint_site_cover_draws(counts, deposition, *arrays)
        for name, arrays in scenarios.items()
    }
    draw_payload = {
        "schema_version": "reveals-explicit-joint-draws.v1",
        "source_report_sha256": SOURCE_SHA256,
        "source_files": [_identity(repository, relative) for relative in SOURCE_FILES],
        "draw_index_base": 0,
        "site_index_base": 0,
        "site_ids": source["site_ids"],
        "taxon_ids": source["taxon_ids"],
        "site_indices": site_indices.tolist(),
        "count_draws_by_original_site": count_draws.tolist(),
        "shared_ppe_draws": ppe_draws.tolist(),
    }
    draw_bytes = _json_bytes(draw_payload)
    cover_bytes = _cover_csv(source["taxon_ids"], outcomes["joint"].cover_draws)
    report = {
        "schema_version": "reveals-joint-site-draws-example.v1",
        "profile": outcomes["joint"].profile,
        "source_report": SOURCE.as_posix(),
        "source_report_sha256": SOURCE_SHA256,
        "site_ids": source["site_ids"],
        "taxon_ids": source["taxon_ids"],
        "draw_count": REPEATS,
        "seed": SEED,
        "draw_generation": (
            "uniform site bootstrap with replacement; independent fixed-total "
            "multinomial count draws per original site; shared whole-vector "
            "positive multivariate normal PPE draws from the declared covariance"
        ),
        "rejected_ppe_vectors": rejected_ppe_vectors,
        "draw_files": [
            {
                "path": "draws.json",
                "bytes": len(draw_bytes),
                "sha256": sha256(draw_bytes).hexdigest(),
            },
            {
                "path": "joint-cover-draws.csv",
                "bytes": len(cover_bytes),
                "sha256": sha256(cover_bytes).hexdigest(),
            },
        ],
        "scenarios": [
            {
                "name": name,
                "mean_cover": result.mean_cover.tolist(),
                "standard_error": result.standard_error.tolist(),
                "covariance": result.covariance.tolist(),
            }
            for name, result in outcomes.items()
        ],
        "ablation_interpretation": "Paired draw sensitivity; scenario variances are not additive components.",
        "fixed_geometry": True,
        "fixed_chronology": True,
        "source_r_parity_claimed": False,
        "ecological_accuracy_claimed": False,
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "draws.json").write_bytes(draw_bytes)
    (output / "joint-cover-draws.csv").write_bytes(cover_bytes)
    (output / "report.json").write_bytes(_json_bytes(report))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = publish(args.repository.resolve(), args.output)
    print(f"{report['draw_count']} paired joint REVEALS draws retained")


if __name__ == "__main__":
    main()
