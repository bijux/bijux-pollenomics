ROOT_PACKAGE_PROFILE_DIR ?= $(ROOT_MAKEFILE_DIR)/packages
PACKAGE_MAKE_DIR ?= $(ROOT_PACKAGE_PROFILE_DIR)
PACKAGE ?=
PACKAGE_FIELD_SEPARATOR := |

PACKAGE_RECORDS := \
	bijux-pollenomics|primary,check,buildable,sbom,api|bijux-pollenomics.mk \
	bijux-pollenomics-dev|check|bijux-pollenomics-dev.mk

define register_package_record
PACKAGE_GROUPS_$(word 1,$(subst $(PACKAGE_FIELD_SEPARATOR), ,$(1))) := $(word 2,$(subst $(PACKAGE_FIELD_SEPARATOR), ,$(1)))
PACKAGE_PROFILE_$(word 1,$(subst $(PACKAGE_FIELD_SEPARATOR), ,$(1))) := $(ROOT_PACKAGE_PROFILE_DIR)/$(word 3,$(subst $(PACKAGE_FIELD_SEPARATOR), ,$(1)))
endef

$(foreach record,$(PACKAGE_RECORDS),$(eval $(call register_package_record,$(record))))

PRIMARY_PACKAGES := $(foreach record,$(PACKAGE_RECORDS),$(if $(findstring primary,$(word 2,$(subst $(PACKAGE_FIELD_SEPARATOR), ,$(record)))),$(word 1,$(subst $(PACKAGE_FIELD_SEPARATOR), ,$(record)))))
ALL_PACKAGES := $(foreach record,$(PACKAGE_RECORDS),$(word 1,$(subst $(PACKAGE_FIELD_SEPARATOR), ,$(record))))
CHECK_PACKAGES := $(foreach record,$(PACKAGE_RECORDS),$(if $(findstring check,$(word 2,$(subst $(PACKAGE_FIELD_SEPARATOR), ,$(record)))),$(word 1,$(subst $(PACKAGE_FIELD_SEPARATOR), ,$(record)))))
API_PACKAGES := $(foreach record,$(PACKAGE_RECORDS),$(if $(findstring api,$(word 2,$(subst $(PACKAGE_FIELD_SEPARATOR), ,$(record)))),$(word 1,$(subst $(PACKAGE_FIELD_SEPARATOR), ,$(record)))))
BUILD_PACKAGES := $(foreach record,$(PACKAGE_RECORDS),$(if $(findstring buildable,$(word 2,$(subst $(PACKAGE_FIELD_SEPARATOR), ,$(record)))),$(word 1,$(subst $(PACKAGE_FIELD_SEPARATOR), ,$(record)))))
SBOM_PACKAGES := $(foreach record,$(PACKAGE_RECORDS),$(if $(findstring sbom,$(word 2,$(subst $(PACKAGE_FIELD_SEPARATOR), ,$(record)))),$(word 1,$(subst $(PACKAGE_FIELD_SEPARATOR), ,$(record)))))

ROOT_PACKAGE_TARGETS := test lint quality security api build sbom clean
ROOT_TARGET_PACKAGES_test := $(CHECK_PACKAGES)
ROOT_TARGET_PACKAGES_lint := $(CHECK_PACKAGES)
ROOT_TARGET_PACKAGES_quality := $(CHECK_PACKAGES)
ROOT_TARGET_PACKAGES_security := $(CHECK_PACKAGES)
ROOT_TARGET_PACKAGES_api := $(API_PACKAGES)
ROOT_TARGET_PACKAGES_build := $(BUILD_PACKAGES)
ROOT_TARGET_PACKAGES_sbom := $(SBOM_PACKAGES)
ROOT_TARGET_PACKAGES_clean := $(ALL_PACKAGES)
ROOT_TARGET_SHARED_ENV_test := 0
ROOT_TARGET_SHARED_ENV_lint := 1
ROOT_TARGET_SHARED_ENV_quality := 1
ROOT_TARGET_SHARED_ENV_security := 1
ROOT_TARGET_SHARED_ENV_api := 0
ROOT_TARGET_SHARED_ENV_build := 0
ROOT_TARGET_SHARED_ENV_sbom := 0
ROOT_TARGET_SHARED_ENV_clean := 0
ROOT_TARGET_POST_clean = @$(MAKE) clean-root-artifacts

VALID_PACKAGE_VALUES := $(ALL_PACKAGES)
ROOT_PACKAGE_DIRS := $(addprefix $(CURDIR)/packages/,$(ALL_PACKAGES))
ROOT_DISCOVERED_PACKAGE_DIRS := $(sort $(wildcard $(CURDIR)/packages/*))
ROOT_DECLARED_PACKAGE_PROFILE_FILES := $(foreach package,$(ALL_PACKAGES),$(PACKAGE_PROFILE_$(package)))
ROOT_MISSING_PACKAGE_DIRS := $(filter-out $(ROOT_DISCOVERED_PACKAGE_DIRS),$(ROOT_PACKAGE_DIRS))
ROOT_MISSING_PACKAGE_PROFILE_FILES := $(foreach file,$(ROOT_DECLARED_PACKAGE_PROFILE_FILES),$(if $(wildcard $(file)),,$(file)))
ROOT_UNDECLARED_PACKAGE_DIRS := $(filter-out $(ROOT_PACKAGE_DIRS),$(ROOT_DISCOVERED_PACKAGE_DIRS))

ifneq ($(strip $(ROOT_MISSING_PACKAGE_DIRS)),)
$(error Package inventory references missing directories: $(ROOT_MISSING_PACKAGE_DIRS))
endif

ifneq ($(strip $(ROOT_MISSING_PACKAGE_PROFILE_FILES)),)
$(error Package inventory references missing profiles: $(ROOT_MISSING_PACKAGE_PROFILE_FILES))
endif

ifneq ($(strip $(ROOT_UNDECLARED_PACKAGE_DIRS)),)
$(error Package directories are missing from makes/packages.mk: $(notdir $(ROOT_UNDECLARED_PACKAGE_DIRS)))
endif

define resolve_package
$(strip $(if $(filter $(1),$(ALL_PACKAGES)),$(1)))
endef

define resolve_package_profile
$(strip $(or $(PACKAGE_PROFILE_$(1)),$(PACKAGE_MAKE_DIR)/$(1).mk))
endef

define assert_package
	@if [ -n "$(PACKAGE)" ] && [ -z "$(call resolve_package,$(PACKAGE))" ]; then \
	  echo "Unknown package '$(PACKAGE)'."; \
	  echo "Valid package values:"; \
	  printf "  %s\n" $(VALID_PACKAGE_VALUES); \
	  exit 2; \
	fi
endef

PACKAGE_PROFILE_MAPPINGS := $(foreach package,$(ALL_PACKAGES),$(package)=$(call resolve_package_profile,$(package)))
