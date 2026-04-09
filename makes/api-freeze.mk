API_FREEZE_COMMAND ?= $(VENV_PYTHON) -m bijux_pollenomics_dev.api.freeze_contracts
API_OPENAPI_DRIFT_COMMAND ?= $(VENV_PYTHON) -m bijux_pollenomics_dev.api.openapi_drift

include $(ROOT_MAKE_DIR)/bijux-py/api/freeze.mk
