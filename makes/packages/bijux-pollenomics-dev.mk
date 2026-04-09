PACKAGE_KIND := python
PACKAGE_IMPORT_NAME := bijux_pollenomics_dev
PACKAGE_INSTALL_SPEC := .[dev]
RUFF_CONFIG := $(MONOREPO_ROOT)/configs/ruff.toml
TEST_PATHS := tests
TEST_PATHS_UNIT := tests
TEST_SOURCE_PATHS := src
INTERROGATE_PATHS := src
QUALITY_PATHS := src tests
ENABLE_PYDOCSTYLE := 1
SKIP_MYPY := 0
PACKAGE_ALL_TARGETS := clean install test lint quality security build sbom

include $(abspath $(dir $(firstword $(MAKEFILE_LIST))))/../bijux-py/package.mk
