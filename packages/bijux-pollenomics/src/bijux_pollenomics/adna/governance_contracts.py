from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from ..core.files import write_json, write_text
from .paths import adna_governance_root, adna_source_library_root

__all__ = [
    "build_adna_governance_role_registry",
    "build_source_library_project_surface_contract",
    "materialize_adna_governance_contracts",
    "validate_source_library_project_surfaces",
]


@dataclass(frozen=True)
class GovernanceRoleRecord:
    role_key: str
    display_name: str
    path_pattern: str
    owned_responsibility: str
    example_artifacts: tuple[str, ...]


@dataclass(frozen=True)
class ProjectSurfaceRequirement:
    artifact_key: str
    required_files: tuple[str, ...]
    purpose: str


def build_adna_governance_role_registry() -> dict[str, object]:
    """Build the durable role split for the animal ancient-DNA governance tree."""
    rows = (
        GovernanceRoleRecord(
            role_key="source_recovery",
            display_name="Source recovery",
            path_pattern="data/adna/governance/source_library/**",
            owned_responsibility=(
                "capture archive metadata, project dossiers, paper manifests, and "
                "per-project recovery evidence before species normalization"
            ),
            example_artifacts=(
                "data/adna/governance/source_library/project_registry.json",
                "data/adna/governance/source_library/projects/<project_accession>/bundle_manifest.json",
            ),
        ),
        GovernanceRoleRecord(
            role_key="cross_species_review",
            display_name="Cross-species review",
            path_pattern="data/adna/governance/*.json",
            owned_responsibility=(
                "publish truth, caveats, coverage posture, and evidence-honesty "
                "surfaces that compare projects across species"
            ),
            example_artifacts=(
                "data/adna/governance/animal_sample_foundation_truth.json",
                "data/adna/governance/cross_species_map_readiness.json",
                "data/adna/governance/coordinate_caveat_surface.json",
            ),
        ),
        GovernanceRoleRecord(
            role_key="publication_accounting",
            display_name="Publication accounting",
            path_pattern="data/adna/governance/*product*.json",
            owned_responsibility=(
                "state what the repository is allowed to ship and how publication "
                "surfaces are audited against foundation truth"
            ),
            example_artifacts=(
                "data/adna/governance/animal_sample_product_contract.json",
                "data/adna/governance/shipped_product_audit.json",
            ),
        ),
    )
    return {
        "schema_version": "adna-governance-role-registry.v1",
        "row_count": len(rows),
        "rows": [asdict(row) for row in rows],
    }


def build_source_library_project_surface_contract() -> dict[str, object]:
    """Build the file contract that every tracked project directory must satisfy."""
    requirements = (
        ProjectSurfaceRequirement(
            artifact_key="source_bundle_identity",
            required_files=(
                "bundle_manifest.json",
                "intake_dossier.json",
                "curation_note.md",
            ),
            purpose="state tracked project identity, blockers, and intake posture",
        ),
        ProjectSurfaceRequirement(
            artifact_key="sample_foundation",
            required_files=("sample_master.json", "sample_master.csv"),
            purpose="publish stable sample identity rows before downstream normalization",
        ),
        ProjectSurfaceRequirement(
            artifact_key="site_linkage",
            required_files=("sample_sites.json", "sample_sites.csv"),
            purpose="publish the stable sample-to-site mapping for one project",
        ),
        ProjectSurfaceRequirement(
            artifact_key="locality_review",
            required_files=("locality_worksheet.json", "locality_worksheet.csv"),
            purpose="publish the project-level locality worksheet used for locality review",
        ),
        ProjectSurfaceRequirement(
            artifact_key="locality_evidence",
            required_files=(
                "sample_locality_evidence.json",
                "sample_locality_evidence.csv",
            ),
            purpose="publish per-sample locality evidence packets",
        ),
        ProjectSurfaceRequirement(
            artifact_key="chronology_summary",
            required_files=("sample_chronology.json", "sample_chronology.csv"),
            purpose="publish the project-level chronology summary surface",
        ),
        ProjectSurfaceRequirement(
            artifact_key="chronology_evidence",
            required_files=(
                "sample_chronology_evidence.json",
                "sample_chronology_evidence.csv",
            ),
            purpose="publish per-sample chronology evidence packets",
        ),
        ProjectSurfaceRequirement(
            artifact_key="chronology_provenance",
            required_files=(
                "sample_chronology_provenance.json",
                "sample_chronology_provenance.csv",
            ),
            purpose=(
                "publish per-sample chronology provenance packets with wording, "
                "source locator, normalization rule, and uncertainty posture"
            ),
        ),
    )
    return {
        "schema_version": "source-library-project-surface-contract.v1",
        "project_path_pattern": (
            "data/adna/governance/source_library/projects/<project_accession>/"
        ),
        "artifact_groups": [asdict(requirement) for requirement in requirements],
    }


def validate_source_library_project_surfaces(output_root: Path) -> None:
    """Validate that each tracked project directory satisfies the shared surface contract."""
    output_root = Path(output_root)
    source_root = adna_source_library_root(output_root)
    project_contract = build_source_library_project_surface_contract()
    project_root = source_root / "projects"
    if not project_root.is_dir():
        raise ValueError(f"source-library project root missing: {project_root}")
    required_groups = tuple(project_contract["artifact_groups"])
    for directory in sorted(
        child for child in project_root.iterdir() if child.is_dir()
    ):
        for group in required_groups:
            for filename in group["required_files"]:
                path = directory / filename
                if not path.is_file():
                    raise ValueError(
                        "source-library project surface contract violation: "
                        f"missing {path}"
                    )


def materialize_adna_governance_contracts(output_root: Path) -> None:
    """Write durable contract surfaces for the animal ancient-DNA governance tree."""
    output_root = Path(output_root)
    governance_root = adna_governance_root(output_root)
    source_root = adna_source_library_root(output_root)
    governance_root.mkdir(parents=True, exist_ok=True)
    source_root.mkdir(parents=True, exist_ok=True)
    write_json(
        governance_root / "surface_role_registry.json",
        build_adna_governance_role_registry(),
    )
    write_text(
        governance_root / "surface_role_registry.md",
        _render_adna_governance_role_registry_markdown(),
    )
    write_json(
        source_root / "project_surface_contract.json",
        build_source_library_project_surface_contract(),
    )
    validate_source_library_project_surfaces(output_root)


def _render_adna_governance_role_registry_markdown() -> str:
    payload = build_adna_governance_role_registry()
    rows = payload["rows"]
    lines = [
        "# Animal ancient-DNA governance roles",
        "",
        "The governance tree carries three distinct responsibilities so recovery plumbing, cross-species review, and publication accounting do not blur into one vague bucket.",
        "",
        "| Role | Path pattern | Responsibility |",
        "| --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['display_name']} | `{row['path_pattern']}` | {row['owned_responsibility']} |"
        )
    lines.extend(
        [
            "",
            "## Examples",
            "",
            "- Source recovery: `data/adna/governance/source_library/project_registry.json`",
            "- Cross-species review: `data/adna/governance/animal_sample_foundation_truth.json`",
            "- Publication accounting: `data/adna/governance/shipped_product_audit.json`",
            "",
        ]
    )
    return "\n".join(lines)
