.DELETE_ON_ERROR:
.DEFAULT_GOAL := help
.SHELLFLAGS := -eu -o pipefail -c
SHELL := bash

PYTHON ?= python3.11
UV ?= uv
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
ROOT_PYTHONPATH := $(abspath $(ROOT_PACKAGE_SRC_DIR)):$(abspath $(ROOT_DEV_SRC_DIR))
UV_SYNC := UV_PROJECT_ENVIRONMENT=$(VENV) $(UV) sync --frozen --group dev --python $(PYTHON)

export PYTHONDONTWRITEBYTECODE := 1
export PYTHONPYCACHEPREFIX := $(ROOT_ARTIFACTS_DIR)/pycache
