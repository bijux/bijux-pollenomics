PYTHON ?= python3.11
ARTIFACTS_ROOT ?= artifacts
VENV ?= $(ARTIFACTS_ROOT)/.venv
BIN := $(VENV)/bin
VENV_PYTHON := $(BIN)/python
PIP := $(BIN)/pip
RUFF := $(BIN)/ruff
VERSION ?= v62.0
DATA_ROOT ?= data
DIST_ROOT ?= $(ARTIFACTS_ROOT)/dist
DOCS_SITE_ROOT ?= $(ARTIFACTS_ROOT)/docs/site
MKDOCS_LOCAL_SITE_URL ?= http://127.0.0.1:8000/
MKDOCS_ENV := NO_MKDOCS_2_WARNING=true

.PHONY: app-state check clean install lint reports test data-prep build docs docs-serve help

help:
	@printf "Available targets:\n"
	@printf "  install    Create %s and install the project with dev tools\n" "$(VENV)"
	@printf "  reports    Regenerate the checked-in report bundles under docs/report\n"
	@printf "  app-state  Rebuild data, reports, and docs for the current app scope\n"
	@printf "  check      Run lint, tests, and docs build\n"
	@printf "  lint       Run ruff on src/ and tests/\n"
	@printf "  test       Run the unittest suite\n"
	@printf "  data-prep  Rebuild the tracked data tree under %s\n" "$(DATA_ROOT)"
	@printf "  build      Build source and wheel distributions into %s\n" "$(DIST_ROOT)"
	@printf "  docs       Build the MkDocs site into %s\n" "$(DOCS_SITE_ROOT)"
	@printf "  docs-serve Serve the MkDocs site locally on %s\n" "$(MKDOCS_LOCAL_SITE_URL)"
	@printf "  clean      Remove transient virtualenv and build/test caches\n"

$(VENV_PYTHON):
	rm -rf $(VENV)
	mkdir -p $(ARTIFACTS_ROOT)
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip

$(VENV)/.installed: pyproject.toml $(VENV_PYTHON)
	$(PIP) install -e ".[dev]"
	touch $@

install: $(VENV)/.installed

check: lint test docs

lint: install
	$(RUFF) check src tests

test: install
	PYTHONPATH=src $(VENV_PYTHON) -m unittest discover -s tests -v

data-prep: install
	PYTHONPATH=src $(VENV_PYTHON) -m bijux_pollen.cli collect-data all --version $(VERSION) --output-root $(DATA_ROOT)

reports: install
	PYTHONPATH=src $(VENV_PYTHON) -m bijux_pollen.cli publish-reports --aadr-root $(DATA_ROOT)/aadr --version $(VERSION) --output-root docs/report --context-root $(DATA_ROOT)

app-state: data-prep reports docs

build: install
	mkdir -p $(DIST_ROOT)
	$(VENV_PYTHON) -m build --outdir $(DIST_ROOT)
	rm -rf build

docs: install
	$(MKDOCS_ENV) $(BIN)/mkdocs build --strict

docs-serve: install
	SITE_URL=$(MKDOCS_LOCAL_SITE_URL) $(MKDOCS_ENV) $(BIN)/mkdocs serve --dev-addr 127.0.0.1:8000

clean:
	rm -rf $(VENV) .venv build dist $(DIST_ROOT) $(ARTIFACTS_ROOT)/build $(ARTIFACTS_ROOT)/htmlcov .pytest_cache .ruff_cache .mypy_cache htmlcov
	find . -name ".DS_Store" -delete
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete
	find . -type d -name "*.egg-info" -prune -exec rm -rf {} +
