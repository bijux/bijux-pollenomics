"""Owned publication and strict inventory reopening for experiment phases."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import tempfile

from ....core.owned_tree import publish_new_output_tree
from ..contracts import ValidationRefusal, canonical_json, manifest_sha256
from .configuration import object_mapping
from .inputs import _unique_pairs


@dataclass(frozen=True)
class ExperimentProduct:
    """One byte-bound phase, explicitly without scientific acceptance."""

    directory: Path
    manifest_sha256: str
    scientific_content_sha256: str


def stage_directory(destination: Path) -> Path:
    """Create one new diagnostic stage; existing products are never replaced."""
    destination = destination.absolute()
    if destination.exists() or destination.is_symlink():
        raise ValidationRefusal("experiment_output_exists", str(destination))
    destination.parent.mkdir(parents=True, exist_ok=True)
    return Path(
        tempfile.mkdtemp(prefix=f".{destination.name}.pending-", dir=destination.parent)
    )


def write_json(stage: Path, name: str, value: object) -> None:
    """Write a fixed producer-owned JSON member, preserving finite values."""
    if Path(name).name != name or not name.endswith(".json"):
        raise ValidationRefusal("invalid_experiment_output_name", name)
    (stage / name).write_text(canonical_json(value) + "\n")


def _inventory(directory: Path) -> dict[str, str]:
    result = {}
    if directory.is_symlink():
        raise ValidationRefusal("invalid_experiment_product", "Symlink root")
    for path in directory.rglob("*"):
        if path.is_symlink() or (not path.is_file() and not path.is_dir()):
            raise ValidationRefusal("invalid_experiment_product", "Nonregular output")
        if path.is_file() and path != directory / "manifest.json":
            result[path.relative_to(directory).as_posix()] = hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
    return result


def publish_phase(
    stage: Path, destination: Path, *, phase: str, scientific: dict[str, object]
) -> ExperimentProduct:
    """Publish only an enumerated phase; failures must already be accounted for."""
    scientific_digest = manifest_sha256(scientific)
    manifest = {
        "schema_version": "lra-experiment-product.v1",
        "profile": "synthetic-withheld-site-baselines-v1",
        "phase": phase,
        "status": "generated_exploratory",
        "scientific_acceptance": "not_evaluated",
        "scientific_content_sha256": scientific_digest,
        "scientific_payload": scientific,
        "files": _inventory(stage),
    }
    write_json(stage, "manifest.json", manifest)
    digest = hashlib.sha256((stage / "manifest.json").read_bytes()).hexdigest()
    try:
        publish_new_output_tree(
            final_output_root=destination.absolute(), staging_output_root=stage
        )
    except OSError as exc:
        raise ValidationRefusal("experiment_publication_failed", str(exc)) from exc
    return ExperimentProduct(destination.absolute(), digest, scientific_digest)


def read_experiment_product(
    directory: Path, *, expected_manifest_sha256: str
) -> tuple[ExperimentProduct, dict[str, object]]:
    """Authenticate the caller's exact expected inventory before opening outcomes."""
    directory = directory.absolute()
    try:
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError("Expected a nonsymlink product directory")
        content = (directory / "manifest.json").read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        if digest != expected_manifest_sha256:
            raise ValueError(
                "Manifest differs from the independently retained identity"
            )
        manifest = object_mapping(
            json.loads(content, object_pairs_hook=_unique_pairs), "manifest"
        )
        canonical_json(manifest)
        if (
            manifest.get("schema_version") != "lra-experiment-product.v1"
            or manifest.get("profile") != "synthetic-withheld-site-baselines-v1"
            or manifest.get("status") != "generated_exploratory"
            or manifest.get("scientific_acceptance") != "not_evaluated"
        ):
            raise ValueError("Unsupported experimental posture")
        if manifest.get("files") != _inventory(directory):
            raise ValueError("Product byte inventory changed")
        scientific = object_mapping(
            manifest["scientific_payload"], "scientific_payload"
        )
        identity = manifest_sha256(scientific)
        if identity != manifest.get("scientific_content_sha256"):
            raise ValueError("Scientific identity differs from its payload")
        return ExperimentProduct(directory, digest, identity), manifest
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise ValidationRefusal("invalid_experiment_product", str(exc)) from exc


def read_member(product: ExperimentProduct, name: str) -> object:
    """Read one already inventoried JSON member and recheck complete ownership."""
    read_experiment_product(
        product.directory, expected_manifest_sha256=product.manifest_sha256
    )
    if Path(name).name != name or not name.endswith(".json") or name == "manifest.json":
        raise ValidationRefusal("invalid_experiment_output_name", name)
    data = json.loads(
        (product.directory / name).read_bytes(), object_pairs_hook=_unique_pairs
    )
    canonical_json(data)
    read_experiment_product(
        product.directory, expected_manifest_sha256=product.manifest_sha256
    )
    return data
