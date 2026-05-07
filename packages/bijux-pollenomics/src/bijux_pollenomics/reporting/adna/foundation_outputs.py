from __future__ import annotations

import json
from pathlib import Path

from ...adna.catalogs import (
    build_cross_species_map_readiness,
    build_overbroad_site_ledger,
    build_unresolved_site_ledger,
)
from ...adna.paths import adna_species_dir
from ...adna.sample_truth import build_project_locality_count_drift
from ...adna.source_library import (
    build_cross_project_source_audit,
    build_paper_registry,
    build_project_registry,
    build_project_source_bundles,
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
    release_gate_payload = build_animal_publication_release_gate(
        data_root=data_root,
        report_root=output_root,
        docs_root=docs_root,
        point_payload=point_payload,
        review_payload=review_payload,
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
    atlas_rows = [row.as_dict() for row in build_tracked_animal_atlas_evidence_rows(data_root)]
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
    unresolved_rows = build_unresolved_site_ledger(data_root)
    overbroad_rows = build_overbroad_site_ledger(data_root)
    comparator_rows = _build_comparator_only_rows(data_root)
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
            "uncertain_site_assignment_count": len(unresolved_rows),
            "region_only_geography_count": len(overbroad_rows),
            "comparator_only_evidence_count": len(comparator_rows),
        },
        "categories": {
            "missing_supplements": missing_supplements,
            "unreadable_tables": unreadable_rows,
            "uncertain_site_assignment": list(unresolved_rows),
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


def build_animal_publication_release_gate(
    *,
    data_root: Path,
    report_root: Path,
    docs_root: Path,
    point_payload: dict[str, object],
    review_payload: dict[str, object],
) -> dict[str, object]:
    """Fail publication when animal outputs overclaim or lose required traceability."""
    docs_to_scan = (
        docs_root / "index.md",
        docs_root / "05-nordic-evidence-atlas" / "index.md",
        docs_root / "02-bijux-pollenomics-data" / "outputs" / "nordic-atlas.md",
    )
    docs_text = "\n".join(
        path.read_text(encoding="utf-8") for path in docs_to_scan if path.is_file()
    ).lower()
    all_species_claim = "all-species animal map readiness" in docs_text or "all species animal map readiness" in docs_text
    reference_grade_claim = "reference-grade nordic animal adna metadata-and-atlas foundation" in docs_text
    unresolved_rows = build_unresolved_site_ledger(data_root)
    overbroad_rows = build_overbroad_site_ledger(data_root)
    project_locality_drift_rows = build_project_locality_count_drift(data_root)
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
            "docs_do_not_overclaim_all_species_map_readiness",
            not (all_species_claim and (unresolved_rows or overbroad_rows)),
            "Public docs do not claim all-species animal map readiness while blocking ledgers remain.",
            ["docs_claim_all_species_map_readiness"] if all_species_claim else [],
        ),
        _check_row(
            "docs_do_not_claim_reference_grade_without_support",
            not (reference_grade_claim and not review_payload["reference_grade_claim_allowed"]),
            "Public docs do not claim reference-grade posture before the shipped evidence earns it.",
            ["docs_claim_reference_grade"] if reference_grade_claim else [],
        ),
    ]
    overall_ok = all(bool(check["passed"]) for check in checks)
    return {
        "schema_version": "animal-publication-release-gate.v1",
        "overall_ok": overall_ok,
        "checks": checks,
        "reference_grade_claim_allowed": review_payload["reference_grade_claim_allowed"],
    }


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
        f"- Reference-grade claim allowed: `{str(payload['reference_grade_claim_allowed']).lower()}`",
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


def render_animal_publication_release_gate_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Animal publication release gate",
        "",
        f"- Overall ok: `{str(payload['overall_ok']).lower()}`",
        f"- Reference-grade claim allowed: `{str(payload['reference_grade_claim_allowed']).lower()}`",
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
