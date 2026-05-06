from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..config import DEFAULT_AADR_VERSION, DEFAULT_DATA_ROOT
from .ena import build_species_archive_projects
from .manifests import AdnaSpeciesManifest, build_species_manifest
from .species import AdnaSpeciesDefinition

__all__ = [
    "ADNA_PROVENANCE_QUALITIES",
    "ADNA_REVIEW_STRENGTHS",
    "AdnaSampleQuery",
    "AdnaSourceBundle",
    "AdnaSpeciesRuntimeManifest",
    "build_species_runtime_manifest",
    "load_species_samples",
]

ADNA_REVIEW_STRENGTHS = (
    "curated_release_metadata",
    "primary_paper_pinned",
    "archive_verified_needs_paper_pinning",
    "comparator_only",
    "manual_review_required",
)
ADNA_PROVENANCE_QUALITIES = (
    "release_manifest_pinned",
    "archive_project_catalog",
    "manual_curation_only",
)


@dataclass(frozen=True)
class AdnaSourceBundle:
    """Typed source-bundle contract for one species runtime manifest."""

    source_family: str
    source_release: str
    bundle_kind: str
    tracked_root: str
    release_manifest_path: str
    dataset_names: tuple[str, ...]
    record_modality: str
    review_strength: str
    provenance_quality: str

    def as_dict(self) -> dict[str, object]:
        return {
            "source_family": self.source_family,
            "source_release": self.source_release,
            "bundle_kind": self.bundle_kind,
            "tracked_root": self.tracked_root,
            "release_manifest_path": self.release_manifest_path,
            "dataset_names": list(self.dataset_names),
            "record_modality": self.record_modality,
            "review_strength": self.review_strength,
            "provenance_quality": self.provenance_quality,
        }


@dataclass(frozen=True)
class AdnaSpeciesRuntimeManifest:
    """Runtime manifest that turns a species definition into loadable evidence bundles."""

    schema_version: str
    species_manifest: AdnaSpeciesManifest
    source_bundles: tuple[AdnaSourceBundle, ...]
    analysis_boundary: str
    runtime_ready: bool

    @property
    def species(self) -> AdnaSpeciesDefinition:
        return self.species_manifest.species

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "species_manifest": self.species_manifest.as_dict(),
            "source_bundles": [bundle.as_dict() for bundle in self.source_bundles],
            "analysis_boundary": self.analysis_boundary,
            "runtime_ready": self.runtime_ready,
        }


@dataclass(frozen=True)
class AdnaSampleQuery:
    """Filter contract for loading species-aware ancient-DNA samples."""

    political_entity: str | None = None
    locality_token: str | None = None
    dataset_names: tuple[str, ...] = ()
    modalities: tuple[str, ...] = ()
    provenance_qualities: tuple[str, ...] = ()
    review_strengths: tuple[str, ...] = ()
    time_start_bp: int | None = None
    time_end_bp: int | None = None

    def normalized(self) -> AdnaSampleQuery:
        return AdnaSampleQuery(
            political_entity=_clean_optional(self.political_entity),
            locality_token=_clean_optional(self.locality_token),
            dataset_names=_normalize_values(self.dataset_names),
            modalities=_normalize_values(self.modalities),
            provenance_qualities=_normalize_values(self.provenance_qualities),
            review_strengths=_normalize_values(self.review_strengths),
            time_start_bp=self.time_start_bp,
            time_end_bp=self.time_end_bp,
        )


def build_species_runtime_manifest(
    species_name: str,
    *,
    data_root: Path = DEFAULT_DATA_ROOT,
    version: str = DEFAULT_AADR_VERSION,
) -> AdnaSpeciesRuntimeManifest:
    """Build the loadable runtime manifest for one species."""
    species_manifest = build_species_manifest(species_name)
    species = species_manifest.species
    if species.latin_name == "Homo sapiens":
        from .homo_sapiens import build_homo_sapiens_runtime_manifest

        return build_homo_sapiens_runtime_manifest(data_root=data_root, version=version)

    archive_projects = build_species_archive_projects(species_name)
    source_bundles = tuple(
        AdnaSourceBundle(
            source_family=project.source_family,
            source_release=project.project_accession,
            bundle_kind="curated_archive_project",
            tracked_root=f"{species_manifest.data_root}/raw/{project.source_family.casefold()}",
            release_manifest_path=f"{species_manifest.data_root}/review/{project.project_accession.casefold()}.json",
            dataset_names=(project.project_accession,),
            record_modality="archive_reads",
            review_strength=(
                "comparator_only"
                if species.support_status == "comparator_only"
                else "archive_verified_needs_paper_pinning"
            ),
            provenance_quality="archive_project_catalog",
        )
        for project in archive_projects
    )
    return AdnaSpeciesRuntimeManifest(
        schema_version="adna-runtime-manifest.v1",
        species_manifest=species_manifest,
        source_bundles=source_bundles,
        analysis_boundary=(
            "Curated source bundles are known, but normalized runtime ingestion is "
            "not yet implemented for this species."
        ),
        runtime_ready=False,
    )


def load_species_samples(
    manifest: AdnaSpeciesRuntimeManifest,
    *,
    query: AdnaSampleQuery | None = None,
):
    """Load normalized sample records for one runtime manifest."""
    if manifest.species.latin_name == "Homo sapiens":
        from .homo_sapiens import load_homo_sapiens_samples

        return load_homo_sapiens_samples(
            manifest=manifest,
            query=query.normalized() if query is not None else None,
        )
    raise NotImplementedError(
        "Normalized runtime loading is not implemented for "
        f"{manifest.species.latin_name}; use species review and archive manifests instead."
    )


def _clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned if cleaned else None


def _normalize_values(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted({value.strip() for value in values if value.strip()}))
