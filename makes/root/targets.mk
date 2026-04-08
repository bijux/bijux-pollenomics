.PHONY: all app-state check clean help install lock lock-check

install: pyproject.toml uv.lock
	@mkdir -p "$(ARTIFACTS_ROOT)" "$(ROOT_ARTIFACTS_DIR)"
	@$(UV_SYNC)

lock:
	@$(UV) lock --python $(PYTHON)

lock-check:
	@$(UV) lock --check --python $(PYTHON)

check: lock-check lint test quality security docs build sbom api

all: install lint test quality security docs build sbom api
	@echo "✔ Repository targets completed"

app-state: install
	@$(MAKE) data-prep
	@$(MAKE) reports
	@$(MAKE) docs

help:
	@printf "Available targets:\n"
	@printf "  install       Sync %s from pyproject.toml and uv.lock\n" "$(VENV)"
	@printf "  lock          Refresh uv.lock from pyproject.toml\n"
	@printf "  lock-check    Verify uv.lock matches pyproject.toml\n"
	@printf "  lint          Run Ruff checks\n"
	@printf "  test          Run unit, regression, and e2e suites\n"
	@printf "  quality       Run repository quality checks\n"
	@printf "  security      Run Bandit and pip-audit\n"
	@printf "  docs          Build the MkDocs site\n"
	@printf "  build         Build runtime package distributions\n"
	@printf "  sbom          Write CycloneDX-style audit artifacts\n"
	@printf "  api           Verify API contract state\n"
	@printf "  check         Run the full repository verification flow\n"
	@printf "  app-state     Rebuild tracked data, reports, and docs\n"
	@printf "  clean         Remove local virtualenvs and generated artifacts\n"

clean:
	@rm -rf "$(VENV)" .venv build dist "$(ARTIFACTS_ROOT)/build" "$(ARTIFACTS_ROOT)/docs" "$(ARTIFACTS_ROOT)/security" "$(ARTIFACTS_ROOT)/sbom" "$(ROOT_ARTIFACTS_DIR)" .pytest_cache .ruff_cache .mypy_cache htmlcov
	@find . -name ".DS_Store" -delete
	@find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	@find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete
	@find . -type d -name "*.egg-info" -prune -exec rm -rf {} +
