"""Keep metadata transport additions separate from fixed original Atlas witnesses."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.retained_source.index import _descriptor
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.source_roles import (
    atlas_context,
    atlas_evidence_selection,
)

_BASE = "packages/bijux-pollenomics/src/bijux_pollenomics/"
_PATHS = (
    "reporting/service.py",
    "reporting/bundles/atlas_bundle/layers.py",
    "reporting/bundles/atlas_bundle/operations_api.py",
    "reporting/bundles/atlas_bundle/workflow.py",
    "reporting/bundles/atlas_bundle/contracts.py",
    "reporting/bundles/published_reports.py",
    "reporting/map_document/static_assets/asset_inventory.py",
    "reporting/map_document/render.py",
)
_CONTEXTS = (
    ("data/atlas/sample-chronology-source-view-capture", "source/"),
    (
        "data/method-certification/author-optimizer-diagnostic-source-capture",
        "executions/optimizer-diagnostics/first-party-inputs/",
    ),
)


@pytest.mark.parametrize("relative", _PATHS)
@pytest.mark.parametrize("prefix,lane", _CONTEXTS)
def test_actual_metadata_transport_uses_unchanged_original_git_witnesses(
    relative: str,
    prefix: str,
    lane: str,
) -> None:
    repository = Path(__file__).resolve().parents[7]
    raw = (repository / prefix / "capture.json").read_bytes()
    capture = json.loads(raw)
    source = _descriptor(
        repository, prefix, capture.get("members", capture.get("files"))
    )
    name = _BASE + relative
    logical = lane + name
    original = source.read_source(logical)
    row = {"path": name, "bytes": len(original), "sha256": sha256(original).hexdigest()}
    current = (repository / name).read_bytes()
    if relative.endswith("/render.py"):
        result = atlas_evidence_selection.validated_atlas_evidence_selection_source(
            repository, row, logical, source
        )
        match = atlas_evidence_selection.atlas_evidence_selection_extension_matches
        assert result["classification"] == "atlas_evidence_selection_extension"
    else:
        result = atlas_context.validated_atlas_context_source(
            repository, row, logical, source
        )
        match = atlas_context.atlas_context_extension_matches
        assert result["classification"] == "source_view_context_extension"
    assert match(name, original, current)
    assert not match(name, original, current + b"# unowned executable change\n")
    assert not match(name, original + b"# counterfeit old bytes\n", current)
    assert not match(_BASE + "analysis/unowned.py", original, current)
    source.fresh()
    assert (repository / prefix / "capture.json").read_bytes() == raw
