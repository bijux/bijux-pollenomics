"""Capture committed generator bytes and produce a local artifact candidate."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys

from ..atlas_media.process_execution import BoundedProcessError, run_bounded_argv
from .artifact_candidate import (
    ENTRY_POINT,
    GENERATOR_SCRIPT,
    SIGNED_GENERATOR_SCRIPT,
    canonical_digest,
    committed_source,
    git_bytes,
    inventory,
    json_bytes,
    regular_bytes,
    sha256,
    source_inventory,
)
from .contracts import (
    SIGNED_CALENDAR_PROFILE,
    AtlasArtifactCandidate,
    AtlasBrowserContractError,
)


def _path(root: Path, value: Path) -> tuple[Path, str]:
    spelling = value.absolute()
    if any(parent.is_symlink() for parent in (spelling, *spelling.parents)):
        raise AtlasBrowserContractError("generator paths cannot contain symbolic links")
    path = Path(os.path.abspath(spelling))
    try:
        return path, path.relative_to(root).as_posix()
    except ValueError as error:
        raise AtlasBrowserContractError(
            "generator paths must belong to repository"
        ) from error


def generate_artifact_candidate(
    *,
    repository_root: Path,
    source_root: Path,
    product_directory: Path,
    expected_product_manifest_sha256: str,
    geometry_path: Path,
    expected_geometry_sha256: str,
    destination: Path,
    receipt_path: Path,
    python_binary: Path | None = None,
    temporal_profile: str | None = None,
) -> AtlasArtifactCandidate:
    """Generate from a new, byte-verified committed snapshot, never Git output commits.

    All writes are local and exclusive. Failed source/output stages are preserved;
    no receipt is issued for a failed or changed generation. Invoke this producer
    through the repository's managed background-job workflow.
    """
    if temporal_profile not in (None, SIGNED_CALENDAR_PROFILE):
        raise AtlasBrowserContractError("unsupported generator temporal profile")
    root = repository_root.resolve()
    source, source_relative = _path(root, source_root)
    product, product_relative = _path(root, product_directory)
    geometry, geometry_relative = _path(root, geometry_path)
    output, output_relative = _path(root, destination)
    receipt, receipt_relative = _path(root, receipt_path)
    for path in (source, output, receipt):
        if (
            not path.is_relative_to(root / "artifacts")
            or path == root / "artifacts"
            or path.exists()
        ):
            raise AtlasBrowserContractError(
                "generator outputs must be new dedicated artifact paths"
            )
    trees = (source, output, product)
    if (
        any(
            a.is_relative_to(b) or b.is_relative_to(a)
            for i, a in enumerate(trees)
            for b in trees[i + 1 :]
        )
        or any(
            receipt.is_relative_to(path) or geometry.is_relative_to(path)
            for path in (source, output)
        )
        or receipt.is_relative_to(product)
    ):
        raise AtlasBrowserContractError("generator input/output paths overlap")
    if (
        sha256(regular_bytes(product / "manifest.json"))
        != expected_product_manifest_sha256
        or sha256(regular_bytes(geometry)) != expected_geometry_sha256
    ):
        raise AtlasBrowserContractError(
            "generation inputs differ from expected digests"
        )
    product_files = inventory(product)
    head = git_bytes(root, "rev-parse", "HEAD").decode().strip()
    tree = git_bytes(root, "rev-parse", f"{head}^{{tree}}").decode().strip()
    objects = committed_source(root, head, tree)
    source_files = source_inventory(root, objects)
    source.mkdir(parents=True, exist_ok=False)
    for member, expected in source_files.items():
        value = regular_bytes(root / member)
        if sha256(value) != expected:
            raise AtlasBrowserContractError("generator changed during source capture")
        target = source / member
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(value)
    if source_inventory(source, objects) != source_files:
        raise AtlasBrowserContractError("captured generator source differs")
    command: tuple[str, ...] = (
        str(python_binary or Path(sys.executable)),
        "-I",
        "-c",
        SIGNED_GENERATOR_SCRIPT if temporal_profile is not None else GENERATOR_SCRIPT,
        str(source / "packages/bijux-pollenomics/src"),
        str(product),
        expected_product_manifest_sha256,
        str(geometry),
        expected_geometry_sha256,
        str(output),
    )
    if temporal_profile is not None:
        command += (temporal_profile,)
    try:
        completed = run_bounded_argv(command, cwd=source, timeout_seconds=120)
    except BoundedProcessError as error:
        raise AtlasBrowserContractError("cannot launch frozen generator") from error
    if completed.returncode or completed.timed_out:
        raise AtlasBrowserContractError(
            "frozen presentation generation failed: "
            + completed.stderr.decode(errors="replace")
        )
    runtime = json_bytes(completed.stdout)
    if source_inventory(source, objects) != source_files:
        raise AtlasBrowserContractError("generator snapshot changed during execution")
    if (
        inventory(product) != product_files
        or sha256(regular_bytes(geometry)) != expected_geometry_sha256
    ):
        raise AtlasBrowserContractError(
            "original generation inputs changed during execution"
        )
    manifest_bytes = regular_bytes(output / "manifest.json")
    manifest = json_bytes(manifest_bytes)
    output_identity = {
        "presentation_root": output_relative,
        "presentation_manifest_sha256": sha256(manifest_bytes),
        "presentation_inventory_sha256": canonical_digest(inventory(output)),
        "product_manifest_sha256": expected_product_manifest_sha256,
        "display_geometry_sha256": expected_geometry_sha256,
        "build_id": manifest["map_build_id"],
    }
    payload = {
        "schema_version": "atlas-artifact-generation.v2"
        if temporal_profile is not None
        else "atlas-artifact-generation.v1",
        "source_relation": "committed_tree",
        "generator_repository_head": head,
        "generator_repository_tree": tree,
        "source_root": source_relative,
        "source_files": source_files,
        "entry_point": ENTRY_POINT,
        "runtime": runtime,
        "invocation": {
            "argv": list(completed.command),
            "cwd": str(source),
            "python_binary": completed.command[0],
        },
        "inputs": {
            "product_directory": product_relative,
            "geometry_path": geometry_relative,
        },
        "output": output_identity,
    }
    if temporal_profile is not None:
        payload.update(temporal_profile=temporal_profile, temporal_axis="BP1950")
    encoded = (
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode()
    candidate = AtlasArtifactCandidate(
        **output_identity,
        generator_repository_head=head,
        generator_repository_tree=tree,
        generator_receipt=receipt_relative,
        generator_receipt_sha256=sha256(encoded),
    )
    receipt.parent.mkdir(parents=True, exist_ok=True)
    with receipt.open("xb") as stream:
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())
    return candidate
