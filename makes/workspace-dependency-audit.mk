# Repository-owned workspace identities remain separate from public CVE pins.
WORKSPACE_AUDIT_DISTRIBUTION ?= $(PROJECT_SLUG)
WORKSPACE_AUDIT_EXTRAS ?= dev
WORKSPACE_AUDIT_ADDITIONAL_DISTRIBUTIONS ?=
WORKSPACE_AUDIT_SOURCE := $(MONOREPO_ROOT)/packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/dependency_audit.py
WORKSPACE_AUDIT_SELECTION = --distribution "$(WORKSPACE_AUDIT_DISTRIBUTION)" $(foreach extra,$(WORKSPACE_AUDIT_EXTRAS),--extra "$(extra)") $(foreach package,$(WORKSPACE_AUDIT_ADDITIONAL_DISTRIBUTIONS),--additional-distribution "$(package)")

SECURITY_AUDIT_PREPARE_MODE = none
PIP_AUDIT_INPUTS = --strict --no-deps --disable-pip -r "$(SECURITY_REQS)"

security-audit: security-locked-inputs
security-locked-inputs: install
	@"$(VENV_PYTHON)" "$(WORKSPACE_AUDIT_SOURCE)" --repository "$(MONOREPO_ROOT)" $(WORKSPACE_AUDIT_SELECTION) --output "$(SECURITY_REQS)" --account "$(SECURITY_REPORT_DIR)/workspace-account.json" --verify-installed --uv "$(UV)"
.PHONY: security-locked-inputs
