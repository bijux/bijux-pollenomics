BIJUX_PY_WORKSPACE_DIR ?= $(abspath $(PROJECT_DIR)/..)
BIJUX_PY_REPOS ?= bijux-canon bijux-proteomics bijux-pollenomics
BIJUX_PY_REQUIRED_FILES ?= bijux.mk api/contract.mk api/freeze.mk api/live-contract.mk api/root.mk ci/build.mk ci/docs.mk ci/help.mk ci/lint.mk ci/quality.mk ci/sbom.mk ci/security.mk ci/test.mk ci/util.mk package/api-python.mk package/catalog.mk package/freeze-python.mk package/gates.mk package/lifecycle.mk package/profile.mk package/python.mk package/repository-python.mk package/workspace-python.mk repository/config-layout.mk repository/env.mk repository/make-layout.mk repository/publish.mk repository/root.mk root/docs.mk root/env.mk root/lifecycle.mk root/package-dispatch.mk
BIJUX_PY_OPTIONAL_FILES ?=

.PHONY: check-shared-bijux-py

check-shared-bijux-py: ## Verify shared bijux-py make modules match across sibling repositories
	@set -eu; \
	current_repo="$(PROJECT_SLUG)"; \
	workspace_dir="$(BIJUX_PY_WORKSPACE_DIR)"; \
	current_dir="$$workspace_dir/$$current_repo/makes/bijux-py"; \
	[ -d "$$current_dir" ] || { echo "✘ Missing shared make directory: $$current_dir"; exit 2; }; \
	for repo in $(BIJUX_PY_REPOS); do \
	  [ "$$repo" = "$$current_repo" ] && continue; \
	  other_dir="$$workspace_dir/$$repo/makes/bijux-py"; \
	  [ -d "$$other_dir" ] || { echo "✘ Missing sibling shared make directory: $$other_dir"; exit 2; }; \
	  for file in $(BIJUX_PY_REQUIRED_FILES); do \
	    [ -f "$$current_dir/$$file" ] || { echo "✘ Missing $$current_dir/$$file"; exit 2; }; \
	    [ -f "$$other_dir/$$file" ] || { echo "✘ Missing $$other_dir/$$file"; exit 2; }; \
	    cmp -s "$$current_dir/$$file" "$$other_dir/$$file" || { echo "✘ Shared make drift: $$file differs between $$current_repo and $$repo"; exit 1; }; \
	  done; \
	  for file in $(BIJUX_PY_OPTIONAL_FILES); do \
	    if [ -f "$$current_dir/$$file" ] && [ -f "$$other_dir/$$file" ]; then \
	      cmp -s "$$current_dir/$$file" "$$other_dir/$$file" || { echo "✘ Shared make drift: $$file differs between $$current_repo and $$repo"; exit 1; }; \
	    fi; \
	  done; \
	done; \
	echo "✔ bijux-py modules match across $(BIJUX_PY_REPOS)"
