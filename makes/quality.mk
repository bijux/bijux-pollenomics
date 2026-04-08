.PHONY: quality

quality: install
	@mkdir -p "$(ARTIFACTS_ROOT)/quality"
	@$(ACT)/ruff format --check --config configs/ruff.toml $(ROOT_PACKAGE_SRC_DIR) $(ROOT_PACKAGE_TEST_DIR) $(ROOT_DEV_SRC_DIR) docs/hooks | tee "$(ARTIFACTS_ROOT)/quality/ruff-format.log"
	@PYTHONPATH="$(ROOT_PYTHONPATH)" "$(VENV_PYTHON)" -m compileall "$(ROOT_PACKAGE_SRC_DIR)" "$(ROOT_DEV_SRC_DIR)" | tee "$(ARTIFACTS_ROOT)/quality/compileall.log"
