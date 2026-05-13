PACKAGE_KIND := repository-python
PACKAGE_IMPORT_NAME := bijux_pollenomics
PACKAGE_INSTALL_SPEC := .[dev]
API_MODE := freeze
PACKAGE_INSTALL_PYTHON_PACKAGES = "$(MONOREPO_ROOT)/packages/bijux-pollenomics-dev[dev]"
LINT_DIRS = src tests
# Keep strict mypy on the package entry and control layers that currently
# carry stable type contracts. The broader data-heavy domain modules still
# use loose machine-readable payload dicts and are not yet package-wide
# strict-mypy clean.
MYPY_TARGETS = src/bijux_pollenomics/cli.py src/bijux_pollenomics/config.py src/bijux_pollenomics/command_line src/bijux_pollenomics/core
ENABLE_MYPY := 1
ENABLE_CODESPELL := 0
ENABLE_RADON := 0
ENABLE_PYDOCSTYLE := 0
TEST_PATHS_UNIT := tests/unit
TEST_PATHS_E2E := tests/e2e
TEST_PATHS_REGRESSION := tests/regression
TEST_GENERATED_ARTIFACTS_PATH := tests
TEST_MAIN_ARGS := -m "not generated_artifacts"
TEST_UNIT_DIR_ARGS := -m "not slow and not generated_artifacts" --maxfail=1 -q
TEST_UNIT_FALLBACK_ARGS := -k "not e2e and not integration and not functional" -m "not slow and not generated_artifacts" --maxfail=1 -q
TEST_E2E_ARGS := -m "not generated_artifacts" --maxfail=1 -q
# The regression lane is already path-scoped to tests/regression. Adding a
# regression marker filter silently deselects the whole suite because these
# tests are organized by directory rather than marker.
TEST_REGRESSION_ARGS := -m "not generated_artifacts" --maxfail=1 -q
TEST_GENERATED_ARTIFACTS_ARGS := -m "generated_artifacts" --maxfail=1 -q
# The checked-in regression suite is entirely governed generated-artifact work.
# Keep the fast CI lane on unit and e2e checks, and leave heavy artifact
# verification to test-generated-artifacts or test-all.
TEST_CI_TARGETS := test-unit test-e2e
QUALITY_PATHS = src tests
QUALITY_MYPY_CONFIG = $(MONOREPO_ROOT)/configs/mypy.ini
QUALITY_MYPY_TARGETS = $(MYPY_TARGETS)
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

test-generated-artifacts:
	@echo "→ Running generated-artifact tests only"
	$(call run_make_targets,$(TEST_PRE_TARGETS),$(TEST_SELF_MAKE))
	@$(PYTEST) $(PYTEST_INFO_FLAGS) --version
	@rm -rf "$(TMP_DIR_ABS)"
	@mkdir -p "$(TEST_ARTIFACTS_DIR)" "$(HYPOTHESIS_DB_DIR)" "$(BENCHMARK_DIR)" "$(TMP_DIR)" "$(COV_HTML_ABS)"
	$(call clean_paths,$(TEST_CLEAN_PATHS))
	@if [ -n "$(TEST_GENERATED_ARTIFACTS_PATH)" ] && [ -d "$(TEST_GENERATED_ARTIFACTS_PATH)" ] && find "$(TEST_GENERATED_ARTIFACTS_PATH)" -type f -name 'test_*.py' | grep -q .; then \
	  ( cd "$(PYTEST_ROOTDIR_ABS)" && \
	    PYTHONPATH="$(TEST_SOURCE_PATH_ABS)$${PYTHONPATH:+:$${PYTHONPATH}}" \
	    PYTHONDONTWRITEBYTECODE=1 \
	    COVERAGE_FILE="$(COV_DATA_ABS)" \
	    HYPOTHESIS_DATABASE_DIRECTORY="$(HYPOTHESIS_DB_ABS)" \
	    $(TEST_PYCACHE_ENV) \
	    sh -c '$(PYTEST) --rootdir "$(PYTEST_ROOTDIR_ABS)" -c "$(PYTEST_INI_ABS)" $(TEST_PATH_ARGS) $(TEST_GENERATED_ARTIFACTS_ARGS) $(PYTEST_FLAGS)' ); \
	else \
	  echo "   • no $(TEST_GENERATED_ARTIFACTS_PATH); skipping"; \
	fi
	$(call clean_paths,$(TEST_CLEAN_PATHS))
.PHONY: test-generated-artifacts

test-all:
	@$(SELF_MAKE) test
	@$(SELF_MAKE) test-generated-artifacts
	@echo "✔ Full test categories completed"
.PHONY: test-all

test-full: test-all
.PHONY: test-full

include $(abspath $(dir $(firstword $(MAKEFILE_LIST))))/../bijux-py/package.mk
