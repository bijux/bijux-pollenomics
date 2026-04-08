SECURITY_TARGETS ?= $(ROOT_PACKAGE_SRC_DIR) $(ROOT_DEV_SRC_DIR)

.PHONY: security

security: install
	@mkdir -p "$(ARTIFACTS_ROOT)/security"
	@PYTHONPATH="$(ROOT_PYTHONPATH)" "$(VENV_PYTHON)" -m bandit -r $(SECURITY_TARGETS) -f json -o "$(ARTIFACTS_ROOT)/security/bandit.json" || true
	@PYTHONPATH="$(ROOT_PYTHONPATH)" "$(VENV_PYTHON)" -m bandit -r $(SECURITY_TARGETS) | tee "$(ARTIFACTS_ROOT)/security/bandit.txt"
	@"$(ACT)/pip-audit" --progress-spinner off -f json -o "$(ARTIFACTS_ROOT)/security/pip-audit.json" || true
	@"$(ACT)/pip-audit" --progress-spinner off | tee "$(ARTIFACTS_ROOT)/security/pip-audit.txt" || true
