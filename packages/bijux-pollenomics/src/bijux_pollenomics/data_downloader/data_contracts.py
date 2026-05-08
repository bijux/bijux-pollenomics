from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

__all__ = [
    "DataFactOwnershipRecord",
    "EvidenceArtifactContractRecord",
    "build_contract_artifact_paths",
    "build_evidence_artifact_contract_payload",
    "build_source_fact_ownership_payload",
]


@dataclass(frozen=True)
class DataFactOwnershipRecord:
    fact_key: str
    display_name: str
    evidence_scope: str
    governing_surface_path: str
    supporting_surface_paths: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class EvidenceArtifactContractRecord:
    artifact_key: str
    artifact_scope: str
    canonical_path_pattern: str
    governing_surface_path: str
    companion_surface_patterns: tuple[str, ...]
    purpose: str
    required_artifacts: tuple[str, ...]


def build_contract_artifact_paths(output_root: Path) -> dict[str, str]:
    """Build the canonical contract-artifact path mapping for one data root."""
    output_root = Path(output_root)
    return {
        "source_family_contracts": str(output_root / "source_family_contracts.json"),
        "source_family_evidence_stage_matrix": str(
            output_root / "source_family_evidence_stage_matrix.json"
        ),
        "source_fact_ownership_registry": str(
            output_root / "source_fact_ownership_registry.json"
        ),
        "evidence_artifact_contracts": str(
            output_root / "evidence_artifact_contracts.json"
        ),
        "adna_governance_role_registry": str(
            output_root / "adna" / "governance" / "surface_role_registry.json"
        ),
        "source_library_project_surface_contract": str(
            output_root
            / "adna"
            / "governance"
            / "source_library"
            / "project_surface_contract.json"
        ),
    }


def build_source_fact_ownership_payload() -> dict[str, object]:
    """Build the registry that names one governing surface for recurring facts."""
    rows = (
        DataFactOwnershipRecord(
            fact_key="human_archive_program_identity",
            display_name="Human ancient-DNA source program identity",
            evidence_scope="source_family",
            governing_surface_path="data/aadr",
            supporting_surface_paths=(
                "data/adna/species/homo_sapiens/raw/aadr",
                "data/collection_summary.json",
            ),
            reason="The governed AADR snapshot is the root identity for human archive provenance.",
        ),
        DataFactOwnershipRecord(
            fact_key="animal_project_inventory",
            display_name="Animal ancient-DNA project inventory",
            evidence_scope="project",
            governing_surface_path="data/adna/governance/source_library/project_registry.json",
            supporting_surface_paths=(
                "data/adna/governance/source_library/tracked_project_and_paper_inventory.json",
                "data/adna/governance/source_library/projects/<project_accession>/bundle_manifest.json",
            ),
            reason="Cross-project project registry rows govern whether one archive project is tracked at all.",
        ),
        DataFactOwnershipRecord(
            fact_key="animal_paper_inventory",
            display_name="Animal ancient-DNA paper inventory",
            evidence_scope="paper",
            governing_surface_path="data/adna/governance/source_library/paper_registry.json",
            supporting_surface_paths=(
                "data/adna/governance/source_library/tracked_project_and_paper_inventory.json",
                "data/adna/governance/source_library/papers/<paper_doi_slug>/supplementary_manifest.json",
            ),
            reason="Paper registry rows govern which publication surfaces anchor the animal source program.",
        ),
        DataFactOwnershipRecord(
            fact_key="animal_sample_identity",
            display_name="Animal sample identity",
            evidence_scope="sample",
            governing_surface_path="data/adna/governance/source_library/projects/<project_accession>/sample_master.json",
            supporting_surface_paths=(
                "data/adna/species/<latin_name>/normalized/sample_records.json",
                "data/adna/governance/source_library/project_sample_master_completeness.json",
            ),
            reason="Per-project sample masters govern the stable sample row before cross-species normalization rolls it up.",
        ),
        DataFactOwnershipRecord(
            fact_key="animal_sample_site_linkage",
            display_name="Animal sample-to-site linkage",
            evidence_scope="site",
            governing_surface_path="data/adna/governance/source_library/projects/<project_accession>/sample_sites.json",
            supporting_surface_paths=(
                "data/adna/governance/source_library/project_sample_site_review.json",
                "data/adna/species/<latin_name>/normalized/site_evidence.json",
            ),
            reason="Per-project sample-site tables govern the stable site attachment for one sample lineage.",
        ),
        DataFactOwnershipRecord(
            fact_key="animal_sample_locality_claims",
            display_name="Animal locality evidence claims",
            evidence_scope="sample",
            governing_surface_path="data/adna/governance/source_library/projects/<project_accession>/sample_locality_evidence.json",
            supporting_surface_paths=(
                "data/adna/governance/source_library/locality_worksheet.json",
                "data/adna/governance/source_library/sample_locality_conflict_ledger.json",
                "data/adna/species/<latin_name>/normalized/locality_summaries.json",
            ),
            reason="Locality evidence packets govern locality provenance before species normalization and atlas publication.",
        ),
        DataFactOwnershipRecord(
            fact_key="animal_sample_chronology_claims",
            display_name="Animal chronology evidence claims",
            evidence_scope="sample",
            governing_surface_path="data/adna/governance/source_library/projects/<project_accession>/sample_chronology_evidence.json",
            supporting_surface_paths=(
                "data/adna/governance/source_library/project_sample_chronology_review.json",
                "data/adna/species/<latin_name>/normalized/sample_records.json",
            ),
            reason="Chronology evidence packets govern temporal support before downstream species and atlas surfaces reuse it.",
        ),
        DataFactOwnershipRecord(
            fact_key="animal_species_normalized_records",
            display_name="Animal species normalized records",
            evidence_scope="species",
            governing_surface_path="data/adna/species/<latin_name>/normalized/sample_records.json",
            supporting_surface_paths=(
                "data/adna/species/<latin_name>/normalized/site_evidence.json",
                "data/adna/species/<latin_name>/normalized/project_summaries.json",
            ),
            reason="Species-owned normalized sample records are the governing cross-project merge surface for one taxon.",
        ),
        DataFactOwnershipRecord(
            fact_key="animal_foundation_truth",
            display_name="Animal sample foundation truth",
            evidence_scope="cross_species_review",
            governing_surface_path="data/adna/governance/animal_sample_foundation_truth.json",
            supporting_surface_paths=(
                "data/adna/governance/animal_sample_product_contract.json",
                "data/adna/governance/cross_species_map_readiness.json",
            ),
            reason="Foundation truth governs whether the repository can claim sample-backed animal coverage with a straight face.",
        ),
        DataFactOwnershipRecord(
            fact_key="animal_atlas_candidates",
            display_name="Animal atlas publication candidates",
            evidence_scope="region",
            governing_surface_path="data/adna/final/atlas/animal_atlas_point_candidates.json",
            supporting_surface_paths=(
                "docs/report/animal_output_honesty_review.json",
                "docs/report/nordic-atlas/animal_points.geojson",
            ),
            reason="Atlas candidate rows govern region-level publication inputs before public map bundles reinterpret them.",
        ),
        DataFactOwnershipRecord(
            fact_key="country_publication_bundles",
            display_name="Country publication bundles",
            evidence_scope="country",
            governing_surface_path="docs/report/<country_slug>/<country_slug>_aadr_<version>_bundle.json",
            supporting_surface_paths=(
                "docs/report/published_reports_summary.json",
                "docs/report/<country_slug>/README.md",
            ),
            reason="Country bundles govern public country deliveries; summaries and readmes only explain the same artifact set.",
        ),
        DataFactOwnershipRecord(
            fact_key="landclim_pollen_context",
            display_name="LandClim pollen context",
            evidence_scope="source_family",
            governing_surface_path="data/landclim/normalized/nordic_pollen_site_sequences.geojson",
            supporting_surface_paths=(
                "data/landclim/normalized/landclim_summary.json",
                "docs/report/nordic-atlas/nordic_pollen_sites.geojson",
            ),
            reason="The normalized LandClim sequence surface is the governing pollen-context layer for site-level use.",
        ),
        DataFactOwnershipRecord(
            fact_key="neotoma_pollen_context",
            display_name="Neotoma pollen context",
            evidence_scope="source_family",
            governing_surface_path="data/neotoma/normalized/nordic_pollen_sites.geojson",
            supporting_surface_paths=(
                "data/neotoma/raw/neotoma_pollen_dataset_inventory.json",
                "docs/report/nordic-atlas/nordic_environmental_sites.geojson",
            ),
            reason="The normalized Neotoma site layer governs what survives into publication-grade pollen context.",
        ),
        DataFactOwnershipRecord(
            fact_key="sead_archaeology_context",
            display_name="SEAD archaeology context",
            evidence_scope="source_family",
            governing_surface_path="data/sead/normalized/nordic_environmental_sites.geojson",
            supporting_surface_paths=("data/sead/raw/nordic_sites.json",),
            reason="The normalized SEAD site layer governs contextual archaeology that the repository is willing to map.",
        ),
        DataFactOwnershipRecord(
            fact_key="raa_archaeology_context",
            display_name="RAÄ archaeology context",
            evidence_scope="source_family",
            governing_surface_path="data/raa/normalized/sweden_archaeology_layer.json",
            supporting_surface_paths=(
                "data/raa/normalized/sweden_archaeology_density.geojson",
            ),
            reason="The normalized RAÄ layer governs Swedish archaeology context before density rendering publishes it.",
        ),
        DataFactOwnershipRecord(
            fact_key="country_boundary_framing",
            display_name="Country boundary framing",
            evidence_scope="source_family",
            governing_surface_path="data/boundaries/normalized/nordic_country_boundaries.geojson",
            supporting_surface_paths=(
                "docs/report/nordic-atlas/nordic_country_boundaries.geojson",
            ),
            reason="Normalized boundary geometry governs region and country framing across every published map.",
        ),
    )
    return {
        "schema_version": "source-fact-ownership-registry.v1",
        "row_count": len(rows),
        "rows": [asdict(row) for row in rows],
    }


def build_evidence_artifact_contract_payload() -> dict[str, object]:
    """Build the file-contract standard for recurring artifact scopes."""
    rows = (
        EvidenceArtifactContractRecord(
            artifact_key="project_source_bundle",
            artifact_scope="project",
            canonical_path_pattern="data/adna/governance/source_library/projects/<project_accession>/bundle_manifest.json",
            governing_surface_path="data/adna/governance/source_library/project_surface_contract.json",
            companion_surface_patterns=(
                "data/adna/governance/source_library/projects/<project_accession>/intake_dossier.json",
                "data/adna/governance/source_library/projects/<project_accession>/curation_note.md",
            ),
            purpose="govern which source artifacts, blockers, and curation posture belong to one tracked project",
            required_artifacts=("bundle_manifest.json", "intake_dossier.json", "curation_note.md"),
        ),
        EvidenceArtifactContractRecord(
            artifact_key="paper_supporting_materials",
            artifact_scope="paper",
            canonical_path_pattern="data/adna/governance/source_library/papers/<paper_doi_slug>/supplementary_manifest.json",
            governing_surface_path="data/evidence_artifact_contracts.json",
            companion_surface_patterns=(
                "data/adna/governance/source_library/papers/<paper_doi_slug>/article.html",
                "data/adna/governance/source_library/papers/<paper_doi_slug>/supplementary/*",
            ),
            purpose="govern which article and supplementary assets back one tracked paper surface",
            required_artifacts=("supplementary_manifest.json",),
        ),
        EvidenceArtifactContractRecord(
            artifact_key="sample_foundation_surface",
            artifact_scope="sample",
            canonical_path_pattern="data/adna/governance/source_library/projects/<project_accession>/sample_master.json",
            governing_surface_path="data/source_fact_ownership_registry.json",
            companion_surface_patterns=(
                "data/adna/governance/source_library/projects/<project_accession>/sample_locality_evidence.json",
                "data/adna/governance/source_library/projects/<project_accession>/sample_chronology_evidence.json",
            ),
            purpose="govern one project-owned sample foundation before species normalization reuses it",
            required_artifacts=(
                "sample_master.json",
                "sample_locality_evidence.json",
                "sample_chronology_evidence.json",
            ),
        ),
        EvidenceArtifactContractRecord(
            artifact_key="site_evidence_surface",
            artifact_scope="site",
            canonical_path_pattern="data/adna/governance/source_library/projects/<project_accession>/sample_sites.json",
            governing_surface_path="data/source_fact_ownership_registry.json",
            companion_surface_patterns=(
                "data/adna/governance/source_library/projects/<project_accession>/locality_worksheet.json",
            ),
            purpose="govern sample-to-site linkage and site evidence review for one project",
            required_artifacts=("sample_sites.json", "locality_worksheet.json"),
        ),
        EvidenceArtifactContractRecord(
            artifact_key="regional_atlas_bundle",
            artifact_scope="region",
            canonical_path_pattern="data/adna/final/atlas/animal_atlas_point_candidates.json",
            governing_surface_path="data/source_fact_ownership_registry.json",
            companion_surface_patterns=(
                "docs/report/nordic-atlas/nordic-atlas_bundle.json",
                "docs/report/nordic-atlas/animal_points.geojson",
            ),
            purpose="govern shared region-level publication inputs and downstream bundle assembly",
            required_artifacts=("animal_atlas_point_candidates.json",),
        ),
        EvidenceArtifactContractRecord(
            artifact_key="country_publication_bundle",
            artifact_scope="country",
            canonical_path_pattern="docs/report/<country_slug>/<country_slug>_aadr_<version>_bundle.json",
            governing_surface_path="data/source_fact_ownership_registry.json",
            companion_surface_patterns=(
                "docs/report/<country_slug>/<country_slug>_aadr_<version>.csv",
                "docs/report/<country_slug>/<country_slug>_aadr_<version>.json",
            ),
            purpose="govern the durable published country delivery for one geography and version",
            required_artifacts=("bundle.json", "csv", "json"),
        ),
    )
    return {
        "schema_version": "evidence-artifact-contracts.v1",
        "row_count": len(rows),
        "rows": [asdict(row) for row in rows],
    }
