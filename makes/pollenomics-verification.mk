POLLENOMICS_VERIFICATION_PYTHON := $(abspath $(ROOT_CHECK_VENV))/bin/python
POLLENOMICS_VERIFICATION_PYTEST := $(abspath $(ROOT_CHECK_VENV))/bin/pytest
POLLENOMICS_SOURCE_ROOT := packages/bijux-pollenomics/src/bijux_pollenomics
POLLENOMICS_TEST_ROOT := packages/bijux-pollenomics/tests
POLLENOMICS_GATE_ARTIFACTS := artifacts/execution-control/gates
POLLENOMICS_RELEASE_EVIDENCE_REQUEST ?= artifacts/execution-control/release-evidence-request.json
POLLENOMICS_RELEASE_EVIDENCE_OUTPUT ?= artifacts/execution-control/release-evidence.json
POLLENOMICS_GATE_TIMEOUT_SECONDS ?= 900
POLLENOMICS_NODE_DIRECTORY := $(patsubst %/,%,$(dir $(shell command -v node 2>/dev/null)))
POLLENOMICS_GATE_PATH := $(abspath $(ROOT_CHECK_VENV))/bin$(if $(POLLENOMICS_NODE_DIRECTORY),:$(POLLENOMICS_NODE_DIRECTORY)):/usr/bin:/bin

POLLENOMICS_SCIENCE_TESTS := \
	$(POLLENOMICS_TEST_ROOT)/unit/test_temporal_semantics.py \
	$(POLLENOMICS_TEST_ROOT)/unit/test_sead_chronology.py \
	$(POLLENOMICS_TEST_ROOT)/unit/test_ecological_classification.py \
	$(POLLENOMICS_TEST_ROOT)/unit/test_classification_audit_outputs.py \
	$(POLLENOMICS_TEST_ROOT)/unit/test_harmonization.py \
	$(POLLENOMICS_TEST_ROOT)/unit/test_temporal_overlap_consumers.py \
	$(POLLENOMICS_TEST_ROOT)/unit/test_lake_evidence_richness.py \
	$(POLLENOMICS_TEST_ROOT)/unit/test_propagation_evidence_domains.py \
	$(POLLENOMICS_TEST_ROOT)/unit/test_scientific_review.py \
	$(POLLENOMICS_TEST_ROOT)/unit/test_source_spatiotemporal_posture.py \
	$(POLLENOMICS_TEST_ROOT)/unit/test_propagation_network.py
POLLENOMICS_SCIENCE_INPUTS := \
	configs/pytest.ini \
	data/neotoma/raw \
	data/sead/raw \
	$(wildcard $(POLLENOMICS_SOURCE_ROOT)/core/*.py) \
	$(wildcard $(POLLENOMICS_SOURCE_ROOT)/evidence/*.py) \
	$(wildcard $(POLLENOMICS_SOURCE_ROOT)/evidence/classification/*.py) \
	$(wildcard $(POLLENOMICS_SOURCE_ROOT)/analysis/*.py) \
	$(wildcard $(POLLENOMICS_SOURCE_ROOT)/analysis/review/*.py) \
	$(POLLENOMICS_SCIENCE_TESTS)

POLLENOMICS_DATA_TESTS := \
	$(POLLENOMICS_TEST_ROOT)/unit/test_adna_normalization.py \
	$(POLLENOMICS_TEST_ROOT)/unit/test_adna_catalogs.py \
	$(POLLENOMICS_TEST_ROOT)/unit/test_adna_runtime.py \
	$(POLLENOMICS_TEST_ROOT)/unit/test_adna_temporal_query.py \
	$(POLLENOMICS_TEST_ROOT)/unit/test_sead_acquisition.py \
	$(POLLENOMICS_TEST_ROOT)/unit/test_sead_scoped_acquisition.py \
	$(POLLENOMICS_TEST_ROOT)/unit/test_neotoma_data.py \
	$(POLLENOMICS_TEST_ROOT)/unit/test_neotoma_relational.py \
	$(POLLENOMICS_TEST_ROOT)/unit/test_neotoma_materialization.py \
	$(POLLENOMICS_TEST_ROOT)/unit/test_neotoma_production.py \
	$(POLLENOMICS_TEST_ROOT)/unit/test_landclim_data.py \
	$(POLLENOMICS_TEST_ROOT)/unit/test_landclim_raw_receipt.py \
	$(POLLENOMICS_TEST_ROOT)/unit/test_raa_data.py \
	$(POLLENOMICS_TEST_ROOT)/unit/test_raa_authority.py \
	$(POLLENOMICS_TEST_ROOT)/unit/test_svar_data.py \
	$(POLLENOMICS_TEST_ROOT)/unit/test_boundaries.py \
	$(POLLENOMICS_TEST_ROOT)/unit/test_data_contract_surfaces.py \
	$(POLLENOMICS_TEST_ROOT)/unit/test_data_layout.py \
	$(POLLENOMICS_TEST_ROOT)/unit/test_source_identity.py \
	$(POLLENOMICS_TEST_ROOT)/unit/test_source_layout_contract.py \
	$(POLLENOMICS_TEST_ROOT)/unit/test_source_provenance.py \
	$(POLLENOMICS_TEST_ROOT)/unit/test_source_traceability.py \
	$(POLLENOMICS_TEST_ROOT)/unit/test_source_validation.py
POLLENOMICS_DATA_INPUTS := \
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
	$(wildcard $(POLLENOMICS_SOURCE_ROOT)/data_downloader/*.py) \
	$(wildcard $(POLLENOMICS_SOURCE_ROOT)/data_downloader/*/*.py) \
	$(wildcard $(POLLENOMICS_SOURCE_ROOT)/data_downloader/*/*/*.py) \
	$(wildcard $(POLLENOMICS_SOURCE_ROOT)/adna/*.py) \
	$(wildcard $(POLLENOMICS_SOURCE_ROOT)/adna/*/*.py) \
	$(wildcard $(POLLENOMICS_SOURCE_ROOT)/adna/*/*/*.py) \
	$(POLLENOMICS_DATA_TESTS)

POLLENOMICS_MAP_TESTS := \
	$(POLLENOMICS_TEST_ROOT)/unit/test_map_publication.py \
	$(POLLENOMICS_TEST_ROOT)/unit/test_publication_geography.py \
	$(POLLENOMICS_TEST_ROOT)/unit/test_reporting_artifacts.py \
	$(POLLENOMICS_TEST_ROOT)/unit/test_report_portal.py \
	$(POLLENOMICS_TEST_ROOT)/unit/test_evidence_surface.py \
	$(POLLENOMICS_TEST_ROOT)/unit/test_propagation_outputs.py \
	$(POLLENOMICS_TEST_ROOT)/unit/test_public_artifact_language.py
POLLENOMICS_MAP_INPUTS := \
	configs/pytest.ini \
	$(wildcard $(POLLENOMICS_SOURCE_ROOT)/reporting/*.py) \
	$(wildcard $(POLLENOMICS_SOURCE_ROOT)/reporting/*/*.py) \
	$(wildcard $(POLLENOMICS_SOURCE_ROOT)/reporting/*/*/*.py) \
	$(wildcard $(POLLENOMICS_SOURCE_ROOT)/evidence/*.py) \
	$(POLLENOMICS_MAP_TESTS)

POLLENOMICS_PROVENANCE_TESTS := \
	$(POLLENOMICS_TEST_ROOT)/unit/test_release_evidence.py \
	$(POLLENOMICS_TEST_ROOT)/unit/test_release_evidence_writer.py \
	$(POLLENOMICS_TEST_ROOT)/unit/test_recorded_gates.py \
	$(POLLENOMICS_TEST_ROOT)/unit/test_pollenomics_gate_runner.py
POLLENOMICS_PROVENANCE_INPUTS := \
	configs/pytest.ini \
	$(wildcard $(POLLENOMICS_SOURCE_ROOT)/provenance/*.py) \
	$(POLLENOMICS_PROVENANCE_TESTS)

POLLENOMICS_DOC_COUNT_TESTS := \
	$(POLLENOMICS_TEST_ROOT)/unit/test_data_reference_docs.py \
	$(POLLENOMICS_TEST_ROOT)/unit/test_repository_snapshot.py \
	$(POLLENOMICS_TEST_ROOT)/unit/test_repository_truth.py \
	$(POLLENOMICS_TEST_ROOT)/regression/test_docs_breadth.py
POLLENOMICS_DOC_COUNT_INPUTS := \
	configs/pytest.ini \
	data/collection_summary.json \
	data/evidence_artifact_contracts.json \
	data/source_fact_ownership_registry.json \
	data/source_family_contracts.json \
	data/source_family_evidence_stage_matrix.json \
	data/source_spatiotemporal_posture_registry.json \
	docs/public/pollenomics-data \
	$(wildcard $(POLLENOMICS_SOURCE_ROOT)/foundation/*.py) \
	$(wildcard $(POLLENOMICS_SOURCE_ROOT)/reporting/review/*.py) \
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

.PHONY: verify-science verify-data verify-map verify-provenance verify-doc-counts release-evidence verify-release-candidate

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

release-evidence: verify-science verify-data verify-map verify-provenance verify-doc-counts ## Build canonical evidence after every required gate passes
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
