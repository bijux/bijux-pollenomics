"""Exercise finite source correspondence without copying scientific packets or packages."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.retained_source.capsule import (
    validate_physical_capsule,
)
from bijux_pollenomics_dev.lra_validation.native_reference import (
    finite_covariance_capture as capture,
)


def _identity(body: bytes) -> dict[str, Any]:
    return {"sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body)}


@pytest.fixture
def source_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    body = b"controlled_source = 1\n"
    (tmp_path / "source.py").write_bytes(body)
    original = "84040f998392398c91779befcbac6807d107b3d1c62a57e4b440dbf1fcc680c5"
    row = {
        "schema_version": "native-finite-generated-source.v1",
        "source_path": capture.GENERATED_SOURCE,
        "identity": {"sha256": original, "bytes": 539},
        "correspondence": {
            "member": capture.GENERATED_SOURCE,
            "generator": {
                "provider": "vcs-versioning.default-python",
                "sha256": "dd7ded849d3bacc8e13b0b675ed991904eb896fc79b4607f4f70ee32e47171d9",
                "bytes": 4479,
            },
            "scalars": {
                "version": "0.1.9.dev1462",
                "version_tuple": [0, 1, 9, "dev1462"],
                "short_node": None,
            },
            "original_generator_execution_claimed": False,
            "original_version_derivation_claimed": False,
        },
    }
    context = {
        "protected_science_sha256": {
            "source.py": _identity(body)["sha256"],
            capture.GENERATED_SOURCE: original,
        },
        "generated_source_sha256": {capture.GENERATED_SOURCE: original},
    }
    payload = json.dumps(row, separators=(",", ":")).encode()
    path = tmp_path / capture.GENERATED_CONFIG
    path.parent.mkdir(parents=True)
    path.write_bytes(payload)
    monkeypatch.setattr(
        capture, "GENERATED_CONFIG_SHA256", hashlib.sha256(payload).hexdigest()
    )
    monkeypatch.setattr(capture, "GENERATED_CONFIG_BYTES", len(payload))
    return tmp_path, context, row


def test_generated_content_correspondence_keeps_original_bytes(
    source_metadata: tuple[Path, dict[str, Any], dict[str, Any]],
) -> None:
    root, context, row = source_metadata
    body = capture._generated_source(root, context)
    assert _identity(body) == row["identity"]
    assert row["correspondence"]["original_generator_execution_claimed"] is False
    assert row["correspondence"]["original_version_derivation_claimed"] is False
    capture._require_current_sources(root, context)
    assert not (root / capture.GENERATED_SOURCE).exists()


@pytest.mark.parametrize(
    "change",
    [
        "source-bytes",
        "source-missing",
        "source-link",
        "generated-bytes",
        "generated-missing",
        "metadata-context",
    ],
)
def test_current_source_or_generated_metadata_change_refuses(
    source_metadata: tuple[Path, dict[str, Any], dict[str, Any]], change: str
) -> None:
    root, context, _ = source_metadata
    path = root / "source.py"
    if change == "source-bytes":
        path.write_bytes(b"controlled_source = 2\n")
    elif change == "source-missing":
        path.unlink()
    elif change == "source-link":
        other = root / "backing.py"
        path.rename(other)
        path.symlink_to(other)
    elif change == "generated-bytes":
        path = root / capture.GENERATED_CONFIG
        path.write_bytes(path.read_bytes() + b" ")
    elif change == "generated-missing":
        (root / capture.GENERATED_CONFIG).unlink()
    else:
        context["generated_source_sha256"].clear()
    with pytest.raises(ValueError, match="protected source"):
        capture._require_current_sources(root, context)


@pytest.mark.parametrize(
    "change",
    [
        "provider",
        "scalar",
        "tuple",
        "size",
        "hash",
        "boolean-size",
        "generation-claim",
        "derivation-claim",
        "member",
        "extra",
    ],
)
def test_reviewed_scalar_configuration_cannot_widen_correspondence(
    source_metadata: tuple[Path, dict[str, Any], dict[str, Any]],
    monkeypatch: pytest.MonkeyPatch,
    change: str,
) -> None:
    root, context, original = source_metadata
    row = deepcopy(original)
    if change == "provider":
        row["correspondence"]["generator"]["provider"] = "unreviewed"
    elif change == "scalar":
        row["correspondence"]["scalars"]["version"] = "0.1.9.dev1463"
    elif change == "tuple":
        row["correspondence"]["scalars"]["version_tuple"][0] = True
    elif change == "size":
        row["identity"]["bytes"] += 1
    elif change == "hash":
        row["identity"]["sha256"] = "0" * 64
    elif change == "boolean-size":
        row["identity"]["bytes"] = True
    elif change == "generation-claim":
        row["correspondence"]["original_generator_execution_claimed"] = True
    elif change == "derivation-claim":
        row["correspondence"]["original_version_derivation_claimed"] = True
    elif change == "member":
        row["correspondence"]["member"] = "unreviewed.py"
    else:
        row["accepted"] = True
    payload = json.dumps(row, separators=(",", ":")).encode()
    (root / capture.GENERATED_CONFIG).write_bytes(payload)
    monkeypatch.setattr(
        capture, "GENERATED_CONFIG_SHA256", hashlib.sha256(payload).hexdigest()
    )
    monkeypatch.setattr(capture, "GENERATED_CONFIG_BYTES", len(payload))
    with pytest.raises((ValueError, ReportRebuildError)):
        capture._generated_source(root, context)


@pytest.mark.parametrize("change", ["extra", "missing", "symlink", "hardlink"])
def test_physical_capsule_membership_and_alias_guards(
    tmp_path: Path, change: str
) -> None:
    prefix = "data/controlled-capture"
    root = tmp_path / prefix
    root.mkdir(parents=True)
    body = b"1\n"
    target = root / "values.csv"
    target.write_bytes(body)
    manifest = b"{}"
    (root / "capture.json").write_bytes(manifest)
    (root / "source-transport.json").write_bytes(b"{}")
    args = (
        tmp_path,
        prefix,
        {"values.csv": _identity(body)},
        frozenset[str](),
        "source-transport.json",
        _identity(manifest),
    )
    validate_physical_capsule(*args)
    if change == "extra":
        (root / "extra.csv").write_bytes(body)
    elif change == "missing":
        target.unlink()
    else:
        backing = tmp_path / "backing.csv"
        target.rename(backing)
        if change == "symlink":
            target.symlink_to(backing)
        else:
            os.link(backing, target)
    with pytest.raises(ReportRebuildError):
        validate_physical_capsule(*args)
