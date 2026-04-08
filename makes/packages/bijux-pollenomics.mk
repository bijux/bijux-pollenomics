include $(abspath $(dir $(lastword $(MAKEFILE_LIST))))/../package/profile.mk
include $(ROOT_MAKE_DIR)/package/python-package.mk

PACKAGE_IMPORT_NAME := bijux_pollenomics
PACKAGE_LINT_EXTRA_DIRS := $(MONOREPO_ROOT)/docs/hooks
PACKAGE_INSTALL_PYTHON_PACKAGES := $(MONOREPO_ROOT)/packages/bijux-pollenomics-dev
LINT_DIRS := src tests $(PACKAGE_LINT_EXTRA_DIRS)
RUFF_CONFIG := $(MONOREPO_ROOT)/configs/ruff.toml
ENABLE_MYPY := 0
ENABLE_CODESPELL := 0
ENABLE_RADON := 0
ENABLE_PYDOCSTYLE := 0
TEST_PATHS := tests
TEST_PATHS_UNIT := tests/unit
TEST_PATHS_E2E := tests/e2e
TEST_PATHS_REGRESSION := tests/regression
TEST_CI_TARGETS := test-unit test-regression test-e2e
TEST_SOURCE_PATHS := src
INTERROGATE_PATHS := src
QUALITY_PATHS := src tests $(MONOREPO_ROOT)/docs/hooks
SKIP_DEPTRY := 1
SKIP_INTERROGATE := 1
SKIP_MYPY := 1
QUALITY_POST_TARGETS := quality-compileall
SECURITY_PATHS := src
BUILD_DIR := $(MONOREPO_ROOT)/artifacts/build
BUILD_PACKAGE_NAME := bijux-pollenomics
BUILD_CHECK_DISTS := 0
BUILD_TEMP_CLEAN_PATHS := build dist *.egg-info
PACKAGE_NAME := bijux-pollenomics
SBOM_DIR := $(MONOREPO_ROOT)/artifacts/sbom
API_MODE := freeze
API_FREEZE_COMMAND := $(VENV_PYTHON) -m bijux_pollenomics_dev.api.freeze_contracts
API_OPENAPI_DRIFT_COMMAND := $(VENV_PYTHON) -m bijux_pollenomics_dev.api.openapi_drift

quality-compileall:
	@"$(VENV_PYTHON)" -m compileall src | tee "$(PROJECT_ARTIFACTS_DIR)/quality/compileall.log"
.PHONY: quality-compileall

include $(ROOT_MAKE_DIR)/package/gates.mk
