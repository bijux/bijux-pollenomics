PACKAGE_DEFINE_VENV ?= 1
PACKAGE_DEFINE_INSTALL ?= 1
PACKAGE_DEFINE_BOOTSTRAP ?= 1
PACKAGE_DEFINE_CLEAN ?= 1
PACKAGE_DEFINE_ALL ?= 1
PACKAGE_DEFINE_HELP ?= 1

PACKAGE_NOTPARALLEL_TARGETS ?= all clean
PACKAGE_VENV_CREATE_MESSAGE ?= → Creating virtualenv with '$$(which $(PYTHON))' ...
PACKAGE_INSTALL_MESSAGE ?= → Installing dependencies...
PACKAGE_INSTALL_SPEC ?= .[dev]
PACKAGE_INSTALL_EDITABLE ?= 1
PACKAGE_INSTALL_BOOTSTRAP_PACKAGES ?= pip setuptools wheel
PACKAGE_INSTALL_PYTHON_PACKAGES ?=
PACKAGE_INSTALL_STAMP ?=
PACKAGE_BOOTSTRAP_PREREQS ?= install
PACKAGE_CLEAN_MESSAGE ?= → Cleaning ($(VENV)) ...
PACKAGE_CLEAN_SOFT_MESSAGE ?= → Cleaning (artifacts, caches) ...
PACKAGE_CLEAN_PATHS ?=
PACKAGE_CLEAN_DELETE_PYCACHE ?= 1
PACKAGE_CLEAN_DELETE_PYC_FILES ?= 1
PACKAGE_ALL_TARGETS ?= clean install test lint quality security api build sbom
PACKAGE_ALL_MESSAGE ?= ✔ All targets completed
PACKAGE_HELP_WIDTH ?= 20
PACKAGE_BOOTSTRAP_TARGETS ?=
PACKAGE_INSTALL_TARGETS ?=

.NOTPARALLEL: $(PACKAGE_NOTPARALLEL_TARGETS)

ifeq ($(PACKAGE_DEFINE_VENV),1)
$(VENV):
	@echo "$(PACKAGE_VENV_CREATE_MESSAGE)"
	@$(UV) venv --python "$(PYTHON)" "$(VENV)"
endif

ifeq ($(PACKAGE_DEFINE_INSTALL),1)
ifneq ($(strip $(PACKAGE_INSTALL_STAMP)),)
$(PACKAGE_INSTALL_STAMP): $(VENV)
	@echo "$(PACKAGE_INSTALL_MESSAGE)"
	@mkdir -p "$(PROJECT_ARTIFACTS_DIR)"
	@if [ -n "$(strip $(PACKAGE_INSTALL_BOOTSTRAP_PACKAGES))" ]; then \
	  $(UV) pip install --python "$(VENV_PYTHON)" --upgrade $(PACKAGE_INSTALL_BOOTSTRAP_PACKAGES); \
	fi
	@if [ -n "$(strip $(PACKAGE_INSTALL_PYTHON_PACKAGES))" ]; then \
	  $(UV) pip install --python "$(VENV_PYTHON)" --upgrade $(PACKAGE_INSTALL_PYTHON_PACKAGES); \
	fi
	@if [ "$(PACKAGE_INSTALL_EDITABLE)" = "1" ] && [ -n "$(strip $(PACKAGE_INSTALL_SPEC))" ]; then \
	  $(UV) pip install --python "$(VENV_PYTHON)" --editable "$(PACKAGE_INSTALL_SPEC)"; \
	fi
	@touch "$(PACKAGE_INSTALL_STAMP)"

install: $(PACKAGE_INSTALL_STAMP)
else
install: $(VENV)
	@echo "$(PACKAGE_INSTALL_MESSAGE)"
	@if [ -n "$(strip $(PACKAGE_INSTALL_BOOTSTRAP_PACKAGES))" ]; then \
	  $(UV) pip install --python "$(VENV_PYTHON)" --upgrade $(PACKAGE_INSTALL_BOOTSTRAP_PACKAGES); \
	fi
	@if [ -n "$(strip $(PACKAGE_INSTALL_PYTHON_PACKAGES))" ]; then \
	  $(UV) pip install --python "$(VENV_PYTHON)" --upgrade $(PACKAGE_INSTALL_PYTHON_PACKAGES); \
	fi
	@if [ "$(PACKAGE_INSTALL_EDITABLE)" = "1" ] && [ -n "$(strip $(PACKAGE_INSTALL_SPEC))" ]; then \
	  $(UV) pip install --python "$(VENV_PYTHON)" --editable "$(PACKAGE_INSTALL_SPEC)"; \
	fi
endif
.PHONY: install
endif

ifeq ($(PACKAGE_DEFINE_BOOTSTRAP),1)
bootstrap: $(PACKAGE_BOOTSTRAP_PREREQS)
.PHONY: bootstrap
endif

ifneq ($(strip $(PACKAGE_BOOTSTRAP_TARGETS)),)
$(PACKAGE_BOOTSTRAP_TARGETS): | bootstrap
endif

ifneq ($(strip $(PACKAGE_INSTALL_TARGETS)),)
$(PACKAGE_INSTALL_TARGETS): install
endif

ifeq ($(PACKAGE_DEFINE_CLEAN),1)
clean: clean-soft
	@echo "$(PACKAGE_CLEAN_MESSAGE)"
	@$(RM) "$(VENV)"

clean-soft:
	@echo "$(PACKAGE_CLEAN_SOFT_MESSAGE)"
	@$(RM) $(PACKAGE_CLEAN_PATHS) || true
ifeq ($(PACKAGE_CLEAN_DELETE_PYCACHE),1)
	@if [ "$(OS)" != "Windows_NT" ]; then \
	  find . -type d -name '__pycache__' -exec $(RM) {} +; \
	fi
endif
ifeq ($(PACKAGE_CLEAN_DELETE_PYC_FILES),1)
	@if [ "$(OS)" != "Windows_NT" ]; then \
	  find . -type f -name '*.pyc' -delete; \
	fi
endif
.PHONY: clean clean-soft
endif

ifeq ($(PACKAGE_DEFINE_ALL),1)
all: $(PACKAGE_ALL_TARGETS)
	@echo "$(PACKAGE_ALL_MESSAGE)"
.PHONY: all
endif

ifeq ($(PACKAGE_DEFINE_HELP),1)
HELP_WIDTH := $(PACKAGE_HELP_WIDTH)
include $(ROOT_MAKE_DIR)/bijux-py/ci/help.mk
endif
