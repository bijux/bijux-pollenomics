"""Deterministic publisher doubles for report-partition tests."""

from __future__ import annotations

from collections.abc import Mapping
import csv
import json
from pathlib import Path

from bijux_pollenomics.reporting.bundles.report_partitions.artifacts import (
    scientific_artifact_inventory,
)
from bijux_pollenomics.reporting.geography import GeographicScope
from bijux_pollenomics.reporting.models import CountryReport, MultiCountryMapReport


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def generate_map(
    *,
    countries: tuple[str, ...],
    output_dir: Path,
    title: str,
    slug: str,
    published_output_dir: Path,
    geography_scope: GeographicScope,
    **_: object,
) -> MultiCountryMapReport:
    output_dir.mkdir(parents=True, exist_ok=True)
    country_counts = dict.fromkeys(countries, 1)
    report = MultiCountryMapReport(
        title=title,
        slug=slug,
        version="v66",
        generated_on="2026-09-08",
        countries=countries,
        country_sample_counts=country_counts,
        total_unique_samples=len(countries),
        output_dir=published_output_dir,
        scope_key=geography_scope.key,
        scope_label=geography_scope.label,
        scope_kind=geography_scope.kind,
        parent_scope_key=geography_scope.parent_key,
    )
    write_json(
        output_dir / f"{slug}_summary.json",
        {
            "schema_version": "geographic-evidence-surface-summary.v1",
            "title": title,
            "slug": slug,
            "version": report.version,
            "generated_on": report.generated_on,
            "countries": list(countries),
            "country_sample_counts": country_counts,
            "total_unique_samples": len(countries),
            "scope_key": report.scope_key,
            "scope_label": report.scope_label,
            "scope_kind": report.scope_kind,
            "parent_scope_key": report.parent_scope_key,
        },
    )
    write_json(
        output_dir / f"{slug}_samples.geojson",
        {
            "type": "FeatureCollection",
            "features": [
                {"properties": {"genetic_id": f"human:{country.lower()}"}}
                for country in countries
            ],
        },
    )
    write_json(
        output_dir / f"{slug}_animal_atlas_evidence.json",
        {
            "schema_version": "animal-atlas-evidence-rows.v1",
            "rows": [
                {"evidence_row_id": f"animal:{country.lower()}"}
                for country in countries
            ],
        },
    )
    (output_dir / f"{slug}_map.html").write_text("<html></html>", encoding="utf-8")
    return report


def generate_country(
    *,
    country: str,
    output_dir: Path,
    published_output_dir: Path,
    map_reference: tuple[str, str],
    **_: object,
) -> CountryReport:
    output_dir.mkdir(parents=True, exist_ok=True)
    country_slug = country.lower().replace(" ", "-")
    write_json(
        output_dir / f"{country_slug}_aadr_v66_summary.json",
        {
            "schema_version": "country-report-summary.v1",
            "country": country,
            "version": "v66",
            "generated_on": "2026-09-08",
            "total_unique_samples": 1,
            "total_unique_localities": 1,
            "dataset_row_counts": {"1240k": 1},
        },
    )
    with (output_dir / f"{country_slug}_aadr_v66_localities.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("time_start_bp", "time_end_bp", "time_mean_bp"),
        )
        writer.writeheader()
        writer.writerow(
            {"time_start_bp": "100", "time_end_bp": "200", "time_mean_bp": "150"}
        )
    write_json(
        output_dir / f"{country_slug}_aadr_v66_samples.geojson",
        {
            "type": "FeatureCollection",
            "features": [{"properties": {"genetic_id": f"human:{country_slug}"}}],
        },
    )
    write_json(
        output_dir / f"{country_slug}_animal_adna_v66_summary.json",
        {"sample_rows": [{"evidence_row_id": f"animal:{country_slug}"}]},
    )
    (output_dir / "README.md").write_text(
        f"{map_reference[0]}: {map_reference[1]}\n", encoding="utf-8"
    )
    return CountryReport(
        country=country,
        version="v66",
        generated_on="2026-09-08",
        total_unique_samples=1,
        total_unique_localities=1,
        dataset_row_counts={"1240k": 1},
        samples=(),
        localities=(),
        output_dir=published_output_dir,
    )


def publish_public(output_root: Path, **_: object) -> dict[str, str]:
    selected = publish_public_inventory()
    _write_artifacts(output_root, selected)
    return selected


def publish_foundation(output_root: Path, **_: object) -> dict[str, str]:
    public_keys = set(publish_public_inventory())
    selected = {
        key: filename
        for key, filename in scientific_artifact_inventory().items()
        if key not in public_keys
    }
    _write_artifacts(output_root, selected)
    write_json(
        output_root / "animal_publication_release_gate.json", {"overall_ok": True}
    )
    return selected


def publish_public_inventory() -> dict[str, str]:
    prefixes = (
        "animal_country_",
        "animal_output_honesty_",
        "animal_human_",
        "animal_pollen_",
        "animal_first_",
        "animal_atlas_",
        "nordic_farming_",
    )
    return {
        key: value
        for key, value in scientific_artifact_inventory().items()
        if key.startswith(prefixes)
    }


def _write_artifacts(output_root: Path, artifacts: Mapping[str, str]) -> None:
    for filename in artifacts.values():
        path = output_root / filename
        if path.name == "animal_publication_release_gate.json":
            write_json(path, {"overall_ok": True})
        elif path.suffix == ".json":
            write_json(path, {"schema_version": "fixture.v1"})
        else:
            path.write_text(f"# {path.stem}\n", encoding="utf-8")


def build_audit(_data_root: Path, _report_root: Path) -> dict[str, object]:
    return {"schema_version": "animal-output-audit.v2", "report_root": "unbound"}


def render_audit(_payload: dict[str, object]) -> str:
    return "# Animal Output Audit\n"


def publish_truth(output_root: Path, **_: object) -> dict[str, str]:
    write_json(output_root / "repository_claim_audit.json", {"overall_ok": True})
    write_json(output_root / "repository_truth_posture.json", {"posture": "fixture"})
    return {
        "repository_claim_audit_json": "repository_claim_audit.json",
        "repository_truth_posture_json": "repository_truth_posture.json",
    }


def publish_portal(output_root: Path) -> dict[str, str]:
    write_json(output_root / "report_surface_registry.json", {"rows": []})
    return {"report_surface_registry_json": "report_surface_registry.json"}


def publish_sustainability(output_root: Path, **_: object) -> None:
    write_json(
        output_root / "repository_output_sustainability_review.json", {"ok": True}
    )
