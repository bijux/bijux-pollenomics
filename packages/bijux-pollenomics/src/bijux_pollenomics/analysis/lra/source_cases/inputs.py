"""Capture selected literal inputs once under explicit reference and byte budgets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ....core.filesystem import BoundedInputTree, DirectoryAnchor, OwnedTreeWriter
from .contracts import digest, reference, refuse


class SourceInputs:
    """Hold a source root and immutable captured bytes without opening siblings."""

    def __init__(self, root: Path, snapshot: Path, limits: dict[str, int]) -> None:
        """Create a private evidence snapshot separate from the source namespace."""
        self.anchor = DirectoryAnchor(root)
        self.root = self.anchor.path
        self.limits = limits
        self.buffers: dict[str, bytes] = {}
        self.pins: dict[str, dict[str, Any]] = {}
        self.stamps: dict[str, dict[str, tuple[int, ...]]] = {}
        try:
            if snapshot.absolute().is_relative_to(self.root):
                refuse("Private snapshots must be outside the declared source tree")
            with DirectoryAnchor(snapshot.parent, create=True):
                self.writer = OwnedTreeWriter(
                    snapshot.absolute(),
                    max_bytes=limits["max_input_bytes"],
                    max_files=limits["max_input_files"],
                )
        except BaseException:
            self.anchor.close()
            raise
        self.snapshot = snapshot.absolute()

    def capture(self, value: object) -> bytes:
        """Verify a selected member before caching its single immutable buffer."""
        ref = reference(value)
        name = ref["path"]
        if name in self.pins:
            if self.pins[name] != ref:
                refuse("One input path has conflicting independent source pins")
            return self.buffers[name]
        if (
            len(self.pins) >= self.limits["max_input_files"]
            or sum(len(v) for v in self.buffers.values()) + ref["bytes"]
            > self.limits["max_input_bytes"]
        ):
            refuse("Input inventory exceeds the declared operation budget")
        path = self.root / name
        self.anchor.check()
        with BoundedInputTree(
            path.parent, selected=path.name, max_bytes=max(1, ref["bytes"]), max_files=1
        ) as tree:
            self.anchor.check()
            raw = tree.read(path, max_bytes=ref["bytes"])
            if len(raw) != ref["bytes"] or digest(raw) != ref["sha256"]:
                refuse("Input bytes differ from their independent size/hash pin")
            tree.check()
            self.stamps[name] = dict(tree.files)
        self.anchor.check()
        self.writer.write_bytes(name, raw)
        self.pins[name], self.buffers[name] = ref, raw
        return raw

    def object(self, ref: object) -> dict[str, Any]:
        """Decode an object from its authenticated buffer with duplicate-key refusal."""

        def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
            result: dict[str, Any] = {}
            for key, value in pairs:
                if key in result:
                    refuse("Duplicate JSON object keys are ambiguous")
                result[key] = value
            return result

        try:
            value = json.loads(
                self.capture(ref),
                object_pairs_hook=unique,
                parse_constant=lambda _: refuse("Nonfinite input JSON"),
            )
        except (ValueError, UnicodeError) as exc:
            refuse(f"Invalid source control JSON: {type(exc).__name__}")
        if not isinstance(value, dict):
            refuse("Source control must be a JSON object")
        return value

    def check(self) -> None:
        """Recheck held namespace and captured file stamps without rereading bodies."""
        self.anchor.check()
        for name, ref in self.pins.items():
            path = self.root / name
            with BoundedInputTree(
                path.parent,
                selected=path.name,
                max_bytes=max(1, ref["bytes"]),
                max_files=1,
            ) as tree:
                if tree.files != self.stamps[name]:
                    refuse("Source identity changed after its authenticated capture")
        self.anchor.check()
        self.writer.validate_publication_attachment(self.snapshot)

    def close(self) -> None:
        """Release capabilities while retaining private analytical evidence."""
        self.writer.close()
        self.anchor.close()
