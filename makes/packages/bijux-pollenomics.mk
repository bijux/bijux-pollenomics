PACKAGE_KIND := repository-python
PACKAGE_IMPORT_NAME := bijux_pollenomics
API_MODE := freeze
PACKAGE_LINT_EXTRA_DIRS = $(MONOREPO_ROOT)/docs/hooks
PACKAGE_INSTALL_PYTHON_PACKAGES = "$(MONOREPO_ROOT)/packages/bijux-pollenomics-dev[dev]"
LINT_DIRS = src tests $(PACKAGE_LINT_EXTRA_DIRS)
MYPY_TARGETS = src tests $(MONOREPO_ROOT)/docs/hooks/publish_site_assets.py
ENABLE_MYPY := 1
ENABLE_CODESPELL := 0
ENABLE_RADON := 0
ENABLE_PYDOCSTYLE := 0
TEST_PATHS_UNIT := tests/unit
TEST_PATHS_E2E := tests/e2e
TEST_PATHS_REGRESSION := tests/regression
TEST_CI_TARGETS := test-unit test-regression test-e2e
QUALITY_PATHS = src tests $(MONOREPO_ROOT)/docs/hooks
QUALITY_MYPY_CONFIG = $(MONOREPO_ROOT)/configs/mypy.ini
QUALITY_MYPY_TARGETS = src tests $(MONOREPO_ROOT)/docs/hooks/publish_site_assets.py
QUALITY_POST_TARGETS := quality-compileall
BUILD_PACKAGE_NAME := bijux-pollenomics
BUILD_TEMP_CLEAN_PATHS := build dist *.egg-info
BUILD_POST_TARGETS := build-install-smoke
PACKAGE_NAME := bijux-pollenomics
API_FREEZE_COMMAND = $(VENV_PYTHON) -m bijux_pollenomics_dev.api.freeze_contracts
API_OPENAPI_DRIFT_COMMAND = $(VENV_PYTHON) -m bijux_pollenomics_dev.api.openapi_drift

quality-compileall:
	@"$(VENV_PYTHON)" -m compileall src | tee "$(PROJECT_ARTIFACTS_DIR)/quality/compileall.log"
.PHONY: quality-compileall

build-install-smoke:
	@tmp_root="$(PROJECT_ARTIFACTS_DIR)/tmp/build-install-smoke"; \
	rm -rf "$$tmp_root"; \
	"$(BUILD_PYTHON)" -m venv "$$tmp_root/wheel"; \
	"$$tmp_root/wheel/bin/python" -m pip install "$(BUILD_DIR_ABS)"/*.whl; \
	"$$tmp_root/wheel/bin/bijux-pollenomics" --version; \
	"$$tmp_root/wheel/bin/bijux-pollenomics" --help >/dev/null; \
	"$(BUILD_PYTHON)" -m venv "$$tmp_root/sdist"; \
	"$$tmp_root/sdist/bin/python" -m pip install "$(BUILD_DIR_ABS)"/*.tar.gz; \
	"$$tmp_root/sdist/bin/bijux-pollenomics" --version; \
	"$$tmp_root/sdist/bin/bijux-pollenomics" --help >/dev/null
.PHONY: build-install-smoke

include $(abspath $(dir $(firstword $(MAKEFILE_LIST))))/../bijux-py/package.mk
