PACKAGE_KIND := repository-python
PACKAGE_IMPORT_NAME := bijux_pollenomics
API_MODE := freeze
PACKAGE_INSTALL_PYTHON_PACKAGES = "$(MONOREPO_ROOT)/packages/bijux-pollenomics-dev[dev]"
LINT_DIRS = src tests
MYPY_TARGETS = src tests
ENABLE_MYPY := 1
ENABLE_CODESPELL := 0
ENABLE_RADON := 0
ENABLE_PYDOCSTYLE := 0
TEST_PATHS_UNIT := tests/unit
TEST_PATHS_E2E := tests/e2e
TEST_PATHS_REGRESSION := tests/regression
TEST_CI_TARGETS := test-unit test-regression test-e2e
QUALITY_PATHS = src tests
QUALITY_MYPY_CONFIG = $(MONOREPO_ROOT)/configs/mypy.ini
QUALITY_MYPY_TARGETS = src tests
QUALITY_POST_TARGETS := quality-compileall
BUILD_PACKAGE_NAME := bijux-pollenomics
BUILD_PRE_TARGETS := sync-license-assets-package
BUILD_TEMP_CLEAN_PATHS := build dist *.egg-info
BUILD_POST_TARGETS := build-install-smoke
PACKAGE_NAME := bijux-pollenomics
API_FREEZE_COMMAND = $(VENV_PYTHON) -m bijux_pollenomics_dev.api.freeze_contracts
API_OPENAPI_DRIFT_COMMAND = $(VENV_PYTHON) -m bijux_pollenomics_dev.api.openapi_drift

quality-compileall:
	@"$(VENV_PYTHON)" -m compileall src | tee "$(PROJECT_ARTIFACTS_DIR)/quality/compileall.log"
.PHONY: quality-compileall

sync-license-assets-package:
	@for file_name in LICENSE NOTICE; do \
	  source_path="$(MONOREPO_ROOT)/$$file_name"; \
	  target_path="$(PROJECT_DIR)/$$file_name"; \
	  if [ ! -f "$$target_path" ] || ! cmp -s "$$source_path" "$$target_path"; then \
	    cp "$$source_path" "$$target_path"; \
	  fi; \
	done
.PHONY: sync-license-assets-package

build-install-smoke:
	@tmp_root="$(PROJECT_ARTIFACTS_DIR)/tmp/build-install-smoke"; \
	dist_name="$$(printf '%s' "$(BUILD_PACKAGE_NAME)" | tr '-' '_')"; \
	wheel_path="$$(ls -1t "$(BUILD_DIR_ABS)/$${dist_name}"-*.whl | head -n 1)"; \
	sdist_path="$$(ls -1t "$(BUILD_DIR_ABS)/$${dist_name}"-*.tar.gz | head -n 1)"; \
	if [ -z "$$wheel_path" ] || [ -z "$$sdist_path" ]; then \
	  echo "✘ Missing build artifacts for $(BUILD_PACKAGE_NAME) in $(BUILD_DIR_ABS)"; \
	  exit 1; \
	fi; \
	rm -rf "$$tmp_root"; \
	"$(BUILD_PYTHON)" -m venv "$$tmp_root/wheel"; \
	"$$tmp_root/wheel/bin/python" -m pip install "$$wheel_path"; \
	"$$tmp_root/wheel/bin/bijux-pollenomics" --version; \
	"$$tmp_root/wheel/bin/bijux-pollenomics" --help >/dev/null; \
	"$(BUILD_PYTHON)" -m venv "$$tmp_root/sdist"; \
	"$$tmp_root/sdist/bin/python" -m pip install "$$sdist_path"; \
	"$$tmp_root/sdist/bin/bijux-pollenomics" --version; \
	"$$tmp_root/sdist/bin/bijux-pollenomics" --help >/dev/null
.PHONY: build-install-smoke

include $(abspath $(dir $(firstword $(MAKEFILE_LIST))))/../bijux-py/package.mk
