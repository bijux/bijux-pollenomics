DOCS_SITE_ROOT ?= $(ARTIFACTS_ROOT)/root/docs/site
MKDOCS_LOCAL_SITE_URL ?= http://127.0.0.1:8000/
MKDOCS_ENV := NO_MKDOCS_2_WARNING=true

.PHONY: docs docs-serve

docs: install
	@mkdir -p "$(ARTIFACTS_ROOT)/root/docs"
	@SITE_URL=$${SITE_URL:-https://bijux.io/pollenomics/} "$(ACT)/mkdocs" build --strict --site-dir "$(DOCS_SITE_ROOT)"

docs-serve: install
	@SITE_URL="$(MKDOCS_LOCAL_SITE_URL)" "$(ACT)/mkdocs" serve --dev-addr 127.0.0.1:8000
