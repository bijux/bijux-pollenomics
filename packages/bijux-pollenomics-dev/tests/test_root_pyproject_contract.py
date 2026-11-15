from __future__ import annotations

from pathlib import Path
import tomllib
from typing import Any, cast

REPO_ROOT = Path(__file__).resolve().parents[3]
WORKSPACE_TOOL = "bijux_pollenomics"


def _root_pyproject() -> dict[str, Any]:
    with (REPO_ROOT / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)


def test_root_pyproject_keeps_distribution_builds_in_workspace_packages() -> None:
    pyproject = _root_pyproject()
    tool_section = cast(dict[str, Any], pyproject["tool"])
    assert "project" not in pyproject
    assert "build-system" not in pyproject
    assert "hatch" not in tool_section
    assert tool_section["uv"]["workspace"]["members"] == ["packages/*"]
    names = []
    for path in sorted((REPO_ROOT / "packages").glob("*/pyproject.toml")):
        package = tomllib.loads(path.read_text())
        names.append(package["project"]["name"])
        assert "build-system" in package
    assert set(names) == set(tool_section[WORKSPACE_TOOL]["packages"])
    assert len(names) == len(set(names))


def test_root_pyproject_exposes_all_workspace_packages_to_root_dev_installs() -> None:
    pyproject = _root_pyproject()
    tool_section = cast(dict[str, Any], pyproject["tool"])
    workspace_config = cast(dict[str, object], tool_section[WORKSPACE_TOOL])
    workspace_packages = set(cast(list[str], workspace_config["packages"]))
    dependency_groups = cast(dict[str, list[str]], pyproject["dependency-groups"])
    dev_group = dependency_groups["dev"]
    dev_group_entries = {entry.split("[", 1)[0] for entry in dev_group}

    assert dev_group_entries.issuperset(workspace_packages)


def test_root_pyproject_uses_workspace_sources_for_every_workspace_package() -> None:
    pyproject = _root_pyproject()
    tool_section = cast(dict[str, Any], pyproject["tool"])
    workspace_config = cast(dict[str, object], tool_section[WORKSPACE_TOOL])
    workspace_packages = set(cast(list[str], workspace_config["packages"]))
    uv_sources = cast(dict[str, dict[str, bool]], tool_section["uv"]["sources"])

    assert set(uv_sources) == workspace_packages
    assert {
        name for name, config in uv_sources.items() if config == {"workspace": True}
    } == (workspace_packages)
