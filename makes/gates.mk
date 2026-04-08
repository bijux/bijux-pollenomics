PROJECT_ARTIFACTS_DIR ?= $(ARTIFACTS_ROOT)

LINT_DIRS ?= $(ROOT_PACKAGE_SRC_DIR) $(ROOT_PACKAGE_TEST_DIR) $(ROOT_DEV_SRC_DIR) docs/hooks
RUFF_CONFIG ?= configs/ruff.toml
ENABLE_MYPY ?= 0
ENABLE_CODESPELL ?= 0
ENABLE_RADON ?= 0
ENABLE_PYDOCSTYLE ?= 0

include $(ROOT_MAKEFILE_DIR)/bijux-py/lint.mk

VERSION ?= $(shell PYTHONPATH=$(ROOT_PACKAGE_SRC_DIR) $(PYTHON) -c "from bijux_pollenomics.config import DEFAULT_AADR_VERSION; print(DEFAULT_AADR_VERSION)")
VERSION_ARG = $(if $(strip $(VERSION)),--version $(VERSION),)
DATA_ROOT ?= data

.PHONY: data-prep reports test test-all test-dev test-e2e test-regression test-unit

test: test-all

test-all: test-unit test-regression test-e2e test-dev

test-unit: install
	@PYTHONPATH="$(ROOT_PYTHONPATH)" "$(VENV_PYTHON)" -m unittest discover -s "$(ROOT_PACKAGE_TEST_DIR)/unit" -v

test-regression: install
	@PYTHONPATH="$(ROOT_PYTHONPATH)" "$(VENV_PYTHON)" -m unittest discover -s "$(ROOT_PACKAGE_TEST_DIR)/regression" -v

test-e2e: install
	@PYTHONPATH="$(ROOT_PYTHONPATH)" "$(VENV_PYTHON)" -m unittest discover -s "$(ROOT_PACKAGE_TEST_DIR)/e2e" -v

test-dev: install
	@PYTHONPATH="$(ROOT_PYTHONPATH)" "$(VENV_PYTHON)" -m unittest discover -s "$(ROOT_DEV_TEST_DIR)" -v

data-prep: install
	@BIJUX_POLLENOMICS_ALLOW_INSECURE_TLS=1 PYTHONPATH="$(ROOT_PYTHONPATH)" "$(CLI)" collect-data all $(VERSION_ARG) --output-root "$(DATA_ROOT)"

reports: install
	@PYTHONPATH="$(ROOT_PYTHONPATH)" "$(CLI)" publish-reports --aadr-root "$(DATA_ROOT)/aadr" $(VERSION_ARG) --output-root docs/report --context-root "$(DATA_ROOT)"

INTERROGATE_PATHS ?= $(ROOT_PACKAGE_SRC_DIR)
QUALITY_PATHS ?= $(ROOT_PACKAGE_SRC_DIR) $(ROOT_PACKAGE_TEST_DIR) $(ROOT_DEV_SRC_DIR) docs/hooks
SKIP_DEPTRY ?= 1
SKIP_INTERROGATE ?= 1
SKIP_MYPY ?= 1
QUALITY_POST_TARGETS ?= quality-compileall

include $(ROOT_MAKEFILE_DIR)/bijux-py/quality.mk

quality-compileall:
	@PYTHONPATH="$(ROOT_PYTHONPATH)" "$(VENV_PYTHON)" -m compileall "$(ROOT_PACKAGE_SRC_DIR)" "$(ROOT_DEV_SRC_DIR)" | tee "$(PROJECT_ARTIFACTS_DIR)/quality/compileall.log"
.PHONY: quality-compileall

SECURITY_PATHS ?= $(ROOT_PACKAGE_SRC_DIR) $(ROOT_DEV_SRC_DIR)
PIP_AUDIT ?= $(ACT)/pip-audit

include $(ROOT_MAKEFILE_DIR)/bijux-py/security.mk

BUILD_DIR ?= $(ARTIFACTS_ROOT)/build
BUILD_PACKAGE_DIR ?= $(ROOT_PACKAGE_DIR)
BUILD_PACKAGE_NAME ?= bijux-pollenomics
BUILD_CHECK_DISTS ?= 0
BUILD_TEMP_CLEAN_PATHS ?= build dist *.egg-info
BUILD_TOOLS_COMMAND ?= $(BUILD_PYTHON) -m build --version >/dev/null && $(BUILD_PYTHON) -m twine --version >/dev/null

include $(ROOT_MAKEFILE_DIR)/bijux-py/build.mk

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

PACKAGE_NAME ?= bijux-pollenomics
SBOM_DIR ?= $(ARTIFACTS_ROOT)/sbom
PIP_AUDIT ?= $(ACT)/pip-audit

include $(ROOT_MAKEFILE_DIR)/bijux-py/sbom.mk

DOCS_SITE_DIR ?= $(ARTIFACTS_ROOT)/root/docs/site
DOCS_BUILD_SITE_DIR ?= $(DOCS_SITE_DIR)
DOCS_CHECK_SITE_DIR ?= $(DOCS_SITE_DIR)
DOCS_SERVE_SITE_DIR ?= $(DOCS_SITE_DIR)
DOCS_CACHE_DIR ?= $(ARTIFACTS_ROOT)/root/docs/.cache
DOCS_BUILD_CONFIG_FILE ?= $(MKDOCS_CFG)
DOCS_CHECK_CONFIG_FILE ?= $(MKDOCS_CFG)
DOCS_SERVE_CONFIG_FILE ?= $(MKDOCS_CFG)
DOCS_BUILD_PREPARE_TARGETS :=
DOCS_CHECK_PREPARE_TARGETS :=
DOCS_SERVE_PREPARE_TARGETS :=
DOCS_BUILD_PRE_CLEAN_PATHS ?= $(DOCS_BUILD_SITE_DIR) $(DOCS_CACHE_DIR)
DOCS_CHECK_PRE_CLEAN_PATHS ?= $(DOCS_CHECK_SITE_DIR) $(DOCS_CACHE_DIR)
DOCS_EXTRA_CLEAN_PATHS ?= $(DOCS_SITE_DIR) $(DOCS_CACHE_DIR)
MKDOCS_LOCAL_SITE_URL ?= http://127.0.0.1:8000/
DOCS_DEV_ADDR ?= 127.0.0.1:8000
DOCS_SERVE_SITE_URL ?= $(MKDOCS_LOCAL_SITE_URL)
DOCS_BUILD_ENV ?= NO_MKDOCS_2_WARNING=true
DOCS_CHECK_ENV ?= NO_MKDOCS_2_WARNING=true
DOCS_SERVE_ENV ?= NO_MKDOCS_2_WARNING=true

include $(ROOT_MAKEFILE_DIR)/bijux-py/docs.mk

API_MODE ?= freeze
API_REPO_DIR := $(ROOT_MAKEFILE_DIR)/api
include $(ROOT_MAKEFILE_DIR)/bijux-py/api.mk
