"""Shared repository roots for truth-assessment tests."""

from __future__ import annotations

import unittest

import pytest

from tests.support.repository import REPOSITORY_ROOT


class RepositoryTruthTestCase(unittest.TestCase):
    """Own the canonical repository paths used by truth assessments."""

    pytestmark = pytest.mark.generated_artifacts

    def setUp(self) -> None:
        self.repo_root = REPOSITORY_ROOT
        self.data_root = self.repo_root / "data"
        self.docs_root = self.repo_root / "docs"
        self.report_root = self.docs_root / "report"
