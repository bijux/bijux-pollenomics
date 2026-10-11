"""Shared repository roots for truth-assessment tests."""

from __future__ import annotations

from collections.abc import Mapping
import unittest

import pytest

from tests.support.repository import REPOSITORY_ROOT


def require_mapping(value: object) -> Mapping[str, object]:
    """Check the string-keyed report-object boundary before field assertions."""
    assert isinstance(value, dict)
    assert all(isinstance(key, str) for key in value)
    return value


def require_rows(value: object) -> list[Mapping[str, object]]:
    """Check row population and object shape without changing report fields."""
    assert isinstance(value, list)
    return [require_mapping(row) for row in value]


def require_strings(value: object) -> list[str]:
    assert isinstance(value, list)
    assert all(isinstance(item, str) for item in value)
    return value


def require_string(value: object) -> str:
    assert isinstance(value, str)
    return value


def require_integer(value: object) -> int:
    assert type(value) is int
    return value


class RepositoryTruthTestCase(unittest.TestCase):
    """Own the canonical repository paths used by truth assessments."""

    pytestmark = pytest.mark.generated_artifacts

    def setUp(self) -> None:
        self.repo_root = REPOSITORY_ROOT
        self.data_root = self.repo_root / "data"
        self.docs_root = self.repo_root / "docs"
        self.report_root = self.docs_root / "report"
