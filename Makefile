PYTHON ?= python3.11
UV ?= uv
ARTIFACTS_ROOT ?= artifacts
VENV ?= $(ARTIFACTS_ROOT)/.venv
BIN := $(VENV)/bin
VENV_PYTHON := $(BIN)/python
CLI := $(BIN)/bijux-pollenomics
RUFF := $(BIN)/ruff
VERSION ?= $(shell PYTHONPATH=src $(PYTHON) -c "from bijux_pollenomics.settings import DEFAULT_AADR_VERSION; print(DEFAULT_AADR_VERSION)")
DATA_ROOT ?= data
DIST_ROOT ?= $(ARTIFACTS_ROOT)/dist
DOCS_SITE_ROOT ?= $(ARTIFACTS_ROOT)/docs/site
MKDOCS_LOCAL_SITE_URL ?= http://127.0.0.1:8000/
MKDOCS_ENV := NO_MKDOCS_2_WARNING=true
UV_PROJECT_ENVIRONMENT := $(VENV)
UV_SYNC := UV_PROJECT_ENVIRONMENT=$(UV_PROJECT_ENVIRONMENT) $(UV) sync --frozen --python $(PYTHON)

.DEFAULT_GOAL := help

.PHONY: app-state build check clean data-prep docs docs-serve help install lint lock lock-check package-check package-smoke package-verify reports test test-all test-e2e test-regression test-unit

help:
	@printf "Available targets:\n"
	@printf "  install    Sync %s from pyproject.toml and uv.lock\n" "$(VENV)"
	@printf "  lock       Refresh uv.lock from pyproject.toml\n"
	@printf "  lock-check Verify uv.lock matches pyproject.toml\n"
	@printf "  package-verify Build distributions, validate metadata, and smoke-test installation\n"
	@printf "  package-check Build and validate source and wheel distributions\n"
	@printf "  package-smoke Install the built wheel into a temporary environment and run the CLI\n"
	@printf "  reports    Regenerate the checked-in report bundles under docs/report\n"
	@printf "  app-state  Rebuild data, reports, and docs for the current app scope\n"
	@printf "  check      Verify uv.lock, lint, tests, docs, and package installs\n"
	@printf "  lint       Run ruff on src/ and tests/\n"
	@printf "  test       Run unit, regression, and e2e test suites\n"
	@printf "  test-unit  Run the unit test suite\n"
	@printf "  test-regression Run the regression test suite\n"
	@printf "  test-e2e   Run the end-to-end test suite\n"
	@printf "  data-prep  Rebuild the tracked data tree under %s\n" "$(DATA_ROOT)"
	@printf "  build      Build source and wheel distributions into %s\n" "$(DIST_ROOT)"
	@printf "  docs       Build the MkDocs site into %s\n" "$(DOCS_SITE_ROOT)"
	@printf "  docs-serve Serve the MkDocs site locally on %s\n" "$(MKDOCS_LOCAL_SITE_URL)"
	@printf "  clean      Remove transient virtualenv and build/test caches\n"

install: pyproject.toml uv.lock
	mkdir -p $(ARTIFACTS_ROOT)
	$(UV_SYNC)

lock:
	$(UV) lock --python $(PYTHON)

lock-check:
	$(UV) lock --check --python $(PYTHON)

check: lock-check lint test docs package-verify

lint: install
	$(RUFF) check src tests

test: test-all

test-all: install
	PYTHONPATH=src $(VENV_PYTHON) -m unittest discover -s tests -v

test-unit: install
	PYTHONPATH=src $(VENV_PYTHON) -m unittest discover -s tests/unit -v

test-regression: install
	PYTHONPATH=src $(VENV_PYTHON) -m unittest discover -s tests/regression -v

test-e2e: install
	PYTHONPATH=src $(VENV_PYTHON) -m unittest discover -s tests/e2e -v

data-prep: install
	$(CLI) collect-data all --version $(VERSION) --output-root $(DATA_ROOT)

reports: install
	$(CLI) publish-reports --aadr-root $(DATA_ROOT)/aadr --version $(VERSION) --output-root docs/report --context-root $(DATA_ROOT)

app-state: data-prep reports docs

build: install
	rm -rf $(DIST_ROOT) build
	mkdir -p $(DIST_ROOT)
	$(VENV_PYTHON) -m build --outdir $(DIST_ROOT)
	rm -rf build

package-check: build
	$(VENV_PYTHON) -m twine check $(DIST_ROOT)/*

package-smoke: build
	rm -rf $(ARTIFACTS_ROOT)/tmp/package-smoke
	$(UV) venv --python $(PYTHON) $(ARTIFACTS_ROOT)/tmp/package-smoke
	$(UV) pip install --python $(ARTIFACTS_ROOT)/tmp/package-smoke/bin/python --no-deps $(DIST_ROOT)/*.whl
	$(ARTIFACTS_ROOT)/tmp/package-smoke/bin/bijux-pollenomics --version
	$(ARTIFACTS_ROOT)/tmp/package-smoke/bin/bijux-pollenomics --help > /dev/null
	rm -rf $(ARTIFACTS_ROOT)/tmp/package-smoke

package-verify: build
	$(VENV_PYTHON) -m twine check $(DIST_ROOT)/*
	rm -rf $(ARTIFACTS_ROOT)/tmp/package-smoke
	$(UV) venv --python $(PYTHON) $(ARTIFACTS_ROOT)/tmp/package-smoke
	$(UV) pip install --python $(ARTIFACTS_ROOT)/tmp/package-smoke/bin/python --no-deps $(DIST_ROOT)/*.whl
	$(ARTIFACTS_ROOT)/tmp/package-smoke/bin/bijux-pollenomics --version
	$(ARTIFACTS_ROOT)/tmp/package-smoke/bin/bijux-pollenomics --help > /dev/null
	rm -rf $(ARTIFACTS_ROOT)/tmp/package-smoke

docs: install
	$(MKDOCS_ENV) $(BIN)/mkdocs build --strict

docs-serve: install
	SITE_URL=$(MKDOCS_LOCAL_SITE_URL) $(MKDOCS_ENV) $(BIN)/mkdocs serve --dev-addr 127.0.0.1:8000

clean:
	rm -rf $(VENV) .venv build dist $(DIST_ROOT) $(ARTIFACTS_ROOT)/build $(ARTIFACTS_ROOT)/docs $(ARTIFACTS_ROOT)/htmlcov .pytest_cache .ruff_cache .mypy_cache htmlcov
	find . -name ".DS_Store" -delete
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete
	find . -type d -name "*.egg-info" -prune -exec rm -rf {} +
