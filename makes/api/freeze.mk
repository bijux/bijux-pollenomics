PRANCE ?= $(if $(ACT),$(ACT)/prance,prance)
OPENAPI_SPEC_VALIDATOR ?= $(if $(ACT),$(ACT)/openapi-spec-validator,openapi-spec-validator)
ALL_API_SCHEMAS := $(shell if [ -d "$(API_DIR)" ]; then find "$(API_DIR)" -type f -path '*/v1/schema.yaml'; fi)
API_LINT_DIR_ABS := $(abspath $(API_LINT_DIR))
API_FREEZE_COMMAND ?= $(VENV_PYTHON) -m bijux_pollenomics_dev.api.freeze_contracts
API_OPENAPI_DRIFT_COMMAND ?= $(VENV_PYTHON) -m bijux_pollenomics_dev.api.openapi_drift
API_NO_SCHEMA_MESSAGE ?= ✘ No OpenAPI schemas found under $(API_DIR)/*/v1/schema.yaml

.PHONY: api api-install api-lint api-freeze openapi-drift api-clean api-test api-serve api-serve-bg api-stop

api: api-install api-lint api-freeze openapi-drift
	@echo "✔ API checks passed"

api-install:
	@echo "→ API tooling is managed by the package install target"
	@"$(VENV_PYTHON)" -m prance --version >/dev/null
	@"$(VENV_PYTHON)" -m openapi_spec_validator --help >/dev/null

api-lint:
	@if [ -z "$(ALL_API_SCHEMAS)" ]; then echo "$(API_NO_SCHEMA_MESSAGE)"; exit 1; fi
	@mkdir -p "$(API_LINT_DIR_ABS)"
	@set -e; \
	for schema in $(ALL_API_SCHEMAS); do \
	  name="$$(echo "$$schema" | tr '/' '_')"; \
	  echo "→ Validating $$schema"; \
	  { \
	    $(PRANCE) validate "$$schema"; \
	    $(OPENAPI_SPEC_VALIDATOR) "$$schema"; \
	  } 2>&1 | tee "$(API_LINT_DIR_ABS)/$$name.log"; \
	done
	@echo "✔ API lint complete"

api-freeze:
	@echo "→ Enforcing API schema freeze contracts"
	@$(API_FREEZE_COMMAND)
	@echo "✔ API freeze contracts validated"

openapi-drift:
	@if [ -z "$(strip $(API_OPENAPI_DRIFT_COMMAND))" ]; then \
	  echo "→ No live OpenAPI drift command configured; skipping"; \
	else \
	  echo "→ Checking OpenAPI drift"; \
	  $(API_OPENAPI_DRIFT_COMMAND); \
	  echo "✔ OpenAPI drift check complete"; \
	fi

api-clean:
	@rm -rf "$(API_ARTIFACTS_DIR)" || true

api-test:
	@echo "→ API_MODE=freeze does not run live HTTP tests"

api-serve:
	@echo "→ API_MODE=freeze does not provide api-serve"

api-serve-bg:
	@echo "→ API_MODE=freeze does not provide api-serve-bg"

api-stop:
	@echo "→ API_MODE=freeze does not provide api-stop"

##@ API
api:            ## Validate and enforce frozen API contracts for checked-in schemas
api-install:    ## Validate API lint tooling in the active environment
api-lint:       ## Validate OpenAPI schemas under apis/*/v1
api-freeze:     ## Ensure pinned_openapi.json and schema.hash match schema.yaml
openapi-drift:  ## Detect breaking schema changes without version bumps when configured
api-clean:      ## Remove API artifacts
