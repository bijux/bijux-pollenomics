ROOT_MAKEFILE_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))

include $(ROOT_MAKEFILE_DIR)/bijux-py/root/env.mk
include $(ROOT_MAKEFILE_DIR)/env.mk
include $(ROOT_MAKEFILE_DIR)/packages.mk

ROOT_DEV_PYTHONPATH := $(CURDIR)/packages/bijux-pollenomics-dev/src
ROOT_CHECK_VENV := $(CURDIR)/artifacts/.venv
ROOT_DOCS_DEV_ADDR ?= 127.0.0.1:8000
UV_SYNC := UV_PROJECT_ENVIRONMENT="$(ROOT_CHECK_VENV)" $(UV) sync --frozen --group dev --python "$(PYTHON)"
CLI := $(ROOT_CHECK_VENV)/bin/bijux-pollenomics
DEV_RUN := PYTHONPATH="$(CURDIR)/packages/bijux-pollenomics-dev/src$${PYTHONPATH:+:$$PYTHONPATH}" "$(ROOT_CHECK_PYTHON)"
DOCS_RENDER_SERVE_CONFIG := 0

include $(ROOT_MAKEFILE_DIR)/bijux-py/repository/root.mk

include $(ROOT_MAKEFILE_DIR)/bijux-py/root/package-dispatch.mk
include $(ROOT_MAKEFILE_DIR)/bijux-py/root/docs.mk
include $(ROOT_MAKEFILE_DIR)/bijux-py/repository/config-layout.mk
include $(ROOT_MAKEFILE_DIR)/bijux-py/repository/make-layout.mk
include $(ROOT_MAKEFILE_DIR)/bijux-py/bijux.mk

.PHONY: \
	help list list-all install lock lock-check lint quality security test docs docs-check docs-serve api build sbom clean all \
	check app-state data-prep reports package-check package-smoke package-source-smoke package-verify \
	clean-root-artifacts root-check-env check-shared-bijux-py

check: lock-check lint test quality security docs build sbom api ## Run the full repository verification flow

data-prep: root-check-env ## Refresh tracked source data under data/
	@BIJUX_POLLENOMICS_ALLOW_INSECURE_TLS=1 "$(CLI)" collect-data all --version "$$($(ROOT_CHECK_PYTHON) -c 'from bijux_pollenomics.config import DEFAULT_AADR_VERSION; print(DEFAULT_AADR_VERSION)')" --output-root "$(CURDIR)/data"

reports: root-check-env ## Refresh tracked report outputs under docs/report
	@"$(CLI)" publish-reports --aadr-root "$(CURDIR)/data/aadr" --version "$$($(ROOT_CHECK_PYTHON) -c 'from bijux_pollenomics.config import DEFAULT_AADR_VERSION; print(DEFAULT_AADR_VERSION)')" --output-root "$(CURDIR)/docs/report" --context-root "$(CURDIR)/data"

app-state: data-prep reports docs ## Rebuild tracked data, reports, and docs

package-check: build ## Validate built distributions with twine
	@"$(ROOT_CHECK_PYTHON)" -m twine check "$(CURDIR)/artifacts/build"/*
.PHONY: package-check

package-smoke: build ## Install the wheel into a temp venv and run the CLI
	@rm -rf "$(CURDIR)/artifacts/tmp/package-smoke"
	@"$(UV)" venv --python "$(PYTHON)" "$(CURDIR)/artifacts/tmp/package-smoke"
	@"$(UV)" pip install --python "$(CURDIR)/artifacts/tmp/package-smoke/bin/python" --no-deps "$(CURDIR)/artifacts/build"/*.whl
	@"$(CURDIR)/artifacts/tmp/package-smoke/bin/bijux-pollenomics" --version
	@"$(CURDIR)/artifacts/tmp/package-smoke/bin/bijux-pollenomics" --help >/dev/null
.PHONY: package-smoke

package-source-smoke: build ## Install the sdist into a temp venv and run the CLI
	@rm -rf "$(CURDIR)/artifacts/tmp/package-source-smoke"
	@"$(UV)" venv --python "$(PYTHON)" "$(CURDIR)/artifacts/tmp/package-source-smoke"
	@"$(UV)" pip install --python "$(CURDIR)/artifacts/tmp/package-source-smoke/bin/python" --no-deps "$(CURDIR)/artifacts/build"/*.tar.gz
	@"$(CURDIR)/artifacts/tmp/package-source-smoke/bin/bijux-pollenomics" --version
	@"$(CURDIR)/artifacts/tmp/package-source-smoke/bin/bijux-pollenomics" --help >/dev/null
.PHONY: package-source-smoke

package-verify: package-check package-smoke package-source-smoke ## Run the full packaging proof surface
.PHONY: package-verify

HELP_WIDTH := 22
include $(ROOT_MAKEFILE_DIR)/bijux-py/ci/help.mk

##@ Repository
help: ## Show generated repository commands from included make modules
check-shared-bijux-py: ## Verify shared bijux-py make modules match across sibling repositories
check-config-layout: ## Validate the repository config tree shape and required tool configs
check-make-layout: ## Validate the repository make tree shape and required entrypoints
