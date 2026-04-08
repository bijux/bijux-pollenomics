PROJECT_ARTIFACTS_DIR ?= $(ARTIFACTS_ROOT)
INTERROGATE_PATHS ?= $(ROOT_PACKAGE_SRC_DIR)
QUALITY_PATHS ?= $(ROOT_PACKAGE_SRC_DIR) $(ROOT_PACKAGE_TEST_DIR) $(ROOT_DEV_SRC_DIR) docs/hooks
SKIP_DEPTRY ?= 1
SKIP_INTERROGATE ?= 1
SKIP_MYPY ?= 1
QUALITY_POST_TARGETS ?= quality-compileall

include $(abspath $(dir $(lastword $(MAKEFILE_LIST))))/bijux-py/quality.mk

quality-compileall:
	@PYTHONPATH="$(ROOT_PYTHONPATH)" "$(VENV_PYTHON)" -m compileall "$(ROOT_PACKAGE_SRC_DIR)" "$(ROOT_DEV_SRC_DIR)" | tee "$(PROJECT_ARTIFACTS_DIR)/quality/compileall.log"
.PHONY: quality-compileall
