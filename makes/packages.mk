ROOT_PACKAGE_TARGETS ?= test test-generated-artifacts test-all lint quality security api build sbom clean
ROOT_TARGET_PACKAGES_test-generated-artifacts ?= bijux-pollenomics
ROOT_TARGET_SHARED_ENV_test-generated-artifacts ?= 1
ROOT_TARGET_GROUPS_test-all ?= check
ROOT_TARGET_SHARED_ENV_test-all ?= 1

ROOT_PACKAGE_PROFILE_DIR ?= $(ROOT_MAKEFILE_DIR)/packages

PACKAGE_RECORDS := \
	bijux-pollenomics|primary,check,buildable,sbom,api|bijux-pollenomics.mk \
	pollenomics|compat,check,buildable,sbom|pollenomics.mk \
	bijux-pollenomics-dev|check|bijux-pollenomics-dev.mk

include $(ROOT_MAKEFILE_DIR)/bijux-py/package-catalog.mk
