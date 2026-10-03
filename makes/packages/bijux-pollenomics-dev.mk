PACKAGE_KIND := python
PACKAGE_IMPORT_NAME := bijux_pollenomics_dev
PACKAGE_INSTALL_SPEC := .[dev,reports]
RUFF_CONFIG = $(MONOREPO_ROOT)/configs/ruff.toml
BUILD_PRE_TARGETS := sync-license-assets-package
TEST_PATHS := tests
TEST_PATHS_UNIT := tests
TEST_SOURCE_PATHS := src
INTERROGATE_PATHS := src
QUALITY_INTERROGATE_FLAGS = --config "$(MONOREPO_ROOT)/pyproject.toml"
QUALITY_PATHS := src tests
SECURITY_AUDIT_PREPARE_MODE = none
PIP_AUDIT_INPUTS = --strict --no-deps --disable-pip -r "$(SECURITY_REQS)"
ENABLE_PYDOCSTYLE := 1
SKIP_MYPY := 0
PACKAGE_ALL_TARGETS := clean install test lint quality security build sbom

sync-license-assets-package:
	@for file_name in LICENSE NOTICE; do \
	  target_path="$(PROJECT_DIR)/$$file_name"; \
	  source_path="$(MONOREPO_ROOT)/$$file_name"; \
	  if [ -f "$$target_path" ] && [ ! -L "$$target_path" ] && cmp -s "$$source_path" "$$target_path"; then \
	    continue; \
	  fi; \
	  if [ -L "$$target_path" ] || [ -e "$$target_path" ]; then \
	    rm -f "$$target_path"; \
	  fi; \
	  cp "$$source_path" "$$target_path"; \
	done
.PHONY: sync-license-assets-package

test-all: TEST_MAIN_ARGS =
test-all: PYTEST_ADDOPTS_EXTRA = -o timeout=0
test-all: test
.PHONY: test-all

test-all-plus-run-time: TEST_MAIN_ARGS =
test-all-plus-run-time: PYTEST_ADDOPTS_EXTRA = -o timeout=0 --durations=0 --durations-min=0
test-all-plus-run-time: test
.PHONY: test-all-plus-run-time

include $(abspath $(dir $(firstword $(MAKEFILE_LIST))))/../bijux-py/package.mk

# Export the selected package closure from the authenticated workspace lock.
# Local distributions have a separate source custody account, not PyPI identity.
security-audit: security-locked-inputs
security-locked-inputs: install
	@"$(VENV_PYTHON)" -m bijux_pollenomics_dev.ci.dependency_audit --repository "$(MONOREPO_ROOT)" --distribution bijux-pollenomics-dev --extra dev --extra reports --output "$(SECURITY_REQS)" --account "$(SECURITY_REPORT_DIR)/workspace-account.json" --verify-installed
.PHONY: security-locked-inputs
