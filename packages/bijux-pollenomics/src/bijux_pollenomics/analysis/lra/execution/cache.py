"""Reuse verified host products under explicit request and implementation identity."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path

from ..engine.discovery import load_engine
from ..engine.errors import LRARefusal
from ..inputs.validation import validate_request
from ..outputs.identity import capture_code_identity, verify_code_identity
from ..outputs.publication import LRAProduct, publish_result
from ..outputs.reading import read_lra_product
from .adapter import reconstruct, validate_engine_configuration


@dataclass(frozen=True)
class CachedLRAProduct:
    """One calculated or reused product and its content-addressed lookup key."""

    product: LRAProduct
    cache_key: str
    cache_hit: bool


def run_lra_cached(
    payload: Mapping[str, object], *, input_root: Path, cache_root: Path
) -> CachedLRAProduct:
    """Calculate once per request/code identity, refusing corrupt or busy entries.

    This is a local cache, not a trusted store of third-party scientific claims.
    Reuse revalidates current source bytes and all cached outputs. Failed work
    never becomes a cache hit; pending publication directories remain diagnostic
    evidence. Concurrent writers receive a reasoned busy refusal and may retry
    after the active owner finishes; this call does not poll or wait.
    """
    request = validate_request(payload, input_root=input_root)
    binding = load_engine()
    validate_engine_configuration(binding, request)
    identity = capture_code_identity(binding)
    lookup = {
        "schema_version": "lra-cache-key.v1",
        "request_sha256": request.sha256,
        "engine": binding.as_dict(),
        **identity.payload(),
    }
    key = hashlib.sha256(
        json.dumps(lookup, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    cache_root = cache_root.absolute()
    cache_root.mkdir(parents=True, exist_ok=True)
    destination = cache_root / key
    reservation = cache_root / f".{key}.cache.lock"
    try:
        descriptor = os.open(reservation, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise LRARefusal("lra_cache_busy", key) from exc
    os.close(descriptor)
    try:
        hit = destination.exists() or destination.is_symlink()
        if hit:
            verified = read_lra_product(destination)
            manifest = verified.manifest()
            scientific = manifest["scientific_identity"]
            if any(
                scientific.get(field) != value
                for field, value in lookup.items()
                if field != "schema_version"
            ):
                raise LRARefusal("lra_cache_identity_mismatch", key)
            product = verified.product
        else:
            result = reconstruct(binding, request)
            validate_request(request.payload(), input_root=input_root)
            verify_code_identity(binding, identity)
            product = publish_result(
                result,
                binding,
                request,
                destination=destination,
                input_root=input_root,
                code_identity=identity,
            )
        validate_request(request.payload(), input_root=input_root)
        verify_code_identity(binding, identity)
        return CachedLRAProduct(product, key, hit)
    finally:
        reservation.unlink()
