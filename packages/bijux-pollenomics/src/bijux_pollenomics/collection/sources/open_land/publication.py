"""Private-only, immutable materialization for governed OpenLand review."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

from ..quarantine import IntakeRefusal
from .authority import (
    SOURCE_ATTRIBUTION,
    SOURCE_CITATION_DOI,
    SOURCE_COMMIT,
    SOURCE_DATA_LICENSE,
    SOURCE_REPOSITORY,
)
from .models import OpenLandPrivateReview
from .normalization import iter_modeled_land_cover
from .projection import (
    project_nordic_modeled_land_cover,
    projection_configuration,
    projection_configuration_sha256,
)

_ARTIFACT_FILENAMES = (
    "nordic_spatial_land_cover_temporal_grid_cells.geojson",
    "country_decisions.json",
    "reconciliation.json",
)
_IMPLEMENTATION_FILENAMES = (
    "__init__.py",
    "authority.py",
    "models.py",
    "normalization.py",
    "projection.py",
    "publication.py",
)


def materialize_private_review(
    archive_path: Path,
    *,
    repository_root: Path,
    country_boundaries: dict[str, dict[str, object]],
    boundary_artifact_digest: str,
    boundary_version: str,
) -> OpenLandPrivateReview:
    """Write one private review under the repository artifacts boundary only."""
    root = _validated_repository_root(repository_root)
    cells = tuple(iter_modeled_land_cover(archive_path))
    if not cells:
        raise IntakeRefusal("open_land_private_review_empty", str(archive_path))
    source_digests = {cell.source_archive_sha256 for cell in cells}
    if len(source_digests) != 1:
        raise IntakeRefusal(
            "open_land_source_archive_identity_mismatch", str(sorted(source_digests))
        )
    archive_sha256 = next(iter(source_digests))
    projection = project_nordic_modeled_land_cover(
        cells,
        country_boundaries=country_boundaries,
        boundary_artifact_digest=boundary_artifact_digest,
        boundary_version=boundary_version,
    )
    projection_config = projection_configuration(
        boundary_artifact_digest=boundary_artifact_digest,
        boundary_version=boundary_version,
    )
    if projection_config["source_archive_sha256"] != archive_sha256:
        raise IntakeRefusal(
            "open_land_projection_source_identity_mismatch",
            f"expected={projection_config['source_archive_sha256']} observed={archive_sha256}",
        )
    projection_config_digest = projection_configuration_sha256(projection_config)
    implementation_digest, implementation_files = _implementation_receipt()

    artifacts_root = _owned_directory(root, "artifacts")
    execution_root = _owned_directory(artifacts_root, "execution-control")
    source_root = _owned_directory(execution_root, "open-land")
    receipt_root = _owned_directory(source_root, archive_sha256)
    output_root = receipt_root / "private-review"
    if output_root.is_symlink() or output_root.exists():
        raise IntakeRefusal("open_land_private_review_target_exists", str(output_root))

    staging = Path(tempfile.mkdtemp(prefix=".private-review-", dir=receipt_root))
    try:
        payloads: dict[str, object] = {
            _ARTIFACT_FILENAMES[0]: projection.feature_collection,
            _ARTIFACT_FILENAMES[1]: {
                "schema_version": "open-land-country-decisions.v1",
                "decisions": list(projection.country_decisions),
            },
            _ARTIFACT_FILENAMES[2]: projection.reconciliation,
        }
        artifacts: list[dict[str, object]] = []
        artifact_digests: list[tuple[str, str]] = []
        for filename in _ARTIFACT_FILENAMES:
            digest, size_bytes = _write_json_exclusive(
                staging / filename, payloads[filename]
            )
            artifacts.append(
                {"path": filename, "sha256": digest, "size_bytes": size_bytes}
            )
            artifact_digests.append((filename, digest))
        manifest = {
            "schema_version": "open-land-private-review-manifest.v1",
            "source_family": "open_land",
            "source_archive_sha256": archive_sha256,
            "source_repository": SOURCE_REPOSITORY,
            "source_commit": SOURCE_COMMIT,
            "source_citation_doi": SOURCE_CITATION_DOI,
            "source_data_license": SOURCE_DATA_LICENSE,
            "required_attribution": SOURCE_ATTRIBUTION,
            "boundary_artifact_digest": boundary_artifact_digest,
            "boundary_version": boundary_version,
            "projection_configuration": projection_config,
            "projection_configuration_sha256": projection_config_digest,
            "implementation_sha256": implementation_digest,
            "implementation_files": implementation_files,
            "artifacts": artifacts,
            "raw_archive_copied": False,
            "source_spatial_interpolation_retained": True,
            "added_spatial_interpolation": False,
            "added_temporal_interpolation": False,
            "propagation_use_allowed": False,
            "public_release_allowed": False,
            "release_posture": "private_review_only",
            "release_blockers": [
                "uncertainty_surface_not_supplied",
                "human_licensing_review_required",
                "scientific_model_review_required",
                "independent_release_review_required",
            ],
        }
        _write_json_exclusive(staging / "manifest.json", manifest)
        os.replace(staging, output_root)
    except BaseException:
        if staging.exists() and not staging.is_symlink():
            shutil.rmtree(staging)
        raise
    return OpenLandPrivateReview(
        output_root=output_root,
        manifest_path=output_root / "manifest.json",
        artifact_sha256=tuple(artifact_digests),
    )


def _validated_repository_root(repository_root: Path) -> Path:
    root = Path(repository_root)
    if not root.is_absolute():
        raise ValueError("OpenLand repository root must be absolute")
    if root.is_symlink() or not root.is_dir():
        raise ValueError(f"OpenLand repository root must be a real directory: {root}")
    resolved = root.resolve()
    if resolved == Path(resolved.anchor) or resolved == Path.home().resolve():
        raise ValueError(f"Unsafe OpenLand repository root: {root}")
    return root


def _owned_directory(parent: Path, name: str) -> Path:
    path = parent / name
    if path.is_symlink():
        raise IntakeRefusal("open_land_artifact_directory_symlink", str(path))
    if path.exists() and not path.is_dir():
        raise IntakeRefusal("open_land_artifact_directory_not_directory", str(path))
    path.mkdir(exist_ok=True)
    return path


def _write_json_exclusive(path: Path, payload: object) -> tuple[str, int]:
    content = _canonical_json_bytes(payload) + b"\n"
    with path.open("xb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())
    return hashlib.sha256(content).hexdigest(), len(content)


def _implementation_receipt() -> tuple[str, list[dict[str, str]]]:
    module_root = Path(__file__).parent
    records: list[dict[str, str]] = []
    for filename in _IMPLEMENTATION_FILENAMES:
        path = module_root / filename
        if path.is_symlink() or not path.is_file():
            raise IntakeRefusal("open_land_implementation_file_missing", str(path))
        records.append(
            {"path": filename, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        )
    return hashlib.sha256(_canonical_json_bytes(records)).hexdigest(), records


def _canonical_json_bytes(payload: object) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
