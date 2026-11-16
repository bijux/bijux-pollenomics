"""Replay complete evidence pins with optional outer operation refusals."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from ...facets.models import NeotomaFacetScopeInputs
from ...receipts import _safe_root
from ...resources.replay import _same_json
from ..authority import source_bindings, source_pins


def _load_linked_evidence(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    expected_roster_sha256: str,
    scope: NeotomaFacetScopeInputs,
    source_facets: Mapping[str, Path],
    legacy_rosters: Mapping[str, Path] | None = None,
    _before_body_read: Callable[[], None] | None = None,
) -> dict[str, Any]:
    """Run the original complete validator; a callback can only add a refusal."""
    from .. import evidence as owner

    root = _safe_root(directory)
    index = owner._index(root, expected_manifest_sha256)
    if index["authority"]["roster_sha256"] != expected_roster_sha256:
        raise ValueError("Linked evidence frozen roster identity differs")
    inputs: dict[str, Any] = {
        "expected_roster_sha256": expected_roster_sha256,
        "scope": scope,
        "source_facets": source_facets,
        "legacy_rosters": legacy_rosters,
    }

    def pins() -> dict[str, dict[str, Any]]:
        bindings = source_bindings(**inputs)
        if _before_body_read is None:
            return source_pins(bindings)
        return source_pins(bindings, _before_body_read=_before_body_read)

    if not _same_json(pins(), index["source_input_pins"]):
        raise ValueError("Linked evidence source pins or namespace differ")
    owner._namespace(root, index)
    for descriptor in index["parts"]:
        owner._part(root, descriptor)
    owner._namespace(root, index)
    if not _same_json(pins(), index["source_input_pins"]):
        raise ValueError("Linked evidence source pins changed during readback")
    return index
