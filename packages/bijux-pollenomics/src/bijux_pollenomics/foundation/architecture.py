from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "ArchitectureStage",
    "CrossTreeSurfaceContract",
    "PackageOwnershipContract",
    "RepositoryArchitectureContract",
    "build_repository_architecture_contract",
]


@dataclass(frozen=True)
class ArchitectureStage:
    """One enduring stage in the repository lifecycle."""

    stage_key: str
    owner_module: str
    owner_path: str
    purpose: str
    tracked_inputs: tuple[str, ...]
    tracked_outputs: tuple[str, ...]
    upstream_stage_keys: tuple[str, ...]
    downstream_stage_keys: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "stage_key": self.stage_key,
            "owner_module": self.owner_module,
            "owner_path": self.owner_path,
            "purpose": self.purpose,
            "tracked_inputs": list(self.tracked_inputs),
            "tracked_outputs": list(self.tracked_outputs),
            "upstream_stage_keys": list(self.upstream_stage_keys),
            "downstream_stage_keys": list(self.downstream_stage_keys),
        }


@dataclass(frozen=True)
class PackageOwnershipContract:
    """Ownership rules for one distribution in the workspace."""

    distribution_name: str
    owner_package: str
    responsibility: str
    forbidden_ownership: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "distribution_name": self.distribution_name,
            "owner_package": self.owner_package,
            "responsibility": self.responsibility,
            "forbidden_ownership": list(self.forbidden_ownership),
        }


@dataclass(frozen=True)
class CrossTreeSurfaceContract:
    """Durable contract that links code, tracked data, and public docs."""

    surface_key: str
    repository_path: str
    owner_modules: tuple[str, ...]
    purpose: str

    def as_dict(self) -> dict[str, object]:
        return {
            "surface_key": self.surface_key,
            "repository_path": self.repository_path,
            "owner_modules": list(self.owner_modules),
            "purpose": self.purpose,
        }


@dataclass(frozen=True)
class RepositoryArchitectureContract:
    """Canonical architecture contract for the runtime and tracked surfaces."""

    lifecycle_stages: tuple[ArchitectureStage, ...]
    animal_adna_stages: tuple[ArchitectureStage, ...]
    package_split: tuple[PackageOwnershipContract, ...]
    cross_tree_surfaces: tuple[CrossTreeSurfaceContract, ...]
    allowed_broad_boundaries: dict[str, str]

    def as_dict(self) -> dict[str, object]:
        return {
            "lifecycle_stages": [stage.as_dict() for stage in self.lifecycle_stages],
            "animal_adna_stages": [
                stage.as_dict() for stage in self.animal_adna_stages
            ],
            "package_split": [contract.as_dict() for contract in self.package_split],
            "cross_tree_surfaces": [
                surface.as_dict() for surface in self.cross_tree_surfaces
            ],
            "allowed_broad_boundaries": dict(self.allowed_broad_boundaries),
        }


def build_repository_architecture_contract() -> RepositoryArchitectureContract:
    """Return the canonical repository architecture contract."""
    lifecycle_stages = (
        ArchitectureStage(
            stage_key="runtime_commands",
            owner_module="bijux_pollenomics.command_line",
            owner_path="packages/bijux-pollenomics/src/bijux_pollenomics/command_line",
            purpose="turn command arguments into one governed runtime action",
            tracked_inputs=("cli arguments", "tracked repository roots"),
            tracked_outputs=("resolved runtime handlers",),
            upstream_stage_keys=(),
            downstream_stage_keys=("source_collection",),
        ),
        ArchitectureStage(
            stage_key="source_collection",
            owner_module="bijux_pollenomics.data_downloader",
            owner_path="packages/bijux-pollenomics/src/bijux_pollenomics/data_downloader",
            purpose="collect source-family data and normalize raw context artifacts",
            tracked_inputs=("source APIs", "tracked source inventories"),
            tracked_outputs=("data/*/raw", "data/*/normalized"),
            upstream_stage_keys=("runtime_commands",),
            downstream_stage_keys=("evidence_normalization",),
        ),
        ArchitectureStage(
            stage_key="evidence_normalization",
            owner_module="bijux_pollenomics.adna",
            owner_path="packages/bijux-pollenomics/src/bijux_pollenomics/adna",
            purpose="recover sample, site, chronology, coordinate, and species-owned evidence",
            tracked_inputs=("data/adna/governance", "data/adna/source_library"),
            tracked_outputs=("data/adna/normalized", "data/adna/species"),
            upstream_stage_keys=("source_collection",),
            downstream_stage_keys=("evidence_review", "publication_assembly"),
        ),
        ArchitectureStage(
            stage_key="evidence_review",
            owner_module="bijux_pollenomics.foundation",
            owner_path="packages/bijux-pollenomics/src/bijux_pollenomics/foundation",
            purpose="publish repository-truth, release, and ranking review surfaces",
            tracked_inputs=("data/adna/species", "docs/report"),
            tracked_outputs=("docs/report/*review*", "docs/report/*audit*"),
            upstream_stage_keys=("evidence_normalization",),
            downstream_stage_keys=("publication_assembly", "public_artifact_writing"),
        ),
        ArchitectureStage(
            stage_key="publication_assembly",
            owner_module="bijux_pollenomics.reporting",
            owner_path="packages/bijux-pollenomics/src/bijux_pollenomics/reporting",
            purpose="assemble atlas, country, and scope-filtered publication bundles",
            tracked_inputs=("data", "data/adna/species", "review surfaces"),
            tracked_outputs=("bundle payloads", "map payloads", "markdown payloads"),
            upstream_stage_keys=("evidence_normalization", "evidence_review"),
            downstream_stage_keys=("public_artifact_writing",),
        ),
        ArchitectureStage(
            stage_key="public_artifact_writing",
            owner_module="bijux_pollenomics.reporting.rendering",
            owner_path=(
                "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/rendering"
            ),
            purpose="write governed publication artifacts into docs/report",
            tracked_inputs=("bundle payloads", "review payloads", "context layers"),
            tracked_outputs=("docs/report",),
            upstream_stage_keys=("publication_assembly", "evidence_review"),
            downstream_stage_keys=(),
        ),
    )
    animal_adna_stages = (
        ArchitectureStage(
            stage_key="animal_adna_intake",
            owner_module="bijux_pollenomics.adna.source_library",
            owner_path=(
                "packages/bijux-pollenomics/src/"
                "bijux_pollenomics/adna/source_library.py"
            ),
            purpose="admit projects, papers, and supplements into tracked intake",
            tracked_inputs=("ENA accessions", "paper DOIs", "supplements"),
            tracked_outputs=("data/adna/governance/source_library",),
            upstream_stage_keys=(),
            downstream_stage_keys=("animal_adna_extraction",),
        ),
        ArchitectureStage(
            stage_key="animal_adna_extraction",
            owner_module="bijux_pollenomics.adna.sample_master",
            owner_path=(
                "packages/bijux-pollenomics/src/bijux_pollenomics/adna/sample_master.py"
            ),
            purpose="recover sample-owned rows, site claims, and chronology evidence",
            tracked_inputs=("source-library reviews", "archive manifests"),
            tracked_outputs=("data/adna/intermediate", "data/adna/governance/reviews"),
            upstream_stage_keys=("animal_adna_intake",),
            downstream_stage_keys=("animal_adna_normalization",),
        ),
        ArchitectureStage(
            stage_key="animal_adna_normalization",
            owner_module="bijux_pollenomics.adna.normalization",
            owner_path=(
                "packages/bijux-pollenomics/src/bijux_pollenomics/adna/normalization.py"
            ),
            purpose="materialize species-owned normalized sample and locality records",
            tracked_inputs=("sample-owned evidence rows",),
            tracked_outputs=("data/adna/species", "data/adna/final"),
            upstream_stage_keys=("animal_adna_extraction",),
            downstream_stage_keys=("animal_adna_validation", "animal_adna_publication"),
        ),
        ArchitectureStage(
            stage_key="animal_adna_validation",
            owner_module="bijux_pollenomics.adna.reviews",
            owner_path="packages/bijux-pollenomics/src/bijux_pollenomics/adna/reviews.py",
            purpose="classify blockers, conflicts, and evidence honesty before publication",
            tracked_inputs=("normalized species bundles", "review ledgers"),
            tracked_outputs=("governance review surfaces", "release gates"),
            upstream_stage_keys=("animal_adna_normalization",),
            downstream_stage_keys=("animal_adna_publication",),
        ),
        ArchitectureStage(
            stage_key="animal_adna_publication",
            owner_module="bijux_pollenomics.reporting.adna",
            owner_path="packages/bijux-pollenomics/src/bijux_pollenomics/reporting/adna",
            purpose="publish atlas, country, and public review outputs from validated animal rows",
            tracked_inputs=("data/adna/final", "validation reviews"),
            tracked_outputs=("docs/report",),
            upstream_stage_keys=("animal_adna_normalization", "animal_adna_validation"),
            downstream_stage_keys=(),
        ),
    )
    package_split = (
        PackageOwnershipContract(
            distribution_name="bijux-pollenomics",
            owner_package="bijux_pollenomics",
            responsibility=(
                "canonical runtime, scientific logic, and publication behavior"
            ),
            forbidden_ownership=(),
        ),
        PackageOwnershipContract(
            distribution_name="bijux-pollenomics-dev",
            owner_package="bijux_pollenomics_dev",
            responsibility="maintainer checks, docs integrity, release support",
            forbidden_ownership=(
                "project intake",
                "source collection",
                "species normalization",
                "atlas publication logic",
            ),
        ),
        PackageOwnershipContract(
            distribution_name="pollenomics",
            owner_package="pollenomics",
            responsibility="compatibility alias for the canonical runtime package",
            forbidden_ownership=(
                "independent scientific logic",
                "independent data collection",
                "independent publication logic",
            ),
        ),
    )
    cross_tree_surfaces = (
        CrossTreeSurfaceContract(
            surface_key="tracked_source_state",
            repository_path="data/",
            owner_modules=(
                "bijux_pollenomics.data_downloader",
                "bijux_pollenomics.adna",
            ),
            purpose="checked-in raw, normalized, and reviewed evidence surfaces",
        ),
        CrossTreeSurfaceContract(
            surface_key="public_publication_state",
            repository_path="docs/report/",
            owner_modules=(
                "bijux_pollenomics.reporting",
                "bijux_pollenomics.foundation",
            ),
            purpose="governed public outputs, review surfaces, and release-facing artifacts",
        ),
        CrossTreeSurfaceContract(
            surface_key="reader_explanation_state",
            repository_path="docs/",
            owner_modules=(
                "bijux_pollenomics.foundation",
                "bijux_pollenomics_dev.docs",
            ),
            purpose="handbook explanations that interpret the tracked code and data surfaces",
        ),
    )
    return RepositoryArchitectureContract(
        lifecycle_stages=lifecycle_stages,
        animal_adna_stages=animal_adna_stages,
        package_split=package_split,
        cross_tree_surfaces=cross_tree_surfaces,
        allowed_broad_boundaries={
            "core": "low-level shared primitives such as files, text, geojson, and HTTP",
            "foundation": (
                "repository truth, release posture, architecture contracts, and ownership maps"
            ),
        },
    )
