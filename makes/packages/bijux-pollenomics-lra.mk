PACKAGE_KIND := repository-python
PACKAGE_NAME := bijux-pollenomics-lra
PACKAGE_IMPORT_NAME := bijux_pollenomics_lra
PACKAGE_INSTALL_SPEC := .[dev]
PACKAGE_INSTALL_PYTHON_PACKAGES = "$(MONOREPO_ROOT)/packages/bijux-pollenomics-dev[dev]"
LINT_DIRS = src tests
QUALITY_PATHS = src tests
MYPY_TARGETS = src/bijux_pollenomics_lra/api.py
QUALITY_MYPY_TARGETS = $(MYPY_TARGETS)
QUALITY_MYPY_CONFIG = $(MONOREPO_ROOT)/configs/mypy.ini
ENABLE_MYPY := 1
ENABLE_CODESPELL := 0
ENABLE_RADON := 0
ENABLE_PYDOCSTYLE := 0
TEST_PATHS_UNIT := tests
TEST_MAIN_ARGS := -m "not live_r"
TEST_UNIT_DIR_ARGS := -m "not live_r" --maxfail=1 -q
TEST_CI_TARGETS := test-unit
BUILD_PACKAGE_NAME := bijux-pollenomics-lra
# This GPL-derived package retains its own LICENSE/NOTICE. The host's Apache
# license-copy build hook must never overwrite those source obligations.
BUILD_TEMP_CLEAN_PATHS := build dist *.egg-info
SECURITY_AUDIT_PREPARE_MODE = pyproject
PIP_AUDIT_INPUTS = -r "$(SECURITY_REQS)"

include $(abspath $(dir $(firstword $(MAKEFILE_LIST))))/../bijux-py/package.mk
