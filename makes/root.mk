ROOT_MAKEFILE_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))

include $(ROOT_MAKEFILE_DIR)/root/env.mk
include $(ROOT_MAKEFILE_DIR)/lint.mk
include $(ROOT_MAKEFILE_DIR)/test.mk
include $(ROOT_MAKEFILE_DIR)/quality.mk
include $(ROOT_MAKEFILE_DIR)/security.mk
include $(ROOT_MAKEFILE_DIR)/build.mk
include $(ROOT_MAKEFILE_DIR)/sbom.mk
include $(ROOT_MAKEFILE_DIR)/docs.mk
include $(ROOT_MAKEFILE_DIR)/api.mk
include $(ROOT_MAKEFILE_DIR)/root/targets.mk
