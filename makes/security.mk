PROJECT_ARTIFACTS_DIR ?= $(ARTIFACTS_ROOT)
SECURITY_PATHS ?= $(ROOT_PACKAGE_SRC_DIR) $(ROOT_DEV_SRC_DIR)
PIP_AUDIT ?= $(ACT)/pip-audit

include $(abspath $(dir $(lastword $(MAKEFILE_LIST))))/bijux-py/security.mk
