"""Keep historical generated provenance separate from current numerical source."""

from __future__ import annotations

import copy
import hashlib
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.retained_source import SourceCapsule
from bijux_pollenomics_dev.ci.report_rebuild.retained_source.generated import (
    reconstruct,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.author_grid.admission import (
    _current_numerical_source_role,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.source_correspondence import (
    VERSION_IDENTITY,
    VERSION_SOURCE,
)


def _version() -> tuple[dict[str, Any], dict[str, Any], Any]:
    logical = "numerical-source/" + VERSION_SOURCE
    declaration = {
        "member": logical,
        "generator": {
            "provider": "vcs-versioning.default-python",
            "sha256": "dd7ded849d3bacc8e13b0b675ed991904eb896fc79b4607f4f70ee32e47171d9",
            "bytes": 4479,
        },
        "original_generator_execution_claimed": False,
        "original_version_derivation_claimed": False,
        "scalars": {
            "version": "0.1.9.dev1462",
            "version_tuple": [0, 1, 9, "dev1462"],
            "short_node": None,
        },
    }
    identity = dict(VERSION_IDENTITY)
    body = reconstruct(declaration, identity)
    assert len(body) == 539
    buffer = SimpleNamespace(
        descriptor=SimpleNamespace(
            members={logical: identity}, generated=[declaration]
        ),
        detached=frozenset({logical}),
        read_source=lambda name: body,
    )
    row = {"path": VERSION_SOURCE, "captured_path": logical, **identity}
    return row, {logical: identity}, buffer


def test_generated_version_uses_its_declared_source_not_current_file(
    tmp_path: Path,
) -> None:
    row, members, buffer = _version()
    role = _current_numerical_source_role(
        tmp_path, row, members, cast(SourceCapsule, buffer)
    )
    assert role is not None
    assert role["classification"] == "historical_generated_version_metadata"
    assert role["current_file_equality_claimed"] is False
    current = tmp_path / VERSION_SOURCE
    current.parent.mkdir(parents=True)
    current.write_text("version = 'synthetic-current'\n", encoding="utf-8")
    assert (
        _current_numerical_source_role(
            tmp_path, row, members, cast(SourceCapsule, buffer)
        )
        == role
    )
    assert current.read_text(encoding="utf-8") == "version = 'synthetic-current'\n"


@pytest.mark.parametrize(
    "violation",
    [
        "provider",
        "generator_hash",
        "generator_size",
        "scalars",
        "logical_path",
        "declared_member_path",
        "duplicate_authority",
        "row_hash",
        "row_size",
        "boolean_size",
        "source_bytes",
        "genesis_claim",
    ],
)
def test_generated_version_refuses_changed_authority(
    tmp_path: Path, violation: str
) -> None:
    row, members, buffer = _version()
    declaration = buffer.descriptor.generated[0]
    if violation == "provider":
        declaration["generator"]["provider"] = "another-generator"
    elif violation == "generator_hash":
        declaration["generator"]["sha256"] = "0" * 64
    elif violation == "generator_size":
        declaration["generator"]["bytes"] = 4480
    elif violation == "scalars":
        declaration["scalars"]["version"] = "0.0.0"
    elif violation == "logical_path":
        row["captured_path"] = "another-source/" + VERSION_SOURCE
        members[row["captured_path"]] = dict(VERSION_IDENTITY)
    elif violation == "declared_member_path":
        declaration["member"] = "another-source/" + VERSION_SOURCE
    elif violation == "duplicate_authority":
        buffer.descriptor.generated.append(copy.deepcopy(declaration))
    elif violation == "row_hash":
        row["sha256"] = "0" * 64
    elif violation == "row_size":
        row["bytes"] = 540
    elif violation == "boolean_size":
        row["bytes"] = True
    elif violation == "genesis_claim":
        declaration["original_generator_execution_claimed"] = True
    else:
        buffer.read_source = lambda name: b"synthetic changed source"
    with pytest.raises((ReportRebuildError, ValueError)):
        _current_numerical_source_role(
            tmp_path, row, members, cast(SourceCapsule, buffer)
        )


def test_other_numerical_sources_remain_byte_strict(tmp_path: Path) -> None:
    body = b"coefficient = 1.0\n"
    path = "numeric.py"
    logical = "numerical-source/" + path
    current = tmp_path / path
    current.write_bytes(body)
    identity = {"bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}
    row = {"path": path, "captured_path": logical, **identity}
    members = {logical: identity}
    _, _, buffer = _version()
    assert (
        _current_numerical_source_role(
            tmp_path, row, members, cast(SourceCapsule, buffer)
        )
        is None
    )
    current.write_bytes(b"coefficient = 2.0\n")
    with pytest.raises(ValueError, match="numerical source changed"):
        _current_numerical_source_role(
            tmp_path, row, members, cast(SourceCapsule, buffer)
        )


def test_version_authority_does_not_admit_another_source_path(
    tmp_path: Path,
) -> None:
    row, members, buffer = _version()
    row["path"] = VERSION_SOURCE.replace("_build_version.py", "another.py")
    with pytest.raises(ValueError, match="physical file required"):
        _current_numerical_source_role(
            tmp_path, row, members, cast(SourceCapsule, buffer)
        )
