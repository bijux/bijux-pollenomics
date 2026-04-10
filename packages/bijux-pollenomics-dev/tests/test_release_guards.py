"""Release guard coverage."""

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics_dev.release.publication_guard import (
    artifact_versions,
    assert_artifacts_match_version,
    assert_publishable_version,
)
from bijux_pollenomics_dev.release.version_resolver import resolve_version


def test_resolve_version_uses_static_pyproject_version(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[project]
name = "example-package"
version = "1.2.3"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    assert resolve_version(pyproject, "example-package") == "1.2.3"


def test_assert_publishable_version_rejects_prerelease() -> None:
    with pytest.raises(ValueError, match="prerelease"):
        assert_publishable_version("1.2.3rc1")


def test_assert_publishable_version_rejects_local_build_marker() -> None:
    with pytest.raises(ValueError, match="local build marker"):
        assert_publishable_version("1.2.3+dirty")


def test_artifact_versions_read_wheel_and_sdist_names(tmp_path: Path) -> None:
    (tmp_path / "example_package-1.2.3-py3-none-any.whl").write_text(
        "",
        encoding="utf-8",
    )
    (tmp_path / "example-package-1.2.3.tar.gz").write_text("", encoding="utf-8")

    assert artifact_versions(tmp_path) == {
        "example-package-1.2.3.tar.gz": "1.2.3",
        "example_package-1.2.3-py3-none-any.whl": "1.2.3",
    }


def test_assert_artifacts_match_version_rejects_mismatch(tmp_path: Path) -> None:
    (tmp_path / "example_package-1.2.4-py3-none-any.whl").write_text(
        "",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="artifact versions do not match"):
        assert_artifacts_match_version(tmp_path, "1.2.3")
