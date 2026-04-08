ROOT_MAKEFILE_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))

include $(ROOT_MAKEFILE_DIR)/bijux-py/root-env.mk

.DEFAULT_GOAL := help
ARTIFACTS_ROOT ?= artifacts
PROJECT_DIR ?= $(CURDIR)
PROJECT_SLUG ?= bijux-pollenomics
PROJECT_ARTIFACTS_DIR ?= $(ARTIFACTS_ROOT)
CONFIG_DIR ?= configs
VENV ?= $(ROOT_VENV)
BIN := $(VENV)/bin
VENV_PYTHON := $(BIN)/python
ACT := $(BIN)
CLI := $(BIN)/bijux-pollenomics
ROOT_PACKAGE_DIR := packages/bijux-pollenomics
ROOT_PACKAGE_SRC_DIR := $(ROOT_PACKAGE_DIR)/src
ROOT_PACKAGE_TEST_DIR := $(ROOT_PACKAGE_DIR)/tests
ROOT_DEV_PACKAGE_DIR := packages/bijux-pollenomics-dev
ROOT_DEV_SRC_DIR := $(ROOT_DEV_PACKAGE_DIR)/src
ROOT_DEV_TEST_DIR := $(ROOT_DEV_PACKAGE_DIR)/tests
MKDOCS_CFG ?= $(PROJECT_DIR)/mkdocs.yml
ROOT_PYTHONPATH := $(abspath $(ROOT_PACKAGE_DIR)):$(abspath $(ROOT_PACKAGE_SRC_DIR)):$(abspath $(ROOT_DEV_SRC_DIR))
UV_SYNC := UV_PROJECT_ENVIRONMENT=$(VENV) $(UV) sync --frozen --group dev --python $(PYTHON)

include $(ROOT_MAKEFILE_DIR)/gates.mk
include $(ROOT_MAKEFILE_DIR)/bijux-py/standard.mk

.PHONY: all app-state check clean help install lock lock-check

ROOT_INSTALL_PREREQS := $(VENV) pyproject.toml uv.lock
ROOT_INSTALL_COMMAND := @mkdir -p "$(ARTIFACTS_ROOT)" "$(ROOT_ARTIFACTS_DIR)" && $(UV_SYNC)
ROOT_ALL_TARGETS := install lint test quality security docs build sbom api
ROOT_CLEAN_COMMAND := @rm -rf "$(PROJECT_ARTIFACTS_DIR)" && \
	find . -name ".DS_Store" -delete && \
	find . -type d -name "__pycache__" -prune -exec rm -rf {} + && \
	find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete && \
	find . -type d -name "*.egg-info" -prune -exec rm -rf {} +

include $(ROOT_MAKEFILE_DIR)/bijux-py/root-lifecycle.mk

$(VENV):
	@mkdir -p "$(ROOT_ARTIFACTS_DIR)"
	@$(UV) venv --python "$(PYTHON)" "$(VENV)"

##@ Repository
check: lock-check lint test quality security docs build sbom api ## Run the full repository verification flow

app-state: install ## Rebuild tracked data, reports, and docs
	@$(MAKE) data-prep
	@$(MAKE) reports
	@$(MAKE) docs

HELP_WIDTH := 22
include $(ROOT_MAKEFILE_DIR)/bijux-py/help.mk

help: ## Show generated repository commands from included make modules
