from __future__ import annotations

from pathlib import Path
import tomllib
from typing import Any, cast

REPO_ROOT = Path(__file__).resolve().parents[3]
WORKSPACE_TOOL = "bijux_pollenomics"


def _root_pyproject() -> dict[str, Any]:
    with (REPO_ROOT / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)


def test_root_pyproject_uses_shared_workspace_build_contract() -> None:
    pyproject = _root_pyproject()

    assert pyproject["build-system"] == {
        "requires": ["hatchling>=1.27.0,<1.30", "hatch-vcs>=0.4.0,<1.0"],
        "build-backend": "hatchling.build",
    }

    project = cast(dict[str, object], pyproject["project"])
    assert project["dynamic"] == ["version"]
    assert "version" not in project

    tool_section = cast(dict[str, Any], pyproject["tool"])
    hatch_version = cast(dict[str, object], tool_section["hatch"]["version"])
    assert hatch_version["source"] == "vcs"
    assert hatch_version["tag-pattern"] == "^v(?P<version>.*)$"

    assert tool_section["uv"]["workspace"]["members"] == ["packages/*"]
    assert tool_section["hatch"]["build"]["targets"]["wheel"] == {
        "bypass-selection": True
    }


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
