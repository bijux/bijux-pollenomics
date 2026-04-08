include $(ROOT_MAKE_DIR)/bijux-py/lint.mk
include $(ROOT_MAKE_DIR)/bijux-py/test.mk
include $(ROOT_MAKE_DIR)/bijux-py/quality.mk
include $(ROOT_MAKE_DIR)/bijux-py/security.mk
include $(ROOT_MAKE_DIR)/bijux-py/build.mk
include $(ROOT_MAKE_DIR)/bijux-py/sbom.mk
API_REPO_DIR ?= $(ROOT_MAKE_DIR)/api
include $(ROOT_MAKE_DIR)/bijux-py/api.mk
include $(ROOT_MAKE_DIR)/publish.mk
include $(ROOT_MAKE_DIR)/bijux-py/package-lifecycle.mk

PACKAGE_DEFINE_ALL_PARALLEL ?= 0
PACKAGE_ALL_PARALLEL_PRE_TARGETS ?= clean install
PACKAGE_ALL_PARALLEL_MAIN_TARGETS ?= quality security api
PACKAGE_ALL_PARALLEL_MAIN_JOBS ?= 4
PACKAGE_ALL_PARALLEL_FINAL_TARGETS ?= build sbom
PACKAGE_ALL_PARALLEL_MESSAGE ?= ✔ All targets completed (parallel mode)

ifeq ($(PACKAGE_DEFINE_ALL_PARALLEL),1)
all-parallel: $(PACKAGE_ALL_PARALLEL_PRE_TARGETS)
	@$(SELF_MAKE) -j$(PACKAGE_ALL_PARALLEL_MAIN_JOBS) $(PACKAGE_ALL_PARALLEL_MAIN_TARGETS)
	@$(SELF_MAKE) $(PACKAGE_ALL_PARALLEL_FINAL_TARGETS)
	@echo "$(PACKAGE_ALL_PARALLEL_MESSAGE)"
.PHONY: all-parallel
endif

##@ Core
clean: ## Remove virtualenv plus package artifacts
clean-soft: ## Remove build artifacts but keep the virtualenv
install: ## Install package dependencies into the virtualenv
help: ## Show package commands
bootstrap: ## Install package prerequisites for gate targets
all-parallel: ## Run parallel package checks when enabled
