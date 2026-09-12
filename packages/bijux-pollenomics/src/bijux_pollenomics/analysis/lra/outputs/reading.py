"""Reopen complete exploratory products through their recorded byte inventory."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

from ..engine.errors import LRARefusal
from .contracts import request_metadata, validate_numerical_tables
from .publication import LRAProduct


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _json(value: bytes) -> dict[str, Any]:
    result = json.loads(value, object_pairs_hook=_object)
    if not isinstance(result, dict):
        raise ValueError("Expected a JSON object")
    # Reject nonfinite values accepted by the Python JSON decoder.
    json.dumps(result, allow_nan=False)
    return result


def _hash(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _inventory(directory: Path) -> dict[str, str]:
    paths = list(directory.rglob("*"))
    if directory.is_symlink() or any(path.is_symlink() for path in paths):
        raise ValueError("Product contains a symbolic link")
    if any(not path.is_file() and not path.is_dir() for path in paths):
        raise ValueError("Product contains a non-regular entry")
    return {
        path.relative_to(directory).as_posix(): _hash(path.read_bytes())
        for path in paths
        if path.is_file() and path != directory / "manifest.json"
    }


@dataclass(frozen=True)
class VerifiedLRAProduct:
    """A byte-verified bundle, without scientific approval or source authentication."""

    product: LRAProduct
    canonical_manifest: str

    def manifest(self) -> dict[str, Any]:
        """Return a fresh manifest copy; callers cannot mutate verified state."""
        return _json(self.canonical_manifest.encode())


def read_lra_product(
    directory: Path, *, expected_manifest_sha256: str | None = None
) -> VerifiedLRAProduct:
    """Verify all product bytes and identities without importing the optional engine.

    An independently retained manifest digest can authenticate an expected local
    product. Without it, this verifies internal consistency, not the identity of
    an author or scientific reviewer. Source evidence is checked separately when
    reusing a calculation. Symlinks and unlisted files are refused.
    """
    directory = directory.absolute()
    try:
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError("Product must be a real directory")
        encoded = (directory / "manifest.json").read_bytes()
        digest = _hash(encoded)
        if expected_manifest_sha256 is not None and digest != expected_manifest_sha256:
            raise ValueError("Manifest differs from the expected digest")
        manifest = _json(encoded)
        if (
            manifest["schema_version"] != "lra-product.v1"
            or manifest["status"] != "generated_exploratory"
            or manifest["scientific_acceptance"] != "not_evaluated"
        ):
            raise ValueError("Unsupported product schema or acceptance posture")
        inventory = _inventory(directory)
        if inventory != manifest["files"]:
            raise ValueError("Product inventory differs from recorded bytes")
        request = _json((directory / "request.json").read_bytes())
        canonical_request = json.dumps(
            request, sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        if _hash(canonical_request.encode()) != manifest["request_sha256"]:
            raise ValueError("Request identity differs from recorded content")
        if any(
            manifest.get(key) != value
            for key, value in request_metadata(request).items()
        ):
            raise ValueError("Product metadata contradicts its request")
        identity = manifest["scientific_identity"]
        canonical_identity = (
            json.dumps(identity, sort_keys=True, separators=(",", ":"), allow_nan=False)
            + "\n"
        ).encode()
        if _hash(canonical_identity) != manifest["scientific_content_sha256"]:
            raise ValueError("Scientific content identity is inconsistent")
        scientific = _json((directory / "scientific_manifest.json").read_bytes())
        if (
            identity["request_sha256"] != manifest["request_sha256"]
            or identity["engine"] != manifest["engine"]
            or identity["engine_scientific_manifest"] != scientific
        ):
            raise ValueError("Product identity graph is inconsistent")
        numerical = {
            key.removeprefix("numerical/"): value
            for key, value in inventory.items()
            if key.startswith("numerical/")
            and Path(key).name
            not in {"run_manifest.json", "checksums.json", "sha256_manifest.json"}
        }
        if numerical != identity["numerical_files"] or not numerical:
            raise ValueError("Numerical outputs differ from scientific identity")
        validate_numerical_tables(directory, request)
        if _inventory(directory) != inventory:
            raise ValueError("Product entries changed during verification")
        if (directory / "manifest.json").read_bytes() != encoded:
            raise ValueError("Manifest changed during verification")
        return VerifiedLRAProduct(
            LRAProduct(directory, digest, manifest["scientific_content_sha256"]),
            json.dumps(manifest, sort_keys=True, separators=(",", ":")),
        )
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise LRARefusal("invalid_lra_product", str(exc)) from exc
