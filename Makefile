PYTHON ?= python3.11
VENV ?= .venv
BIN := $(VENV)/bin
VENV_PYTHON := $(BIN)/python
PIP := $(BIN)/pip
RUFF := $(BIN)/ruff
VERSION ?= v62.0
DATA_ROOT ?= data

.PHONY: clean install lint test data-prep build docs docs-serve help

help:
	@printf "Available targets:\n"
	@printf "  install    Create %s and install the project with dev tools\n" "$(VENV)"
	@printf "  lint       Run ruff on src/ and tests/\n"
	@printf "  test       Run the unittest suite\n"
	@printf "  data-prep  Rebuild the tracked data tree under %s\n" "$(DATA_ROOT)"
	@printf "  build      Build source and wheel distributions\n"
	@printf "  docs       Build the MkDocs site into artifacts/docs/site\n"
	@printf "  docs-serve Serve the MkDocs site locally on 127.0.0.1:8000\n"
	@printf "  clean      Remove local virtualenv and build/test caches\n"

$(VENV_PYTHON):
	rm -rf $(VENV)
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip

$(VENV)/.installed: pyproject.toml $(VENV_PYTHON)
	$(PIP) install -e ".[dev]"
	touch $@

install: $(VENV)/.installed

lint: install
	$(RUFF) check src tests

test: install
	PYTHONPATH=src $(VENV_PYTHON) -m unittest discover -s tests -v

data-prep: install
	PYTHONPATH=src $(VENV_PYTHON) -m bijux_pollen.cli collect-data all --version $(VERSION) --output-root $(DATA_ROOT)

build: install
	$(VENV_PYTHON) -m build

docs: install
	$(BIN)/mkdocs build --strict

docs-serve: install
	$(BIN)/mkdocs serve --dev-addr 127.0.0.1:8000

clean:
	rm -rf $(VENV) build dist .pytest_cache .ruff_cache .mypy_cache htmlcov
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete
	find . -type d -name "*.egg-info" -prune -exec rm -rf {} +
