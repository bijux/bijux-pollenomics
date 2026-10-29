"""Keep the Sweden merge extension confined to detached old payload source."""

from __future__ import annotations

import hashlib
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.retained_source import SourceCapsule
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.country_reports.sweden.metadata import (
    validate_recorded_source_contracts,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.presentation_source_roles import (
    PAYLOAD,
)

OLD = b"""from __future__ import annotations

def build_map_document_payload(native_lra=None, static_assets=None, asset_base_path="own", escape_html_fn=str):
    return {
        "own": 7,
        "__NATIVE_LRA_CONTROLLER__": NATIVE_LRA_CONTROLLER
        if native_lra is not None
        else "",
    }
"""
NEW = b"""from __future__ import annotations

def build_map_document_payload(native_lra=None, static_assets=None, asset_base_path="own", escape_html_fn=str):
    return {
        "own": 7,
        "__NATIVE_LRA_SCRIPT_TAG__": (
            f'<script src="{escape_html_fn(asset_base_path)}/native-lra.js"></script>'
            if native_lra is not None and static_assets is not None
            else ""
        ),
        "__NATIVE_LRA_CONTROLLER__": NATIVE_LRA_CONTROLLER
        if native_lra is not None and static_assets is None
        else "",
    }
"""


def _world(root: Path) -> tuple[list[dict[str, Any]], Any]:
    rows: list[dict[str, Any]] = []
    members: dict[str, dict[str, Any]] = {}
    bodies: dict[str, bytes] = {}
    resolved: list[tuple[str, str]] = []
    for index in range(51):
        name = PAYLOAD if index == 0 else f"packages/own/contract_{index}.py"
        body = OLD if index == 0 else f"VALUE = {index}\n".encode()
        digest = hashlib.sha256(body).hexdigest()
        logical = "members/" + digest
        identity = {"bytes": len(body), "sha256": digest}
        rows.append({"path": name, **identity})
        members[logical] = identity
        resolved.append((logical, name))
        bodies[logical] = body
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(NEW if index == 0 else body)
    resolver = SimpleNamespace(
        repository=root,
        descriptor=SimpleNamespace(
            members=members, groups=[{"resolved_paths": resolved}]
        ),
        detached=frozenset(members),
        read_source=bodies.__getitem__,
        fresh=lambda: None,
        owned_bodies=bodies,
    )
    return rows, resolver


def test_only_named_detached_payload_extension_is_reported(tmp_path: Path) -> None:
    rows, resolver = _world(tmp_path)
    facts = validate_recorded_source_contracts(
        tmp_path, rows, cast(SourceCapsule, resolver)
    )
    assert facts["original_source_contracts_authenticated"] == 51
    assert facts["current_default_exact_sources"] == 50
    assert facts["finite_atlas_asset_extension_sources"] == [PAYLOAD]
    assert facts["historical_renderer_sources"] == []
    assert facts["current_browser_or_native_equivalence_claimed"] is False


@pytest.mark.parametrize(
    "damage", ["attached", "old_bytes", "wrong_binding", "math", "guard", "unknown"]
)
def test_extension_never_waives_original_custody_or_other_math(
    tmp_path: Path, damage: str
) -> None:
    rows, resolver = _world(tmp_path)
    logical = "members/" + rows[0]["sha256"]
    target = tmp_path / PAYLOAD
    if damage == "attached":
        resolver.detached = frozenset()
    elif damage == "old_bytes":
        resolver.owned_bodies[logical] = b"OTHER_SOURCE = 1\n"
    elif damage == "wrong_binding":
        resolver.descriptor.groups[0]["resolved_paths"][0] = (
            logical,
            "packages/other.py",
        )
    elif damage == "math":
        target.write_bytes(NEW.replace(b'"own": 7', b'"own": 9'))
    elif damage == "guard":
        target.write_bytes(
            NEW.replace(b"and static_assets is None", b"or static_assets is None")
        )
    else:
        (tmp_path / rows[1]["path"]).write_bytes(b"VALUE = 9\n")
    with pytest.raises((ValueError, OSError)):
        validate_recorded_source_contracts(
            tmp_path, rows, cast(SourceCapsule, resolver)
        )
