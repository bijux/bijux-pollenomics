include $(ROOT_MAKE_DIR)/bijux-py/package/python.mk

PYTHON ?= python3.11
ACT ?= $(if $(wildcard $(VENV)/bin/activate),$(VENV)/bin,$(ACT))
ENABLE_CODESPELL ?= 1
ENABLE_RADON ?= 1
ENABLE_PYDOCSTYLE ?= 1
ENABLE_PYTYPE ?= 0
LINT_PRE_TARGETS ?= ensure-venv
RUFF_CHECK_FIX ?= 0
MYPY_FLAGS ?= --strict --follow-imports silent
RADON_COMPLEXITY_MAX ?= 48
PYDOCSTYLE_ARGS ?= --convention=google --add-ignore=D100,D101,D102,D103,D104,D105,D106,D107
QUALITY_MYPY_CONFIG ?= $(MONOREPO_ROOT)/configs/mypy.ini
QUALITY_MYPY_FLAGS ?= --strict --follow-imports silent
QUALITY_PRE_TARGETS ?= ensure-venv
SKIP_MYPY ?= 0
QUALITY_VULTURE_MIN_CONFIDENCE ?= 90
SECURITY_IGNORE_IDS ?= PYSEC-2022-42969 CVE-2025-68463
SECURITY_BANDIT_SKIP_IDS ?= B311
API_MODE ?= contract
API_BASE_PATH ?=
API_DYNAMIC_PORT ?= 1
OPENAPI_GENERATOR_NPM_PACKAGE ?= @openapitools/openapi-generator-cli@7.14.0
BUILD_CHECK_DISTS ?= 0
BUILD_TEMP_CLEAN_PATHS ?= $(COMMON_BUILD_CLEAN_PATHS) src/*.egg-info
BUILD_TEMP_CLEAN_PYCACHE ?= 1
PUBLISH_UPLOAD_ENABLED ?= 0
TEST_PRE_TARGETS ?= ensure-venv
TEST_PATHS_E2E ?= tests/e2e
TEST_PATHS_REGRESSION ?= tests/regression
TEST_PATHS_EVALUATION ?= tests/regression
TEST_MAIN_ARGS ?= -m "not real_local and not api"
TEST_CI_TARGETS ?= test-unit test-e2e test-regression test-evaluation
TEST_REAL_LOCAL_PATH ?= tests/real_local
PACKAGE_DEFINE_INSTALL ?= 0
PACKAGE_DEFINE_CLEAN ?= 0
PACKAGE_ALL_TARGETS ?= clean install test lint quality security sbom build api
PACKAGE_HELP_WIDTH ?= 22
PACKAGE_VENV_CREATE_MESSAGE ?= → Creating virtualenv at '$(VENV)' with '$$(which $(PYTHON))' ...
WORKSPACE_EDITABLE_EXTRAS ?= $${EXTRAS:-dev}
WORKSPACE_DEPENDENCY_PATHS ?= "$(VENV_PYTHON)" -c 'from packaging.requirements import Requirement; from pathlib import Path; import tomllib; root = Path("$(MONOREPO_ROOT)"); workspace = tomllib.loads((root / "pyproject.toml").read_text()); package = tomllib.loads(Path("pyproject.toml").read_text()); package_dirs = workspace.get("tool", {}).get("bijux_canon", {}).get("package_dirs", {}); dependencies = package.get("project", {}).get("dependencies", []); current_name = package.get("project", {}).get("name"); [print(root / package_dirs[name]) for dep in dependencies if (name := Requirement(dep).name) != current_name and name in package_dirs]'
WORKSPACE_SOFT_CLEAN_PATHS ?= $(COMMON_PYTHON_CLEAN_PATHS) demo .tmp_home $(COMMON_ARTIFACT_CLEAN_PATHS)

.PHONY: install ensure-venv nlenv \
	clean clean-soft clean-venv \
	all help

ensure-venv: $(VENV) ## Ensure venv exists and deps are installed
	@set -e; \
	echo "→ Ensuring dependencies in $(VENV) ..."; \
	$(UV) pip install --python "$(VENV_PYTHON)" --upgrade pip setuptools wheel; \
	echo "→ Installing workspace runtime dependencies"; \
	$(WORKSPACE_DEPENDENCY_PATHS) | while IFS= read -r package_dir; do \
	  [ -n "$$package_dir" ] || continue; \
	  $(UV) pip install --python "$(VENV_PYTHON)" --editable "$$package_dir"; \
	done; \
	EXTRAS="$(WORKSPACE_EDITABLE_EXTRAS)"; \
	if [ -n "$$EXTRAS" ]; then SPEC=".[$$EXTRAS]"; else SPEC="."; fi; \
	echo "→ Installing: $$SPEC"; \
	$(UV) pip install --python "$(VENV_PYTHON)" --editable "$$SPEC"

install: ensure-venv ## Install project into .venv (dev)
	@true

nlenv: ## Print activate command
	@echo "Run: source $(ACT)/activate"

clean-soft: ## Remove build artifacts but keep venv
	@echo "→ Cleaning (no .venv removal) ..."
	@$(RM) $(WORKSPACE_SOFT_CLEAN_PATHS) || true
	@if [ "$(OS)" != "Windows_NT" ]; then \
	  find . -type d -name '__pycache__' -exec $(RM) {} +; \
	fi

clean-venv: ## Remove the virtualenv only
	@echo "→ Cleaning ($(VENV)) ..."
	@$(RM) "$(VENV)"

clean: clean-soft clean-venv ## Remove venv + artifacts

all: ## Full pipeline
help: ## Show this help
