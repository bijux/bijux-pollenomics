"""Authenticate one capture's selected proof metadata in a single bounded pass."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from bijux_pollenomics.core.filesystem import BoundedInputTree

from ...capture.linked_resources.evidence import (
    MAX_EVIDENCE_BYTES,
    MAX_PARTS,
    _index,
    _occurrences,
)
from ...capture.linked_resources.models import EVIDENCE_SCHEMA
from ...capture.receipts import _safe_root
from ...resource_catalogue.source_projection import _same
from ..context.validation import NeotomaAncillaryContext
from .sources import (
    _restrict_scoped_target,
    _scoped_current_metadata,
    resolve_linked_evidence,
)


def _verify_scoped_metadata_selection(
    document: dict[str, Any],
    control: dict[str, Any],
    context: NeotomaAncillaryContext,
    evidence_sources: Mapping[str, Path] | None,
) -> str:
    """Keep independently pinned metadata and its physical namespace local to one call."""
    evidence = resolve_linked_evidence(control, evidence_sources)
    root = _safe_root(evidence.directory)
    with BoundedInputTree(
        root, max_bytes=MAX_EVIDENCE_BYTES, max_files=MAX_PARTS + 1
    ) as tree:

        def read(path: Path, _digest: str, bound: int) -> bytes:
            tree.check()
            return tree.read(path, max_bytes=bound)

        index = _index(root, evidence.manifest_sha256, read)
        expected = {"evidence-manifest.json"} | {
            "proofs/" + row["sha256"] + ".json" for row in index["parts"]
        }
        if set(tree.files) != expected:
            raise ValueError("Scoped linked evidence metadata namespace differs")
        current = _scoped_current_metadata(control, context, index)
        if not _same(document.get("source_evidence"), control["source_evidence"]):
            raise ValueError("Scoped linked capture evidence reference differs")
        entries = document["resources"]
        targets = control["targets"]
        if len(entries) != len(targets):
            raise ValueError("Scoped linked target population differs")
        selected = {}
        for identity in targets:
            kind, native = identity.get("kind"), identity.get("native_id")
            if not isinstance(kind, str) or type(native) is not int:
                raise ValueError(
                    "Scoped linked native target identity is missing or malformed"
                )
            key = f"{kind}-{native}"
            if key not in index["targets"] or key in selected:
                raise ValueError(
                    "Linked target has no unique authenticated source proof"
                )
            selected[key] = {
                "target": index["targets"][key],
                "source_proofs": [],
                "proof_locators": [],
                "scientific_admission": "not_asserted",
                "source_epoch": EVIDENCE_SCHEMA,
            }
        for proof, locator in _occurrences(root, index, set(selected), read):
            key = f"{proof['target_kind']}-{proof['native_id']}"
            selected[key]["source_proofs"].append(proof)
            selected[key]["proof_locators"].append(
                {"evidence_manifest_sha256": evidence.manifest_sha256, **locator}
            )
        for entry, identity in zip(entries, targets, strict=True):
            key = f"{identity['kind']}-{identity['native_id']}"
            row = selected[key]
            row["source_proofs"] = tuple(row["source_proofs"])
            row["proof_locators"] = tuple(row["proof_locators"])
            _restrict_scoped_target(
                row, identity, current, attempted=bool(entry["attempts"])
            )
            if (
                not control["plan"]["include_higher_taxa"]
                and not row["target"]["has_direct_proof"]
            ):
                raise ValueError("Scoped linked target is outside direct selection")
        tree.check()
    return evidence.manifest_sha256
