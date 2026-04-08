.PHONY: sbom

sbom: install
	@mkdir -p "$(ARTIFACTS_ROOT)/sbom"
	@"$(ACT)/pip-audit" --progress-spinner off --format cyclonedx-json --output "$(ARTIFACTS_ROOT)/sbom/bijux-pollenomics.cdx.json" || true
