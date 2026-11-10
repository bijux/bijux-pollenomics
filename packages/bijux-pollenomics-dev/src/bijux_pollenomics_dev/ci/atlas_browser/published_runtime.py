"""Authenticate the executable transport of a published static atlas."""

from __future__ import annotations

import base64
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from bijux_pollenomics.reporting.map_document.render import (
    _RUNTIME_LOADER,
    _FixedJsonBindings,
    _runtime_resources,
    static_map_optional_controller_paths,
)
from bijux_pollenomics.reporting.map_document.static_assets import StaticAtlasAssets

from .candidate_files import regular_bytes
from .contracts import AtlasBrowserContractError


@dataclass(frozen=True)
class PublishedRuntime:
    """An authenticated main runtime and its declared optional controllers."""

    script: str
    paths: tuple[Path, ...] = ()
    payloads: tuple[bytes, ...] = ()
    binding_bytes: int = 0


def read_published_runtime(
    document_path: Path,
    manifest_path: Path,
    document: str,
    manifest: dict[str, Any],
) -> PublishedRuntime:
    """Keep inline documents compatible and authenticate distributed executable bytes."""
    parser = _FixedJsonBindings()
    parser.bindings["atlas-static-bootstrap"] = []
    parser.feed(document)
    parser.close()
    bootstraps = parser.bindings["atlas-static-bootstrap"]
    if not bootstraps:
        return PublishedRuntime(document)
    try:
        if len(bootstraps) != 1 or bootstraps[0] is None:
            raise ValueError("bootstrap ID or script/JSON shape is not unique")
        bootstrap = json.loads("".join(bootstraps[0]))
        if (
            not isinstance(bootstrap, dict)
            or {key: value for key, value in bootstrap.items() if key != "runtime"}
            != manifest
        ):
            raise ValueError("bootstrap differs from its manifest")
        if "runtime" not in bootstrap:
            return PublishedRuntime(document)
        runtime = bootstrap["runtime"]
        if not isinstance(runtime, dict) or set(runtime) not in (
            {"path", "byte_count", "integrity"},
            {"path", "byte_count", "integrity", "optional_controllers"},
        ):
            raise ValueError("runtime reference fields differ")
        name = runtime["path"]
        if (
            not isinstance(name, str)
            or re.fullmatch(
                re.escape(document_path.stem) + r"\.atlas-runtime\.[a-f0-9]{16}\.js",
                name,
            )
            is None
        ):
            raise ValueError("runtime path is not a confined digest basename")
        path = document_path.parent / name
        payload = regular_bytes(path)
        digest = hashlib.sha256(payload).hexdigest()
        if (
            type(runtime["byte_count"]) is not int
            or runtime["byte_count"] != len(payload)
            or name != document_path.stem + ".atlas-runtime." + digest[:16] + ".js"
            or runtime["integrity"]
            != "sha256-"
            + base64.b64encode(hashlib.sha256(payload).digest()).decode("ascii")
            or path.stat().st_nlink != 1
            or document.count(_RUNTIME_LOADER) != 1
            or regular_bytes(document_path).decode("utf-8") != document
        ):
            raise ValueError("runtime bytes, SRI or maintained loader differ")
        paths = (path, *static_map_optional_controller_paths(document_path))
        payloads = (payload, *(regular_bytes(member) for member in paths[1:]))
        _runtime_resources(
            StaticAtlasAssets(manifest_path, manifest, ()),
            len(payload),
            document,
            tuple(len(body) for body in payloads[1:]),
        )
        bindings = _FixedJsonBindings()
        bindings.feed(document)
        bindings.close()
        binding_bytes = sum(
            len("".join(value[0] or []).encode("utf-8"))
            for value in bindings.bindings.values()
        )
        return PublishedRuntime(payload.decode("utf-8"), paths, payloads, binding_bytes)
    except (ValueError, KeyError, TypeError, OSError) as error:
        raise AtlasBrowserContractError(
            "Published runtime graph differs: " + str(error)
        ) from error
