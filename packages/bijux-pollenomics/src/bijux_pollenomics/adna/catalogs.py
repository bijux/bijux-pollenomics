from __future__ import annotations

import csv
import io
import json
from pathlib import Path

from .ena import build_archive_project_catalog
from .paths import adna_species_root
from .project_context import build_species_freshness_rows, resolve_project_context
from .tracked_species import TRACKED_ADNA_SPECIES

__all__ = [
    "build_coordinate_caveat_surface",
    "build_cross_species_archive_inventory",
    "build_cross_species_bibliography",
    "build_cross_species_coverage_dashboard",
    "build_cross_species_map_readiness",
    "build_public_animal_output_audit",
    "build_shipped_adna_product_audit",
    "build_species_freshness_table",
    "build_overbroad_site_ledger",
    "build_unresolved_site_ledger",
    "render_csv_rows",
    "render_coordinate_caveat_surface_markdown",
    "render_coordinate_confidence_scale_markdown",
    "render_public_animal_output_audit_markdown",
]


def build_cross_species_bibliography() -> tuple[dict[str, object], ...]:
    """Deduplicate cited animal aDNA literature across all tracked species."""
    grouped: dict[str, dict[str, object]] = {}
    for project in build_archive_project_catalog():
        linkage = project.paper_linkage
        if linkage is None:
            continue
        key = linkage.doi or linkage.paper_title.casefold()
        current = grouped.setdefault(
            key,
            {
                "paper_title": linkage.paper_title,
                "paper_doi": linkage.doi,
                "journal_title": linkage.journal_title,
                "publication_year": linkage.publication_year,
                "reference_kind": linkage.reference_kind,
                "species_latin_names": set(),
                "project_accessions": set(),
            },
        )
        current["species_latin_names"].add(project.species_latin_name)
        current["project_accessions"].add(project.project_accession)
    rows = []
    for row in grouped.values():
        rows.append(
            {
                "paper_title": row["paper_title"],
                "paper_doi": row["paper_doi"],
                "journal_title": row["journal_title"],
                "publication_year": row["publication_year"],
                "reference_kind": row["reference_kind"],
                "species_latin_names": sorted(row["species_latin_names"]),
                "project_accessions": sorted(row["project_accessions"]),
                "species_count": len(row["species_latin_names"]),
                "project_count": len(row["project_accessions"]),
            }
        )
    return tuple(
        sorted(
            rows,
            key=lambda item: (
                item["publication_year"] or 0,
                item["paper_title"].casefold(),
            ),
            reverse=True,
        )
    )


def build_cross_species_archive_inventory() -> tuple[dict[str, object], ...]:
    """Deduplicate the tracked cross-species archive inventory."""
    grouped: dict[tuple[str, str], dict[str, object]] = {}
    for project in build_archive_project_catalog():
        key = (project.source_family, project.project_accession)
        current = grouped.setdefault(
            key,
            {
                "source_family": project.source_family,
                "project_accession": project.project_accession,
                "metadata_url": project.metadata_url,
                "result_kind": project.result_kind,
                "archive_status": project.archive_status,
                "evidence_strength": project.as_dict()["evidence_strength"],
                "access_policy": project.access_policy,
                "species_latin_names": set(),
            },
        )
        current["species_latin_names"].add(project.species_latin_name)
    rows = []
    for row in grouped.values():
        rows.append(
            {
                "source_family": row["source_family"],
                "project_accession": row["project_accession"],
                "metadata_url": row["metadata_url"],
                "result_kind": row["result_kind"],
                "archive_status": row["archive_status"],
                "evidence_strength": row["evidence_strength"],
                "access_policy": row["access_policy"],
                "species_latin_names": sorted(row["species_latin_names"]),
                "species_count": len(row["species_latin_names"]),
            }
        )
    return tuple(
        sorted(rows, key=lambda item: (item["source_family"], item["project_accession"]))
    )


def build_species_freshness_table() -> tuple[dict[str, object], ...]:
    """Return one freshness row per tracked animal species."""
    rows = build_species_freshness_rows(build_archive_project_catalog())
    tracked = set(TRACKED_ADNA_SPECIES)
    return tuple(
        row for row in rows if row["species_latin_name"] in tracked
    )


def build_cross_species_coverage_dashboard(
    data_root: Path,
    report_root: Path,
) -> dict[str, object]:
    """Report which animal evidence surfaces are actually shipped per species."""
    rows = [
        _build_species_coverage_row(
            data_root=Path(data_root),
            report_root=Path(report_root),
            species_name=species_name,
        )
        for species_name in TRACKED_ADNA_SPECIES
    ]
    return {
        "schema_version": "adna-cross-species-coverage-dashboard.v1",
        "rows": rows,
    }


def build_shipped_adna_product_audit(
    data_root: Path,
    report_root: Path,
) -> dict[str, object]:
    """Build a fuller product audit for what animal aDNA the repo really ships."""
    dashboard = build_cross_species_coverage_dashboard(data_root, report_root)
    rows = dashboard["rows"]
    return {
        "schema_version": "adna-shipped-product-audit.v1",
        "tracked_species_count": len(rows),
        "species_with_source_snapshots": sum(
            1 for row in rows if row["raw_source_snapshot_present"]
        ),
        "species_with_coordinate_provenance": sum(
            1 for row in rows if row["coordinate_provenance_present"]
        ),
        "species_with_locality_artifacts": sum(
            1 for row in rows if row["normalized_locality_artifact_present"]
        ),
        "species_with_country_outputs": sum(
            1 for row in rows if row["country_output_count"] > 0
        ),
        "species_with_atlas_layers": sum(
            1 for row in rows if row["atlas_layer_count"] > 0
        ),
        "rows": rows,
        "missing_public_outputs": [
            row["species_latin_name"]
            for row in rows
            if row["country_output_count"] == 0 and row["atlas_layer_count"] == 0
        ],
    }


def build_cross_species_map_readiness(data_root: Path) -> dict[str, object]:
    """Report point-readiness and refusal posture across tracked animal sample rows."""
    rows = []
    totals = {
        "direct_coordinate_backed": 0,
        "indirectly_geocoded": 0,
        "unresolved": 0,
        "refused_from_mapping": 0,
    }
    for species_name in TRACKED_ADNA_SPECIES:
        row = _build_species_map_readiness_row(Path(data_root), species_name)
        rows.append(row)
        for key in totals:
            totals[key] += int(row[key])
    return {
        "schema_version": "adna-cross-species-map-readiness.v1",
        "rows": rows,
        "totals": totals,
    }


def build_unresolved_site_ledger(data_root: Path) -> tuple[dict[str, object], ...]:
    """List accession-backed sample rows whose site context is still unresolved."""
    rows: list[dict[str, object]] = []
    for species_name in TRACKED_ADNA_SPECIES:
        species_root = _species_root(Path(data_root), species_name)
        for sample in _load_sample_rows(species_root):
            if str(sample.get("inclusion_status", "")) != "sample_context_blocked":
                continue
            rows.append(
                {
                    "species_latin_name": sample.get("species_latin_name", ""),
                    "species_common_name": sample.get("species_common_name", ""),
                    "project_accession": sample.get("project_accession", ""),
                    "stable_sample_id": sample.get("identity", {}).get("stable_token", ""),
                    "site_label": sample.get("locality_identity", {}).get("locality_text", ""),
                    "paper_doi": sample.get("paper_doi", ""),
                    "supplementary_source": sample.get("supplementary_source", ""),
                    "inclusion_note": sample.get("inclusion_note", ""),
                }
            )
    return tuple(
        sorted(rows, key=lambda item: (str(item["species_latin_name"]), str(item["project_accession"])))
    )


def build_overbroad_site_ledger(data_root: Path) -> tuple[dict[str, object], ...]:
    """List curated site leads refused from point mapping because geography is too broad."""
    rows: list[dict[str, object]] = []
    for species_name in TRACKED_ADNA_SPECIES:
        species_root = _species_root(Path(data_root), species_name)
        for provenance in _load_coordinate_provenance_rows(species_root):
            if str(provenance.get("mapping_posture", "")) != "refused_region_only":
                continue
            rows.append(
                {
                    "species_latin_name": provenance.get("species_latin_name", ""),
                    "species_common_name": provenance.get("species_common_name", ""),
                    "project_accession": provenance.get("project_accession", ""),
                    "site_label": provenance.get("site_label", ""),
                    "original_place_text": provenance.get("original_place_text", ""),
                    "resolved_place_text": provenance.get("resolved_place_text", ""),
                    "coordinate_basis": provenance.get("coordinate_basis", ""),
                    "confidence_rationale": provenance.get("confidence_rationale", ""),
                    "support_gap_note": provenance.get("support_gap_note", ""),
                }
            )
    return tuple(
        sorted(rows, key=lambda item: (str(item["species_latin_name"]), str(item["project_accession"])))
    )


def build_coordinate_caveat_surface(data_root: Path) -> dict[str, object]:
    """Group current animal coordinate posture into reader-visible categories."""
    direct_coordinates: list[dict[str, object]] = []
    point_resolution: list[dict[str, object]] = []
    weak_geography: list[dict[str, object]] = []
    for species_name in TRACKED_ADNA_SPECIES:
        species_root = _species_root(Path(data_root), species_name)
        for provenance in _load_coordinate_provenance_rows(species_root):
            row = {
                "species_latin_name": provenance.get("species_latin_name", ""),
                "species_common_name": provenance.get("species_common_name", ""),
                "project_accession": provenance.get("project_accession", ""),
                "site_label": provenance.get("site_label", ""),
                "original_place_text": provenance.get("original_place_text", ""),
                "resolved_place_text": provenance.get("resolved_place_text", ""),
                "coordinate_basis": provenance.get("coordinate_basis", ""),
                "coordinate_confidence": provenance.get("coordinate_confidence", ""),
                "mapping_posture": provenance.get("mapping_posture", ""),
                "confidence_rationale": provenance.get("confidence_rationale", ""),
            }
            if str(provenance.get("mapping_posture", "")) == "mappable_point":
                if str(provenance.get("coordinate_basis", "")) in {
                    "direct_published_coordinates",
                    "supplementary_table_coordinates",
                    "archive_coordinates",
                }:
                    direct_coordinates.append(row)
                else:
                    point_resolution.append(row)
            else:
                weak_geography.append(row)
    return {
        "schema_version": "adna-coordinate-caveat-surface.v1",
        "direct_coordinates": direct_coordinates,
        "place_name_resolution": point_resolution,
        "still_weak_geography": weak_geography,
    }


def build_public_animal_output_audit(
    data_root: Path,
    report_root: Path,
) -> dict[str, object]:
    """Summarize what the shipped public report tree currently exposes for animal aDNA."""
    report_root = Path(report_root)
    dashboard = build_cross_species_coverage_dashboard(data_root, report_root)
    countries = tuple(
        path.name
        for path in sorted(report_root.iterdir())
        if path.is_dir() and path.name not in {"nordic-atlas", "_map_assets"}
    ) if report_root.exists() else ()
    atlas_readme = report_root / "nordic-atlas" / "README.md"
    atlas_notes = (
        atlas_readme.read_text(encoding="utf-8")
        if atlas_readme.exists()
        else ""
    )
    return {
        "schema_version": "animal-output-audit.v1",
        "report_root": str(report_root),
        "countries": list(countries),
        "atlas_bundle_present": (report_root / "nordic-atlas").is_dir(),
        "country_bundle_count": len(countries),
        "atlas_notes": atlas_notes,
        "species_rows": dashboard["rows"],
    }


def render_public_animal_output_audit_markdown(payload: dict[str, object]) -> str:
    """Render the shipped public animal-output audit as reader-facing markdown."""
    rows = payload["species_rows"]
    atlas_layer_total = sum(int(row["atlas_layer_count"]) for row in rows)
    country_output_total = sum(int(row["country_output_count"]) for row in rows)
    lines = [
        "# Animal output audit",
        "",
        f"- Report root: `{payload['report_root']}`",
        f"- Atlas bundle present: `{str(payload['atlas_bundle_present']).lower()}`",
        f"- Country bundle count: `{payload['country_bundle_count']}`",
        "",
        "## Species output counts",
        "",
        "| Species | Atlas layers | Country outputs | Locality artifact shipped | Nordic lead count |",
        "| --- | ---: | ---: | --- | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['species_latin_name']} | {row['atlas_layer_count']} | "
            f"{row['country_output_count']} | "
            f"{str(row['normalized_locality_artifact_present']).lower()} | "
            f"{row['nordic_unmapped_lead_count']} |"
        )
    lines.append("")
    if atlas_layer_total == 0 and country_output_total == 0:
        lines.extend(
            [
                "The current public report tree still ships no mapped non-human animal atlas "
                "layers or country bundles. The species rows above stay zero until those "
                "artifacts become real tracked report outputs.",
                "",
            ]
        )
    elif country_output_total == 0:
        lines.extend(
            [
                f"The current public report tree now ships `{atlas_layer_total}` mapped "
                "non-human animal atlas layer rows across the species table above. "
                "Country-bundle animal outputs remain zero until those country surfaces "
                "become real tracked report outputs.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                f"The current public report tree now ships `{atlas_layer_total}` mapped "
                "non-human animal atlas layer rows and "
                f"`{country_output_total}` country-resolved animal output hits across the "
                "species table above.",
                "",
            ]
        )
    return "\n".join(lines)


def render_coordinate_confidence_scale_markdown() -> str:
    """Render the reader-visible animal coordinate confidence scale."""
    return "\n".join(
        [
            "# Coordinate confidence scale",
            "",
            "- `exact`: direct published coordinates or explicit archive coordinate pairs.",
            "- `approximate`: named-place geocoding where the place is explicit but the archived source does not ship the exact point pair.",
            "- `inferred`: indirect coordinate derivation retained only for non-public internal context.",
            "- `withheld`: the repository refuses point-level mapping because the current geography is unresolved or region-only.",
            "- `unknown`: legacy or foreign records where the confidence basis is not yet normalized.",
            "",
            "Animal point publication is currently allowed only for rows whose coordinate provenance keeps an explicit basis and whose mapping posture is `mappable_point`.",
        ]
    )


def render_coordinate_caveat_surface_markdown(payload: dict[str, object]) -> str:
    """Render grouped animal coordinate caveats as reader-facing markdown."""
    lines = [
        "# Coordinate caveat surface",
        "",
        f"- Direct-coordinate points: `{len(payload['direct_coordinates'])}`",
        f"- Place-name resolved points: `{len(payload['place_name_resolution'])}`",
        f"- Still-weak geography rows: `{len(payload['still_weak_geography'])}`",
        "",
        "## Direct-coordinate points",
        "",
        "| Species | Project | Site | Basis | Confidence |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in payload["direct_coordinates"]:
        lines.append(
            f"| {row['species_latin_name']} | {row['project_accession']} | "
            f"{row['site_label']} | {row['coordinate_basis']} | {row['coordinate_confidence']} |"
        )
    lines.extend(
        [
            "",
            "## Place-name resolved points",
            "",
            "| Species | Project | Site | Basis | Confidence |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in payload["place_name_resolution"]:
        lines.append(
            f"| {row['species_latin_name']} | {row['project_accession']} | "
            f"{row['site_label']} | {row['coordinate_basis']} | {row['coordinate_confidence']} |"
        )
    lines.extend(
        [
            "",
            "## Still-weak geography",
            "",
            "| Species | Project | Original place text | Resolved place | Posture |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in payload["still_weak_geography"]:
        lines.append(
            f"| {row['species_latin_name']} | {row['project_accession']} | "
            f"{row['original_place_text']} | {row['resolved_place_text']} | "
            f"{row['mapping_posture']} |"
        )
    return "\n".join(lines)


def render_csv_rows(rows: tuple[dict[str, object], ...]) -> str:
    """Render homogeneous dict rows as CSV."""
    if not rows:
        return ""
    fieldnames = tuple(rows[0].keys())
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {
                key: _csv_value(value)
                for key, value in row.items()
            }
        )
    return buffer.getvalue()


def _build_species_coverage_row(
    *,
    data_root: Path,
    report_root: Path,
    species_name: str,
) -> dict[str, object]:
    from .species import resolve_species_definition

    species = resolve_species_definition(species_name)
    species_root = adna_species_root(data_root, species_name)
    context_rows = [
        resolve_project_context(project)
        for project in build_archive_project_catalog()
        if project.species_latin_name == species.latin_name
    ]
    country_output_count = _country_output_count(
        report_root,
        species.latin_name,
        species.common_name,
    )
    atlas_layer_count = _atlas_layer_count(
        report_root / "nordic-atlas",
        species.latin_name,
        species.common_name,
    )
    return {
        "species_latin_name": species.latin_name,
        "species_common_name": species.common_name,
        "raw_inventory_present": (species_root / "raw" / "archive_inventory.csv").is_file(),
        "raw_source_snapshot_present": (
            species_root / "raw" / "source_snapshot.json"
        ).is_file(),
        "citation_manifest_present": (
            species_root / "manifests" / "citation_manifest.csv"
        ).is_file(),
        "normalized_project_summary_present": (
            species_root / "normalized" / "project_summaries.csv"
        ).is_file(),
        "coordinate_provenance_present": (
            species_root / "normalized" / "coordinate_provenance.csv"
        ).is_file(),
        "normalized_locality_artifact_present": (
            species_root / "normalized" / "locality_summaries.csv"
        ).is_file(),
        "review_markdown_present": (species_root / "review" / "species_review.md").is_file(),
        "review_json_present": (species_root / "review" / "species_review.json").is_file(),
        "country_output_count": country_output_count,
        "atlas_layer_count": atlas_layer_count,
        "map_ready_sample_count": _count_sample_rows_by_mapping_posture(
            species_root,
            "mappable_point",
        ),
        "region_refused_sample_count": _count_sample_rows_by_mapping_posture(
            species_root,
            "refused_region_only",
        ),
        "unresolved_sample_count": sum(
            1
            for sample in _load_sample_rows(species_root)
            if str(sample.get("inclusion_status", "")) == "sample_context_blocked"
        ),
        "nordic_unmapped_lead_count": sum(
            1 for row in context_rows if row.nordic_relevance == "nordic_relevant_unmapped"
        ),
    }


def _build_species_map_readiness_row(data_root: Path, species_name: str) -> dict[str, object]:
    from .species import resolve_species_definition

    species = resolve_species_definition(species_name)
    species_root = _species_root(data_root, species_name)
    provenance_rows = _load_coordinate_provenance_rows(species_root)
    direct_coordinate_backed = sum(
        1
        for row in provenance_rows
        if str(row.get("mapping_posture", "")) == "mappable_point"
        and str(row.get("coordinate_basis", "")) in {
            "direct_published_coordinates",
            "supplementary_table_coordinates",
            "archive_coordinates",
        }
    )
    indirectly_geocoded = sum(
        1
        for row in provenance_rows
        if str(row.get("mapping_posture", "")) == "mappable_point"
        and str(row.get("coordinate_basis", "")) == "named_site_geocoding"
    )
    unresolved = sum(
        1
        for sample in _load_sample_rows(species_root)
        if str(sample.get("inclusion_status", "")) == "sample_context_blocked"
    )
    refused_from_mapping = sum(
        1
        for row in provenance_rows
        if str(row.get("mapping_posture", "")) == "refused_region_only"
    )
    return {
        "species_latin_name": species.latin_name,
        "species_common_name": species.common_name,
        "direct_coordinate_backed": direct_coordinate_backed,
        "indirectly_geocoded": indirectly_geocoded,
        "unresolved": unresolved,
        "refused_from_mapping": refused_from_mapping,
    }


def _species_root(data_root: Path, species_name: str) -> Path:
    return adna_species_root(Path(data_root), species_name)


def _load_sample_rows(species_root: Path) -> list[dict[str, object]]:
    path = species_root / "normalized" / "sample_records.json"
    if not path.is_file():
        return []
    payload = json.loads(
        path.read_text(encoding="utf-8")
    )
    rows = payload.get("samples", [])
    return [row for row in rows if isinstance(row, dict)]


def _load_coordinate_provenance_rows(species_root: Path) -> list[dict[str, object]]:
    path = species_root / "normalized" / "coordinate_provenance.json"
    if not path.is_file():
        return []
    payload = json.loads(
        path.read_text(encoding="utf-8")
    )
    rows = payload.get("coordinate_provenance", [])
    return [row for row in rows if isinstance(row, dict)]


def _count_sample_rows_by_mapping_posture(species_root: Path, mapping_posture: str) -> int:
    return sum(
        1
        for row in _load_coordinate_provenance_rows(species_root)
        if str(row.get("mapping_posture", "")) == mapping_posture
    )


def _species_output_count(
    root: Path,
    latin_name: str,
    common_name: str,
) -> int:
    if not root.exists():
        return 0
    del common_name
    latin_token = latin_name.casefold()
    explicit_markers = (
        "species_latin_name",
        "species_common_name",
        "support_class",
        "nordic_relevance",
    )
    matches = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.name in {
            "animal_output_audit.json",
            "animal_output_audit.md",
            "published_reports_summary.json",
        }:
            continue
        if path.suffix.lower() not in {".json", ".md", ".csv", ".geojson", ".html"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").casefold()
        if latin_token in text and any(marker in text for marker in explicit_markers):
            matches += 1
    return matches


def _country_output_count(
    report_root: Path,
    latin_name: str,
    common_name: str,
) -> int:
    if not report_root.exists():
        return 0
    return sum(
        1
        for path in report_root.iterdir()
        if path.is_dir()
        and path.name not in {"nordic-atlas", "_map_assets"}
        and _species_output_count(path, latin_name, common_name) > 0
    )


def _atlas_layer_count(
    atlas_root: Path,
    latin_name: str,
    common_name: str,
) -> int:
    summary_path = atlas_root / "nordic-atlas_summary.json"
    if summary_path.is_file():
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
        animal_atlas = payload.get("animal_atlas", {})
        if isinstance(animal_atlas, dict):
            species_layers = animal_atlas.get("species_layers", [])
            if isinstance(species_layers, list):
                for row in species_layers:
                    if not isinstance(row, dict):
                        continue
                    if str(row.get("latin_name", "")).strip() == latin_name:
                        return int(row.get("locality_count", 0) or 0)
    return _species_output_count(atlas_root, latin_name, common_name)


def _csv_value(value: object) -> object:
    if isinstance(value, (list, tuple)):
        return ";".join(str(item) for item in value)
    if isinstance(value, bool):
        return str(value).lower()
    return value
