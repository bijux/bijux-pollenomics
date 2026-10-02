"""Release guard coverage."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

from bijux_pollenomics_dev.release import publication_guard
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
        assert_artifacts_match_version(tmp_path, "1.2.3", "example-package")


def test_release_artifacts_require_one_project_and_both_archive_kinds(
    tmp_path: Path,
) -> None:
    (tmp_path / "example_package-1.2.3-py3-none-any.whl").write_bytes(b"")
    with pytest.raises(ValueError, match="one wheel and one sdist"):
        assert_artifacts_match_version(tmp_path, "1.2.3", "example-package")

    (tmp_path / "example-package-1.2.3.tar.gz").write_bytes(b"")
    assert_artifacts_match_version(tmp_path, "1.2.3", "example-package")
    (tmp_path / "other_package-1.2.3-py3-none-any.whl").write_bytes(b"")
    with pytest.raises(ValueError, match="does not match requested project"):
        assert_artifacts_match_version(tmp_path, "1.2.3", "example-package")


def test_distinct_platform_wheels_are_permitted(tmp_path: Path) -> None:
    for name in (
        "example_package-1.2.3-py3-none-any.whl",
        "example_package-1.2.3-cp311-cp311-manylinux_x86_64.whl",
        "example-package-1.2.3.tar.gz",
    ):
        (tmp_path / name).write_bytes(b"")
    assert_artifacts_match_version(tmp_path, "1.2.3", "example-package")


def test_duplicate_normalized_sdist_is_refused(tmp_path: Path) -> None:
    for name in (
        "example_package-1.2.3-py3-none-any.whl",
        "example-package-1.2.3.tar.gz",
        "example_package-1.2.3.tar.gz",
    ):
        (tmp_path / name).write_bytes(b"")
    with pytest.raises(ValueError, match="duplicate normalized"):
        assert_artifacts_match_version(tmp_path, "1.2.3", "example-package")


def test_malformed_wheel_name_is_refused(tmp_path: Path) -> None:
    (tmp_path / "example_package-1.2.3-improper.whl").write_bytes(b"")
    (tmp_path / "example-package-1.2.3.tar.gz").write_bytes(b"")
    with pytest.raises(ValueError, match="unrecognized wheel filename"):
        assert_artifacts_match_version(tmp_path, "1.2.3", "example-package")


@pytest.mark.parametrize(
    ("wheel", "reason"),
    [
        ("example_package-1.2.3-py3..py2-none-any.whl", "compatibility tags"),
        ("example_package-1.2.3-py3-none-any..whl", "compatibility tags"),
        ("example_package-1.2.3-abc-py3-none-any.whl", "build tag"),
        ("example_package_-1.2.3-py3-none-any.whl", "invalid distribution name"),
    ],
)
def test_malformed_wheel_components_are_refused(
    tmp_path: Path, wheel: str, reason: str
) -> None:
    (tmp_path / wheel).write_bytes(b"")
    (tmp_path / "example-package-1.2.3.tar.gz").write_bytes(b"")
    with pytest.raises(ValueError, match=reason):
        assert_artifacts_match_version(tmp_path, "1.2.3", "example-package")


def test_normalized_wheel_alias_does_not_duplicate_same_tag(tmp_path: Path) -> None:
    for name in (
        "example_package-1.2.3-py3-none-any.whl",
        "Example.Package-1.2.3-py3-none-any.whl",
        "example-package-1.2.3.tar.gz",
    ):
        (tmp_path / name).write_bytes(b"")
    with pytest.raises(ValueError, match="duplicate normalized"):
        assert_artifacts_match_version(tmp_path, "1.2.3", "example-package")


def test_cli_binds_requested_project_to_staged_archives(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "example-package"\nversion = "1.2.3"\n',
        encoding="utf-8",
    )
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "example_package-1.2.3-py3-none-any.whl").write_bytes(b"")
    (dist / "example-package-1.2.3.tar.gz").write_bytes(b"")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "publication_guard",
            "--pyproject",
            str(pyproject),
            "--package-name",
            "example-package",
            "--dist-dir",
            str(dist),
        ],
    )
    assert publication_guard.main() == 0
    assert capsys.readouterr().out == "1.2.3\n"
    pyproject.write_text(
        '[project]\nname = "different-package"\nversion = "1.2.3"\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="pyproject project name"):
        publication_guard.main()
    pyproject.write_text(
        '[project]\nname = "example-package"\nversion = "1.2.3"\n',
        encoding="utf-8",
    )
    (dist / "other_package-1.2.3-py3-none-any.whl").write_bytes(b"")
    with pytest.raises(ValueError, match="does not match requested project"):
        publication_guard.main()
