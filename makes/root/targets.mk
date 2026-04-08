.PHONY: all app-state check clean help install lock lock-check

ROOT_INSTALL_PREREQS := $(VENV) pyproject.toml uv.lock
ROOT_INSTALL_COMMAND := @mkdir -p "$(ARTIFACTS_ROOT)" "$(ROOT_ARTIFACTS_DIR)" && $(UV_SYNC)
ROOT_ALL_TARGETS := install lint test quality security docs build sbom api
ROOT_CLEAN_COMMAND := @rm -rf "$(PROJECT_ARTIFACTS_DIR)" && \
	find . -name ".DS_Store" -delete && \
	find . -type d -name "__pycache__" -prune -exec rm -rf {} + && \
	find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete && \
	find . -type d -name "*.egg-info" -prune -exec rm -rf {} +

include $(ROOT_MAKEFILE_DIR)/bijux-py/root-lifecycle.mk

$(VENV):
	@mkdir -p "$(ROOT_ARTIFACTS_DIR)"
	@$(UV) venv --python "$(PYTHON)" "$(VENV)"

check: lock-check lint test quality security docs build sbom api

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
