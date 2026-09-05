"""Fixtures for materialized source-library verification."""

from pathlib import Path

import pytest

from .support import materialize_test_library


@pytest.fixture(scope="package")
def materialized_output_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Materialize the expensive shared fixture once for this test package."""
    return materialize_test_library(tmp_path_factory.mktemp("source-library") / "data")
