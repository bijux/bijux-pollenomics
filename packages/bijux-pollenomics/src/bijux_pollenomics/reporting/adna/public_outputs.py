from __future__ import annotations

import json
from pathlib import Path

from ...adna.catalogs import (
    build_cross_species_map_readiness,
    build_public_animal_output_honesty,
)
from ...adna.paths import adna_species_dir
from .atlas_evidence_rows import build_tracked_animal_atlas_evidence_rows
from ..models import CountryReport

__all__ = ["publish_public_animal_reporting_outputs"]


def publish_public_animal_reporting_outputs(
    output_root: Path,
    *,
    data_root: Path,
    country_reports: tuple[CountryReport, ...],
    country_output_dirs: tuple[Path, ...],
    atlas_output_dir: Path,
) -> dict[str, str]:
    """Write public cross-country animal reporting outputs from generated bundles."""
    country_payloads = _load_country_payloads(country_reports, country_output_dirs)
    coverage_payload = _build_country_species_coverage(country_payloads)
    honesty_payload = build_public_animal_output_honesty(Path(data_root), output_root)
    human_overlap_payload = _build_animal_human_chronology_overlap(
        country_payloads, country_reports
    )
    pollen_overlap_payload = _build_animal_pollen_chronology_overlap(
        country_payloads, atlas_output_dir
    )
    first_appearance_payload = _build_first_appearance_by_country(country_payloads)
    atlas_readiness_payload = _build_animal_atlas_readiness(
        Path(data_root),
        country_payloads,
    )
    atlas_exclusion_payload = _build_animal_atlas_exclusion_report(Path(data_root))
    scenario_payload = _build_farming_history_scenario(
        coverage_payload=coverage_payload,
        human_overlap_payload=human_overlap_payload,
        pollen_overlap_payload=pollen_overlap_payload,
        first_appearance_payload=first_appearance_payload,
    )

    artifact_payloads = {
        "animal_country_species_coverage": coverage_payload,
        "animal_output_honesty": honesty_payload,
        "animal_human_chronology_overlap": human_overlap_payload,
        "animal_pollen_chronology_overlap": pollen_overlap_payload,
        "animal_first_appearance_by_country": first_appearance_payload,
        "animal_atlas_readiness": atlas_readiness_payload,
        "animal_atlas_exclusion_report": atlas_exclusion_payload,
        "nordic_farming_history_scenario": scenario_payload,
    }
    for stem, payload in artifact_payloads.items():
        (output_root / f"{stem}.json").write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )
    (output_root / "animal_country_species_coverage.md").write_text(
        _render_country_species_coverage_markdown(coverage_payload),
        encoding="utf-8",
    )
    (output_root / "animal_output_honesty.md").write_text(
        _render_output_honesty_markdown(honesty_payload),
        encoding="utf-8",
    )
    (output_root / "animal_human_chronology_overlap.md").write_text(
        _render_human_overlap_markdown(human_overlap_payload),
        encoding="utf-8",
    )
    (output_root / "animal_pollen_chronology_overlap.md").write_text(
        _render_pollen_overlap_markdown(pollen_overlap_payload),
        encoding="utf-8",
    )
    (output_root / "animal_first_appearance_by_country.md").write_text(
        _render_first_appearance_markdown(first_appearance_payload),
        encoding="utf-8",
    )
    (output_root / "animal_atlas_readiness.md").write_text(
        _render_animal_atlas_readiness_markdown(atlas_readiness_payload),
        encoding="utf-8",
    )
    (output_root / "animal_atlas_exclusion_report.md").write_text(
        _render_animal_atlas_exclusion_report_markdown(atlas_exclusion_payload),
        encoding="utf-8",
    )
    (output_root / "nordic_farming_history_scenario.md").write_text(
        _render_scenario_markdown(scenario_payload),
        encoding="utf-8",
    )
    return {
        "animal_country_species_coverage_json": "animal_country_species_coverage.json",
        "animal_country_species_coverage_markdown": "animal_country_species_coverage.md",
        "animal_output_honesty_json": "animal_output_honesty.json",
        "animal_output_honesty_markdown": "animal_output_honesty.md",
        "animal_human_chronology_overlap_json": "animal_human_chronology_overlap.json",
        "animal_human_chronology_overlap_markdown": "animal_human_chronology_overlap.md",
        "animal_pollen_chronology_overlap_json": "animal_pollen_chronology_overlap.json",
        "animal_pollen_chronology_overlap_markdown": "animal_pollen_chronology_overlap.md",
        "animal_first_appearance_by_country_json": "animal_first_appearance_by_country.json",
        "animal_first_appearance_by_country_markdown": "animal_first_appearance_by_country.md",
        "animal_atlas_readiness_json": "animal_atlas_readiness.json",
        "animal_atlas_readiness_markdown": "animal_atlas_readiness.md",
        "animal_atlas_exclusion_report_json": "animal_atlas_exclusion_report.json",
        "animal_atlas_exclusion_report_markdown": "animal_atlas_exclusion_report.md",
        "nordic_farming_history_scenario_json": "nordic_farming_history_scenario.json",
        "nordic_farming_history_scenario_markdown": "nordic_farming_history_scenario.md",
    }


def _load_country_payloads(
    country_reports: tuple[CountryReport, ...],
    country_output_dirs: tuple[Path, ...],
) -> list[dict[str, object]]:
    by_dir = {path.name: path for path in country_output_dirs}
    payloads: list[dict[str, object]] = []
    for report in country_reports:
        country_dir = by_dir.get(report.output_dir.name)
        if country_dir is None:
            continue
        summary_path = country_dir / f"{country_dir.name}_animal_adna_{report.version}_summary.json"
        if not summary_path.is_file():
            continue
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            payloads.append(payload)
    return payloads


def _build_country_species_coverage(
    country_payloads: list[dict[str, object]],
) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for payload in country_payloads:
        sample_rows = payload.get("sample_rows", [])
        if not isinstance(sample_rows, list):
            sample_rows = []
        sample_counts: dict[str, int] = {}
        direct_counts: dict[str, int] = {}
        geocoded_counts: dict[str, int] = {}
        unresolved_counts: dict[str, int] = {}
        sample_lineage_counts: dict[str, int] = {}
        site_evidence_counts: dict[str, int] = {}
        chronology_provenance_counts: dict[str, int] = {}
        coordinate_provenance_counts: dict[str, int] = {}
        exact_coordinate_counts: dict[str, int] = {}
        approximate_coordinate_counts: dict[str, int] = {}
        for sample_row in sample_rows:
            if not isinstance(sample_row, dict):
                continue
            species_name = str(sample_row.get("species_latin_name", ""))
            if not species_name:
                continue
            sample_counts[species_name] = sample_counts.get(species_name, 0) + 1
            if str(sample_row.get("sample_lineage_path", "")).strip():
                sample_lineage_counts[species_name] = (
                    sample_lineage_counts.get(species_name, 0) + 1
                )
            if str(sample_row.get("site_evidence_path", "")).strip():
                site_evidence_counts[species_name] = (
                    site_evidence_counts.get(species_name, 0) + 1
                )
            if str(sample_row.get("chronology_provenance_path", "")).strip():
                chronology_provenance_counts[species_name] = (
                    chronology_provenance_counts.get(species_name, 0) + 1
                )
            if str(sample_row.get("coordinate_provenance_path", "")).strip():
                coordinate_provenance_counts[species_name] = (
                    coordinate_provenance_counts.get(species_name, 0) + 1
                )
            coordinate_basis = str(sample_row.get("coordinate_basis", ""))
            if coordinate_basis in {
                "direct_published_coordinates",
                "supplementary_table_coordinates",
                "archive_coordinates",
            }:
                direct_counts[species_name] = direct_counts.get(species_name, 0) + 1
            if coordinate_basis in {"named_site_geocoding", "named_site_geocoded"}:
                geocoded_counts[species_name] = geocoded_counts.get(species_name, 0) + 1
            coordinate_confidence = str(sample_row.get("coordinate_confidence", ""))
            if coordinate_confidence == "exact":
                exact_coordinate_counts[species_name] = (
                    exact_coordinate_counts.get(species_name, 0) + 1
                )
            if coordinate_confidence in {"approximate", "inferred"}:
                approximate_coordinate_counts[species_name] = (
                    approximate_coordinate_counts.get(species_name, 0) + 1
                )
            if str(sample_row.get("inclusion_status", "")) == "sample_context_blocked":
                unresolved_counts[species_name] = (
                    unresolved_counts.get(species_name, 0) + 1
                )
        for row in payload.get("species_rows", []):
            if not isinstance(row, dict):
                continue
            species_name = str(row.get("species_latin_name", ""))
            rows.append(
                {
                    **row,
                    "sample_row_count": sample_counts.get(species_name, 0),
                    "direct_coordinate_site_count": direct_counts.get(species_name, 0),
                    "geocoded_site_count": geocoded_counts.get(species_name, 0),
                    "unresolved_sample_count": unresolved_counts.get(species_name, 0),
                    "sample_lineage_backed_sample_count": sample_lineage_counts.get(
                        species_name, 0
                    ),
                    "site_evidence_backed_sample_count": site_evidence_counts.get(
                        species_name, 0
                    ),
                    "chronology_provenance_backed_sample_count": (
                        chronology_provenance_counts.get(species_name, 0)
                    ),
                    "coordinate_provenance_backed_sample_count": (
                        coordinate_provenance_counts.get(species_name, 0)
                    ),
                    "exact_coordinate_sample_count": exact_coordinate_counts.get(
                        species_name, 0
                    ),
                    "approximate_coordinate_sample_count": (
                        approximate_coordinate_counts.get(species_name, 0)
                    ),
                }
            )
    rows.sort(key=lambda row: (str(row["country"]), str(row["species_latin_name"])))
    return {
        "schema_version": "animal-country-species-coverage.v1",
        "rows": rows,
    }


def _build_animal_human_chronology_overlap(
    country_payloads: list[dict[str, object]],
    country_reports: tuple[CountryReport, ...],
) -> dict[str, object]:
    report_by_country = {report.country: report for report in country_reports}
    rows: list[dict[str, object]] = []
    for payload in country_payloads:
        country = str(payload.get("country", ""))
        report = report_by_country.get(country)
        if report is None:
            continue
        localities = payload.get("localities", [])
        if not isinstance(localities, list):
            continue
        grouped: dict[str, list[dict[str, object]]] = {}
        for row in localities:
            if not isinstance(row, dict):
                continue
            grouped.setdefault(str(row["species_latin_name"]), []).append(row)
        for species_name, species_rows in sorted(grouped.items()):
            overlapping = 0
            non_overlapping = 0
            noncomparable = 0
            for human_locality in report.localities:
                matched = False
                comparable = False
                for row in species_rows:
                    animal_interval = _interval_from_row(row)
                    human_interval = _interval_from_record(human_locality)
                    if animal_interval is None or human_interval is None:
                        continue
                    comparable = True
                    if _intervals_overlap(animal_interval, human_interval):
                        matched = True
                        break
                if matched:
                    overlapping += 1
                elif comparable:
                    non_overlapping += 1
                else:
                    noncomparable += 1
            rows.append(
                {
                    "country": country,
                    "species_latin_name": species_name,
                    "species_common_name": str(species_rows[0]["species_common_name"]),
                    "animal_scope": str(species_rows[0]["animal_scope"]),
                    "animal_locality_count": len(species_rows),
                    "human_locality_count": len(report.localities),
                    "overlapping_human_localities": overlapping,
                    "non_overlapping_human_localities": non_overlapping,
                    "noncomparable_human_localities": noncomparable,
                    "assignment_confidence": str(species_rows[0]["country_assignment_confidence"]),
                    "overlap_status": _overlap_status(overlapping, non_overlapping, noncomparable),
                }
            )
    return {
        "schema_version": "animal-human-chronology-overlap.v1",
        "rows": rows,
    }


def _build_animal_pollen_chronology_overlap(
    country_payloads: list[dict[str, object]],
    atlas_output_dir: Path,
) -> dict[str, object]:
    pollen_records = _load_pollen_records(atlas_output_dir)
    rows: list[dict[str, object]] = []
    for payload in country_payloads:
        country = str(payload.get("country", ""))
        localities = payload.get("localities", [])
        if not isinstance(localities, list):
            continue
        grouped: dict[str, list[dict[str, object]]] = {}
        for row in localities:
            if not isinstance(row, dict):
                continue
            grouped.setdefault(str(row["species_latin_name"]), []).append(row)
        country_pollen = [row for row in pollen_records if row["country"] == country]
        for species_name, species_rows in sorted(grouped.items()):
            overlapping = 0
            non_overlapping = 0
            noncomparable = 0
            for pollen_row in country_pollen:
                matched = False
                comparable = False
                pollen_interval = _interval_from_row(pollen_row)
                for row in species_rows:
                    animal_interval = _interval_from_row(row)
                    if animal_interval is None or pollen_interval is None:
                        continue
                    comparable = True
                    if _intervals_overlap(animal_interval, pollen_interval):
                        matched = True
                        break
                if matched:
                    overlapping += 1
                elif comparable:
                    non_overlapping += 1
                else:
                    noncomparable += 1
            rows.append(
                {
                    "country": country,
                    "species_latin_name": species_name,
                    "species_common_name": str(species_rows[0]["species_common_name"]),
                    "animal_scope": str(species_rows[0]["animal_scope"]),
                    "animal_locality_count": len(species_rows),
                    "pollen_record_count": len(country_pollen),
                    "overlapping_pollen_records": overlapping,
                    "non_overlapping_pollen_records": non_overlapping,
                    "noncomparable_pollen_records": noncomparable,
                    "assignment_confidence": str(species_rows[0]["country_assignment_confidence"]),
                    "overlap_status": _overlap_status(overlapping, non_overlapping, noncomparable),
                }
            )
    return {
        "schema_version": "animal-pollen-chronology-overlap.v1",
        "rows": rows,
    }


def _build_first_appearance_by_country(
    country_payloads: list[dict[str, object]],
) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for payload in country_payloads:
        country = str(payload.get("country", ""))
        localities = payload.get("localities", [])
        if not isinstance(localities, list):
            continue
        grouped: dict[str, list[dict[str, object]]] = {}
        for row in localities:
            if not isinstance(row, dict):
                continue
            grouped.setdefault(str(row["species_latin_name"]), []).append(row)
        for species_name, species_rows in sorted(grouped.items()):
            oldest_row = max(species_rows, key=_first_signal_bp)
            rows.append(
                {
                    "country": country,
                    "species_latin_name": species_name,
                    "species_common_name": str(oldest_row["species_common_name"]),
                    "animal_scope": str(oldest_row["animal_scope"]),
                    "first_signal_bp": _first_signal_bp(oldest_row),
                    "time_label": str(oldest_row["time_label"]),
                    "project_accession": str(oldest_row["project_accession"]),
                    "locality": str(oldest_row["locality"]),
                    "assignment_confidence": str(oldest_row["country_assignment_confidence"]),
                }
            )
    rows.sort(key=lambda row: (row["country"], -int(row["first_signal_bp"]), row["species_latin_name"]))
    return {
        "schema_version": "animal-first-appearance-by-country.v1",
        "rows": rows,
    }


def _build_farming_history_scenario(
    *,
    coverage_payload: dict[str, object],
    human_overlap_payload: dict[str, object],
    pollen_overlap_payload: dict[str, object],
    first_appearance_payload: dict[str, object],
) -> dict[str, object]:
    coverage_rows = [row for row in coverage_payload.get("rows", []) if isinstance(row, dict)]
    human_rows = [row for row in human_overlap_payload.get("rows", []) if isinstance(row, dict)]
    pollen_rows = [row for row in pollen_overlap_payload.get("rows", []) if isinstance(row, dict)]
    first_rows = [row for row in first_appearance_payload.get("rows", []) if isinstance(row, dict)]

    support: list[str] = []
    weak_support: list[str] = []
    non_support: list[str] = []

    if first_rows:
        earliest = first_rows[0]
        support.append(
            f"The current Nordic publication surface can now name one first animal signal: "
            f"`{earliest['species_latin_name']}` in `{earliest['country']}` with a tracked "
            f"window of `{earliest['time_label']}` from `{earliest['project_accession']}`."
        )
    for row in coverage_rows:
        if str(row.get("assignment_confidence")) == "regional_projection":
            weak_support.append(
                f"`{row['species_latin_name']}` contributes `{row['country']}` evidence only "
                "through a regional projection, not a country-exact excavation label."
            )
        if str(row.get("animal_scope")) == "comparator":
            weak_support.append(
                f"`{row['species_latin_name']}` remains comparator-only in `{row['country']}` "
                "and cannot be promoted into domesticated-core farming support."
            )
    represented_species = {str(row["species_latin_name"]) for row in coverage_rows}
    for species_name in (
        "Equus caballus",
        "Sus scrofa domesticus",
        "Bos taurus",
        "Capra hircus",
        "Canis lupus familiaris",
        "Felis catus",
        "Camelus dromedarius",
        "Equus asinus",
    ):
        if species_name not in represented_species:
            non_support.append(
                f"The shipped Nordic country outputs still do not support a country-localized "
                f"claim for `{species_name}`."
            )
    if not support:
        support.append(
            "The repo now has a real country-resolved animal publication surface, but it "
            "still supports only a narrow set of Nordic-facing claims."
        )
    return {
        "schema_version": "nordic-farming-history-scenario.v1",
        "question": (
            "What does the currently shipped Nordic animal aDNA surface actually support "
            "about early farming history?"
        ),
        "support_statements": support,
        "weak_support_statements": _deduplicate_lines(weak_support),
        "non_support_statements": _deduplicate_lines(non_support),
        "evidence_anchors": {
            "country_species_coverage_rows": len(coverage_rows),
            "animal_human_overlap_rows": len(human_rows),
            "animal_pollen_overlap_rows": len(pollen_rows),
            "first_appearance_rows": len(first_rows),
        },
    }


def _build_animal_atlas_readiness(
    data_root: Path,
    country_payloads: list[dict[str, object]],
) -> dict[str, object]:
    readiness_payload = build_cross_species_map_readiness(Path(data_root))
    honesty_payload = build_public_animal_output_honesty(Path(data_root), Path(data_root) / "__no_report_root__")
    mapped_sample_ids_by_species = _mapped_sample_ids_by_species(Path(data_root))
    candidate_rows_by_species = _candidate_rows_by_species(Path(data_root))
    rows = []
    country_counts: dict[str, dict[str, int]] = {}
    for payload in country_payloads:
        country = str(payload.get("country", ""))
        for row in payload.get("species_rows", []):
            if not isinstance(row, dict):
                continue
            species_name = str(row.get("species_latin_name", ""))
            if not species_name:
                continue
            species_counts = country_counts.setdefault(species_name, {})
            species_counts[country] = int(row.get("mapped_locality_count", 0) or 0)
    for row in readiness_payload.get("rows", []):
        if not isinstance(row, dict):
            continue
        species_name = str(row.get("species_latin_name", ""))
        direct_count = int(row.get("direct_coordinate_backed", 0) or 0)
        geocoded_count = int(row.get("indirectly_geocoded", 0) or 0)
        unresolved_count = int(row.get("unresolved", 0) or 0)
        refused_count = int(row.get("refused_from_mapping", 0) or 0)
        map_ready_count = direct_count + geocoded_count
        total_curated = map_ready_count + unresolved_count + refused_count
        honesty_row = next(
            (
                item
                for item in honesty_payload.get("rows", [])
                if isinstance(item, dict)
                and str(item.get("species_latin_name", "")) == species_name
            ),
            {},
        )
        candidate_point_count = len(candidate_rows_by_species.get(species_name, []))
        mapped_sample_count = len(mapped_sample_ids_by_species.get(species_name, set()))
        blocked_sample_count = int(honesty_row.get("blocked_sample_count", 0) or 0)
        readiness_status, status_reason = _atlas_readiness_status(
            candidate_point_count=candidate_point_count,
            mapped_sample_count=mapped_sample_count,
            blocked_sample_count=blocked_sample_count,
            unresolved_count=unresolved_count,
            refused_count=refused_count,
        )
        rows.append(
            {
                **row,
                "candidate_point_count": candidate_point_count,
                "mapped_sample_count": mapped_sample_count,
                "blocked_sample_count": blocked_sample_count,
                "map_ready_count": map_ready_count,
                "total_curated_rows": total_curated,
                "map_ready_share": (
                    round(map_ready_count / total_curated, 4) if total_curated else 0.0
                ),
                "readiness_status": readiness_status,
                "status_reason": status_reason,
                "country_mapped_locality_counts": country_counts.get(
                    species_name,
                    {},
                ),
            }
        )
    status_counts: dict[str, int] = {}
    for row in rows:
        status = str(row.get("readiness_status", ""))
        status_counts[status] = status_counts.get(status, 0) + 1
    return {
        "schema_version": "animal-atlas-readiness.v1",
        "status_counts": status_counts,
        "rows": rows,
    }


def _build_animal_atlas_exclusion_report(data_root: Path) -> dict[str, object]:
    mapped_sample_ids_by_species = _mapped_sample_ids_by_species(Path(data_root))
    rows = []
    species_dir = adna_species_dir(Path(data_root))
    if not species_dir.is_dir():
        return {
            "schema_version": "animal-atlas-exclusion-report.v1",
            "row_count": 0,
            "rows": [],
        }
    for species_root in sorted(path for path in species_dir.iterdir() if path.is_dir()):
        if species_root.name == "homo_sapiens":
            continue
        provenance_lookup = _coordinate_provenance_by_project_and_locality(species_root)
        for sample_row in _load_species_sample_rows(species_root):
            species_name = str(sample_row.get("species_latin_name", "")).strip()
            sample_id = str(sample_row.get("identity", {}).get("stable_token", "")).strip()
            if not species_name or not sample_id:
                continue
            if sample_id in mapped_sample_ids_by_species.get(species_name, set()):
                continue
            locality_identity = sample_row.get("locality_identity", {})
            project_accession = str(sample_row.get("project_accession", "")).strip()
            locality_text = str(locality_identity.get("locality_text", "")).strip()
            provenance = provenance_lookup.get((project_accession, locality_text), {})
            chronology = sample_row.get("chronology", {})
            exclusion_reason = _atlas_exclusion_reason(
                sample_row=sample_row,
                provenance=provenance,
            )
            rows.append(
                {
                    "species_latin_name": species_name,
                    "species_common_name": str(sample_row.get("species_common_name", "")),
                    "project_accession": project_accession,
                    "sample_record_id": sample_id,
                    "locality": str(sample_row.get("locality") or locality_text),
                    "political_entity": str(locality_identity.get("political_entity", "")),
                    "inclusion_status": str(sample_row.get("inclusion_status", "")),
                    "inclusion_note": str(sample_row.get("inclusion_note", "")),
                    "chronology_normalization_status": str(
                        sample_row.get("chronology_normalization_status", "")
                    ),
                    "chronology_precision_posture": str(
                        chronology.get("precision_posture", "")
                    ),
                    "coordinate_basis": str(provenance.get("coordinate_basis", "")),
                    "mapping_posture": str(provenance.get("mapping_posture", "")),
                    "coordinate_confidence": str(
                        provenance.get("coordinate_confidence", "")
                    ),
                    "sample_lineage_path": str(sample_row.get("sample_lineage_path", "")),
                    "chronology_provenance_path": str(
                        sample_row.get("chronology_provenance_path", "")
                    ),
                    "coordinate_provenance_path": str(
                        provenance.get("source_artifact_path", "")
                    ),
                    "coordinate_provenance_locator": str(
                        provenance.get("source_locator", "")
                    ),
                    "exclusion_reason": exclusion_reason,
                }
            )
    rows.sort(
        key=lambda row: (
            str(row["species_latin_name"]),
            str(row["project_accession"]),
            str(row["sample_record_id"]),
        )
    )
    return {
        "schema_version": "animal-atlas-exclusion-report.v1",
        "row_count": len(rows),
        "rows": rows,
    }


def _mapped_sample_ids_by_species(data_root: Path) -> dict[str, set[str]]:
    mapped: dict[str, set[str]] = {}
    for row in build_tracked_animal_atlas_evidence_rows(Path(data_root)):
        mapped.setdefault(row.species_latin_name, set()).update(row.sample_record_ids)
    return mapped


def _candidate_rows_by_species(data_root: Path) -> dict[str, list[object]]:
    rows: dict[str, list[object]] = {}
    for row in build_tracked_animal_atlas_evidence_rows(Path(data_root)):
        rows.setdefault(row.species_latin_name, []).append(row)
    return rows


def _load_species_sample_rows(species_root: Path) -> list[dict[str, object]]:
    path = species_root / "normalized" / "sample_records.json"
    if not path.is_file():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("samples", [])
    return [row for row in rows if isinstance(row, dict)]


def _coordinate_provenance_by_project_and_locality(
    species_root: Path,
) -> dict[tuple[str, str], dict[str, object]]:
    path = species_root / "normalized" / "coordinate_provenance.json"
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("coordinate_provenance", [])
    lookup: dict[tuple[str, str], dict[str, object]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        project_accession = str(row.get("project_accession", "")).strip()
        locality_text = str(row.get("site_label", "")).strip()
        if project_accession:
            lookup[(project_accession, locality_text)] = row
    return lookup


def _atlas_readiness_status(
    *,
    candidate_point_count: int,
    mapped_sample_count: int,
    blocked_sample_count: int,
    unresolved_count: int,
    refused_count: int,
) -> tuple[str, str]:
    if candidate_point_count == 0 and (unresolved_count > 0 or refused_count > 0):
        return (
            "blocked",
            f"{blocked_sample_count} blocked sample rows still fail atlas publication.",
        )
    if candidate_point_count == 0:
        return ("absent", "No candidate point rows are currently published for this species.")
    if candidate_point_count < 5 or mapped_sample_count < 5:
        return (
            "thin",
            f"{candidate_point_count} candidate point rows remain too thin for broad atlas claims.",
        )
    return (
        "publishable",
        f"{candidate_point_count} candidate point rows now survive the current atlas contract.",
    )


def _atlas_exclusion_reason(
    *,
    sample_row: dict[str, object],
    provenance: dict[str, object],
) -> str:
    inclusion_status = str(sample_row.get("inclusion_status", "")).strip()
    mapping_posture = str(provenance.get("mapping_posture", "")).strip()
    chronology_status = str(
        sample_row.get("chronology_normalization_status", "")
    ).strip()
    if inclusion_status == "sample_context_blocked":
        return "sample locality remains unresolved and cannot be mapped honestly"
    if mapping_posture == "refused_region_only":
        return "geography remains region-only and the atlas refuses a false point"
    if chronology_status in {"unresolved", "conflict"}:
        return "chronology remains unresolved enough that the sample stays out of the public map"
    if not provenance:
        return "no coordinate provenance row currently supports point publication"
    return "sample is tracked but does not yet satisfy the full atlas point contract"


def _load_pollen_records(atlas_output_dir: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for filename in (
        "nordic_pollen_sites.geojson",
        "nordic_pollen_site_sequences.geojson",
    ):
        path = atlas_output_dir / filename
        if not path.is_file():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        for feature in payload.get("features", []):
            if not isinstance(feature, dict):
                continue
            properties = feature.get("properties", {})
            if not isinstance(properties, dict):
                continue
            records.append(
                {
                    "country": str(properties.get("country", "")),
                    "time_start_bp": _optional_int(properties.get("time_start_bp")),
                    "time_end_bp": _optional_int(properties.get("time_end_bp")),
                    "time_mean_bp": _optional_int(properties.get("time_mean_bp")),
                    "time_label": str(properties.get("time_label", "")),
                    "source": str(properties.get("source", "")),
                    "name": str(properties.get("name", "")),
                }
            )
    return records


def _interval_from_record(record: object) -> tuple[int, int] | None:
    time_start = getattr(record, "time_start_bp", None)
    time_end = getattr(record, "time_end_bp", None)
    time_mean = getattr(record, "time_mean_bp", None)
    return _normalize_interval(time_start, time_end, time_mean)


def _interval_from_row(row: dict[str, object]) -> tuple[int, int] | None:
    return _normalize_interval(
        _optional_int(row.get("time_start_bp")),
        _optional_int(row.get("time_end_bp")),
        _optional_int(row.get("time_mean_bp")),
    )


def _normalize_interval(
    time_start: int | None,
    time_end: int | None,
    time_mean: int | None,
) -> tuple[int, int] | None:
    values = [value for value in (time_start, time_end) if value is not None]
    if values:
        return (min(values), max(values))
    if time_mean is not None:
        return (time_mean, time_mean)
    return None


def _intervals_overlap(
    left: tuple[int, int],
    right: tuple[int, int],
) -> bool:
    return max(left[0], right[0]) <= min(left[1], right[1])


def _overlap_status(
    overlapping: int,
    non_overlapping: int,
    noncomparable: int,
) -> str:
    if overlapping > 0:
        return "overlap_detected"
    if non_overlapping > 0:
        return "no_overlap_detected"
    if noncomparable > 0:
        return "chronology_not_comparable"
    return "no_context_rows"


def _first_signal_bp(row: dict[str, object]) -> int:
    candidates = [
        value
        for value in (
            _optional_int(row.get("time_start_bp")),
            _optional_int(row.get("time_end_bp")),
            _optional_int(row.get("time_mean_bp")),
        )
        if value is not None
    ]
    return max(candidates) if candidates else 0


def _optional_int(value: object) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip():
        return int(value)
    return None


def _deduplicate_lines(lines: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for line in lines:
        if line in seen:
            continue
        seen.add(line)
        unique.append(line)
    return unique


def _render_country_species_coverage_markdown(payload: dict[str, object]) -> str:
    rows = [row for row in payload.get("rows", []) if isinstance(row, dict)]
    lines = [
        "# Animal country species coverage",
        "",
        "| Country | Species | Scope | Sample rows | Localities | Sample evidence | Site evidence | Chronology evidence | Coordinate evidence | Exact coordinates | Approximate coordinates | Unresolved rows | Assignment posture |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    if not rows:
        lines.append("| No country-resolved animal rows yet | - | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | - |")
    else:
        for row in rows:
            lines.append(
                f"| {row['country']} | {row['species_latin_name']} | {row['animal_scope']} | "
                f"{row['sample_row_count']} | {row['mapped_locality_count']} | "
                f"{row['sample_lineage_backed_sample_count']} | "
                f"{row['site_evidence_backed_sample_count']} | "
                f"{row['chronology_provenance_backed_sample_count']} | "
                f"{row['coordinate_provenance_backed_sample_count']} | "
                f"{row['exact_coordinate_sample_count']} | "
                f"{row['approximate_coordinate_sample_count']} | "
                f"{row['unresolved_sample_count']} | "
                f"{row['assignment_confidence']} |"
            )
    lines.append("")
    return "\n".join(lines)


def _render_human_overlap_markdown(payload: dict[str, object]) -> str:
    rows = [row for row in payload.get("rows", []) if isinstance(row, dict)]
    lines = [
        "# Animal versus human chronology overlap",
        "",
        "| Country | Species | Human localities | Overlapping | Non-overlapping | Non-comparable | Status |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    if not rows:
        lines.append("| No overlap rows | - | 0 | 0 | 0 | 0 | no_context_rows |")
    else:
        for row in rows:
            lines.append(
                f"| {row['country']} | {row['species_latin_name']} | "
                f"{row['human_locality_count']} | {row['overlapping_human_localities']} | "
                f"{row['non_overlapping_human_localities']} | {row['noncomparable_human_localities']} | "
                f"{row['overlap_status']} |"
            )
    lines.append("")
    return "\n".join(lines)


def _render_pollen_overlap_markdown(payload: dict[str, object]) -> str:
    rows = [row for row in payload.get("rows", []) if isinstance(row, dict)]
    lines = [
        "# Animal versus pollen chronology overlap",
        "",
        "| Country | Species | Pollen records | Overlapping | Non-overlapping | Non-comparable | Status |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    if not rows:
        lines.append("| No overlap rows | - | 0 | 0 | 0 | 0 | no_context_rows |")
    else:
        for row in rows:
            lines.append(
                f"| {row['country']} | {row['species_latin_name']} | "
                f"{row['pollen_record_count']} | {row['overlapping_pollen_records']} | "
                f"{row['non_overlapping_pollen_records']} | {row['noncomparable_pollen_records']} | "
                f"{row['overlap_status']} |"
            )
    lines.append("")
    return "\n".join(lines)


def _render_first_appearance_markdown(payload: dict[str, object]) -> str:
    rows = [row for row in payload.get("rows", []) if isinstance(row, dict)]
    lines = [
        "# First animal appearance by country",
        "",
        "| Country | Species | First signal BP | Source project | Assignment posture |",
        "| --- | --- | ---: | --- | --- |",
    ]
    if not rows:
        lines.append("| No first-appearance rows | - | 0 | - | - |")
    else:
        for row in rows:
            lines.append(
                f"| {row['country']} | {row['species_latin_name']} | {row['first_signal_bp']} | "
                f"{row['project_accession']} | {row['assignment_confidence']} |"
            )
    lines.append("")
    return "\n".join(lines)


def _render_animal_atlas_readiness_markdown(payload: dict[str, object]) -> str:
    rows = [row for row in payload.get("rows", []) if isinstance(row, dict)]
    lines = [
        "# Animal atlas readiness",
        "",
        f"- Status counts: `{payload.get('status_counts', {})}`",
        "",
        "| Species | Status | Candidate points | Mapped samples | Blocked samples | Unresolved rows | Region-refused rows | Map-ready share | Reason |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    if not rows:
        lines.append("| No readiness rows yet | absent | 0 | 0 | 0 | 0 | 0 | 0.0000 | no tracked sample rows |")
    else:
        for row in rows:
            lines.append(
                f"| {row['species_latin_name']} | {row['readiness_status']} | "
                f"{row['candidate_point_count']} | {row['mapped_sample_count']} | "
                f"{row['blocked_sample_count']} | {row['unresolved']} | "
                f"{row['refused_from_mapping']} | {row['map_ready_share']:.4f} | "
                f"{row['status_reason']} |"
            )
    lines.append("")
    return "\n".join(lines)


def _render_output_honesty_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Animal output honesty",
        "",
        f"- Tracked sample rows: `{payload['totals']['tracked_sample_count']}`",
        f"- Mapped sample rows: `{payload['totals']['mapped_sample_count']}`",
        f"- Blocked sample rows: `{payload['totals']['blocked_sample_count']}`",
        f"- Unresolved sample rows: `{payload['totals']['unresolved_sample_count']}`",
        "",
        "| Species | Tracked samples | Mapped samples | Blocked samples | Unresolved samples | Country-published samples | Region-refused rows |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload.get("rows", []):
        lines.append(
            f"| {row['species_latin_name']} | {row['tracked_sample_count']} | "
            f"{row['mapped_sample_count']} | {row['blocked_sample_count']} | "
            f"{row['unresolved_sample_count']} | {row['country_published_sample_count']} | "
            f"{row['region_refused_count']} |"
        )
    lines.append("")
    return "\n".join(lines)


def _render_animal_atlas_exclusion_report_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Animal atlas exclusion report",
        "",
        f"- Excluded tracked sample rows: `{payload['row_count']}`",
        "",
        "| Species | Project | Sample record | Locality | Inclusion status | Mapping posture | Exclusion reason |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    rows = [row for row in payload.get("rows", []) if isinstance(row, dict)]
    if not rows:
        lines.append("| No excluded rows | - | - | - | - | - | - |")
    else:
        for row in rows:
            lines.append(
                f"| {row['species_latin_name']} | {row['project_accession']} | "
                f"{row['sample_record_id']} | {row['locality']} | "
                f"{row['inclusion_status']} | {row['mapping_posture']} | "
                f"{row['exclusion_reason']} |"
            )
    lines.append("")
    return "\n".join(lines)


def _render_scenario_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Nordic farming history scenario",
        "",
        payload["question"],
        "",
        "## Support",
        "",
    ]
    lines.extend(f"- {line}" for line in payload.get("support_statements", []))
    lines.extend(["", "## Weak support", ""])
    lines.extend(f"- {line}" for line in payload.get("weak_support_statements", []))
    lines.extend(["", "## Non-support", ""])
    lines.extend(f"- {line}" for line in payload.get("non_support_statements", []))
    lines.append("")
    return "\n".join(lines)
