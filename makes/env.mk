MONOREPO_ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/..)
ROOT_MAKE_DIR := $(MONOREPO_ROOT)/makes
DEPTRY_SCAN_SCRIPT ?= PYTHONPATH="$(MONOREPO_ROOT)/packages/bijux-pollenomics-dev/src$${PYTHONPATH:+:$$PYTHONPATH}" "$(VENV_PYTHON)" -m bijux_pollenomics_dev.quality.deptry_scan
DEPTRY_CONFIG ?= $(MONOREPO_ROOT)/configs/deptry.toml
QUALITY_DEPTRY_COMMAND ?= $(DEPTRY_SCAN_SCRIPT) --config "$(DEPTRY_CONFIG)" --project-dir . $(QUALITY_PATHS)

include $(ROOT_MAKE_DIR)/bijux-py/repository/env.mk
