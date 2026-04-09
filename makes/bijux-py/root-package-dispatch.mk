ROOT_SHARED_CHECK_OVERRIDES := \
	VENV="$(abspath $(ROOT_CHECK_VENV))" \
	VENV_PYTHON="$(abspath $(ROOT_CHECK_PYTHON))" \
	PYTHON="$(abspath $(ROOT_CHECK_PYTHON))" \
	ACT="$(abspath $(ROOT_CHECK_VENV))/bin"

define run_root_package_target
	@set -eu; \
	resolved_package="$(call resolve_package,$(PACKAGE))"; \
	if [ -n "$$resolved_package" ]; then \
	  package_list="$$resolved_package"; \
	else \
	  package_list="$(2)"; \
	fi; \
	mkdir -p "$(ROOT_ARTIFACTS_DIR)"; \
	cleanup() { $(MAKE) clean-root-artifacts >/dev/null; }; \
	trap cleanup EXIT; \
	if [ "$(3)" = "1" ]; then \
	  $(MAKE) root-check-env >/dev/null; \
	fi; \
	failures=""; \
	for package in $$package_list; do \
	  profile_path="$$(printf '%s\n' $(PACKAGE_PROFILE_MAPPINGS) | awk -F= -v pkg="$$package" '$$1 == pkg { print $$2 }')"; \
	  if [ -z "$$profile_path" ]; then \
	    profile_path="$(PACKAGE_MAKE_DIR)/$$package.mk"; \
	  fi; \
	  if [ ! -f "$$profile_path" ]; then \
	    echo "Missing package profile: $$profile_path"; \
	    failures="$$failures $$package"; \
	    continue; \
	  fi; \
	  echo "==> $$package: $(1)"; \
	  if [ "$(3)" = "1" ]; then \
	    if ! $(MAKE) -C "packages/$$package" -f "$$profile_path" \
	      PROJECT_SLUG="$$package" \
	      $(ROOT_SHARED_CHECK_OVERRIDES) \
	      $(1); then \
	      failures="$$failures $$package"; \
	    fi; \
	  elif ! $(MAKE) -C "packages/$$package" -f "$$profile_path" PROJECT_SLUG="$$package" $(1); then \
	    failures="$$failures $$package"; \
	  fi; \
	done; \
	if [ -n "$$failures" ]; then \
	  echo; \
	  echo "Packages with $(1) failures:$$failures"; \
	  exit 2; \
	fi
endef

define define_root_package_target
$(1):
	$$(call assert_package)
	$$(call run_root_package_target,$(1),$$(ROOT_TARGET_PACKAGES_$(1)),$$(ROOT_TARGET_SHARED_ENV_$(1)))
	$$(ROOT_TARGET_POST_$(1))
endef

$(foreach target,$(ROOT_PACKAGE_TARGETS),$(eval $(call define_root_package_target,$(target))))

##@ Orchestration
test: ## Run primary package tests package by package
lint: ## Run repository lint checks package by package with the shared check environment
quality: ## Run repository quality checks package by package with the shared check environment
security: ## Run repository security checks package by package with the shared check environment
api: ## Run primary package API checks package by package
build: ## Build primary package artifacts package by package
sbom: ## Generate primary package SBOMs package by package
clean: ## Clean package artifacts across the repository
