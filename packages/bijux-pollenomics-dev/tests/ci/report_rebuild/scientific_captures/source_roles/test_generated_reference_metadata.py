"""Authenticate literal version retrieval without changing historical reader contracts."""

from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.retained_source.objects import (
    environment,
    git_executable,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.source_roles import (
    native_reference_transport as subject,
)

_REPOSITORY = Path(__file__).resolve().parents[7]
_PARENT = "26e526a3e126d195d71da29c05696a344f147ac4"
_WITNESSES = {
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/lra_reference/evidence.py": (
        "f59e38ff5f3fef623611dd47a6fa821f070ba9cb",
        17083,
        "9bd4b32cdaba1a1cd313ad3209d3e63b5ea17a2a41b1125070cf3bd2c4472a0c",
    ),
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/retained_reference/identity.py": (
        "2da70e3da4f3391af306472174342f236d1cb792",
        4875,
        "bab7252e9e0b8059a58aa486555163b1cbde321bf1b870da719b23a3253f44bf",
    ),
}


def _git_bytes(*arguments: str) -> bytes:
    """Read normal retained Git objects without executing their source bytes."""
    return subprocess.run(
        [
            str(git_executable()),
            "--no-replace-objects",
            "-C",
            str(_REPOSITORY),
            *arguments,
        ],
        env=environment(),
        capture_output=True,
        check=True,
        timeout=10,
    ).stdout


def _case(name: str) -> tuple[bytes, bytes]:
    blob, size, checksum = _WITNESSES[name]
    captured = _git_bytes("cat-file", "blob", blob)
    assert len(captured) == size
    assert hashlib.sha256(captured).hexdigest() == checksum
    assert subject._NATIVE_REFERENCE_TRANSPORT_CONTRACTS[name][:2] == (size, checksum)
    current = (_REPOSITORY / name).read_bytes()
    assert subject.native_reference_transport_extension_matches(name, captured, current)
    return captured, current


@pytest.mark.parametrize("name", tuple(_WITNESSES))
@pytest.mark.parametrize("basis", ["five_member_parent", "six_member_current"])
def test_both_generated_metadata_populations_recover_exact_original_reader(
    name: str, basis: str
) -> None:
    captured, current = _case(name)
    selected = (
        _git_bytes("show", _PARENT + ":" + name)
        if basis == "five_member_parent"
        else current
    )
    assert subject.native_reference_transport_extension_matches(
        name, captured, selected
    )


@pytest.mark.parametrize("name", tuple(_WITNESSES))
@pytest.mark.parametrize(
    "damage", ["generated_name", "source_lock", "import", "statement", "suffix"]
)
def test_generated_metadata_layer_refuses_every_unreviewed_source_change(
    name: str, damage: str
) -> None:
    captured, current = _case(name)
    if damage == "generated_name":
        changed = current.replace(b"_build_version.py", b"_unlisted_version.py", 1)
    elif damage == "source_lock":
        changed = current.replace(b'"source-lock.json",', b'"unlisted-lock.json",', 1)
    elif damage == "import":
        changed = current.replace(
            b"from __future__ import annotations\n",
            b"from __future__ import annotations\nimport unexpected_dependency\n",
            1,
        )
    elif damage == "statement":
        changed = current + b"\nunexpected_action()\n"
    else:
        changed = current + b"\n# unreviewed residual bytes\n"
    assert changed != current
    assert not subject.native_reference_transport_extension_matches(
        name, captured, changed
    )


@pytest.mark.parametrize("span", [0, 1])
def test_partial_generated_reader_layer_does_not_hide_missing_scope_or_callback(
    span: int,
) -> None:
    name = next(iter(_WITNESSES))
    captured, current = _case(name)
    previous, inserted = subject._GENERATED_REFERENCE_METADATA_IO_SPANS[name][span]
    assert current.count(inserted) == 1
    partial = current.replace(inserted, previous, 1)
    assert partial != current
    assert not subject.native_reference_transport_extension_matches(
        name, captured, partial
    )


@pytest.mark.parametrize("name", tuple(_WITNESSES))
def test_duplicate_generated_reader_seam_remains_unreviewed(name: str) -> None:
    captured, current = _case(name)
    inserted = subject._GENERATED_REFERENCE_METADATA_IO_SPANS[name][0][1]
    assert current.count(inserted) == 1
    assert not subject.native_reference_transport_extension_matches(
        name, captured, current + inserted
    )


@pytest.mark.parametrize("name", tuple(_WITNESSES))
def test_generated_metadata_retrieval_cannot_rebind_the_original_reader(
    name: str,
) -> None:
    captured, current = _case(name)
    assert not subject.native_reference_transport_extension_matches(
        name, captured + b"\n# changed original\n", current
    )


def test_generated_metadata_layer_does_not_create_an_unlisted_reader() -> None:
    name = next(iter(_WITNESSES))
    captured, current = _case(name)
    assert not subject.native_reference_transport_extension_matches(
        "packages/owned/unlisted_reader.py", captured, current
    )
