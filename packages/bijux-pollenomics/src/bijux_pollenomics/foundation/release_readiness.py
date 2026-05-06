from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..adna import (
    build_archive_integrity_report,
    build_species_dataset_review,
    build_species_manifest,
    build_species_normalization_bundle,
    build_species_runtime_manifest,
)

__all__ = ["ReleaseReadinessReport", "build_release_readiness_report"]


@dataclass(frozen=True)
class ReleaseReadinessReport:
    """Medium-weight cross-surface gate for scientific and publication readiness."""

    schema_version: str
    species_latin_name: str
    source_identity_ok: bool
    curation_integrity_ok: bool
    normalized_record_contract_ok: bool
    atlas_bundle_contract_ok: bool
    ranking_provenance_ok: bool
    overall_ok: bool
    findings: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "species_latin_name": self.species_latin_name,
            "source_identity_ok": self.source_identity_ok,
            "curation_integrity_ok": self.curation_integrity_ok,
            "normalized_record_contract_ok": self.normalized_record_contract_ok,
            "atlas_bundle_contract_ok": self.atlas_bundle_contract_ok,
            "ranking_provenance_ok": self.ranking_provenance_ok,
            "overall_ok": self.overall_ok,
            "findings": list(self.findings),
        }


def build_release_readiness_report(species_name: str) -> ReleaseReadinessReport:
    """Build one medium-weight readiness gate across archive, runtime, and publication surfaces."""
    manifest = build_species_manifest(species_name)
    dataset_review = build_species_dataset_review(species_name)
    integrity = build_archive_integrity_report(species_name=species_name)

    source_identity_ok = _source_identity_ok(species_name)
    curation_integrity_ok = _curation_integrity_ok(dataset_review, integrity)
    normalized_record_contract_ok = _normalized_record_contract_ok(species_name)
    atlas_bundle_contract_ok = _atlas_bundle_contract_ok()
    ranking_provenance_ok = _ranking_provenance_ok()

    findings = []
    if not source_identity_ok:
        findings.append("source_identity_contract_failed")
    if not curation_integrity_ok:
        findings.append("curation_integrity_contract_failed")
    if not normalized_record_contract_ok:
        findings.append("normalized_record_contract_failed")
    if not atlas_bundle_contract_ok:
        findings.append("atlas_bundle_contract_failed")
    if not ranking_provenance_ok:
        findings.append("ranking_provenance_contract_failed")
    overall_ok = not findings

    return ReleaseReadinessReport(
        schema_version="release-readiness-report.v1",
        species_latin_name=manifest.species.latin_name,
        source_identity_ok=source_identity_ok,
        curation_integrity_ok=curation_integrity_ok,
        normalized_record_contract_ok=normalized_record_contract_ok,
        atlas_bundle_contract_ok=atlas_bundle_contract_ok,
        ranking_provenance_ok=ranking_provenance_ok,
        overall_ok=overall_ok,
        findings=tuple(findings),
    )


def _source_identity_ok(species_name: str) -> bool:
    if species_name == "Homo sapiens":
        runtime_manifest = build_species_runtime_manifest("Homo sapiens", version="v66")
        return all(
            bundle.source_family == "AADR" and bundle.release_manifest_path.endswith("release_manifest.json")
            for bundle in runtime_manifest.source_bundles
        )
    normalization_bundle = build_species_normalization_bundle(species_name)
    return bool(normalization_bundle.lineage_records) and all(
        bool(record.source_accessions) for record in normalization_bundle.lineage_records
    )


def _curation_integrity_ok(dataset_review, integrity) -> bool:
    if integrity.duplicates:
        return False
    if integrity.access_findings:
        return False
    if integrity.species_mismatches:
        return False
    return not (
        dataset_review.product_role == "domesticated_core"
        and integrity.domestication_scope_mismatches
    )


def _normalized_record_contract_ok(species_name: str) -> bool:
    if species_name == "Homo sapiens":
        runtime_manifest = build_species_runtime_manifest("Homo sapiens", version="v66")
        return runtime_manifest.schema_version == "adna-runtime-manifest.v1"
    bundle = build_species_normalization_bundle(species_name)
    return (
        bundle.schema_version == "adna-nonhuman-normalization-bundle.v1"
        and all(item.schema_version == "adna-project-summary.v1" for item in bundle.project_summaries)
        and all(item.schema_version == "adna-study-summary.v1" for item in bundle.study_summaries)
    )


def _atlas_bundle_contract_ok() -> bool:
    from ..evidence import build_atlas_evidence_surface
    from ..reporting.bundles.paths import build_atlas_bundle_paths
    from ..reporting.bundles.summary_builders.atlas import (
        build_multi_country_bundle_manifest,
        build_multi_country_map_summary,
    )
    from ..reporting.bundles.summary_builders.published import (
        build_published_reports_summary,
    )
    from ..reporting.models import MultiCountryMapReport, PublishedReportsReport

    report = MultiCountryMapReport(
        title="Readiness Atlas",
        slug="readiness-atlas",
        version="v0",
        generated_on="1970-01-01",
        countries=("Sweden",),
        country_sample_counts={"Sweden": 0},
        total_unique_samples=0,
        output_dir=Path("docs/report/readiness-atlas"),
    )
    paths = build_atlas_bundle_paths(report.output_dir, report.slug, report.version)
    extra_artifacts = [
        ("Candidate site ranking CSV", paths.candidate_sites_csv_path.name),
        ("Candidate site ranking JSON", paths.candidate_sites_json_path.name),
        ("Candidate site ranking markdown", paths.candidate_sites_markdown_path.name),
        (
            "Candidate site sensitivity JSON",
            paths.candidate_site_sensitivity_json_path.name,
        ),
        (
            "Candidate site sensitivity markdown",
            paths.candidate_site_sensitivity_markdown_path.name,
        ),
        (
            "Candidate ranking engine manifest",
            paths.candidate_ranking_engine_manifest_path.name,
        ),
    ]
    summary = build_multi_country_map_summary(report, paths, extra_artifacts)
    manifest = build_multi_country_bundle_manifest(report, paths, extra_artifacts)
    evidence_surface = build_atlas_evidence_surface(
        countries=("Sweden",),
        human_localities=(),
        context_points=(),
    )
    published = build_published_reports_summary(
        PublishedReportsReport(
            version="v0",
            generated_on="1970-01-01",
            countries=("Sweden",),
            shared_map_dir=report.output_dir,
            country_output_dirs=(Path("docs/report/sweden"),),
            summary_path=Path("docs/report/published_reports_summary.json"),
        ),
        report,
    )
    return (
        summary.get("schema_version") == "atlas-bundle-summary.v1"
        and manifest.get("schema_version") == "atlas-bundle-manifest.v1"
        and manifest["artifacts"]["candidate_sites_json"] == paths.candidate_sites_json_path.name
        and manifest["artifacts"]["candidate_site_sensitivity_json"]
        == paths.candidate_site_sensitivity_json_path.name
        and manifest["artifacts"]["candidate_ranking_engine_manifest"]
        == paths.candidate_ranking_engine_manifest_path.name
        and summary["artifacts"]["evidence_surface_json"]
        == paths.evidence_surface_json_path.name
        and summary["artifacts"]["evidence_surface_markdown"]
        == paths.evidence_surface_markdown_path.name
        and manifest["artifacts"]["evidence_surface_json"]
        == paths.evidence_surface_json_path.name
        and manifest["artifacts"]["evidence_surface_markdown"]
        == paths.evidence_surface_markdown_path.name
        and evidence_surface.schema_version == "atlas-evidence-surface.v1"
        and evidence_surface.layers[0].layer_key == "homo_sapiens_direct"
        and published.get("schema_version") == "published-reports-summary.v1"
    )


def _ranking_provenance_ok() -> bool:
    from ..analysis import build_ranking_engine_manifest
    from ..analysis.reporting import (
        build_candidate_site_sensitivity_payload,
        build_candidate_sites_json_payload,
    )

    payload = build_candidate_sites_json_payload([])
    sensitivity_payload = build_candidate_site_sensitivity_payload(
        _build_candidate_sensitivity_stub()
    )
    engine_manifest = build_ranking_engine_manifest()
    return (
        payload.get("schema_version") == "candidate-site-ranking.v2"
        and "explicit evidence and missingness signals" in str(payload.get("evidence_boundary"))
        and payload.get("profile", {}).get("profile_name") == "atlas_exploration"
        and sensitivity_payload.get("schema_version") == "candidate-site-sensitivity.v1"
        and engine_manifest.schema_version == "candidate-ranking-engine-manifest.v1"
        and isinstance(payload.get("rows"), list)
    )


def _build_candidate_sensitivity_stub():
    from ..analysis.ranking import CandidateSensitivityReport

    return CandidateSensitivityReport(
        schema_version="candidate-site-sensitivity.v1",
        baseline_profile="atlas_exploration",
        compared_profiles=("atlas_exploration",),
        rows=(),
    )
