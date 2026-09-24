"""Score retained observed-pollen block predictions with Hellinger distance."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import cast

from bijux_pollenomics.analysis.lra_validation.metrics import hellinger_distance

from .prediction import METHOD_LABELS
from .source import _hash, _rows, _write_rows


def _site_block_summaries(
    distances: dict[str, dict[tuple[str, str], float]],
    grid_by_site: dict[str, str],
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    """Average bins within sites, then sites within blocks and across the cohort."""
    sites = []
    for site_id in sorted(grid_by_site):
        keys = [key for key in distances["training_mean"] if key[0] == site_id]
        if not keys:
            raise ValueError("A scored site has no Hellinger distances")
        values = {
            method: mean(method_distances[key] for key in keys)
            for method, method_distances in distances.items()
        }
        sites.append(
            {
                "site_id": site_id,
                "block_grid_id": grid_by_site[site_id],
                "scored_bins": len(keys),
                "methods": values,
            }
        )
    blocks = []
    for grid_id in sorted(set(grid_by_site.values())):
        block_sites = [site for site in sites if site["block_grid_id"] == grid_id]
        blocks.append(
            {
                "block_grid_id": grid_id,
                "scored_sites": len(block_sites),
                "scored_bins": sum(
                    cast(int, site["scored_bins"]) for site in block_sites
                ),
                "methods": {
                    method: mean(
                        cast(dict[str, float], site["methods"])[method]
                        for site in block_sites
                    )
                    for method in distances
                },
            }
        )
    methods = [
        {
            "method": method,
            "site_macro_hellinger": mean(
                cast(dict[str, float], site["methods"])[method] for site in sites
            ),
        }
        for method in distances
    ]
    reference = next(
        cast(float, item["site_macro_hellinger"])
        for item in methods
        if item["method"] == "training_mean"
    )
    for item in methods:
        item["hellinger_minus_training_mean"] = (
            cast(float, item["site_macro_hellinger"]) - reference
        )
    return sites, blocks, methods


def compare_hellinger(
    comparison_path: Path, score_dirs: dict[str, Path], output: Path
) -> dict[str, object]:
    """Reopen scored outcomes only after the persisted prediction comparison."""
    if set(score_dirs) != set(METHOD_LABELS):
        raise ValueError("Require the three retained baseline methods")
    comparison = json.loads(comparison_path.read_text())
    if (
        comparison["schema_version"]
        != "author-observed-pollen-spatial-baseline-comparison.v3"
        or comparison["common_scored_site_bins"] != 148
        or comparison["target_sites"] != 17
    ):
        raise ValueError("Retained comparison profile differs")
    taxon_names = {item["taxon"] for item in comparison["taxa"]}
    if len(taxon_names) != 31:
        raise ValueError("Retained 31-taxon axis differs")
    distances: dict[str, dict[tuple[str, str], float]] = {}
    grid_by_site: dict[str, str] = {}
    observed_by_key: dict[tuple[str, str, str], int] = {}
    rows: list[dict[str, object]] = []
    expected_keys: set[tuple[str, str]] | None = None
    for method in METHOD_LABELS:
        directory = score_dirs[method]
        receipt = comparison["score_receipts"][method]
        if (
            any(
                _hash(directory / name) != receipt[field]
                for name, field in (
                    ("report.json", "report_sha256"),
                    ("scores.csv", "scores_sha256"),
                )
            )
            or _hash(directory / "scored-predictions.csv")
            != comparison["taxon_prediction_sha256"][method]
        ):
            raise ValueError("Scored prediction inputs differ from retained receipts")
        scores = _rows(directory / "scores.csv")
        score_by_key = {
            (row["target_site_id"], row["bin_id_bp"]): row for row in scores
        }
        scored_keys = {
            key for key, row in score_by_key.items() if row["status"] == "scored"
        }
        if (
            len(scores) != 425
            or len(score_by_key) != len(scores)
            or len(scored_keys) != 148
            or (expected_keys is not None and scored_keys != expected_keys)
        ):
            raise ValueError("Methods differ in scored site-bin support")
        expected_keys = scored_keys
        vectors: dict[tuple[str, str], dict[str, tuple[int, float]]] = {}
        for row in _rows(directory / "scored-predictions.csv"):
            key = (row["target_site_id"], row["bin_id_bp"])
            if (
                key not in scored_keys
                or row["block_grid_id"] != score_by_key[key]["block_grid_id"]
            ):
                raise ValueError("Taxon row lies outside the scored block")
            taxon = row["taxon"]
            vector = vectors.setdefault(key, {})
            if taxon in vector:
                raise ValueError("Duplicate scored taxon")
            count = int(row["observed_count"])
            if count < 0 or str(count) != row["observed_count"]:
                raise ValueError("Invalid observed pollen count")
            vector[taxon] = (count, float(row["predicted_fraction"]))
            count_key = (*key, taxon)
            if count_key in observed_by_key and observed_by_key[count_key] != count:
                raise ValueError("Methods disagree on observed pollen counts")
            observed_by_key[count_key] = count
        if set(vectors) != scored_keys or len(observed_by_key) != 148 * 31:
            raise ValueError("Scored pollen vectors are incomplete")
        method_distances = {}
        for key in sorted(scored_keys):
            vector = vectors[key]
            if len(vector) != 31 or set(vector) != taxon_names:
                raise ValueError("Scored pollen taxon axis differs")
            total = sum(count for count, _ in vector.values())
            if total <= 0 or total != int(score_by_key[key]["observed_total_count"]):
                raise ValueError("Observed pollen denominator differs")
            prediction = {taxon: value[1] for taxon, value in vector.items()}
            observed = {taxon: value[0] / total for taxon, value in vector.items()}
            distance = hellinger_distance(prediction, observed)
            method_distances[key] = distance
            site, bin_id = key
            grid_id = score_by_key[key]["block_grid_id"]
            if site in grid_by_site and grid_by_site[site] != grid_id:
                raise ValueError("One physical site spans two blocks")
            grid_by_site[site] = grid_id
            rows.append(
                {
                    "method": method,
                    "block_grid_id": grid_id,
                    "target_site_id": site,
                    "bin_id_bp": bin_id,
                    "hellinger_distance": distance,
                }
            )
        distances[method] = method_distances
    if len(grid_by_site) != 17:
        raise ValueError("Scored physical-site support differs")
    sites, blocks, methods = _site_block_summaries(distances, grid_by_site)
    result: dict[str, object] = {
        "schema_version": "author-observed-pollen-spatial-hellinger.v1",
        "comparison_sha256": _hash(comparison_path),
        "source": comparison["source"],
        "split": comparison["split"],
        "observed_site_bins": comparison["observed_site_bins"],
        "common_scored_site_bins": 148,
        "refused_no_training_site_bins": comparison["refused_no_training_site_bins"],
        "scored_sites": len(sites),
        "independent_outer_blocks": len(blocks),
        "distance_definition": "sqrt(0.5 * sum_taxa((sqrt(predicted_fraction)-sqrt(observed_count/total_count))^2))",
        "distance_range": [0, 1],
        "methods": methods,
        "sites": sites,
        "blocks": blocks,
        "measured_vegetation_accuracy": "not_evaluated",
        "swedish_lra_cohort": "not_evaluated",
    }
    output.mkdir(parents=True, exist_ok=False)
    _write_rows(
        output / "scores.csv",
        (
            "method",
            "block_grid_id",
            "target_site_id",
            "bin_id_bp",
            "hellinger_distance",
        ),
        rows,
    )
    result["scores_sha256"] = _hash(output / "scores.csv")
    (output / "report.json").write_text(json.dumps(result, indent=2) + "\n")
    lines = [
        "# Hellinger distance for buffered observed-pollen predictions",
        "",
        "The retained author-prepared pollen predictions from two adjacent English "
        "grids are rescored on the identical 148/184 observed site-bin support. "
        "Hellinger distance is between zero and one and uses all 31 named taxa "
        "and exact retained observed counts. Each site has equal weight; the "
        "36 bins without buffered same-bin training remain refusals.",
        "",
        "| Method | Site-macro Hellinger | Difference from training mean |",
        "| --- | ---: | ---: |",
    ]
    for item in methods:
        lines.append(
            f"| {item['method']} | {item['site_macro_hellinger']:.6f} | "
            f"{item['hellinger_minus_training_mean']:+.6f} |"
        )
    lines.extend(
        [
            "",
            "| Grid | Sites | Scored bins | Training mean | Nearest site | Inverse distance squared |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for block in blocks:
        values = cast(dict[str, float], block["methods"])
        lines.append(
            f"| {block['block_grid_id']} | {block['scored_sites']} | {block['scored_bins']} | "
            f"{values['training_mean']:.6f} | {values['nearest_site']:.6f} | "
            f"{values['inverse_distance_squared']:.6f} |"
        )
    lines.extend(
        [
            "",
            "The full per-bin distances and per-site means are in scores.csv and "
            "report.json. This is a descriptive development comparison on two "
            "adjacent blocks. It does not select a method or establish Swedish LRA "
            "skill, long-distance transfer, independent vegetation accuracy or "
            "publication rights. The source denominator is the author's prepared "
            "31-taxon count axis, not a certified full raw-core denominator.",
        ]
    )
    (output / "REPORT.md").write_text("\n".join(lines) + "\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comparison", type=Path, required=True)
    for method in METHOD_LABELS:
        parser.add_argument(f"--{method.replace('_', '-')}", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = compare_hellinger(
        args.comparison,
        {method: getattr(args, method) for method in METHOD_LABELS},
        args.output,
    )
    print(json.dumps(result["methods"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
