.PHONY: api api-install api-lint api-test api-clean openapi-drift

api:
	@$(MAKE) API_MODE=freeze api

api-install:
	@$(MAKE) API_MODE=freeze api-install

api-lint:
	@$(MAKE) API_MODE=freeze api-lint

api-test:
	@$(MAKE) API_MODE=freeze api-test

openapi-drift:
	@$(MAKE) API_MODE=freeze openapi-drift

api-clean:
	@$(MAKE) API_MODE=freeze api-clean
