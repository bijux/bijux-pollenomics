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

# Development certification only. Host and engine wheels do not depend on R.
LRA_REFERENCE_ROOT ?= $(MONOREPO_ROOT)/artifacts/bijux-pollenomics-lra/reference
LRA_REFERENCE_LOCK ?= $(MONOREPO_ROOT)/configs/ci/lra-r-source-lock.v1.json
LRA_REFERENCE_PYTHON ?= $(ACT)/python
LRA_REFERENCE_COMMAND = "$(LRA_REFERENCE_PYTHON)" -m bijux_pollenomics_dev.ci.lra_reference
LRA_REFERENCE_COMMON = --lock "$(LRA_REFERENCE_LOCK)" --repository "$(MONOREPO_ROOT)"

.PHONY: reference-fetch reference-build-r reference-provision test-live-r
reference-fetch: ## Fetch exact hash-pinned reference sources; no rolling CRAN resolution.
	@$(LRA_REFERENCE_COMMAND) fetch $(LRA_REFERENCE_COMMON) --source-cache "$(LRA_REFERENCE_ROOT)/sources" --output "$(LRA_REFERENCE_ROOT)/receipts/acquisition"

reference-build-r: ## Build the exact verified R source into an isolated prefix.
	@$(LRA_REFERENCE_COMMAND) build-r $(LRA_REFERENCE_COMMON) --source-cache "$(LRA_REFERENCE_ROOT)/sources" --prefix "$(LRA_REFERENCE_ROOT)/runtime" --output "$(LRA_REFERENCE_ROOT)/receipts/runtime"

reference-provision: ## Install verified local archives into a new private R library.
	@$(LRA_REFERENCE_COMMAND) provision $(LRA_REFERENCE_COMMON) --source-cache "$(LRA_REFERENCE_ROOT)/sources" --library "$(LRA_REFERENCE_ROOT)/library" --r "$(LRA_REFERENCE_ROOT)/runtime/bin/R" --rscript "$(LRA_REFERENCE_ROOT)/runtime/bin/Rscript" --runtime-receipt "$(LRA_REFERENCE_ROOT)/receipts/runtime/report.json" --output "$(LRA_REFERENCE_ROOT)/receipts/provision"

test-live-r: ## Require actual R execution and exact case/source/runtime receipt closure.
	@$(LRA_REFERENCE_COMMAND) certify $(LRA_REFERENCE_COMMON) --library "$(LRA_REFERENCE_ROOT)/library" --rscript "$(LRA_REFERENCE_ROOT)/runtime/bin/Rscript" --provision-receipt "$(LRA_REFERENCE_ROOT)/receipts/provision/report.json" --output "$(LRA_REFERENCE_ROOT)/receipts/certification"
