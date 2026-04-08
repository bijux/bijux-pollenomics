PACKAGE_PROFILE_MAKEFILE ?= $(abspath $(firstword $(MAKEFILE_LIST)))
PACKAGE_MAKEFILE_DIR ?= $(abspath $(dir $(PACKAGE_PROFILE_MAKEFILE)))
PROJECT_DIR ?= $(CURDIR)
PROJECT_SLUG ?= $(notdir $(abspath $(PROJECT_DIR)))

include $(PACKAGE_MAKEFILE_DIR)/../env.mk
