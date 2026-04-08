VERSION ?= $(shell PYTHONPATH=$(ROOT_PACKAGE_SRC_DIR) $(PYTHON) -c "from bijux_pollenomics.config import DEFAULT_AADR_VERSION; print(DEFAULT_AADR_VERSION)")
VERSION_ARG = $(if $(strip $(VERSION)),--version $(VERSION),)
DATA_ROOT ?= data

.PHONY: data-prep reports test test-all test-e2e test-regression test-unit

test: test-all

test-all: install
	@PYTHONPATH="$(ROOT_PYTHONPATH)" "$(VENV_PYTHON)" -m unittest discover -s "$(ROOT_PACKAGE_TEST_DIR)" -v

test-unit: install
	@PYTHONPATH="$(ROOT_PYTHONPATH)" "$(VENV_PYTHON)" -m unittest discover -s "$(ROOT_PACKAGE_TEST_DIR)/unit" -v

test-regression: install
	@PYTHONPATH="$(ROOT_PYTHONPATH)" "$(VENV_PYTHON)" -m unittest discover -s "$(ROOT_PACKAGE_TEST_DIR)/regression" -v

test-e2e: install
	@PYTHONPATH="$(ROOT_PYTHONPATH)" "$(VENV_PYTHON)" -m unittest discover -s "$(ROOT_PACKAGE_TEST_DIR)/e2e" -v

data-prep: install
	@BIJUX_POLLENOMICS_ALLOW_INSECURE_TLS=1 PYTHONPATH="$(ROOT_PYTHONPATH)" "$(CLI)" collect-data all $(VERSION_ARG) --output-root "$(DATA_ROOT)"

reports: install
	@PYTHONPATH="$(ROOT_PYTHONPATH)" "$(CLI)" publish-reports --aadr-root "$(DATA_ROOT)/aadr" $(VERSION_ARG) --output-root docs/report --context-root "$(DATA_ROOT)"
