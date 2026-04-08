PROJECT_ARTIFACTS_DIR ?= $(ARTIFACTS_ROOT)
BUILD_DIR ?= $(ARTIFACTS_ROOT)/build
BUILD_PACKAGE_DIR ?= $(ROOT_PACKAGE_DIR)
BUILD_PACKAGE_NAME ?= bijux-pollenomics
BUILD_CHECK_DISTS ?= 0
BUILD_TEMP_CLEAN_PATHS ?= build dist *.egg-info
BUILD_TOOLS_COMMAND ?= $(BUILD_PYTHON) -m build --version >/dev/null && $(BUILD_PYTHON) -m twine --version >/dev/null

include $(abspath $(dir $(lastword $(MAKEFILE_LIST))))/bijux-py/build.mk

package-check: build
	@"$(VENV_PYTHON)" -m twine check "$(BUILD_DIR)"/*
.PHONY: package-check

package-smoke: build
	@rm -rf "$(ARTIFACTS_ROOT)/tmp/package-smoke"
	@"$(UV)" venv --python "$(PYTHON)" "$(ARTIFACTS_ROOT)/tmp/package-smoke"
	@"$(UV)" pip install --python "$(ARTIFACTS_ROOT)/tmp/package-smoke/bin/python" --no-deps "$(BUILD_DIR)"/*.whl
	@"$(ARTIFACTS_ROOT)/tmp/package-smoke/bin/bijux-pollenomics" --version
	@"$(ARTIFACTS_ROOT)/tmp/package-smoke/bin/bijux-pollenomics" --help >/dev/null
.PHONY: package-smoke

package-source-smoke: build
	@rm -rf "$(ARTIFACTS_ROOT)/tmp/package-source-smoke"
	@"$(UV)" venv --python "$(PYTHON)" "$(ARTIFACTS_ROOT)/tmp/package-source-smoke"
	@"$(UV)" pip install --python "$(ARTIFACTS_ROOT)/tmp/package-source-smoke/bin/python" --no-deps "$(BUILD_DIR)"/*.tar.gz
	@"$(ARTIFACTS_ROOT)/tmp/package-source-smoke/bin/bijux-pollenomics" --version
	@"$(ARTIFACTS_ROOT)/tmp/package-source-smoke/bin/bijux-pollenomics" --help >/dev/null
.PHONY: package-source-smoke

package-verify: package-check package-smoke package-source-smoke
.PHONY: package-verify
