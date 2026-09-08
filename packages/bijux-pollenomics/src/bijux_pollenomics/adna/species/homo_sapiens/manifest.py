"""Runtime manifest construction for Homo sapiens AADR metadata."""

from __future__ import annotations

from pathlib import Path

from bijux_pollenomics.adna.workflow.manifests import (
    AdnaSpeciesManifest,
    build_species_manifest,
)
from bijux_pollenomics.adna.workflow.paths import ADNA_SPECIES_DIR
from bijux_pollenomics.adna.workflow.runtime import (
    AdnaSourceBundle,
    AdnaSpeciesRuntimeManifest,
)

from .constants import (
    HOMO_SAPIENS_PROVENANCE_QUALITY,
    HOMO_SAPIENS_RECORD_MODALITY,
    HOMO_SAPIENS_REVIEW_STRENGTH,
)
from .release import release_dataset_names

_ANALYSIS_BOUNDARY = (
    "Homo sapiens runtime support is AADR metadata normalization only. "
    "This surface does not imply genotype-aware analysis."
)


def build_homo_sapiens_runtime_manifest(
    *,
    data_root: Path,
    version: str,
) -> AdnaSpeciesRuntimeManifest:
    """Build the canonical Homo sapiens runtime manifest for AADR metadata support."""
    species_manifest = build_species_manifest("Homo sapiens")
    source_root = (
        Path(data_root)
        / ADNA_SPECIES_DIR.removeprefix("data/")
        / species_manifest.root_slug
        / "raw"
        / "aadr"
    )
    release_dir = source_root / version
    release_manifest = Path(data_root) / "aadr" / version / "release_manifest.json"
    return _build_runtime_manifest(
        species_manifest=species_manifest,
        version=version,
        release_dir=release_dir,
        release_manifest=release_manifest,
    )


def build_homo_sapiens_runtime_manifest_for_version_dir(
    version_dir: Path,
) -> AdnaSpeciesRuntimeManifest:
    """Build a Homo sapiens runtime manifest from one concrete version directory."""
    version_dir = Path(version_dir)
    if not version_dir.name:
        raise ValueError(
            "A version directory is required for Homo sapiens runtime loading"
        )
    return _build_runtime_manifest(
        species_manifest=build_species_manifest("Homo sapiens"),
        version=version_dir.name,
        release_dir=version_dir,
        release_manifest=version_dir / "release_manifest.json",
    )


def _build_runtime_manifest(
    *,
    species_manifest: AdnaSpeciesManifest,
    version: str,
    release_dir: Path,
    release_manifest: Path,
) -> AdnaSpeciesRuntimeManifest:
    return AdnaSpeciesRuntimeManifest(
        schema_version="adna-runtime-manifest.v1",
        species_manifest=species_manifest,
        source_bundles=(
            AdnaSourceBundle(
                source_family="AADR",
                source_release=version,
                bundle_kind="source_release",
                tracked_root=str(release_dir),
                release_manifest_path=str(release_manifest),
                dataset_names=release_dataset_names(release_manifest, release_dir),
                record_modality=HOMO_SAPIENS_RECORD_MODALITY,
                review_strength=HOMO_SAPIENS_REVIEW_STRENGTH,
                provenance_quality=HOMO_SAPIENS_PROVENANCE_QUALITY,
            ),
        ),
        analysis_boundary=_ANALYSIS_BOUNDARY,
        runtime_ready=True,
    )
