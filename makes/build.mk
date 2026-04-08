DIST_ROOT ?= $(ARTIFACTS_ROOT)/build

.PHONY: build package-check package-smoke package-source-smoke package-verify

build: install
	@rm -rf "$(DIST_ROOT)" build
	@mkdir -p "$(DIST_ROOT)"
	@"$(VENV_PYTHON)" -m build --outdir "$(DIST_ROOT)" "$(ROOT_PACKAGE_DIR)"

package-check: build
	@"$(VENV_PYTHON)" -m twine check "$(DIST_ROOT)"/*

package-smoke: build
	@rm -rf "$(ARTIFACTS_ROOT)/tmp/package-smoke"
	@"$(UV)" venv --python "$(PYTHON)" "$(ARTIFACTS_ROOT)/tmp/package-smoke"
	@"$(UV)" pip install --python "$(ARTIFACTS_ROOT)/tmp/package-smoke/bin/python" --no-deps "$(DIST_ROOT)"/*.whl
	@"$(ARTIFACTS_ROOT)/tmp/package-smoke/bin/bijux-pollenomics" --version
	@"$(ARTIFACTS_ROOT)/tmp/package-smoke/bin/bijux-pollenomics" --help >/dev/null

package-source-smoke: build
	@rm -rf "$(ARTIFACTS_ROOT)/tmp/package-source-smoke"
	@"$(UV)" venv --python "$(PYTHON)" "$(ARTIFACTS_ROOT)/tmp/package-source-smoke"
	@"$(UV)" pip install --python "$(ARTIFACTS_ROOT)/tmp/package-source-smoke/bin/python" --no-deps "$(DIST_ROOT)"/*.tar.gz
	@"$(ARTIFACTS_ROOT)/tmp/package-source-smoke/bin/bijux-pollenomics" --version
	@"$(ARTIFACTS_ROOT)/tmp/package-source-smoke/bin/bijux-pollenomics" --help >/dev/null

package-verify: package-check package-smoke package-source-smoke
