LINT_TARGETS ?= $(ROOT_PACKAGE_SRC_DIR) $(ROOT_PACKAGE_TEST_DIR) $(ROOT_DEV_SRC_DIR) docs/hooks
RUFF_CONFIG ?= configs/ruff.toml

.PHONY: lint

lint: install
	@mkdir -p "$(ARTIFACTS_ROOT)/lint"
	@$(ACT)/ruff check --config "$(RUFF_CONFIG)" $(LINT_TARGETS) | tee "$(ARTIFACTS_ROOT)/lint/ruff.log"
