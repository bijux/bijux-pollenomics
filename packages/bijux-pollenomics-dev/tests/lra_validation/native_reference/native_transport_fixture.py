"""Bind invented native packets to the real physical SourceCapsule checks."""

from __future__ import annotations

import hashlib
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.retained_source import index
from bijux_pollenomics_dev.ci.report_rebuild.retained_source.descriptor import (
    Descriptor,
)


def install_native_transport(
    repository: Path, subject: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Mock only registered lookup/ref context; validate all invented physical bytes."""
    prefix = subject.CAPTURE_ROOT
    directory = repository / prefix
    descriptor_path = directory / "source-transport.json"
    descriptor_body = b'{"constructed_native_transport":true}\n'
    descriptor_path.write_bytes(descriptor_body)
    monkeypatch.setattr(index, "_refs", lambda root: ())

    def selected(
        root: Path, selected_prefix: str, members: dict[str, dict[str, Any]]
    ) -> index.SourceCapsule:
        assert root == repository and selected_prefix == prefix
        assert descriptor_path.read_bytes() == descriptor_body
        manifest = directory / "capture/capture.json"
        raw = manifest.read_bytes()
        descriptor = Descriptor(
            "capture/capture.json",
            {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)},
            (),
            (),
            frozenset(),
            members,
            prefix,
        )
        source = index.SourceCapsule(
            root,
            prefix,
            "source-transport.json",
            descriptor,
            (
                (manifest, index._seal(manifest)),
                (descriptor_path, index._seal(descriptor_path)),
            ),
            (),
        )
        source.validate()
        return source

    monkeypatch.setattr(subject, "validated_descriptor", selected)
