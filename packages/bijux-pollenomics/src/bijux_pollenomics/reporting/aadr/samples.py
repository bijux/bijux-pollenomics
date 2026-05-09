from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from pathlib import Path

from ...adna import (
    AdnaSampleRecord,
    build_homo_sapiens_runtime_manifest_for_version_dir,
    discover_homo_sapiens_anno_files,
    iter_homo_sapiens_samples_from_anno,
    load_homo_sapiens_country_samples,
)

__all__ = [
    "discover_anno_files",
    "iter_samples_from_anno",
    "load_country_samples",
]


def load_country_samples(
    version_dir: Path, country: str
) -> tuple[list[AdnaSampleRecord], Counter[str]]:
    """Compatibility wrapper for the Homo sapiens country-report sample loader."""
    manifest = build_homo_sapiens_runtime_manifest_for_version_dir(version_dir)
    return load_homo_sapiens_country_samples(manifest, country)


def discover_anno_files(version_dir: Path) -> list[Path]:
    """Compatibility wrapper for governed Homo sapiens AADR anno discovery."""
    manifest = build_homo_sapiens_runtime_manifest_for_version_dir(version_dir)
    return discover_homo_sapiens_anno_files(
        Path(manifest.source_bundles[0].tracked_root)
    )


def iter_samples_from_anno(path: Path, dataset_name: str) -> Iterable[AdnaSampleRecord]:
    """Compatibility wrapper for direct anno iteration."""
    manifest = build_homo_sapiens_runtime_manifest_for_version_dir(path.parents[1])
    bundle = manifest.source_bundles[0]
    return iter_homo_sapiens_samples_from_anno(
        path,
        dataset_name=dataset_name,
        source_release=bundle.source_release,
        source_family=bundle.source_family,
        record_modality=bundle.record_modality,
        review_strength=bundle.review_strength,
        provenance_quality=bundle.provenance_quality,
    )
