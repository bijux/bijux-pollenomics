include $(abspath $(dir $(lastword $(MAKEFILE_LIST))))/../bijux-py/package/bootstrap.mk
include $(ROOT_MAKE_DIR)/bijux-py/package/python.mk

PACKAGE_IMPORT_NAME := bijux_pollenomics_dev
PACKAGE_INSTALL_SPEC := .
RUFF_CONFIG := $(MONOREPO_ROOT)/configs/ruff.toml
ENABLE_MYPY := 0
ENABLE_CODESPELL := 0
ENABLE_RADON := 0
ENABLE_PYDOCSTYLE := 0
TEST_PATHS := tests
TEST_PATHS_UNIT := tests
TEST_SOURCE_PATHS := src
INTERROGATE_PATHS := src
QUALITY_PATHS := src tests
SKIP_DEPTRY := 1
SKIP_INTERROGATE := 1
SKIP_MYPY := 1
PACKAGE_ALL_TARGETS := clean install test lint quality security build sbom

include $(ROOT_MAKE_DIR)/bijux-py/package/gates.mk
