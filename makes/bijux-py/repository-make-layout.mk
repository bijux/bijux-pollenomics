MAKE_LAYOUT_REQUIRED_FILES ?= env.mk packages.mk publish.mk root.mk
MAKE_LAYOUT_REQUIRED_DIRS ?= api bijux-py packages
MAKE_LAYOUT_API_FILES ?= contract.mk freeze.mk live-contract.mk

.PHONY: check-make-layout

check-make-layout: ## Validate the repository make tree shape and required entrypoints
	@set -eu; \
	make_dir="$(ROOT_MAKE_DIR)"; \
	for file in $(MAKE_LAYOUT_REQUIRED_FILES); do \
	  test -f "$$make_dir/$$file" || { echo "✘ Missing make root file: $$make_dir/$$file"; exit 1; }; \
	done; \
	for dir in $(MAKE_LAYOUT_REQUIRED_DIRS); do \
	  test -d "$$make_dir/$$dir" || { echo "✘ Missing make directory: $$make_dir/$$dir"; exit 1; }; \
	done; \
	for file in $(MAKE_LAYOUT_API_FILES); do \
	  test -f "$$make_dir/api/$$file" || { echo "✘ Missing API make entrypoint: $$make_dir/api/$$file"; exit 1; }; \
	done; \
	for mapping in $(PACKAGE_PROFILE_MAPPINGS); do \
	  profile_path="$${mapping#*=}"; \
	  test -f "$$profile_path" || { echo "✘ Missing package profile: $$profile_path"; exit 1; }; \
	  case "$$profile_path" in \
	    "$$make_dir"/packages/*) ;; \
	    *) echo "✘ Package profile is outside makes/packages: $$profile_path"; exit 1 ;; \
	  esac; \
	done; \
	echo "✔ make tree layout is complete"
