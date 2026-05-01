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
SECURITY_AUDIT_PREPARE_MODE = pyproject
PIP_AUDIT_INPUTS = -r "$(SECURITY_REQS)"
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
	  target_path="$(PROJECT_DIR)/$$file_name"; \
	  expected_target="../../$$file_name"; \
	  if [ -L "$$target_path" ] && [ "$$(readlink "$$target_path")" = "$$expected_target" ]; then \
	    continue; \
	  fi; \
	  if [ -L "$$target_path" ] || [ -e "$$target_path" ]; then \
	    rm -f "$$target_path"; \
	  fi; \
	  ln -s "$$expected_target" "$$target_path"; \
	done
.PHONY: sync-license-assets-package

build-install-smoke:
	@tmp_root="$(PROJECT_ARTIFACTS_DIR)/tmp/build-install-smoke"; \
	dist_name="$$(printf '%s' "$(BUILD_PACKAGE_NAME)" | tr '-' '_')"; \
	wheel_path="$$(ls -1t "$(BUILD_DIR_ABS)/$${dist_name}"-*.whl | head -n 1)"; \
	sdist_path="$$(ls -1t "$(BUILD_DIR_ABS)/$${dist_name}"-*.tar.gz | head -n 1)"; \
	export PIP_DISABLE_PIP_VERSION_CHECK=1; \
	if [ -z "$$wheel_path" ] || [ -z "$$sdist_path" ]; then \
	  echo "✘ Missing build artifacts for $(BUILD_PACKAGE_NAME) in $(BUILD_DIR_ABS)"; \
	  exit 1; \
	fi; \
	rm -rf "$$tmp_root"; \
	"$(BUILD_PYTHON)" -m venv "$$tmp_root/smoke"; \
	"$$tmp_root/smoke/bin/python" -m pip install "$$wheel_path"; \
	"$$tmp_root/smoke/bin/bijux-pollenomics" --version; \
	"$$tmp_root/smoke/bin/bijux-pollenomics" --help >/dev/null; \
	"$$tmp_root/smoke/bin/python" -m pip uninstall -y "$(BUILD_PACKAGE_NAME)" >/dev/null; \
	"$$tmp_root/smoke/bin/python" -m pip install "$$sdist_path"; \
	"$$tmp_root/smoke/bin/bijux-pollenomics" --version; \
	"$$tmp_root/smoke/bin/bijux-pollenomics" --help >/dev/null
.PHONY: build-install-smoke

include $(abspath $(dir $(firstword $(MAKEFILE_LIST))))/../bijux-py/package.mk
