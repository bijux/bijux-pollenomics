"""Publish a new local bundle only after numerical and lineage checks succeed."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from ..engine.discovery import EngineBinding
from ..engine.errors import LRARefusal
from ..inputs.validation import ValidatedRequest
from .atomic import publish_directory
from .identity import CodeIdentity, file_inventory, verify_code_identity


def _canonical(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


@dataclass(frozen=True)
class LRAProduct:
    """A generated exploratory bundle; this is not a scientific release verdict."""

    directory: Path
    manifest_sha256: str
    scientific_content_sha256: str


def publish_result(
    result: Any,
    binding: EngineBinding,
    request: ValidatedRequest,
    *,
    destination: Path,
    code_identity: CodeIdentity,
) -> LRAProduct:
    """Preserve explicit units/lineage and publish through one exclusive writer.

    All files have byte hashes. Scientific identity excludes operational timestamps
    and their dependent checksum inventories, but retains numerical output bytes,
    actual package code/resources, dependency identities and the exact input bundle.
    Failed staged output remains available for diagnosis and is never the product.
    """
    destination = destination.absolute()
    destination.parent.mkdir(parents=True, exist_ok=True)
    reservation = destination.with_name(f".{destination.name}.lra.lock")
    try:
        descriptor = os.open(reservation, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise LRARefusal("lra_output_busy", str(destination)) from exc
    os.close(descriptor)
    try:
        if destination.exists() or destination.is_symlink():
            raise LRARefusal("lra_output_exists", str(destination))
        stage = Path(
            tempfile.mkdtemp(
                prefix=f".{destination.name}.pending-", dir=destination.parent
            )
        )
        numerical = stage / "numerical"
        result.write(numerical)
        (stage / "request.json").write_text(
            request.canonical_json + "\n", encoding="utf-8"
        )
        scientific = result.manifest.scientific_identity()
        (stage / "scientific_manifest.json").write_bytes(_canonical(scientific))
        numeric_files = file_inventory(numerical)
        stable_outputs = {
            path: value
            for path, value in numeric_files.items()
            if Path(path).name
            not in {"run_manifest.json", "checksums.json", "sha256_manifest.json"}
        }
        identity = {
            "request_sha256": request.sha256,
            "engine": binding.as_dict(),
            **code_identity.payload(),
            "engine_scientific_manifest": scientific,
            "numerical_files": stable_outputs,
        }
        payload = request.payload()
        manifest = {
            "schema_version": "lra-product.v1",
            "status": "generated_exploratory",
            "scientific_acceptance": "not_evaluated",
            "purpose": payload["purpose"],
            "data_kind": payload["data_kind"],
            "method_profile": payload["method_profile"],
            "operation": payload["operation"],
            "engine": binding.as_dict(),
            "host_version": metadata.version("bijux-pollenomics"),
            "request_sha256": request.sha256,
            "evidence": payload["evidence"],
            "versions": payload["versions"],
            "temporal_matching": payload["temporal_matching"],
            "retained_taxa": payload["taxa"],
            "included_sample_count": sum(
                len(payload[role]["samples"])
                for role in ("regional", "local")
                if role in payload
            ),
            "exclusions": payload["exclusions"],
            "excluded_record_count": len(payload["exclusions"]),
            "uncertainty_omissions": payload["uncertainty_omissions"],
            "units": {
                "regional_cover": "percent",
                "local_cover": "fraction",
                "distance": "metre",
                "age_support": "typed BP intervals; present=1950 CE",
            },
            "scientific_content_sha256": _digest(_canonical(identity)),
            "scientific_identity": identity,
            "files": file_inventory(stage),
        }
        encoded = _canonical(manifest)
        (stage / "manifest.json").write_bytes(encoded)
        verify_code_identity(binding, code_identity)
        publish_directory(stage, destination)
        return LRAProduct(
            destination, _digest(encoded), manifest["scientific_content_sha256"]
        )
    finally:
        reservation.unlink()
