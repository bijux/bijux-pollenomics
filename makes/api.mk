.PHONY: api

api: install
	@mkdir -p "$(ARTIFACTS_ROOT)/api"
	@echo "No API contracts are defined for bijux-pollenomics." | tee "$(ARTIFACTS_ROOT)/api/status.txt"
