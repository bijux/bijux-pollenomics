"""Tests for repository-root discovery independent of module depth."""

import pytest

from bijux_pollenomics.core.repository import (
    RepositoryRootNotFoundError,
    find_repository_root,
    repository_data_root,
)
from tests.support.repository import REPOSITORY_ROOT


def test_find_repository_root_from_nested_source() -> None:
    nested_source = (
        REPOSITORY_ROOT
        / "packages/bijux-pollenomics/src/bijux_pollenomics/adna/projects/evidence/sites.py"
    )

    assert find_repository_root(nested_source) == REPOSITORY_ROOT
    assert repository_data_root(nested_source) == REPOSITORY_ROOT / "data"


def test_find_repository_root_refuses_unowned_tree() -> None:
    unrelated_file = (
        REPOSITORY_ROOT.parent
        / f"{REPOSITORY_ROOT.name}-unowned"
        / "package"
        / "module.py"
    )

    with pytest.raises(RepositoryRootNotFoundError):
        find_repository_root(unrelated_file)
