"""Measure Nordic held-out native pollen coverage by author REVEALS taxa."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
from typing import Any

from .landclim_taxonomy_mass import (
    EXCLUDED_TARGETS,
    LOOKUP,
    LOOKUP_SHA256,
    SIZE_VARIANT_CANDIDATES,
    _lookup,
)
from .nordic_direct_pollen import (
    COUNTRIES,
    _is_direct_pollen_count,
    _neotoma_candidates,
    _read_rows,
    _sha,
)

RELATIONAL = Path("data/neotoma/relational")
RAW = Path("data/neotoma/raw/neotoma_pollen_dataset_downloads")
COHORT = Path("docs/report/regions/nordic/direct-pollen/cohort.csv")
DIRECT_MANIFEST = Path("docs/report/regions/nordic/direct-pollen/manifest.json")


def _top(counter: Counter[str], limit: int = 12) -> list[dict[str, str | int]]:
    return [
        {"source_name": name, "nisp": count}
        for name, count in sorted(
            counter.items(), key=lambda pair: (-pair[1], pair[0])
        )[:limit]
    ]


def _fraction(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 6) if denominator else 0.0


def publish(repository: Path, author_source_root: Path, output: Path) -> dict[str, Any]:
    """Consume the same selected samples as the country-held-out study."""
    repository = repository.resolve()
    lookup_path = author_source_root.resolve() / LOOKUP
    mapping, lookup_rows = _lookup(lookup_path)
    cohort_path, direct_manifest_path = (
        repository / COHORT,
        repository / DIRECT_MANIFEST,
    )
    direct_manifest = json.loads(direct_manifest_path.read_text(encoding="utf-8"))
    if _sha(cohort_path) != direct_manifest["cohort_sha256"]:
        raise ValueError("Published Nordic cohort identity changed")
    profiles, metadata, source_hashes, screen_hash, screen_denominators = (
        _neotoma_candidates(repository / RELATIONAL, repository / RAW)
    )
    identity = direct_manifest["input_identity"]
    if (
        source_hashes != identity["relational_file_sha256"]
        or screen_hash != identity["pollen_screen_sha256"]
        or screen_denominators != identity["source_screen_country_denominators"]
        or {country: metadata[country]["candidate_samples"] for country in COUNTRIES}
        != identity["country_candidate_samples"]
    ):
        raise ValueError("Nordic direct-pollen input closure changed")
    with cohort_path.open(newline="", encoding="utf-8") as stream:
        cohort = list(csv.DictReader(stream))
    site_rows = {
        (site["country"], site["site_id"]): site
        for country in COUNTRIES
        for site in metadata[country]["sites"]
    }
    cohort_rows = {(row["country"], row["site_id"]): row for row in cohort}
    if len(site_rows) != len(cohort_rows) or set(site_rows) != set(cohort_rows):
        raise ValueError("Nordic site cohort changed")
    selected_samples: dict[str, tuple[str, str]] = {}
    for (country, site_id), site in site_rows.items():
        if len(site["candidate_sample_ids"]) != int(
            cohort_rows[(country, site_id)]["candidate_samples"]
        ):
            raise ValueError("Nordic site sample count changed")
        for sample_id in site["candidate_sample_ids"]:
            if sample_id in selected_samples:
                raise ValueError("Selected Nordic sample belongs to multiple sites")
            selected_samples[sample_id] = (country, site_id)
    if len(selected_samples) != sum(
        metadata[country]["candidate_samples"] for country in COUNTRIES
    ):
        raise ValueError("Selected Nordic sample denominator changed")

    status_by_site: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    targets_by_site: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    unmapped_by_country: dict[str, Counter[str]] = defaultdict(Counter)
    excluded_by_country: dict[str, Counter[str]] = defaultdict(Counter)
    variant_by_country: dict[str, Counter[str]] = defaultdict(Counter)
    observation_surface = json.loads(
        (repository / RELATIONAL / "manifest.json").read_text(encoding="utf-8")
    )["surfaces"]["observations"]
    visited = 0
    for part in observation_surface["parts"]:
        path = repository / RELATIONAL / part["path"]
        if _sha(path) != part["sha256"]:
            raise ValueError("Nordic observation source part changed")
        rows = _read_rows(path)
        if len(rows) != part["row_count"]:
            raise ValueError("Nordic observation source row count changed")
        for row in rows:
            selected = selected_samples.get(row["sample_id"])
            if selected is None or not _is_direct_pollen_count(row):
                continue
            count, name = row["source_value"], row["source_reported_name"]
            visited += 1
            status = status_by_site[selected]
            status["all_native_nisp"] += count
            target = mapping.get(name)
            if target is None:
                status["unmapped_nisp"] += count
                unmapped_by_country[selected[0]][name] += count
                if name in SIZE_VARIANT_CANDIDATES:
                    status["size_variant_candidate_nisp"] += count
                    variant_by_country[selected[0]][name] += count
            elif target in EXCLUDED_TARGETS:
                status["author_excluded_nisp"] += count
                excluded_by_country[selected[0]][name] += count
            else:
                status["author_assigned_nisp"] += count
                targets_by_site[selected][target] += count
    sites: list[dict[str, Any]] = []
    for key in sorted(site_rows):
        country, site_id = key
        counts = status_by_site[key]
        if (
            counts["all_native_nisp"] <= 0
            or sum(
                counts[status]
                for status in (
                    "author_assigned_nisp",
                    "author_excluded_nisp",
                    "unmapped_nisp",
                )
            )
            != counts["all_native_nisp"]
        ):
            raise ValueError(f"Nordic native pollen mass does not close: {key}")
        profile = profiles[f"{country}:{site_id}"]
        if counts["all_native_nisp"] != sum(
            cell["all_pollen_nisp"] for cell in profile["bins"].values()
        ):
            raise ValueError(f"Nordic author mass differs from held-out profile: {key}")
        sites.append(
            {
                "country": country,
                "site_id": site_id,
                "site_name": site_rows[key]["site_name"],
                "selected_samples": len(site_rows[key]["candidate_sample_ids"]),
                "all_native_nisp": counts["all_native_nisp"],
                "author_assigned_nisp": counts["author_assigned_nisp"],
                "author_excluded_nisp": counts["author_excluded_nisp"],
                "unmapped_nisp": counts["unmapped_nisp"],
                "size_variant_candidate_nisp": counts["size_variant_candidate_nisp"],
                "assigned_fraction": _fraction(
                    counts["author_assigned_nisp"], counts["all_native_nisp"]
                ),
                "author_targets_present": len(targets_by_site[key]),
                "lra_admitted_samples": 0,
            }
        )
    countries: list[dict[str, Any]] = []
    for country in COUNTRIES:
        members = [row for row in sites if row["country"] == country]
        total = Counter(
            {
                field: sum(int(row[field]) for row in members)
                for field in (
                    "all_native_nisp",
                    "author_assigned_nisp",
                    "author_excluded_nisp",
                    "unmapped_nisp",
                    "size_variant_candidate_nisp",
                )
            }
        )
        countries.append(
            {
                "country": country,
                "site_count": len(members),
                "selected_samples": sum(
                    int(row["selected_samples"]) for row in members
                ),
                **dict(total),
                "assigned_fraction": _fraction(
                    total["author_assigned_nisp"], total["all_native_nisp"]
                ),
                "top_unmapped_names": _top(unmapped_by_country[country]),
                "top_author_excluded_names": _top(excluded_by_country[country]),
                "top_size_variant_candidates": _top(variant_by_country[country]),
            }
        )
    report: dict[str, Any] = {
        "schema_version": "nordic-held-out-author-taxonomy-mass.v1",
        "scope": "source-owned selected EPD pollen NISP from the published DK/FI/NO country-held-out cohorts",
        "author_lookup_rows": lookup_rows,
        "selected_site_count": len(sites),
        "selected_sample_count": len(selected_samples),
        "selected_pollen_observation_rows": visited,
        "countries": countries,
        "sites": sites,
        "lra_admitted_samples": 0,
        "interpretation": "Exact author LUT coverage is source-taxonomy feasibility only; exclusions and unmapped mass remain outside the 31-target assignment, and no country basin or historical model is admitted.",
        "inputs": [
            {
                "source_role": "external_author_lookup",
                "path": LOOKUP.as_posix(),
                "sha256": LOOKUP_SHA256,
            },
            {"path": COHORT.as_posix(), "sha256": _sha(cohort_path)},
            {"path": DIRECT_MANIFEST.as_posix(), "sha256": _sha(direct_manifest_path)},
            {
                "path": "data/neotoma/relational/manifest.json",
                "sha256": source_hashes["manifest.json"],
            },
            {
                "path": "data/neotoma/relational/observations",
                "part_sha256": [
                    part["sha256"] for part in observation_surface["parts"]
                ],
            },
        ],
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    with (output / "sites.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(sites[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(sites)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--author-source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = publish(args.repository, args.author_source_root, args.output)
    print(
        json.dumps(
            {
                "sites": report["selected_site_count"],
                "samples": report["selected_sample_count"],
            }
        )
    )


if __name__ == "__main__":
    main()
