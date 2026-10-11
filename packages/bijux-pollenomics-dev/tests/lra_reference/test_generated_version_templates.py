"""Admit only the publisher's static typing template, never generated execution."""

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics_dev.ci.lra_reference import source_identity as identity
from bijux_pollenomics_dev.ci.lra_reference.contracts import ReferenceRefusal

from . import test_source_identity as FIXTURES

TYPING_BLOCK = b"""TYPE_CHECKING = False
if TYPE_CHECKING:
    from typing import Tuple
    from typing import Union

    VERSION_TUPLE = Tuple[Union[int, str], ...]
    COMMIT_ID = Union[str, None]
else:
    VERSION_TUPLE = object
    COMMIT_ID = object

version: str
__version__: str
__version_tuple__: VERSION_TUPLE
version_tuple: VERSION_TUPLE
commit_id: COMMIT_ID
__commit_id__: COMMIT_ID
"""


def static_typing_template() -> bytes:
    """Build the exact setuptools-scm 9.2.2 AST shape with synthetic literal values."""
    return (
        b'__all__ = ["__version__", "version", "__version_tuple__", "version_tuple", "__commit_id__", "commit_id"]\n'
        + TYPING_BLOCK
        + b"__version__ = version = '0.1.9.dev1207'\n"
        + b"__version_tuple__ = version_tuple = (0, 1, 9, 'dev1207')\n"
        + b"__commit_id__ = commit_id = 'g7eb75cc299'\n"
    )


def test_literal_static_typing_template_retains_git_identity() -> None:
    result = identity.generated_literals(static_typing_template())
    assert result == {
        "version": "0.1.9.dev1207",
        "version_tuple": [0, 1, 9, "dev1207"],
        "commit_id": "g7eb75cc299",
    }


def test_static_typing_template_remains_separate_from_committed_source(
    tmp_path: Path,
) -> None:
    tree = FIXTURES.fixture_tree(tmp_path)
    original = identity.inspect_source_identity(tmp_path, tree)
    target = tmp_path / identity.GENERATED_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(static_typing_template())
    after = identity.inspect_source_identity(tmp_path, tree)
    assert after.tracked_files == original.tracked_files
    assert after.tracked_git_blobs == original.tracked_git_blobs
    assert after.generated_files[identity.GENERATED_PATH]["committed_source"] is False
    assert (
        after.generated_files[identity.GENERATED_PATH]["literals"]["commit_id"]
        == "g7eb75cc299"
    )


@pytest.mark.parametrize(
    "before,after",
    [
        (b"TYPE_CHECKING = False", b"TYPE_CHECKING = True"),
        (b"if TYPE_CHECKING:", b"if __import__('os'):"),
        (b"from typing import Tuple", b"from os import system as Tuple"),
        (b"from typing import Union", b"from typing import Union as Alias"),
        (b"Tuple[Union[int, str], ...]", b"Tuple[Union[int, str], str(1)]"),
        (b"VERSION_TUPLE = object", b"VERSION_TUPLE = __import__('os')"),
        (b"COMMIT_ID = object", b"COMMIT_ID = object()"),
        (b"__version_tuple__: VERSION_TUPLE", b"__version_tuple__: COMMIT_ID"),
        (b"'g7eb75cc299'", b"'h7eb75cc299'"),
        (b"'g7eb75cc299'", b"'gNOTHEX'"),
    ],
)
def test_typing_or_git_literal_mutation_is_refused(before: bytes, after: bytes) -> None:
    with pytest.raises(ReferenceRefusal):
        identity.generated_literals(static_typing_template().replace(before, after))


@pytest.mark.parametrize(
    "suffix",
    [
        b"\nimport os\n",
        b"\nraise RuntimeError('executed')\n",
        b"\nTYPE_CHECKING = False\n",
        b"\n__commit_id__ = commit_id = None\n",
        b"\nif TYPE_CHECKING:\n    import os\n",
    ],
)
def test_static_typing_template_cannot_hide_extra_execution(suffix: bytes) -> None:
    with pytest.raises(ReferenceRefusal):
        identity.generated_literals(static_typing_template() + suffix)


@pytest.mark.parametrize("commit", [None, "0123456789", "g0123456789"])
def test_existing_union_annotation_template_preserves_supported_git_literals(
    commit: str | None,
) -> None:
    template = FIXTURES.TEMPLATE.replace(
        b"__commit_id__ = commit_id = None",
        f"__commit_id__ = commit_id = {commit!r}".encode(),
    )
    result = identity.generated_literals(template)
    assert result["version"] == "0.1.9.dev4+dirty"
    assert result["commit_id"] == commit
