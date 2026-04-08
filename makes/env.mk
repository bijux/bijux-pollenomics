MONOREPO_ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/..)
ROOT_MAKE_DIR := $(MONOREPO_ROOT)/makes

include $(ROOT_MAKE_DIR)/bijux-py/repository-env.mk
