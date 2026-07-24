from __future__ import annotations

from configparser import ConfigParser
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def _tox_config() -> ConfigParser:
    parser = ConfigParser()
    parser.read(REPO_ROOT / "tox.ini", encoding="utf-8")
    return parser


def _envlist() -> set[str]:
    envlist = _tox_config()["tox"]["envlist"]
    return {line.strip() for line in envlist.splitlines() if line.strip()}


def test_root_tox_keeps_the_shared_env_families_and_drops_proteomics_only_ones() -> (
    None
):
    envlist = _envlist()

    assert "security" in envlist
    assert "docs" in envlist
    assert "fmt-{dev,core,alias}" not in envlist
    assert "api-freeze-core" not in envlist
    assert "openapi-drift-core" not in envlist


def test_root_tox_installs_the_locked_workspace_without_ci_only_plugins() -> None:
    tox_config = _tox_config()
    tox_requirements = tox_config["tox"]["requires"]
    test_environment = tox_config["testenv"]
    root_environments = (
        tox_config["testenv:security"],
        tox_config["testenv:docs"],
    )

    assert "tox-gh-actions" not in tox_requirements
    assert (
        "uv sync --frozen --all-packages --all-extras"
        in test_environment["commands_pre"]
    )
    assert "uv" in test_environment["allowlist_externals"].splitlines()
    assert all(
        "uv" in environment["allowlist_externals"].splitlines()
        for environment in root_environments
    )
    assert "UV_PROJECT_ENVIRONMENT = {envdir}" in test_environment["setenv"]


def test_root_make_declares_shared_maintainer_commands() -> None:
    root_make = (REPO_ROOT / "makes" / "root.mk").read_text(encoding="utf-8")

    assert "check:" in root_make
    assert "sync-badges:" in root_make
    assert "check-badges:" in root_make


def test_core_package_make_installs_runtime_dev_extras_for_ci_tests() -> None:
    core_make = (REPO_ROOT / "makes" / "packages" / "bijux-pollenomics.mk").read_text(
        encoding="utf-8"
    )

    assert "PACKAGE_INSTALL_SPEC := .[dev]" in core_make


def test_shared_package_make_uses_virtualenv_interpreter_as_readiness_target() -> None:
    shared_package_make = (REPO_ROOT / "makes" / "bijux-py" / "package.mk").read_text(
        encoding="utf-8"
    )
    build_make = (REPO_ROOT / "makes" / "bijux-py" / "ci" / "build.mk").read_text(
        encoding="utf-8"
    )
    lint_make = (REPO_ROOT / "makes" / "bijux-py" / "ci" / "lint.mk").read_text(
        encoding="utf-8"
    )
    sbom_make = (REPO_ROOT / "makes" / "bijux-py" / "ci" / "sbom.mk").read_text(
        encoding="utf-8"
    )
    api_make = (REPO_ROOT / "makes" / "bijux-py" / "api-contract.mk").read_text(
        encoding="utf-8"
    )

    assert "$(VENV_PYTHON): | setup" in shared_package_make
    assert "$(PACKAGE_INSTALL_STAMP): $(VENV_PYTHON)" in shared_package_make
    assert "install: $(VENV_PYTHON)" in shared_package_make
    assert "ensure-venv: $(VENV_PYTHON)" in shared_package_make
    assert "build-tools: | $(VENV_PYTHON)" in build_make
    assert "fmt-artifacts: | $(VENV_PYTHON)" in lint_make
    assert "lint-artifacts: | $(VENV_PYTHON)" in lint_make
    assert "sbom-tooling: | $(VENV_PYTHON)" in sbom_make
    assert "api-install: | $(VENV_PYTHON)" in api_make
    assert "api-test: | $(VENV_PYTHON)" in api_make
