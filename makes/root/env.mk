include $(ROOT_MAKEFILE_DIR)/bijux-py/root-env.mk

.DEFAULT_GOAL := help
ARTIFACTS_ROOT ?= artifacts
VENV ?= $(ARTIFACTS_ROOT)/.venv
BIN := $(VENV)/bin
VENV_PYTHON := $(BIN)/python
ACT := $(BIN)
CLI := $(BIN)/bijux-pollenomics
ROOT_PACKAGE_DIR := packages/bijux-pollenomics
ROOT_PACKAGE_SRC_DIR := $(ROOT_PACKAGE_DIR)/src
ROOT_PACKAGE_TEST_DIR := $(ROOT_PACKAGE_DIR)/tests
ROOT_DEV_PACKAGE_DIR := packages/bijux-pollenomics-dev
ROOT_DEV_SRC_DIR := $(ROOT_DEV_PACKAGE_DIR)/src
ROOT_ARTIFACTS_DIR := $(ARTIFACTS_ROOT)/root
PROJECT_DIR ?= $(CURDIR)
PROJECT_SLUG ?= bijux-pollenomics
PROJECT_ARTIFACTS_DIR ?= $(ARTIFACTS_ROOT)
CONFIG_DIR ?= configs
MKDOCS_CFG ?= $(PROJECT_DIR)/mkdocs.yml
ROOT_PYTHONPATH := $(abspath $(ROOT_PACKAGE_DIR)):$(abspath $(ROOT_PACKAGE_SRC_DIR)):$(abspath $(ROOT_DEV_SRC_DIR))
UV_SYNC := UV_PROJECT_ENVIRONMENT=$(VENV) $(UV) sync --frozen --group dev --python $(PYTHON)

export PYTHONDONTWRITEBYTECODE := 1
export PYTHONPYCACHEPREFIX := $(ROOT_ARTIFACTS_DIR)/pycache
