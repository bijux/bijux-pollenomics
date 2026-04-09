ROOT_PACKAGE_PROFILE_DIR ?= $(ROOT_MAKEFILE_DIR)/packages

PACKAGE_RECORDS := \
	bijux-pollenomics|primary,check,buildable,sbom,api|bijux-pollenomics.mk \
	bijux-pollenomics-dev|check|bijux-pollenomics-dev.mk

include $(ROOT_MAKEFILE_DIR)/bijux-py/package/catalog.mk
