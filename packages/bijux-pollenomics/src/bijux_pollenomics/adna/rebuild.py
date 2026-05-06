from __future__ import annotations

from dataclasses import dataclass

from .curation import build_species_curation_manifest
from .integrity import build_archive_integrity_report
from .layout import build_species_layout
from .manifests import build_species_manifest
from .normalization import build_species_normalization_bundle
from .reviews import build_species_project_manifest, build_species_review_packet
from .runtime import build_species_runtime_manifest

__all__ = [
    "AdnaArtifactPlanEntry",
    "AdnaSpeciesArtifactPlan",
    "build_species_artifact_plan",
]


@dataclass(frozen=True)
class AdnaArtifactPlanEntry:
    """One deterministic artifact path and payload for a species rebuild."""

    target_path: str
    artifact_kind: str
    payload: dict[str, object]

    def as_dict(self) -> dict[str, object]:
        return {
            "target_path": self.target_path,
            "artifact_kind": self.artifact_kind,
            "payload": self.payload,
        }


@dataclass(frozen=True)
class AdnaSpeciesArtifactPlan:
    """Deterministic manifest of governed species rebuild artifacts."""

    schema_version: str
    species_latin_name: str
    entries: tuple[AdnaArtifactPlanEntry, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "species_latin_name": self.species_latin_name,
            "entries": [entry.as_dict() for entry in self.entries],
        }


def build_species_artifact_plan(species_name: str) -> AdnaSpeciesArtifactPlan:
    """Build the deterministic governed artifact plan for one species rebuild."""
    species_manifest = build_species_manifest(species_name)
    species_layout = build_species_layout(species_name)
    curation_manifest = build_species_curation_manifest(species_name)
    project_manifest = build_species_project_manifest(species_name)
    normalization_bundle = build_species_normalization_bundle(species_name)
    review_packet = build_species_review_packet(species_name)
    integrity_report = build_archive_integrity_report(species_name=species_name)
    runtime_manifest = build_species_runtime_manifest(species_name)
    entries = (
        AdnaArtifactPlanEntry(
            target_path=f"{species_layout.manifests_dir}/species_manifest.json",
            artifact_kind="species_manifest",
            payload=species_manifest.as_dict(),
        ),
        AdnaArtifactPlanEntry(
            target_path=f"{species_layout.manifests_dir}/curation_manifest.json",
            artifact_kind="curation_manifest",
            payload=curation_manifest.as_dict(),
        ),
        AdnaArtifactPlanEntry(
            target_path=f"{species_layout.manifests_dir}/project_manifest.json",
            artifact_kind="project_manifest",
            payload=project_manifest.as_dict(),
        ),
        AdnaArtifactPlanEntry(
            target_path=f"{species_layout.manifests_dir}/runtime_manifest.json",
            artifact_kind="runtime_manifest",
            payload=runtime_manifest.as_dict(),
        ),
        AdnaArtifactPlanEntry(
            target_path=f"{species_layout.manifests_dir}/normalization_bundle.json",
            artifact_kind="normalization_bundle",
            payload=normalization_bundle.as_dict(),
        ),
        AdnaArtifactPlanEntry(
            target_path=f"{species_layout.review_dir}/species_review.json",
            artifact_kind="species_review",
            payload=review_packet.as_dict(),
        ),
        AdnaArtifactPlanEntry(
            target_path=f"{species_layout.review_dir}/archive_integrity.json",
            artifact_kind="archive_integrity",
            payload=integrity_report.as_dict(),
        ),
    )
    return AdnaSpeciesArtifactPlan(
        schema_version="adna-species-artifact-plan.v1",
        species_latin_name=species_manifest.species.latin_name,
        entries=tuple(sorted(entries, key=lambda entry: entry.target_path)),
    )
