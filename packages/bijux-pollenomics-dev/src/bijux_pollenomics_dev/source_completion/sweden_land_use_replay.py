"""Replay one governed Swedish land-use product and classify its semantic diff."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics.reporting.service import generate_country_report

PRODUCT = Path("docs/report/countries/sweden")
VERSION = Path("data/aadr/v66")
SOURCE_FILES = (
    Path("data/aadr/v66/release_manifest.json"),
    Path("data/aadr/v66/1240k/v66.1240K.aadr.PUB.anno"),
    Path("data/aadr/v66/ho/v66.HO.aadr.PUB.anno"),
    Path("data/landclim/normalized/nordic_reveals_temporal_grid_cells.geojson"),
    Path("data/sead/normalized/nordic_temporal_evidence.geojson"),
    Path("data/svar/review/lake_candidate_registry_review.json"),
    Path("data/svar/review/sweden_lake_candidate_registry.geojson"),
)
UPSTREAM_FILES = (
    "sweden_aadr_v66_localities.csv",
    "sweden_animal_adna_v66_localities.geojson",
    "sweden_lake_evidence_richness_v66.json",
)
OUTPUT_FILES = (
    "sweden_land_use_synthesis_v66.json",
    "sweden_land_use_synthesis_v66.csv",
    "sweden_land_use_synthesis_v66.md",
)
ROW_FIELDS = {
    "normalized_identity_or_value": frozenset(
        {
            "landclim_grid_record_id",
            "latitude",
            "longitude",
            "time_start_bp",
            "time_end_bp",
            "time_mean_bp",
        }
    ),
    "admission_or_exclusion": frozenset(
        {"lake_decision", "target_class", "quality_class"}
    ),
    "scientific_result": frozenset(
        {
            "forest_cover",
            "evergreen_tree_cover",
            "summergreen_tree_cover",
            "open_land_cover",
            "agricultural_land_cover",
            "grassland_cover",
            "cereal_type_pollen_cover",
            "rye_pollen_cover",
            "sead_temporal_record_count_20km",
            "sead_site_count_20km",
            "human_adna_locality_count_20km",
            "human_adna_sample_count_20km",
            "animal_adna_locality_count_20km",
            "animal_adna_sample_count_20km",
            "cross_proxy_posture",
        }
    ),
    "presentation": frozenset({"time_label", "cereal_interpretation_posture"}),
}
DECISION_FIELDS = {
    "normalized_identity_or_value": frozenset(
        {
            "registry_id",
            "registry_name",
            "latitude",
            "longitude",
            "lake_area_km2",
            "coordinate_source",
            "source_url",
        }
    ),
    "policy_or_weighting": frozenset({"lake_rank"}),
    "admission_or_exclusion": frozenset(
        {
            "target_class",
            "lake_decision",
            "landclim_coverage_posture",
            "sampling_readiness_posture",
        }
    ),
    "scientific_result": frozenset({"landclim_window_count"}),
    "presentation": frozenset({"decision_reason"}),
}
TOP_FIELDS = {
    "source_membership": frozenset({"target_count", "time_row_count"}),
    "policy_or_weighting": frozenset(
        {
            "schema_version",
            "country",
            "context_radius_km",
            "landclim_dataset_id",
            "interval_semantics",
            "temporal_direction",
            "methodology",
        }
    ),
    "admission_or_exclusion": frozenset(
        {"landclim_covered_target_count", "landclim_uncovered_target_count"}
    ),
    "presentation": frozenset({"landclim_source_url"}),
}
CATEGORIES = (
    "source_membership",
    "normalized_identity_or_value",
    "policy_or_weighting",
    "admission_or_exclusion",
    "scientific_result",
    "presentation",
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _index(
    rows: list[dict[str, Any]], keys: tuple[str, ...]
) -> dict[str, dict[str, Any]]:
    indexed = {}
    for row in rows:
        key = "|".join(str(row[field]) for field in keys)
        if key in indexed:
            raise ValueError(f"Duplicate semantic product key: {key}")
        indexed[key] = row
    return indexed


def semantic_diff(
    baseline: dict[str, Any],
    candidate: dict[str, Any],
    *,
    renderings_equal: bool,
) -> dict[str, list[dict[str, object]]]:
    """Classify one product's fields without mistaking prose changes for science."""
    changes: dict[str, list[dict[str, object]]] = {key: [] for key in CATEGORIES}

    def compare_fields(
        before: dict[str, Any],
        after: dict[str, Any],
        *,
        path: str,
        groups: dict[str, frozenset[str]],
        keys: frozenset[str],
    ) -> None:
        known = keys.union(*(set(fields) for fields in groups.values()))
        if set(before) != known or set(after) != known:
            raise ValueError(f"Unclassified {path} schema field")
        for category, fields in groups.items():
            for field in sorted(fields):
                if before[field] != after[field]:
                    changes[category].append(
                        {
                            "path": f"{path}.{field}",
                            "before": before[field],
                            "after": after[field],
                        }
                    )

    compare_fields(
        baseline,
        candidate,
        path="product",
        groups=TOP_FIELDS,
        keys=frozenset({"rows", "target_decisions"}),
    )
    for kind, keys, groups in (
        ("target_decisions", ("requested_name",), DECISION_FIELDS),
        ("rows", ("target_name", "landclim_record_id"), ROW_FIELDS),
    ):
        before = _index(baseline[kind], keys)
        after = _index(candidate[kind], keys)
        for key in sorted(before.keys() ^ after.keys()):
            changes["source_membership"].append(
                {
                    "path": f"{kind}[{key}]",
                    "before": key in before,
                    "after": key in after,
                }
            )
        for key in sorted(before.keys() & after.keys()):
            compare_fields(
                before[key],
                after[key],
                path=f"{kind}[{key}]",
                groups=groups,
                keys=frozenset(keys),
            )
    if not renderings_equal and all(
        not changes[category] for category in CATEGORIES if category != "presentation"
    ):
        changes["presentation"].append(
            {
                "path": "serialized_json_csv_or_markdown",
                "before": "published",
                "after": "replay",
            }
        )
    return changes


def replay(repository: Path, output: Path) -> dict[str, object]:
    """Rebuild the country consumer once and retain exact source/output IDs."""
    if output.exists():
        raise ValueError("Replay output directory already exists")
    repository = repository.resolve()
    published = repository / PRODUCT
    output.mkdir(parents=True)
    candidate = output / "candidate"
    generate_country_report(
        version_dir=repository / VERSION,
        country="Sweden",
        output_dir=candidate,
        context_root=repository / "data",
    )
    source_files = [
        {"path": path.as_posix(), "sha256": _sha(repository / path)}
        for path in SOURCE_FILES
    ]
    policy_root = (
        repository
        / "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/fieldwork/land_use"
    )
    policy_files = [
        {"path": path.relative_to(repository).as_posix(), "sha256": _sha(path)}
        for path in sorted(policy_root.glob("*.py"))
    ]
    upstream = [
        {
            "path": f"{PRODUCT.as_posix()}/{name}",
            "published_sha256": _sha(published / name),
            "replay_sha256": _sha(candidate / name),
        }
        for name in UPSTREAM_FILES
    ]
    outputs = [
        {
            "path": f"{PRODUCT.as_posix()}/{name}",
            "published_sha256": _sha(published / name),
            "replay_sha256": _sha(candidate / name),
        }
        for name in OUTPUT_FILES
    ]
    source = json.loads((published / OUTPUT_FILES[0]).read_text(encoding="utf-8"))
    rebuilt = json.loads((candidate / OUTPUT_FILES[0]).read_text(encoding="utf-8"))
    changes = semantic_diff(
        source,
        rebuilt,
        renderings_equal=all(
            row["published_sha256"] == row["replay_sha256"] for row in outputs
        ),
    )
    if any(row["published_sha256"] != row["replay_sha256"] for row in upstream):
        changes["normalized_identity_or_value"].append(
            {
                "path": "upstream_country_inputs",
                "before": "published",
                "after": "replay",
            }
        )
    receipt: dict[str, object] = {
        "schema_version": "sweden-land-use-semantic-replay.v1",
        "product": PRODUCT.as_posix(),
        "source_files": source_files,
        "policy_files": policy_files,
        "upstream_products": upstream,
        "outputs": outputs,
        "semantic_changes": changes,
        "change_counts": {key: len(value) for key, value in changes.items()},
        "status": "identical"
        if all(not value for value in changes.values())
        and all(row["published_sha256"] == row["replay_sha256"] for row in outputs)
        else "changed",
    }
    (output / "receipt.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = replay(args.repository, args.output)
    print(receipt["status"], receipt["change_counts"])


if __name__ == "__main__":
    main()
