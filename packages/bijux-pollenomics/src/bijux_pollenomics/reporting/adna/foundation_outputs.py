from __future__ import annotations

import json
from pathlib import Path

from ...adna.catalogs import (
    build_cross_species_map_readiness,
    build_overbroad_site_ledger,
    build_unresolved_site_ledger,
)
from ...adna.ena import build_archive_project_catalog
from ...adna.paths import adna_species_dir
from ...adna.project_sample_chronology import (
    ADNA_CHRONOLOGY_EVIDENCE_CLASSES,
    ADNA_CHRONOLOGY_NORMALIZATION_STATUSES,
    ADNA_CHRONOLOGY_PRECISION_POSTURES,
    ADNA_CHRONOLOGY_STRENGTHS,
    build_sample_chronology_viewer_rows,
)
from ...adna.project_sample_locality_evidence import (
    build_project_locality_completeness_rows,
    build_project_locality_substitution_ledger,
    build_sample_locality_conflict_ledger,
    build_sample_locality_manual_curation_workflow_rows,
    build_site_name_normalization_dictionary_rows,
)
from ...adna.project_sample_sites import (
    ADNA_LOCALITY_RESOLUTION_STATUSES,
    build_project_sample_site_rows,
)
from ...adna.sample_truth import build_project_locality_count_drift
from ...adna.source_library import (
    build_cross_project_source_audit,
    build_paper_registry,
    build_project_registry,
    build_project_source_bundles,
    build_supplement_registry,
)
from .atlas_evidence_rows import build_tracked_animal_atlas_evidence_rows

__all__ = ["publish_animal_foundation_outputs"]


def publish_animal_foundation_outputs(
    output_root: Path,
    *,
    data_root: Path,
    docs_root: Path,
) -> dict[str, str]:
    """Publish outsider-facing scientific foundation artifacts for animal aDNA outputs."""
    output_root = Path(output_root)
    data_root = Path(data_root)
    docs_root = Path(docs_root)

    validation_payload = build_animal_foundation_validation_report(
        data_root=data_root,
        report_root=output_root,
    )
    drift_payload = build_animal_cross_surface_drift_report(
        data_root=data_root,
        report_root=output_root,
    )
    caveat_payload = build_animal_scientific_caveat_ledger(data_root)
    point_payload = build_animal_point_support_packets(
        data_root=data_root,
        report_root=output_root,
    )
    absence_payload = build_animal_project_absence_packets(
        data_root=data_root,
        report_root=output_root,
    )
    review_payload = build_animal_foundation_review_packet(
        data_root=data_root,
        report_root=output_root,
        validation_payload=validation_payload,
        drift_payload=drift_payload,
        caveat_payload=caveat_payload,
        point_payload=point_payload,
        absence_payload=absence_payload,
    )
    chronology_viewer_payload = build_animal_sample_chronology_viewer(data_root=data_root)
    sample_database_review_payload = build_animal_sample_database_review(
        data_root=data_root,
        report_root=output_root,
        point_payload=point_payload,
        review_payload=review_payload,
    )
    release_gate_payload = build_animal_publication_release_gate(
        data_root=data_root,
        report_root=output_root,
        docs_root=docs_root,
        point_payload=point_payload,
        review_payload=review_payload,
        sample_database_review_payload=sample_database_review_payload,
    )

    payloads = {
        "animal_foundation_validation": (
            validation_payload,
            render_animal_foundation_validation_markdown(validation_payload),
        ),
        "animal_cross_surface_drift": (
            drift_payload,
            render_animal_cross_surface_drift_markdown(drift_payload),
        ),
        "animal_scientific_caveat_ledger": (
            caveat_payload,
            render_animal_scientific_caveat_ledger_markdown(caveat_payload),
        ),
        "animal_point_support_packets": (
            point_payload,
            render_animal_point_support_packets_markdown(point_payload),
        ),
        "animal_project_absence_packets": (
            absence_payload,
            render_animal_project_absence_packets_markdown(absence_payload),
        ),
        "animal_foundation_review": (
            review_payload,
            render_animal_foundation_review_markdown(review_payload),
        ),
        "animal_sample_chronology_viewer": (
            chronology_viewer_payload,
            render_animal_sample_chronology_viewer_markdown(chronology_viewer_payload),
        ),
        "animal_sample_database_review": (
            sample_database_review_payload,
            render_animal_sample_database_review_markdown(sample_database_review_payload),
        ),
        "animal_publication_release_gate": (
            release_gate_payload,
            render_animal_publication_release_gate_markdown(release_gate_payload),
        ),
    }
    for stem, (payload, markdown) in payloads.items():
        (output_root / f"{stem}.json").write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )
        (output_root / f"{stem}.md").write_text(markdown, encoding="utf-8")
    return {
        f"{stem}_json": f"{stem}.json" for stem in payloads
    } | {
        f"{stem}_markdown": f"{stem}.md" for stem in payloads
    }


def build_animal_foundation_validation_report(
    *,
    data_root: Path,
    report_root: Path,
) -> dict[str, object]:
    """Validate the structural scientific contract behind published animal outputs."""
    sample_rows = _load_all_sample_rows(data_root)
    site_rows = _load_all_site_evidence_rows(data_root)
    provenance_rows = _load_all_coordinate_rows(data_root)
    try:
        atlas_rows = [row.as_dict() for row in build_tracked_animal_atlas_evidence_rows(data_root)]
    except FileNotFoundError:
        atlas_rows = []
    source_bundles = build_project_source_bundles(data_root)

    sample_tokens: list[str] = []
    duplicate_sample_tokens: set[str] = set()
    for row in sample_rows:
        token = str(row.get("identity", {}).get("stable_token", "")).strip()
        if not token:
            continue
        if token in sample_tokens:
            duplicate_sample_tokens.add(token)
        sample_tokens.append(token)

    checks = [
        _check_row(
            "unique_sample_stable_ids",
            len(duplicate_sample_tokens) == 0,
            "Stable sample identifiers stay unique across all tracked animal rows.",
            sorted(duplicate_sample_tokens),
        ),
        _check_row(
            "sample_project_linkage_present",
            all(str(row.get("project_accession", "")).strip() for row in sample_rows),
            "Every curated animal sample row keeps a project accession.",
            [
                str(row.get("species_latin_name", ""))
                for row in sample_rows
                if not str(row.get("project_accession", "")).strip()
            ],
        ),
        _check_row(
            "sample_paper_linkage_present",
            all(str(row.get("paper_doi", "")).strip() for row in sample_rows),
            "Every curated animal sample row keeps a paper DOI reference.",
            [
                str(row.get("project_accession", ""))
                for row in sample_rows
                if not str(row.get("paper_doi", "")).strip()
            ],
        ),
        _check_row(
            "supplement_required_projects_archived",
            all(
                (not bundle.supplement_required)
                or bundle.supplement_download_status == "archived"
                for bundle in source_bundles
            ),
            "Projects that require supplementary material keep a local archived supplement.",
            [
                bundle.project_accession
                for bundle in source_bundles
                if bundle.supplement_required
                and bundle.supplement_download_status != "archived"
            ],
        ),
        _check_row(
            "site_evidence_keeps_source_traceability",
            all(
                str(row.get("source_artifact_path", "")).strip()
                and str(row.get("source_locator", "")).strip()
                and str(row.get("source_support_status", "")).strip()
                for row in site_rows
            ),
            "Every site-evidence row keeps source artifact, locator, and support status.",
            [
                str(row.get("project_accession", ""))
                for row in site_rows
                if not (
                    str(row.get("source_artifact_path", "")).strip()
                    and str(row.get("source_locator", "")).strip()
                    and str(row.get("source_support_status", "")).strip()
                )
            ],
        ),
        _check_row(
            "mappable_coordinates_keep_complete_basis",
            all(
                str(row.get("coordinate_basis", "")).strip()
                and str(row.get("coordinate_confidence", "")).strip()
                and str(row.get("confidence_rationale", "")).strip()
                and str(row.get("latitude_text", "")).strip()
                and str(row.get("longitude_text", "")).strip()
                for row in provenance_rows
                if str(row.get("mapping_posture", "")) == "mappable_point"
            ),
            "Every mappable coordinate row keeps basis, confidence, rationale, and text coordinates.",
            [
                str(row.get("project_accession", ""))
                for row in provenance_rows
                if str(row.get("mapping_posture", "")) == "mappable_point"
                and not (
                    str(row.get("coordinate_basis", "")).strip()
                    and str(row.get("coordinate_confidence", "")).strip()
                    and str(row.get("confidence_rationale", "")).strip()
                    and str(row.get("latitude_text", "")).strip()
                    and str(row.get("longitude_text", "")).strip()
                )
            ],
        ),
        _check_row(
            "atlas_rows_keep_traceability",
            all(
                (
                    str(row.get("feature_id", "")).strip()
                    and str(row.get("evidence_row_id", "")).strip()
                    and str(row.get("site_record_id", "")).strip()
                    and str(row.get("primary_project_accession", "")).strip()
                    and str(row.get("paper_doi", "")).strip()
                    and str(row.get("paper_url", "")).strip()
                    and bool(row.get("sample_record_ids", []))
                )
                for row in atlas_rows
            )
            ,
            "Every published animal atlas row keeps feature, project, paper, and sample traceability.",
            [
                str(row.get("feature_id", ""))
                for row in atlas_rows
                if not (
                    str(row.get("feature_id", "")).strip()
                    and str(row.get("evidence_row_id", "")).strip()
                    and str(row.get("site_record_id", "")).strip()
                    and str(row.get("primary_project_accession", "")).strip()
                    and str(row.get("paper_doi", "")).strip()
                    and str(row.get("paper_url", "")).strip()
                    and bool(row.get("sample_record_ids", []))
                )
            ],
        ),
    ]
    overall_ok = all(bool(check["passed"]) for check in checks)
    return {
        "schema_version": "animal-foundation-validation.v1",
        "overall_ok": overall_ok,
        "sample_row_count": len(sample_rows),
        "site_evidence_row_count": len(site_rows),
        "coordinate_row_count": len(provenance_rows),
        "atlas_row_count": len(atlas_rows),
        "checks": checks,
    }


def build_animal_cross_surface_drift_report(
    *,
    data_root: Path,
    report_root: Path,
) -> dict[str, object]:
    """Compare counts and traceability across normalized, atlas, and country outputs."""
    atlas_rows = [row.as_dict() for row in build_tracked_animal_atlas_evidence_rows(data_root)]
    atlas_by_species: dict[str, list[dict[str, object]]] = {}
    for row in atlas_rows:
        atlas_by_species.setdefault(str(row.get("species_latin_name", "")), []).append(row)
    country_payloads = _load_country_payloads(report_root)
    rows: list[dict[str, object]] = []
    for species_name, sample_rows in _group_sample_rows_by_species(data_root).items():
        site_rows = _group_site_rows_by_species(data_root).get(species_name, [])
        provenance_rows = _group_coordinate_rows_by_species(data_root).get(species_name, [])
        atlas_species_rows = atlas_by_species.get(species_name, [])
        country_sample_count = 0
        country_locality_count = 0
        for payload in country_payloads:
            for row in payload.get("sample_rows", []):
                if str(row.get("species_latin_name", "")) == species_name:
                    country_sample_count += 1
            for row in payload.get("localities", []):
                if str(row.get("species_latin_name", "")) == species_name:
                    country_locality_count += 1
        sample_ids = {
            str(row.get("identity", {}).get("stable_token", "")).strip()
            for row in sample_rows
            if str(row.get("identity", {}).get("stable_token", "")).strip()
        }
        provenance_projects = {
            str(row.get("project_accession", "")).strip()
            for row in provenance_rows
            if str(row.get("project_accession", "")).strip()
        }
        site_projects = {
            str(row.get("project_accession", "")).strip()
            for row in site_rows
            if str(row.get("project_accession", "")).strip()
        }
        findings: list[str] = []
        for row in atlas_species_rows:
            row_sample_ids = {
                str(item) for item in row.get("sample_record_ids", []) if str(item)
            }
            if not row_sample_ids.issubset(sample_ids):
                findings.append("atlas_rows_reference_unknown_sample_ids")
                break
        for row in atlas_species_rows:
            project = str(row.get("primary_project_accession", "")).strip()
            if project and (project not in provenance_projects or project not in site_projects):
                findings.append("atlas_rows_reference_unlinked_project_evidence")
                break
        if country_locality_count > len(atlas_species_rows):
            findings.append("country_locality_rows_exceed_shared_atlas_rows")
        atlas_sample_count = sum(int(row.get("sample_count", 0) or 0) for row in atlas_species_rows)
        if country_sample_count > atlas_sample_count:
            findings.append("country_sample_rows_exceed_shared_atlas_sample_counts")
        rows.append(
            {
                "species_latin_name": species_name,
                "normalized_sample_row_count": len(sample_rows),
                "normalized_site_evidence_count": len(site_rows),
                "normalized_coordinate_row_count": len(provenance_rows),
                "mappable_coordinate_row_count": sum(
                    1
                    for row in provenance_rows
                    if str(row.get("mapping_posture", "")) == "mappable_point"
                ),
                "atlas_evidence_row_count": len(atlas_species_rows),
                "atlas_evidence_sample_count": atlas_sample_count,
                "published_country_sample_count": country_sample_count,
                "published_country_locality_count": country_locality_count,
                "drift_detected": bool(findings),
                "findings": findings,
            }
        )
    rows.sort(key=lambda row: str(row["species_latin_name"]))
    return {
        "schema_version": "animal-cross-surface-drift.v1",
        "rows": rows,
        "drift_detected": any(bool(row["drift_detected"]) for row in rows),
    }


def build_animal_scientific_caveat_ledger(data_root: Path) -> dict[str, object]:
    """Group the current scientific weak points in the animal evidence foundation."""
    source_bundles = build_project_source_bundles(data_root)
    paper_registry = build_paper_registry(data_root)
    sample_site_rows = _load_all_project_sample_site_rows(data_root)
    unresolved_rows = build_unresolved_site_ledger(data_root)
    overbroad_rows = build_overbroad_site_ledger(data_root)
    comparator_rows = _build_comparator_only_rows(data_root)
    ambiguous_sample_site_rows = [
        row
        for row in sample_site_rows
        if str(row.get("locality_resolution_status", "")) in {
            "sample_group_site",
            "project_level_site_only",
            "region_only",
            "unresolved",
        }
    ]
    unreadable_rows = [
        {
            "paper_doi": row.paper_doi,
            "title": row.title,
            "project_accessions": list(row.project_accessions),
            "parsing_status": row.parsing_status,
        }
        for row in paper_registry
        if row.parsing_status != "ready_for_project_sample_extraction"
    ]
    missing_supplements = [
        {
            "project_accession": bundle.project_accession,
            "species_latin_name": bundle.species_latin_name,
            "paper_doi": bundle.paper_doi,
            "paper_title": bundle.paper_title,
            "blockers": list(bundle.blockers),
        }
        for bundle in source_bundles
        if bundle.supplement_required and bundle.supplement_download_status != "archived"
    ]
    return {
        "schema_version": "animal-scientific-caveat-ledger.v1",
        "summary": {
            "missing_supplement_count": len(missing_supplements),
            "unreadable_table_count": len(unreadable_rows),
            "uncertain_site_assignment_count": len(ambiguous_sample_site_rows),
            "region_only_geography_count": len(overbroad_rows),
            "comparator_only_evidence_count": len(comparator_rows),
        },
        "categories": {
            "missing_supplements": missing_supplements,
            "unreadable_tables": unreadable_rows,
            "uncertain_site_assignment": ambiguous_sample_site_rows,
            "unresolved_sample_rows": list(unresolved_rows),
            "region_only_geography": list(overbroad_rows),
            "comparator_only_evidence": comparator_rows,
        },
    }


def build_animal_point_support_packets(
    *,
    data_root: Path,
    report_root: Path,
) -> dict[str, object]:
    """Explain exactly why each published animal atlas point exists."""
    atlas_rows = [row.as_dict() for row in build_tracked_animal_atlas_evidence_rows(data_root)]
    sample_lookup = _build_sample_lookup(data_root)
    site_lookup = _build_site_lookup(data_root)
    provenance_lookup = _build_coordinate_lookup(data_root)
    project_lookup = {row.project_accession: row for row in build_project_registry(data_root)}

    packets: list[dict[str, object]] = []
    for row in atlas_rows:
        sample_ids = [str(item) for item in row.get("sample_record_ids", []) if str(item).strip()]
        primary_project = str(row.get("primary_project_accession", "")).strip()
        packets.append(
            {
                "feature_id": row["feature_id"],
                "species_latin_name": row["species_latin_name"],
                "species_common_name": row["species_common_name"],
                "locality": row["locality"],
                "political_entity": row["political_entity"],
                "coordinate_basis": row["coordinate_basis"],
                "coordinate_confidence": row["coordinate_confidence"],
                "support_class": row["support_class"],
                "project_accession": primary_project,
                "paper_doi": row["paper_doi"],
                "paper_title": row["paper_title"],
                "paper_url": row["paper_url"],
                "supplementary_sources": list(row.get("supplementary_sources", [])),
                "exact_source_text": row["exact_source_text"],
                "source_locator": row["source_locator"],
                "sample_rows": [sample_lookup[item] for item in sample_ids if item in sample_lookup],
                "site_evidence": site_lookup.get(primary_project, {}),
                "coordinate_provenance": provenance_lookup.get(primary_project, {}),
                "project_registry_row": (
                    project_lookup[primary_project].as_dict()
                    if primary_project in project_lookup
                    else {}
                ),
            }
        )
    packets.sort(key=lambda row: str(row["feature_id"]))
    return {
        "schema_version": "animal-point-support-packets.v1",
        "row_count": len(packets),
        "rows": packets,
    }


def build_animal_project_absence_packets(
    *,
    data_root: Path,
    report_root: Path,
) -> dict[str, object]:
    """Explain why tracked animal projects do not appear as published map points."""
    atlas_projects = {
        str(row.primary_project_accession)
        for row in build_tracked_animal_atlas_evidence_rows(data_root)
    }
    unresolved_counts = _count_rows_by_project(build_unresolved_site_ledger(data_root))
    overbroad_counts = _count_rows_by_project(build_overbroad_site_ledger(data_root))
    source_audit = build_cross_project_source_audit(data_root)
    bundles = {bundle.project_accession: bundle for bundle in build_project_source_bundles(data_root)}

    rows: list[dict[str, object]] = []
    for registry_row in build_project_registry(data_root):
        bundle = bundles[registry_row.project_accession]
        atlas_feature_present = registry_row.project_accession in atlas_projects
        blockers = list(bundle.blockers)
        if unresolved_counts.get(registry_row.project_accession, 0):
            blockers.append("sample_context_blocked")
        if overbroad_counts.get(registry_row.project_accession, 0):
            blockers.append("region_only_geography")
        if registry_row.evidence_strength == "comparator_only" or "comparator" in registry_row.evidence_strength:
            blockers.append("comparator_only_context")
        if atlas_feature_present:
            continue
        rows.append(
            {
                "project_accession": registry_row.project_accession,
                "species_latin_name": registry_row.species_latin_name,
                "paper_doi": registry_row.primary_paper_doi,
                "project_url": registry_row.project_url,
                "archive_status": registry_row.archive_status,
                "evidence_strength": registry_row.evidence_strength,
                "ingestion_status": registry_row.ingestion_status,
                "paper_download_status": registry_row.paper_download_status,
                "supplement_download_status": registry_row.supplement_download_status,
                "unresolved_sample_count": unresolved_counts.get(registry_row.project_accession, 0),
                "region_only_site_count": overbroad_counts.get(registry_row.project_accession, 0),
                "blockers": sorted(set(blockers)),
                "absence_stage": _absence_stage_for(blockers),
            }
        )
    rows.sort(key=lambda row: (str(row["species_latin_name"]), str(row["project_accession"])))
    return {
        "schema_version": "animal-project-absence-packets.v1",
        "source_audit": source_audit,
        "row_count": len(rows),
        "rows": rows,
    }


def build_animal_foundation_review_packet(
    *,
    data_root: Path,
    report_root: Path,
    validation_payload: dict[str, object],
    drift_payload: dict[str, object],
    caveat_payload: dict[str, object],
    point_payload: dict[str, object],
    absence_payload: dict[str, object],
) -> dict[str, object]:
    """Summarize the current public scientific posture of the animal evidence foundation."""
    readiness = build_cross_species_map_readiness(data_root)
    direct_points = int(readiness["totals"]["direct_coordinate_backed"])
    geocoded_points = int(readiness["totals"]["indirectly_geocoded"])
    unresolved = int(readiness["totals"]["unresolved"])
    refused = int(readiness["totals"]["refused_from_mapping"])
    reference_grade_claim_allowed = (
        validation_payload["overall_ok"]
        and not drift_payload["drift_detected"]
        and direct_points > 0
        and geocoded_points == 0
        and unresolved == 0
        and refused == 0
    )
    posture = (
        "reference_grade_claim_allowed"
        if reference_grade_claim_allowed
        else "governed_metadata_foundation_not_reference_grade"
    )
    strengths = []
    if point_payload["row_count"]:
        strengths.append("published animal atlas points remain fully traceable to sample, project, paper, and site evidence rows")
    if validation_payload["checks"][0]["passed"]:
        strengths.append("curated sample rows keep stable identifiers without duplication")
    if validation_payload["checks"][-1]["passed"]:
        strengths.append("published atlas rows keep project, paper, and sample traceability")
    blockers = []
    if not validation_payload["overall_ok"]:
        blockers.append("foundation_validation_not_yet_clean")
    if drift_payload["drift_detected"]:
        blockers.append("cross_surface_drift_detected")
    if unresolved:
        blockers.append("unresolved_site_assignment_rows_remain")
    if refused:
        blockers.append("region_only_geography_rows_remain")
    if geocoded_points:
        blockers.append("published_points_still_depend_on_named_site_geocoding")
    return {
        "schema_version": "animal-foundation-review.v1",
        "public_posture": posture,
        "reference_grade_claim_allowed": reference_grade_claim_allowed,
        "strengths": strengths,
        "blockers": blockers,
        "counts": {
            "published_point_count": point_payload["row_count"],
            "direct_coordinate_point_count": direct_points,
            "geocoded_point_count": geocoded_points,
            "unresolved_sample_count": unresolved,
            "region_only_refusal_count": refused,
            "blocked_project_count": absence_payload["row_count"],
        },
        "validation_overall_ok": validation_payload["overall_ok"],
        "drift_detected": drift_payload["drift_detected"],
        "caveat_summary": caveat_payload["summary"],
    }


def build_animal_sample_chronology_viewer(
    *,
    data_root: Path,
) -> dict[str, object]:
    """Publish one reader-facing chronology view across all governed animal sample rows."""
    rows = list(build_sample_chronology_viewer_rows(data_root))
    strength_counts = {key: 0 for key in ADNA_CHRONOLOGY_STRENGTHS}
    evidence_counts = {key: 0 for key in ADNA_CHRONOLOGY_EVIDENCE_CLASSES}
    precision_counts = {key: 0 for key in ADNA_CHRONOLOGY_PRECISION_POSTURES}
    normalization_counts = {key: 0 for key in ADNA_CHRONOLOGY_NORMALIZATION_STATUSES}
    for row in rows:
        strength_counts[str(row.get("chronology_strength", ""))] += 1
        evidence_counts[str(row.get("chronology_evidence_class", ""))] += 1
        precision_counts[str(row.get("chronology_precision_posture", ""))] += 1
        normalization_counts[str(row.get("chronology_normalization_status", ""))] += 1
    return {
        "schema_version": "animal-sample-chronology-viewer.v1",
        "row_count": len(rows),
        "strength_counts": strength_counts,
        "evidence_counts": evidence_counts,
        "precision_counts": precision_counts,
        "normalization_counts": normalization_counts,
        "rows": rows,
    }


def build_animal_sample_database_review(
    *,
    data_root: Path,
    report_root: Path,
    point_payload: dict[str, object],
    review_payload: dict[str, object],
) -> dict[str, object]:
    """Prove the current repository posture as a checked-in sample database."""
    project_rows = build_project_registry(data_root)
    paper_rows = build_paper_registry(data_root)
    supplement_rows = build_supplement_registry(data_root)
    sample_rows = _load_all_sample_rows(data_root)
    site_rows = _load_all_site_evidence_rows(data_root)
    chronology_rows = _load_all_project_sample_chronology_rows(data_root)
    coordinate_rows = _load_all_coordinate_rows(data_root)
    sample_site_rows = _load_all_project_sample_site_rows(data_root)
    locality_conflict_rows = build_sample_locality_conflict_ledger(data_root)
    locality_curation_rows = build_sample_locality_manual_curation_workflow_rows(data_root)
    locality_substitution_rows = build_project_locality_substitution_ledger(data_root)
    locality_dictionary_rows = build_site_name_normalization_dictionary_rows(data_root)
    locality_completeness_rows = build_project_locality_completeness_rows(data_root)
    country_payloads = _load_country_payloads(report_root)

    locality_status_counts = {status: 0 for status in ADNA_LOCALITY_RESOLUTION_STATUSES}
    for row in sample_site_rows:
        status = str(row.get("locality_resolution_status", "")).strip()
        if status in locality_status_counts:
            locality_status_counts[status] += 1

    chronology_status_counts = {
        status: 0 for status in ADNA_CHRONOLOGY_NORMALIZATION_STATUSES
    }
    chronology_precision_counts = {
        posture: 0 for posture in ADNA_CHRONOLOGY_PRECISION_POSTURES
    }
    for row in chronology_rows:
        status = str(row.get("chronology_normalization_status", "")).strip()
        if status in chronology_status_counts:
            chronology_status_counts[status] += 1
        precision_posture = str(row.get("chronology_precision_posture", "")).strip()
        if precision_posture in chronology_precision_counts:
            chronology_precision_counts[precision_posture] += 1
    paper_with_archived_supplement_count = sum(
        1 for row in paper_rows if int(row.supplementary_count) > 0
    )
    normalized_chronology_count = (
        chronology_status_counts["normalized_interval"]
        + chronology_status_counts["normalized_point"]
    )
    point_row_count = int(point_payload["row_count"])
    mapped_sample_share = (
        round(point_row_count / len(sample_rows), 4) if sample_rows else 0.0
    )

    direct_links = {
        "project_registry": "data/adna/governance/source_library/project_registry.json",
        "paper_registry": "data/adna/governance/source_library/paper_registry.json",
        "supplement_registry": "data/adna/governance/source_library/supplement_registry.json",
        "sample_foundation_truth": "data/adna/governance/animal_sample_foundation_truth.json",
        "sample_database_contract": "data/adna/governance/animal_sample_product_contract.json",
        "sample_query_example": "docs/report/sweden/sweden_animal_adna_v66_samples.md",
        "site_review": "data/adna/governance/source_library/project_sample_site_review.json",
        "locality_conflicts": "data/adna/governance/source_library/sample_locality_conflict_ledger.json",
        "locality_curation_workflow": "data/adna/governance/source_library/sample_locality_manual_curation_workflow.json",
        "locality_substitution_ledger": "data/adna/governance/source_library/project_locality_substitution_ledger.json",
        "locality_normalization_dictionary": "data/adna/governance/source_library/site_name_normalization_dictionary.json",
        "locality_completeness": "data/adna/governance/source_library/project_locality_completeness.json",
        "chronology_review": "data/adna/governance/source_library/project_sample_chronology_review.json",
        "chronology_conflicts": "data/adna/governance/source_library/sample_chronology_conflict_ledger.json",
        "chronology_precision_audit": "data/adna/governance/source_library/sample_chronology_precision_audit.json",
        "date_evidence_gap_queue": "data/adna/governance/source_library/date_evidence_gap_queue.json",
        "coordinate_provenance_example": "data/adna/species/ovis_aries/normalized/coordinate_provenance.json",
        "point_support_packets": "docs/report/animal_point_support_packets.md",
        "atlas_evidence_rows": "docs/report/nordic-atlas/nordic-atlas_animal_atlas_evidence.json",
        "atlas_map": "docs/report/nordic-atlas/nordic-atlas_map.html",
        "country_output_summary": "docs/report/published_reports_summary.json",
    }
    sample_database_claim_supported = all(
        (
            len(project_rows) > 0,
            len(paper_rows) > 0,
            len(supplement_rows) > 0,
            len(sample_rows) > 0,
            len(site_rows) > 0,
            len(chronology_rows) > 0,
            len(coordinate_rows) > 0,
        )
    )
    nordic_view_supported_now = all(
        (
            point_row_count >= 10,
            paper_with_archived_supplement_count >= 5,
            mapped_sample_share >= 0.05,
            normalized_chronology_count >= 100,
            bool(country_payloads),
        )
    )
    region_agnostic_contract_ready = all(
        (
            sample_database_claim_supported,
            not review_payload["blockers"],
            point_row_count >= 25,
            paper_with_archived_supplement_count == len(paper_rows),
            mapped_sample_share >= 0.2,
        )
    )
    posture_findings = []
    if point_row_count < 10:
        posture_findings.append("published_atlas_point_count_below_minimum_reading_depth")
    if paper_with_archived_supplement_count < 5:
        posture_findings.append("supplement_backed_paper_coverage_still_too_low")
    if mapped_sample_share < 0.05:
        posture_findings.append("mapped_sample_share_still_too_low")
    if normalized_chronology_count < 100:
        posture_findings.append("normalized_chronology_depth_still_too_thin")
    return {
        "schema_version": "animal-sample-database-review.v1",
        "public_posture": "partial_sample_owned_animal_evidence_surface",
        "sample_database_claim_supported": sample_database_claim_supported,
        "nordic_view_supported_now": nordic_view_supported_now,
        "region_agnostic_contract_ready": region_agnostic_contract_ready,
        "world_map_expansion_posture": (
            "not_supported_until_source_capture_site_resolution_and_chronology_depth_are_materially_stronger"
        ),
        "readiness_thresholds": {
            "minimum_published_atlas_points": 10,
            "minimum_supplement_backed_papers": 5,
            "minimum_mapped_sample_share": 0.05,
            "minimum_normalized_chronology_rows": 100,
            "minimum_region_agnostic_point_floor": 25,
            "minimum_region_agnostic_mapped_share": 0.2,
        },
        "counts": {
            "tracked_project_count": len(project_rows),
            "tracked_paper_count": len(paper_rows),
            "tracked_supplement_count": len(supplement_rows),
            "papers_with_archived_supplements": paper_with_archived_supplement_count,
            "sample_row_count": len(sample_rows),
            "site_evidence_row_count": len(site_rows),
            "sample_site_row_count": len(sample_site_rows),
            "chronology_row_count": len(chronology_rows),
            "coordinate_row_count": len(coordinate_rows),
            "published_atlas_point_count": point_payload["row_count"],
            "published_country_bundle_count": len(country_payloads),
            "mapped_sample_share": mapped_sample_share,
            "locality_conflict_row_count": len(locality_conflict_rows),
            "locality_curation_row_count": len(locality_curation_rows),
            "locality_substitution_project_count": len(locality_substitution_rows),
            "locality_dictionary_row_count": len(locality_dictionary_rows),
        },
        "locality_status_counts": locality_status_counts,
        "locality_completeness_counts": {
            "exact_site_evidence_count": sum(
                int(row["exact_site_evidence_count"]) for row in locality_completeness_rows
            ),
            "broader_locality_evidence_count": sum(
                int(row["broader_locality_evidence_count"]) for row in locality_completeness_rows
            ),
            "unresolved_geography_count": sum(
                int(row["unresolved_geography_count"]) for row in locality_completeness_rows
            ),
        },
        "chronology_status_counts": chronology_status_counts,
        "chronology_precision_counts": chronology_precision_counts,
        "posture_findings": posture_findings,
        "blockers": list(review_payload["blockers"]),
        "direct_links": direct_links,
    }


def build_animal_publication_release_gate(
    *,
    data_root: Path,
    report_root: Path,
    docs_root: Path,
    point_payload: dict[str, object],
    review_payload: dict[str, object],
    sample_database_review_payload: dict[str, object],
) -> dict[str, object]:
    """Fail publication when animal outputs overclaim or lose required traceability."""
    docs_paths = sorted(path for path in docs_root.rglob("*.md") if path.is_file())
    docs_text = "\n".join(path.read_text(encoding="utf-8") for path in docs_paths).lower()
    all_species_claim = "all-species animal map readiness" in docs_text or "all species animal map readiness" in docs_text
    reference_grade_claim = "reference-grade" in docs_text
    country_payloads = _load_country_payloads(report_root)
    try:
        atlas_rows = [row.as_dict() for row in build_tracked_animal_atlas_evidence_rows(data_root)]
    except FileNotFoundError:
        atlas_rows = []
    unresolved_rows = build_unresolved_site_ledger(data_root)
    overbroad_rows = build_overbroad_site_ledger(data_root)
    project_locality_drift_rows = build_project_locality_count_drift(data_root)
    locality_substitution_rows = build_project_locality_substitution_ledger(data_root)
    sample_site_rows = _load_all_project_sample_site_rows(data_root)
    chronology_rows = _load_all_project_sample_chronology_rows(data_root)
    substitution_blocked_projects = {
        str(row.get("project_accession", "")).strip()
        for row in locality_substitution_rows
        if bool(row.get("publication_blocked"))
    }
    blocked_sample_site_rows = {
        str(row.get("repo_stable_sample_id", "")).strip(): row
        for row in sample_site_rows
        if str(row.get("locality_resolution_status", "")) in {
            "project_level_site_only",
            "region_only",
            "unresolved",
        }
        and str(row.get("repo_stable_sample_id", "")).strip()
    }
    blocked_exact_site_rows = [
        str(row.get("identity", {}).get("stable_token", "")).strip()
        for row in _load_all_sample_rows(data_root)
        if str(row.get("identity", {}).get("stable_token", "")).strip() in blocked_sample_site_rows
        and ":sample-site:" in str(
            row.get("locality_identity", {}).get("stable_token", "")
        )
    ]
    blocked_atlas_rows = sorted(
        {
            str(point.get("feature_id", "")).strip()
            for point in point_payload["rows"]
            for sample_row in point.get("sample_rows", [])
            if str(sample_row.get("identity", {}).get("stable_token", "")).strip()
            in blocked_sample_site_rows
        }
    )
    chronology_blocked_master_ids = {
        str(row.get("repo_stable_sample_id", "")).strip(): row
        for row in chronology_rows
        if _chronology_row_blocks_publication(row)
    }
    sample_master_ids = {
        str(row.get("identity", {}).get("stable_token", "")).strip(): str(row.get("master_id", "")).strip()
        for row in _load_all_sample_rows(data_root)
        if str(row.get("identity", {}).get("stable_token", "")).strip()
    }
    blocked_country_chronology_rows = sorted(
        {
            str(sample_row.get("sample_record_id", "")).strip()
            for payload in country_payloads
            for sample_row in payload.get("sample_rows", [])
            if sample_master_ids.get(str(sample_row.get("sample_record_id", "")).strip(), "")
            in chronology_blocked_master_ids
        }
    )
    blocked_atlas_chronology_rows = sorted(
        {
            str(point.get("feature_id", "")).strip()
            for point in point_payload["rows"]
            for sample_row in point.get("sample_rows", [])
            if sample_master_ids.get(
                str(sample_row.get("identity", {}).get("stable_token", "")).strip(),
                "",
            )
            in chronology_blocked_master_ids
        }
    )
    substitution_blocked_country_rows = sorted(
        {
            str(sample_row.get("sample_record_id", "")).strip()
            for payload in country_payloads
            for sample_row in payload.get("sample_rows", [])
            if str(sample_row.get("project_accession", "")).strip()
            in substitution_blocked_projects
        }
    )
    substitution_blocked_atlas_rows = sorted(
        {
            str(point.get("feature_id", "")).strip()
            for point in point_payload["rows"]
            if str(point.get("primary_project_accession", "")).strip()
            in substitution_blocked_projects
        }
    )
    imprecise_country_chronology_rows = sorted(
        {
            str(locality.get("feature_id", "")).strip()
            for payload in country_payloads
            for locality in payload.get("localities", [])
            if _public_chronology_window_exposed(locality)
        }
    )
    imprecise_atlas_chronology_rows = sorted(
        {
            str(row.get("feature_id", "")).strip()
            for row in atlas_rows
            if _public_chronology_window_exposed(row.get("chronology", {}))
        }
    )
    point_row_count = int(point_payload.get("row_count", len(point_payload.get("rows", []))))
    reference_grade_support_requirements = {
        "sample_database_artifacts_present": bool(
            sample_database_review_payload["sample_database_claim_supported"]
        ),
        "sample_evidence_packets_present": bool(point_row_count),
        "map_outputs_present": bool(
            sample_database_review_payload["nordic_view_supported_now"]
        ),
    }
    reference_grade_support_ready = bool(
        review_payload["reference_grade_claim_allowed"]
        and all(reference_grade_support_requirements.values())
    )
    checks = [
        _check_row(
            "published_points_keep_required_traceability",
            all(
                bool(row.get("sample_rows"))
                and bool(row.get("site_evidence"))
                and bool(row.get("coordinate_provenance"))
                and bool(str(row.get("paper_url", "")).strip())
                for row in point_payload["rows"]
            ),
            "Every published animal point keeps sample, site, coordinate, and citation support.",
            [
                str(row.get("feature_id", ""))
                for row in point_payload["rows"]
                if not (
                    bool(row.get("sample_rows"))
                    and bool(row.get("site_evidence"))
                    and bool(row.get("coordinate_provenance"))
                    and bool(str(row.get("paper_url", "")).strip())
                )
            ],
        ),
        _check_row(
            "project_locality_outputs_do_not_flatten_sample_site_disagreement",
            not project_locality_drift_rows,
            "Animal publication does not flatten multi-site sample evidence into one project-level locality claim.",
            [
                str(row.get("project_accession", ""))
                for row in project_locality_drift_rows
            ],
        ),
        _check_row(
            "blocked_sample_site_rows_do_not_publish_as_exact_sites_or_atlas_points",
            not (blocked_exact_site_rows or blocked_atlas_rows),
            "Sample rows without defensible sample-owned site assignment do not leak into exact site rows or atlas points.",
            blocked_exact_site_rows + blocked_atlas_rows,
        ),
        _check_row(
            "unresolved_sample_chronology_does_not_publish_in_country_or_atlas_outputs",
            not (blocked_country_chronology_rows or blocked_atlas_chronology_rows),
            "Published country and atlas outputs do not carry unresolved or conflicting sample chronology rows.",
            blocked_country_chronology_rows + blocked_atlas_chronology_rows,
        ),
        _check_row(
            "project_level_locality_substitution_projects_do_not_publish_country_or_atlas_rows",
            not (substitution_blocked_country_rows or substitution_blocked_atlas_rows),
            "Projects whose locality evidence still collapses all samples into one blocked context do not leak into country or atlas publication.",
            substitution_blocked_country_rows + substitution_blocked_atlas_rows,
        ),
        _check_row(
            "broad_or_contextual_chronology_does_not_publish_numeric_windows",
            not (imprecise_country_chronology_rows or imprecise_atlas_chronology_rows),
            "Public country and atlas outputs do not expose numeric chronology windows when the underlying chronology posture is broad, contextual, or approximate.",
            imprecise_country_chronology_rows + imprecise_atlas_chronology_rows,
        ),
        _check_row(
            "docs_do_not_overclaim_all_species_map_readiness",
            not (all_species_claim and (unresolved_rows or overbroad_rows)),
            "Public docs do not claim all-species animal map readiness while blocking ledgers remain.",
            ["docs_claim_all_species_map_readiness"] if all_species_claim else [],
        ),
        _check_row(
            "docs_do_not_claim_reference_grade_without_support",
            not (reference_grade_claim and not reference_grade_support_ready),
            "Public docs do not claim the strongest posture before the sample database, evidence packets, and map outputs all support it.",
            ["docs_claim_reference_grade"] if reference_grade_claim else [],
        ),
    ]
    overall_ok = all(bool(check["passed"]) for check in checks)
    return {
        "schema_version": "animal-publication-release-gate.v1",
        "overall_ok": overall_ok,
        "checks": checks,
        "reference_grade_claim_allowed": review_payload["reference_grade_claim_allowed"],
        "reference_grade_support_ready": reference_grade_support_ready,
        "reference_grade_support_requirements": reference_grade_support_requirements,
    }


def _chronology_row_blocks_publication(row: dict[str, object]) -> bool:
    status = str(row.get("chronology_normalization_status", "")).strip()
    precision_posture = str(row.get("chronology_precision_posture", "")).strip()
    return status == "unresolved" or precision_posture == "unresolved"


def _public_chronology_window_exposed(payload: dict[str, object]) -> bool:
    precision_posture = str(payload.get("chronology_precision_posture", "")).strip()
    if not precision_posture and isinstance(payload.get("precision_posture"), str):
        precision_posture = str(payload.get("precision_posture", "")).strip()
    if precision_posture in {"sample_precise_point", "sample_precise_interval", ""}:
        return False
    return any(
        payload.get(field) is not None
        for field in ("time_start_bp", "time_end_bp", "time_mean_bp")
    )


def render_animal_foundation_validation_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Animal foundation validation",
        "",
        f"- Overall ok: `{str(payload['overall_ok']).lower()}`",
        f"- Sample rows: `{payload['sample_row_count']}`",
        f"- Site evidence rows: `{payload['site_evidence_row_count']}`",
        f"- Coordinate rows: `{payload['coordinate_row_count']}`",
        f"- Atlas rows: `{payload['atlas_row_count']}`",
        "",
        "| Check | Passed | Finding count |",
        "| --- | --- | ---: |",
    ]
    for row in payload["checks"]:
        lines.append(
            f"| {row['check_id']} | `{str(row['passed']).lower()}` | {row['finding_count']} |"
        )
    return "\n".join(lines) + "\n"


def render_animal_cross_surface_drift_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Animal cross-surface drift",
        "",
        f"- Drift detected: `{str(payload['drift_detected']).lower()}`",
        "",
        "| Species | Sample rows | Atlas rows | Country sample rows | Drift |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['species_latin_name']} | {row['normalized_sample_row_count']} | "
            f"{row['atlas_evidence_row_count']} | {row['published_country_sample_count']} | "
            f"`{str(row['drift_detected']).lower()}` |"
        )
    return "\n".join(lines) + "\n"


def render_animal_scientific_caveat_ledger_markdown(payload: dict[str, object]) -> str:
    summary = payload["summary"]
    return "\n".join(
        [
            "# Animal scientific caveat ledger",
            "",
            f"- Missing supplements: `{summary['missing_supplement_count']}`",
            f"- Unreadable tables: `{summary['unreadable_table_count']}`",
            f"- Uncertain site assignments: `{summary['uncertain_site_assignment_count']}`",
            f"- Region-only geography rows: `{summary['region_only_geography_count']}`",
            f"- Comparator-only evidence rows: `{summary['comparator_only_evidence_count']}`",
            "",
        ]
    )


def render_animal_point_support_packets_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Animal point support packets",
        "",
        f"- Published point count: `{payload['row_count']}`",
        "",
    ]
    for row in payload["rows"]:
        lines.extend(
            [
                f"## {row['feature_id']}",
                "",
                f"- Species: `{row['species_latin_name']}`",
                f"- Project accession: `{row['project_accession']}`",
                f"- Paper DOI: `{row['paper_doi']}`",
                f"- Coordinate basis: `{row['coordinate_basis']}`",
                f"- Coordinate confidence: `{row['coordinate_confidence']}`",
                f"- Sample rows: `{len(row['sample_rows'])}`",
                "",
            ]
        )
    return "\n".join(lines) + "\n"


def render_animal_project_absence_packets_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Animal project absence packets",
        "",
        f"- Non-published project count: `{payload['row_count']}`",
        "",
        "| Project | Species | Absence stage | Blockers |",
        "| --- | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['project_accession']} | {row['species_latin_name']} | "
            f"{row['absence_stage']} | {', '.join(row['blockers'])} |"
        )
    return "\n".join(lines) + "\n"


def render_animal_foundation_review_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Animal foundation review",
        "",
        f"- Public posture: `{payload['public_posture']}`",
        f"- Strongest claim allowed: `{str(payload['reference_grade_claim_allowed']).lower()}`",
        f"- Published point count: `{payload['counts']['published_point_count']}`",
        f"- Direct-coordinate point count: `{payload['counts']['direct_coordinate_point_count']}`",
        f"- Geocoded point count: `{payload['counts']['geocoded_point_count']}`",
        f"- Unresolved sample count: `{payload['counts']['unresolved_sample_count']}`",
        f"- Region-only refusal count: `{payload['counts']['region_only_refusal_count']}`",
        "",
    ]
    if payload["strengths"]:
        lines.append("## Strengths")
        lines.append("")
        for item in payload["strengths"]:
            lines.append(f"- {item}")
        lines.append("")
    if payload["blockers"]:
        lines.append("## Blockers")
        lines.append("")
        for item in payload["blockers"]:
            lines.append(f"- {item}")
        lines.append("")
    return "\n".join(lines) + "\n"


def render_animal_sample_chronology_viewer_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Animal sample chronology viewer",
        "",
        f"- Sample chronology rows: `{payload['row_count']}`",
        f"- Normalized intervals: `{payload['normalization_counts']['normalized_interval']}`",
        f"- Normalized points: `{payload['normalization_counts']['normalized_point']}`",
        f"- Text-only rows: `{payload['normalization_counts']['text_only_unparsed']}`",
        f"- Unresolved rows: `{payload['normalization_counts']['unresolved']}`",
        f"- Direct radiocarbon rows: `{payload['evidence_counts']['direct_radiocarbon_date']}`",
        f"- Modeled rows: `{payload['evidence_counts']['modeled_sample_date']}`",
        f"- Contextual rows: `{payload['evidence_counts']['archaeological_context_date']}`",
        f"- Broad period rows: `{payload['evidence_counts']['broad_period_label']}`",
        "",
        "| Species | Project accession | Sample id | Strength | Evidence class | Precision posture | Normalization | Chronology |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['species_latin_name']} | {row['project_accession']} | "
            f"{row['repo_stable_sample_id']} | {row['chronology_strength']} | "
            f"{row['chronology_evidence_class']} | {row['chronology_precision_posture']} | "
            f"{row['chronology_normalization_status']} | {row['chronology_text']} |"
        )
    return "\n".join(lines) + "\n"


def render_animal_sample_database_review_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Animal sample database review",
        "",
        f"- Public posture: `{payload['public_posture']}`",
        f"- Sample database claim supported: `{str(payload['sample_database_claim_supported']).lower()}`",
        f"- Nordic view supported now: `{str(payload['nordic_view_supported_now']).lower()}`",
        f"- Region-agnostic contract ready: `{str(payload['region_agnostic_contract_ready']).lower()}`",
        f"- World-map expansion posture: `{payload['world_map_expansion_posture']}`",
        "",
        "## Counts",
        "",
        f"- Tracked projects: `{payload['counts']['tracked_project_count']}`",
        f"- Tracked papers: `{payload['counts']['tracked_paper_count']}`",
        f"- Tracked supplements: `{payload['counts']['tracked_supplement_count']}`",
        f"- Sample rows: `{payload['counts']['sample_row_count']}`",
        f"- Site evidence rows: `{payload['counts']['site_evidence_row_count']}`",
        f"- Sample site rows: `{payload['counts']['sample_site_row_count']}`",
        f"- Chronology rows: `{payload['counts']['chronology_row_count']}`",
        f"- Coordinate rows: `{payload['counts']['coordinate_row_count']}`",
        f"- Published atlas points: `{payload['counts']['published_atlas_point_count']}`",
        f"- Published country bundles: `{payload['counts']['published_country_bundle_count']}`",
        f"- Papers with archived supplements: `{payload['counts']['papers_with_archived_supplements']}`",
        f"- Mapped sample share: `{payload['counts']['mapped_sample_share']}`",
        "",
        "## Thresholds",
        "",
        f"- Minimum published atlas points: `{payload['readiness_thresholds']['minimum_published_atlas_points']}`",
        f"- Minimum supplement-backed papers: `{payload['readiness_thresholds']['minimum_supplement_backed_papers']}`",
        f"- Minimum mapped sample share: `{payload['readiness_thresholds']['minimum_mapped_sample_share']}`",
        f"- Minimum normalized chronology rows: `{payload['readiness_thresholds']['minimum_normalized_chronology_rows']}`",
        f"- Minimum region-agnostic point floor: `{payload['readiness_thresholds']['minimum_region_agnostic_point_floor']}`",
        f"- Minimum region-agnostic mapped share: `{payload['readiness_thresholds']['minimum_region_agnostic_mapped_share']}`",
        "",
        "## Posture Findings",
        "",
    ]
    for finding in payload["posture_findings"]:
        lines.append(f"- {finding}")
    lines.extend(
        [
            "",
        "## Direct Links",
        "",
        ]
    )
    for label, target in payload["direct_links"].items():
        lines.append(f"- {label}: `{target}`")
    if payload["blockers"]:
        lines.extend(
            [
                "",
                "## Current Blockers",
                "",
            ]
        )
        for blocker in payload["blockers"]:
            lines.append(f"- {blocker}")
    return "\n".join(lines) + "\n"


def render_animal_publication_release_gate_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Animal publication release gate",
        "",
        f"- Overall ok: `{str(payload['overall_ok']).lower()}`",
        f"- Strongest claim allowed: `{str(payload['reference_grade_claim_allowed']).lower()}`",
        f"- Strongest claim support ready: `{str(payload['reference_grade_support_ready']).lower()}`",
        "",
        "## Strongest-Claim Support Requirements",
        "",
        f"- Sample database artifacts present: `{str(payload['reference_grade_support_requirements']['sample_database_artifacts_present']).lower()}`",
        f"- Sample evidence packets present: `{str(payload['reference_grade_support_requirements']['sample_evidence_packets_present']).lower()}`",
        f"- Map outputs present: `{str(payload['reference_grade_support_requirements']['map_outputs_present']).lower()}`",
        "",
        "| Check | Passed | Finding count |",
        "| --- | --- | ---: |",
    ]
    for row in payload["checks"]:
        lines.append(
            f"| {row['check_id']} | `{str(row['passed']).lower()}` | {row['finding_count']} |"
        )
    return "\n".join(lines) + "\n"


def _check_row(
    check_id: str,
    passed: bool,
    description: str,
    findings: list[str],
) -> dict[str, object]:
    return {
        "check_id": check_id,
        "passed": passed,
        "description": description,
        "finding_count": len(findings),
        "findings": findings[:10],
    }


def _load_json_rows(path: Path, key: str) -> list[dict[str, object]]:
    if not path.is_file():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get(key, [])
    return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []


def _species_roots(data_root: Path) -> list[Path]:
    species_dir = adna_species_dir(Path(data_root))
    if not species_dir.is_dir():
        return []
    return [
        path
        for path in sorted(species_dir.iterdir())
        if path.is_dir()
    ]


def _load_all_sample_rows(data_root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for root in _species_roots(data_root):
        rows.extend(_load_json_rows(root / "normalized" / "sample_records.json", "samples"))
    return rows


def _load_all_site_evidence_rows(data_root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for root in _species_roots(data_root):
        rows.extend(_load_json_rows(root / "normalized" / "site_evidence.json", "site_evidence"))
    return rows


def _load_all_coordinate_rows(data_root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for root in _species_roots(data_root):
        rows.extend(
            _load_json_rows(root / "normalized" / "coordinate_provenance.json", "coordinate_provenance")
        )
    return rows


def _load_all_project_sample_site_rows(data_root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    project_root = (
        Path(data_root) / "adna" / "governance" / "source_library" / "projects"
    )
    paths = sorted(project_root.glob("*/sample_sites.json")) if project_root.is_dir() else []
    if paths:
        for path in paths:
            payload = json.loads(path.read_text(encoding="utf-8"))
            project_rows = payload.get("rows", [])
            if not isinstance(project_rows, list):
                continue
            for row in project_rows:
                if not isinstance(row, dict):
                    continue
                status = str(row.get("locality_resolution_status", ""))
                if status and status not in ADNA_LOCALITY_RESOLUTION_STATUSES:
                    continue
                rows.append(row)
        return rows
    for project in build_archive_project_catalog():
        rows.extend(
            row.as_dict()
            for row in build_project_sample_site_rows(data_root, project.project_accession)
        )
    return rows


def _load_all_project_sample_chronology_rows(data_root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    project_root = (
        Path(data_root) / "adna" / "governance" / "source_library" / "projects"
    )
    paths = (
        sorted(project_root.glob("*/sample_chronology.json"))
        if project_root.is_dir()
        else []
    )
    if paths:
        for path in paths:
            payload = json.loads(path.read_text(encoding="utf-8"))
            project_rows = payload.get("rows", [])
            if not isinstance(project_rows, list):
                continue
            for row in project_rows:
                if not isinstance(row, dict):
                    continue
                status = str(row.get("chronology_normalization_status", ""))
                if status and status not in ADNA_CHRONOLOGY_NORMALIZATION_STATUSES:
                    continue
                rows.append(row)
        return rows
    rows.extend(dict(row) for row in build_sample_chronology_viewer_rows(data_root))
    return rows


def _group_sample_rows_by_species(data_root: Path) -> dict[str, list[dict[str, object]]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for row in _load_all_sample_rows(data_root):
        grouped.setdefault(str(row.get("species_latin_name", "")), []).append(row)
    return grouped


def _group_site_rows_by_species(data_root: Path) -> dict[str, list[dict[str, object]]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for row in _load_all_site_evidence_rows(data_root):
        grouped.setdefault(str(row.get("species_latin_name", "")), []).append(row)
    return grouped


def _group_coordinate_rows_by_species(data_root: Path) -> dict[str, list[dict[str, object]]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for row in _load_all_coordinate_rows(data_root):
        grouped.setdefault(str(row.get("species_latin_name", "")), []).append(row)
    return grouped


def _build_sample_lookup(data_root: Path) -> dict[str, dict[str, object]]:
    lookup: dict[str, dict[str, object]] = {}
    for row in _load_all_sample_rows(data_root):
        token = str(row.get("identity", {}).get("stable_token", "")).strip()
        if token:
            lookup[token] = row
    return lookup


def _build_site_lookup(data_root: Path) -> dict[str, dict[str, object]]:
    return {
        str(row.get("project_accession", "")).strip(): row
        for row in _load_all_site_evidence_rows(data_root)
        if str(row.get("project_accession", "")).strip()
    }


def _build_coordinate_lookup(data_root: Path) -> dict[str, dict[str, object]]:
    return {
        str(row.get("project_accession", "")).strip(): row
        for row in _load_all_coordinate_rows(data_root)
        if str(row.get("project_accession", "")).strip()
    }


def _count_rows_by_project(rows: tuple[dict[str, object], ...]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        project = str(row.get("project_accession", "")).strip()
        if project:
            counts[project] = counts.get(project, 0) + 1
    return counts


def _build_comparator_only_rows(data_root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for root in _species_roots(data_root):
        review_path = root / "review" / "species_review.json"
        if not review_path.is_file():
            continue
        payload = json.loads(review_path.read_text(encoding="utf-8"))
        for row in payload.get("project_reviews", []):
            if not isinstance(row, dict):
                continue
            if str(row.get("domestication_scope", "")) != "comparator_only":
                continue
            rows.append(
                {
                    "species_latin_name": row.get("species_latin_name", ""),
                    "project_accession": row.get("project_accession", ""),
                    "evidence_strength": row.get("evidence_strength", ""),
                    "blocking_reasons": row.get("blocking_reasons", []),
                }
            )
    rows.sort(key=lambda row: (str(row["species_latin_name"]), str(row["project_accession"])))
    return rows


def _absence_stage_for(blockers: list[str]) -> str:
    blocker_set = set(blockers)
    if "missing_local_paper_evidence" in blocker_set or "paper_linkage_not_curated" in blocker_set:
        return "paper_or_metadata_capture"
    if "missing_local_supplementary_material" in blocker_set:
        return "supplement_capture"
    if "sample_context_blocked" in blocker_set:
        return "site_extraction"
    if "region_only_geography" in blocker_set:
        return "coordinate_resolution"
    if "comparator_only_context" in blocker_set:
        return "comparator_context_only"
    return "not_point_publishable"


def _load_country_payloads(report_root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    report_root = Path(report_root)
    if not report_root.is_dir():
        return rows
    for country_dir in sorted(report_root.iterdir()):
        if not country_dir.is_dir() or country_dir.name in {"_map_assets", "nordic-atlas"}:
            continue
        for summary_path in country_dir.glob("*_animal_adna_*_summary.json"):
            payload = json.loads(summary_path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                rows.append(payload)
    return rows
