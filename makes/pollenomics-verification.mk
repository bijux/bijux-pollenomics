POLLENOMICS_VERIFICATION_PYTHON := $(abspath $(ROOT_CHECK_VENV))/bin/python
POLLENOMICS_VERIFICATION_PYTEST := $(abspath $(ROOT_CHECK_VENV))/bin/pytest
POLLENOMICS_SOURCE_ROOT := packages/bijux-pollenomics/src/bijux_pollenomics
POLLENOMICS_TEST_ROOT := packages/bijux-pollenomics/tests
POLLENOMICS_GATE_ARTIFACTS := artifacts/execution-control/gates
POLLENOMICS_SEAD_GOVERNED_RUN := sead-full-evidence-39bfff6a-ce80714e
POLLENOMICS_RELEASE_CANDIDATE_ID ?= $(shell git rev-parse HEAD 2>/dev/null)
POLLENOMICS_RELEASE_EVIDENCE_DIRECTORY ?= artifacts/execution-control/release-evidence/$(POLLENOMICS_RELEASE_CANDIDATE_ID)
POLLENOMICS_RELEASE_EVIDENCE_REQUEST ?= $(POLLENOMICS_RELEASE_EVIDENCE_DIRECTORY)/request.json
POLLENOMICS_RELEASE_EVIDENCE_OUTPUT ?= $(POLLENOMICS_RELEASE_EVIDENCE_DIRECTORY)/manifest.json
POLLENOMICS_GATE_TIMEOUT_SECONDS ?= 900
POLLENOMICS_NODE_DIRECTORY := $(patsubst %/,%,$(dir $(shell command -v node 2>/dev/null)))
POLLENOMICS_GATE_PATH := $(abspath $(ROOT_CHECK_VENV))/bin$(if $(POLLENOMICS_NODE_DIRECTORY),:$(POLLENOMICS_NODE_DIRECTORY)):/usr/bin:/bin
POLLENOMICS_GATE_TRUST_INPUTS := Makefile makes/pollenomics-verification.mk pyproject.toml packages/bijux-pollenomics/pyproject.toml uv.lock
POLLENOMICS_PYTHON_SOURCES = $(shell find $(1) -type f -name '*.py' -print | LC_ALL=C sort)

POLLENOMICS_SCIENCE_TESTS := \
	$(POLLENOMICS_TEST_ROOT)/unit/core/test_temporal_semantics.py \
	$(POLLENOMICS_TEST_ROOT)/unit/collection/sources/sead/evidence/test_chronology.py \
	$(POLLENOMICS_TEST_ROOT)/unit/analysis/classification/test_ecological_classification.py \
	$(POLLENOMICS_TEST_ROOT)/unit/evidence/test_classification_audit_outputs.py \
	$(POLLENOMICS_TEST_ROOT)/unit/analysis/classification/test_classification_events \
	$(POLLENOMICS_TEST_ROOT)/unit/analysis/classification/test_harmonization.py \
	$(POLLENOMICS_TEST_ROOT)/unit/core/test_temporal_overlap_consumers.py \
	$(POLLENOMICS_TEST_ROOT)/unit/analysis/fieldwork/evidence_richness \
	$(POLLENOMICS_TEST_ROOT)/unit/analysis/propagation/test_propagation_evidence_domains.py \
	$(POLLENOMICS_TEST_ROOT)/unit/evidence/test_scientific_review.py \
	$(POLLENOMICS_TEST_ROOT)/unit/evidence/scientific_review \
	$(POLLENOMICS_TEST_ROOT)/unit/collection/catalog/spatiotemporal/test_posture.py \
	$(POLLENOMICS_TEST_ROOT)/unit/analysis/propagation/network
POLLENOMICS_SCIENCE_INPUTS := \
	$(POLLENOMICS_GATE_TRUST_INPUTS) \
	configs/pytest.ini \
	data/neotoma/raw \
	data/sead/raw \
	$(call POLLENOMICS_PYTHON_SOURCES,$(POLLENOMICS_SOURCE_ROOT)/core) \
	$(call POLLENOMICS_PYTHON_SOURCES,$(POLLENOMICS_SOURCE_ROOT)/evidence) \
	$(call POLLENOMICS_PYTHON_SOURCES,$(POLLENOMICS_SOURCE_ROOT)/analysis) \
	$(POLLENOMICS_SCIENCE_TESTS)

POLLENOMICS_DATA_TESTS := \
	$(POLLENOMICS_TEST_ROOT)/unit/adna/workflow/adna_normalization \
	$(POLLENOMICS_TEST_ROOT)/unit/adna/governance/audit_catalogs \
	$(POLLENOMICS_TEST_ROOT)/unit/adna/species/tracked_data \
	$(POLLENOMICS_TEST_ROOT)/unit/adna/projects/evidence/test_localities.py \
	$(POLLENOMICS_TEST_ROOT)/unit/adna/workflow/test_adna_runtime.py \
	$(POLLENOMICS_TEST_ROOT)/unit/adna/projects/sample_master \
	$(POLLENOMICS_TEST_ROOT)/unit/adna/projects/registry \
	$(POLLENOMICS_TEST_ROOT)/unit/adna/sources/library \
	$(POLLENOMICS_TEST_ROOT)/unit/adna/sources/test_adna_source_recovery.py \
	$(POLLENOMICS_TEST_ROOT)/unit/adna/domain/test_adna_temporal_query.py \
	$(POLLENOMICS_TEST_ROOT)/unit/collection/sources/sead/acquisition/full \
	$(POLLENOMICS_TEST_ROOT)/unit/collection/sources/sead/acquisition/test_admission \
	$(POLLENOMICS_TEST_ROOT)/unit/collection/sources/sead/evidence/test_claims.py \
	$(POLLENOMICS_TEST_ROOT)/unit/collection/sources/sead/evidence/test_observations \
	$(POLLENOMICS_TEST_ROOT)/unit/collection/sources/sead/acquisition/scoped/test_materialization.py \
	$(POLLENOMICS_TEST_ROOT)/unit/collection/sources/sead/acquisition/scoped/test_refusal_boundaries.py \
	$(POLLENOMICS_TEST_ROOT)/unit/collection/sources/neotoma \
	$(POLLENOMICS_TEST_ROOT)/unit/collection/sources/landclim \
	$(POLLENOMICS_TEST_ROOT)/unit/collection/sources/raa/test_raa_data.py \
	$(POLLENOMICS_TEST_ROOT)/unit/collection/sources/raa/test_raa_authority.py \
	$(POLLENOMICS_TEST_ROOT)/unit/collection/sources/svar/test_svar_data.py \
	$(POLLENOMICS_TEST_ROOT)/unit/collection/sources/boundaries/test_boundaries.py \
	$(POLLENOMICS_TEST_ROOT)/unit/collection/sources/boundaries/test_boundary_country_review.py \
	$(POLLENOMICS_TEST_ROOT)/unit/collection/contracts/test_data_contract_surfaces.py \
	$(POLLENOMICS_TEST_ROOT)/unit/collection/workflow/planning/test_layout.py \
	$(POLLENOMICS_TEST_ROOT)/unit/collection/catalog/test_source_identity.py \
	$(POLLENOMICS_TEST_ROOT)/unit/collection/contracts/test_source_family_contracts \
	$(POLLENOMICS_TEST_ROOT)/unit/collection/contracts/test_source_layout_contract.py \
	$(POLLENOMICS_TEST_ROOT)/unit/collection/catalog/test_source_provenance.py \
	$(POLLENOMICS_TEST_ROOT)/unit/collection/catalog/test_source_traceability.py \
	$(POLLENOMICS_TEST_ROOT)/unit/collection/catalog/test_source_validation.py
POLLENOMICS_DATA_INPUTS := \
	$(POLLENOMICS_GATE_TRUST_INPUTS) \
	configs/pytest.ini \
	data/source_family_contracts.json \
	data/source_spatiotemporal_posture_registry.json \
	data/adna/final \
	data/adna/governance \
	$(wildcard data/adna/species/*/manifests) \
	$(wildcard data/adna/species/*/normalized) \
	$(wildcard data/adna/species/*/reports) \
	$(wildcard data/adna/species/*/review) \
	data/neotoma \
	data/sead \
	data/landclim \
	data/raa \
	data/svar \
	data/boundaries \
	$(call POLLENOMICS_PYTHON_SOURCES,$(POLLENOMICS_SOURCE_ROOT)/collection) \
	$(call POLLENOMICS_PYTHON_SOURCES,$(POLLENOMICS_SOURCE_ROOT)/adna) \
	$(POLLENOMICS_DATA_TESTS)

POLLENOMICS_MAP_TESTS := \
	$(POLLENOMICS_TEST_ROOT)/unit/reporting \
	$(POLLENOMICS_TEST_ROOT)/unit/evidence/surfaces \
	$(POLLENOMICS_TEST_ROOT)/unit/analysis/propagation/test_propagation_outputs \
	$(POLLENOMICS_TEST_ROOT)/unit/governance/test_public_artifact_language.py
POLLENOMICS_MAP_INPUTS := \
	$(POLLENOMICS_GATE_TRUST_INPUTS) \
	configs/pytest.ini \
	docs/report \
	$(call POLLENOMICS_PYTHON_SOURCES,$(POLLENOMICS_SOURCE_ROOT)/reporting) \
	$(call POLLENOMICS_PYTHON_SOURCES,$(POLLENOMICS_SOURCE_ROOT)/evidence) \
	$(POLLENOMICS_MAP_TESTS)

POLLENOMICS_PROVENANCE_TESTS := \
	$(POLLENOMICS_TEST_ROOT)/unit/provenance/test_release_evidence \
	$(POLLENOMICS_TEST_ROOT)/unit/provenance/release_evidence_writer \
	$(POLLENOMICS_TEST_ROOT)/unit/provenance/gates \
	$(POLLENOMICS_TEST_ROOT)/unit/provenance/recorded_gates \
	$(POLLENOMICS_TEST_ROOT)/unit/provenance/test_pollenomics_gate_runner.py
POLLENOMICS_PROVENANCE_INPUTS := \
	$(POLLENOMICS_GATE_TRUST_INPUTS) \
	configs/pytest.ini \
	configs/release_evidence_policy.json \
	$(call POLLENOMICS_PYTHON_SOURCES,$(POLLENOMICS_SOURCE_ROOT)/provenance) \
	$(POLLENOMICS_PROVENANCE_TESTS)

POLLENOMICS_DOC_COUNT_TESTS := \
	$(POLLENOMICS_TEST_ROOT)/unit/governance/country_coverage \
	$(POLLENOMICS_TEST_ROOT)/unit/governance/test_data_reference_docs.py \
	$(POLLENOMICS_TEST_ROOT)/unit/collection/catalog/spatiotemporal/test_posture.py \
	$(POLLENOMICS_TEST_ROOT)/unit/collection/workflow/materialization/test_repository_snapshot.py \
	$(POLLENOMICS_TEST_ROOT)/unit/governance/repository_truth/assessments \
	$(POLLENOMICS_TEST_ROOT)/regression/test_docs_breadth.py
POLLENOMICS_DOC_COUNT_INPUTS := \
	$(POLLENOMICS_GATE_TRUST_INPUTS) \
	configs/pytest.ini \
	data/collection_summary.json \
	data/country_dimension_coverage.json \
	data/boundaries/raw/source_manifest.json \
	data/boundaries/normalized/nordic_country_boundaries.geojson \
	data/landclim/normalized/nordic_pollen_site_sequences.geojson \
	data/neotoma/relational/reconciliation.json \
	data/sead/normalized/acquisitions/$(POLLENOMICS_SEAD_GOVERNED_RUN)/evidence_materialization_manifest.json \
	data/sead/normalized/nordic_environmental_sites.geojson \
	data/sead/raw/acquisitions/$(POLLENOMICS_SEAD_GOVERNED_RUN)/admission.json \
	data/sead/raw/acquisitions/$(POLLENOMICS_SEAD_GOVERNED_RUN)/country-decisions.json \
	data/sead/raw/acquisitions/$(POLLENOMICS_SEAD_GOVERNED_RUN)/payloads/tbl_sites.json \
	docs/report/regions/nordic/nordic_pollen_site_sequences.geojson \
	docs/report/regions/nordic/nordic_pollen_sites.geojson \
	docs/report/countries/sweden/sweden_aadr_v66_summary.json \
	docs/report/countries/denmark/denmark_aadr_v66_summary.json \
	docs/report/countries/norway/norway_aadr_v66_summary.json \
	docs/report/countries/finland/finland_aadr_v66_summary.json \
	docs/report/animal_country_species_coverage.json \
	data/evidence_artifact_contracts.json \
	data/source_fact_ownership_registry.json \
	data/source_family_contracts.json \
	data/source_family_evidence_stage_matrix.json \
	data/source_spatiotemporal_posture_registry.json \
	docs/public/pollenomics-data \
	$(call POLLENOMICS_PYTHON_SOURCES,$(POLLENOMICS_SOURCE_ROOT)/governance) \
	$(call POLLENOMICS_PYTHON_SOURCES,$(POLLENOMICS_SOURCE_ROOT)/reporting/review) \
	$(POLLENOMICS_DOC_COUNT_TESTS)

define run_pollenomics_pytest_gate
	@PYTHONPATH="$(CURDIR)/packages/bijux-pollenomics/src" \
	PYTHONPYCACHEPREFIX="$(CURDIR)/$(POLLENOMICS_GATE_ARTIFACTS)/runner-pycache/$(1)" \
	"$(POLLENOMICS_VERIFICATION_PYTHON)" -m bijux_pollenomics.provenance.gate_runner \
		--repository-root "$(CURDIR)" \
		--gate-id "$(1)" \
		--artifacts-directory "$(POLLENOMICS_GATE_ARTIFACTS)" \
		--junit-path "$(POLLENOMICS_GATE_ARTIFACTS)/$(1).junit.xml" \
		--timeout-seconds "$(POLLENOMICS_GATE_TIMEOUT_SECONDS)" \
		$(foreach input,$(3),--input "$(input)") \
		--environment "PATH=$(POLLENOMICS_GATE_PATH)" \
		--environment "PYTHONPATH=$(CURDIR)/packages/bijux-pollenomics/src" \
		--environment "PYTHONPYCACHEPREFIX=$(CURDIR)/$(POLLENOMICS_GATE_ARTIFACTS)/pycache/$(1)" \
		--environment "PYTHONDONTWRITEBYTECODE=1" \
		--environment "PYTHONIOENCODING=utf-8" \
		--environment "HYPOTHESIS_DATABASE_DIRECTORY=$(CURDIR)/$(POLLENOMICS_GATE_ARTIFACTS)/hypothesis/$(1)" \
		--environment "LANG=C" \
		--environment "LC_ALL=C" \
		-- \
		"$(POLLENOMICS_VERIFICATION_PYTEST)" \
		--rootdir "$(CURDIR)" \
		-c "$(CURDIR)/configs/pytest.ini" \
		-q \
		-o "cache_dir=$(CURDIR)/$(POLLENOMICS_GATE_ARTIFACTS)/pytest-cache/$(1)" \
		--junitxml="$(CURDIR)/$(POLLENOMICS_GATE_ARTIFACTS)/$(1).junit.xml" \
		$(2)
endef

.PHONY: verify-science verify-data verify-map verify-provenance verify-doc-counts verify-rebuild verify-sead-evidence-fixed-point refresh-release-gates release-evidence-request release-evidence verify-release-candidate

verify-rebuild: root-check-env ## Prove tracked reports rebuild deterministically
	@evidence_parent="$$(mktemp -d "$(CURDIR)/artifacts/execution-control/reproducible-report-build.XXXXXX")"; \
	$(DEV_RUN) -m bijux_pollenomics_dev.ci.rebuild_reports \
		--repo-root "$(CURDIR)" \
		--policy "$(CURDIR)/configs/ci/reproducible-report-build.json" \
		--evidence-root "$$evidence_parent/evidence"

verify-sead-evidence-fixed-point: root-check-env ## Prove governed SEAD evidence rebuilds byte-identically without network
	@evidence_parent="$$(mktemp -d "$(CURDIR)/artifacts/execution-control/sead-evidence-fixed-point.XXXXXX")"; \
	$(DEV_RUN) -m bijux_pollenomics_dev.ci.rebuild_sead_evidence \
		--repo-root "$(CURDIR)" \
		--evidence-root "$$evidence_parent/evidence"

verify-science: root-check-env ## Record focused scientific-semantics verification
	$(call run_pollenomics_pytest_gate,science,$(POLLENOMICS_SCIENCE_TESTS),$(POLLENOMICS_SCIENCE_INPUTS))

verify-data: root-check-env ## Record source, relation, and data-contract verification
	$(call run_pollenomics_pytest_gate,data,$(POLLENOMICS_DATA_TESTS),$(POLLENOMICS_DATA_INPUTS))

verify-map: root-check-env ## Record map and publication-surface verification
	$(call run_pollenomics_pytest_gate,map,$(POLLENOMICS_MAP_TESTS),$(POLLENOMICS_MAP_INPUTS))

verify-provenance: root-check-env ## Record provenance and release-evidence verification
	$(call run_pollenomics_pytest_gate,provenance,$(POLLENOMICS_PROVENANCE_TESTS),$(POLLENOMICS_PROVENANCE_INPUTS))

verify-doc-counts: root-check-env ## Record documentation and governed-count verification
	$(call run_pollenomics_pytest_gate,doc-counts,$(POLLENOMICS_DOC_COUNT_TESTS),$(POLLENOMICS_DOC_COUNT_INPUTS))

refresh-release-gates: verify-science verify-data verify-map verify-provenance verify-doc-counts ## Force-run and record every required local gate

release-evidence-request: root-check-env ## Derive a request only from fresh existing gate records and governed inputs
	@PYTHONPATH="$(CURDIR)/packages/bijux-pollenomics/src" \
	PYTHONPYCACHEPREFIX="$(CURDIR)/$(POLLENOMICS_GATE_ARTIFACTS)/runner-pycache/release-evidence" \
	"$(POLLENOMICS_VERIFICATION_PYTHON)" -m bijux_pollenomics.provenance request \
		--repository-root "$(CURDIR)" \
		--output "$(POLLENOMICS_RELEASE_EVIDENCE_REQUEST)"

release-evidence: release-evidence-request ## Build canonical evidence without rerunning recorded gates
	@PYTHONPATH="$(CURDIR)/packages/bijux-pollenomics/src" \
	PYTHONPYCACHEPREFIX="$(CURDIR)/$(POLLENOMICS_GATE_ARTIFACTS)/runner-pycache/release-evidence" \
	"$(POLLENOMICS_VERIFICATION_PYTHON)" -m bijux_pollenomics.provenance write \
		--repository-root "$(CURDIR)" \
		--request "$(POLLENOMICS_RELEASE_EVIDENCE_REQUEST)" \
		--output "$(POLLENOMICS_RELEASE_EVIDENCE_OUTPUT)"

verify-release-candidate: release-evidence ## Refuse a candidate unless canonical release evidence validates as ready
	@PYTHONPATH="$(CURDIR)/packages/bijux-pollenomics/src" \
	PYTHONPYCACHEPREFIX="$(CURDIR)/$(POLLENOMICS_GATE_ARTIFACTS)/runner-pycache/release-evidence" \
	"$(POLLENOMICS_VERIFICATION_PYTHON)" -m bijux_pollenomics.provenance validate \
		--repository-root "$(CURDIR)" \
		--manifest "$(POLLENOMICS_RELEASE_EVIDENCE_OUTPUT)"
