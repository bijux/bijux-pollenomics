PROJECT_ARTIFACTS_DIR ?= $(ARTIFACTS_ROOT)
PACKAGE_NAME ?= bijux-pollenomics
SBOM_DIR ?= $(ARTIFACTS_ROOT)/sbom
PIP_AUDIT ?= $(ACT)/pip-audit

include $(abspath $(dir $(lastword $(MAKEFILE_LIST))))/bijux-py/sbom.mk
