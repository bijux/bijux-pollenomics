"""Returned review decisions close the source denominator without outcomes."""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from hashlib import sha256
import json
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra_validation.evaluation.api import (
    freeze_evaluation_scope,
)
from bijux_pollenomics_dev.source_completion.empd2_nfi_reference import (
    Empd2NfiDecisionResult,
    review_empd2_nfi_decisions,
)
from bijux_pollenomics_dev.source_completion.empd2_nfi_reference.parameters import (
    authenticated_parameter_manifest,
)

from .factories import (
    admission,
    digest,
    json_bytes,
    mapping_manifest,
    nfi_schema,
    parameter_manifest,
    pollen_count_index,
    projection,
    returned,
    sources,
)


def _review(
    value: dict[str, Any],
    receipt_sha256: str | None = None,
    evidence_bytes: bytes | None = None,
    evidence_sha256: str | None = None,
    index_bytes: bytes | None = None,
    index_sha256: str | None = None,
    attestation_bytes: bytes | None = None,
    attestation_sha256: str | None = None,
    mapping_bytes: bytes | None = None,
    mapping_sha256: str | None = None,
    parameter_bytes: bytes | None = None,
    parameter_sha256: str | None = None,
    schema_bytes: bytes | None = None,
    schema_sha256: str | None = None,
    supply_default_sources: bool = True,
) -> Empd2NfiDecisionResult:
    if supply_default_sources and any(
        item.get("disposition") == "declared_inclusion" for item in value["decisions"]
    ):
        projected = projection()
        default_parameter_bytes, default_parameter_sha, parameter_rows = (
            parameter_manifest(projected)
        )
        default_mapping_bytes, default_mapping_sha = mapping_manifest(
            projected, default_parameter_sha, parameter_rows
        )
        defaults = pollen_count_index(
            projected, default_mapping_sha, default_parameter_sha
        )
        (
            default_index_bytes,
            default_index_sha,
            default_attestation_bytes,
            default_attestation_sha,
            _,
        ) = defaults
        parameter_bytes = parameter_bytes or default_parameter_bytes
        parameter_sha256 = parameter_sha256 or default_parameter_sha
        mapping_bytes = mapping_bytes or default_mapping_bytes
        mapping_sha256 = mapping_sha256 or default_mapping_sha
        index_bytes = index_bytes or default_index_bytes
        index_sha256 = index_sha256 or default_index_sha
        attestation_bytes = attestation_bytes or default_attestation_bytes
        attestation_sha256 = attestation_sha256 or default_attestation_sha
        default_schema_bytes, default_schema_sha = nfi_schema()
        schema_bytes = schema_bytes or default_schema_bytes
        schema_sha256 = schema_sha256 or default_schema_sha
    return review_empd2_nfi_decisions(
        **sources(),
        returned=value,
        taxon_ppe_receipt_sha256=receipt_sha256,
        evidence_manifest_bytes=evidence_bytes,
        evidence_manifest_sha256=evidence_sha256,
        pollen_count_index_bytes=index_bytes,
        pollen_count_index_sha256=index_sha256,
        pollen_count_producer_attestation_bytes=attestation_bytes,
        pollen_count_producer_attestation_sha256=attestation_sha256,
        taxon_mapping_manifest_bytes=mapping_bytes,
        taxon_mapping_manifest_sha256=mapping_sha256,
        taxon_parameter_manifest_bytes=parameter_bytes,
        taxon_parameter_manifest_sha256=parameter_sha256,
        nfi_schema_bytes=schema_bytes,
        nfi_schema_sha256=schema_sha256,
    )


def _evidence(content: bytes) -> dict[str, Any]:
    value = json.loads(content)
    assert isinstance(value, dict)
    return value


def _change_support(row: dict[str, Any], name: str, **changes: object) -> None:
    support = row[name]
    support.update(changes)
    support["footprint_sha256"] = digest(
        {key: item for key, item in support.items() if key != "footprint_sha256"}
    )


def _swap_estimand_columns(row: dict[str, Any]) -> None:
    rows = row["estimand"]["rows"]
    rows[0]["source_column"], rows[1]["source_column"] = (
        rows[1]["source_column"],
        rows[0]["source_column"],
    )


def test_complete_refusal_closes_denominator_without_cohort() -> None:
    value, _, _, _ = returned(admit_first=False)
    result = _review(value)
    assert result.cohort is None
    assert result.validation["declared_inclusion_count"] == 0
    assert result.validation["scientific_admitted_pair_count"] == 0
    assert result.validation["refused_pair_count"] == 16
    assert result.validation["awaiting_review_count"] == 0


def test_complete_supported_return_builds_declared_inclusion_only() -> None:
    value, receipt_sha, evidence_bytes, evidence_sha = returned(admit_first=True)
    result = _review(value, receipt_sha, evidence_bytes, evidence_sha)
    assert result.cohort is not None
    assert result.cohort.admitted_record_ids == (
        result.projection["candidate_rows"][0]["record_id"],
    )
    assert len(result.cohort.refused_record_ids) == 15
    pollen_support = result.cohort.sites[0].support
    assert pollen_support is not None
    assert pollen_support.radius_m == pytest.approx(100.0)
    assert result.cohort.taxa == ("taxon:birch", "taxon:pine")
    assert "country:SE" in result.cohort.sites[0].strata
    observed = next(
        item for item in result.cohort.external_inputs if item.role == "observed_source"
    )
    assert (
        observed.input_id
        == (result.cohort.observation_channels[0].vegetation_input_ids[0])
    )
    assert observed.source_manifest_sha256 == "8" * 64
    assert observed.support is not None and observed.support != pollen_support
    fixed = {
        item.input_id: item
        for item in result.cohort.external_inputs
        if item.role == "fixed_parameter"
    }
    parameter_sha = result.validation["taxon_parameter_manifest_sha256"]
    assert fixed[f"taxon-parameters:{parameter_sha}"].support is None
    assert result.validation["pollen_count_closure"] == (
        "externally_attested_not_runtime_verified"
    )
    pollen = result.cohort.observation_channels[0].pollen_channels[0]
    assert pollen.input_id.startswith("empd2-count-sample:sample-00:")
    assert pollen.source_sha256 != result.validation["pollen_count_index_sha256"]
    assert result.validation["evidence_manifest_sha256"] == evidence_sha
    assert result.validation["declared_inclusion_count"] == 1
    assert result.validation["scientific_admitted_pair_count"] == 0
    assert result.validation["cohort_status"] == (
        "declared_reviewed_inclusion_engineering_intent"
    )
    assert result.validation["reviewer_authority"] == "declared_not_authenticated"
    assert result.validation["outcome_access_status"] == "not_started"
    assert result.validation["scientific_acceptance"] == "not_evaluated"
    assert result.validation["release_acceptance"] == "not_evaluated"


@pytest.mark.parametrize("mode", ["missing", "duplicate", "reordered"])
def test_candidate_denominator_and_canonical_order_are_closed(mode: str) -> None:
    value, _, _, _ = returned(admit_first=False)
    decisions = value["decisions"]
    if mode == "missing":
        decisions.pop()
        match = "16-lead denominator"
    elif mode == "duplicate":
        decisions[-1] = deepcopy(decisions[0])
        match = "unknown or duplicated"
    else:
        decisions.reverse()
        match = "canonical record order"
    with pytest.raises(ValueError, match=match):
        _review(value)


def test_stale_source_row_or_projection_substitution_is_refused() -> None:
    value, receipt_sha, evidence_bytes, evidence_sha = returned(admit_first=True)
    value["decisions"][0]["source_row_sha256"] = value["decisions"][1][
        "source_row_sha256"
    ]
    with pytest.raises(ValueError, match="stale source evidence"):
        _review(value, receipt_sha, evidence_bytes, evidence_sha)

    value, receipt_sha, evidence_bytes, evidence_sha = returned(admit_first=True)
    value["projection_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="unsupported projection"):
        _review(value, receipt_sha, evidence_bytes, evidence_sha)


def test_acceptance_requires_external_receipt_and_evidence_anchors() -> None:
    value, receipt_sha, evidence_bytes, evidence_sha = returned(admit_first=True)
    with pytest.raises(ValueError, match="externally pinned taxon"):
        _review(value, evidence_bytes=evidence_bytes, evidence_sha256=evidence_sha)
    with pytest.raises(ValueError, match="pinned evidence"):
        _review(value, receipt_sha)
    with pytest.raises(ValueError, match="all pinned evidence and source manifests"):
        _review(
            value,
            receipt_sha,
            evidence_bytes,
            evidence_sha,
            supply_default_sources=False,
        )

    assert receipt_sha is not None
    forged = deepcopy(value)
    forged["taxon_ppe_receipt"]["accepted_taxon_ids"] = ["taxon:forged"]
    forged_sha = digest(forged["taxon_ppe_receipt"])
    forged["decisions"][0]["admission"]["taxon_ppe_receipt_sha256"] = forged_sha
    with pytest.raises(ValueError, match="external trust anchor"):
        _review(forged, receipt_sha, evidence_bytes, evidence_sha)


def test_evidence_bytes_reject_forgery_and_embedded_self_hash() -> None:
    value, receipt_sha, evidence_bytes, evidence_sha = returned(admit_first=True)
    assert evidence_bytes is not None and evidence_sha is not None
    forged = _evidence(evidence_bytes)
    forged["rows"][0]["nfi_rights_evidence_reference_ids"] = ["evidence:forged"]
    forged_bytes = json_bytes(forged)
    with pytest.raises(ValueError, match="external trust anchor"):
        _review(value, receipt_sha, forged_bytes, evidence_sha)

    forged["manifest_sha256"] = sha256(forged_bytes).hexdigest()
    self_rehashed = json_bytes(forged)
    with pytest.raises(ValueError, match="exact schema"):
        _review(value, receipt_sha, self_rehashed, sha256(self_rehashed).hexdigest())


def test_all_refused_return_rejects_unused_review_baggage() -> None:
    value, _, _, _ = returned(admit_first=False)
    admitted, _, evidence_bytes, evidence_sha = returned(admit_first=True)
    value["taxon_ppe_receipt"] = admitted["taxon_ppe_receipt"]
    with pytest.raises(ValueError, match="all-refused"):
        _review(value)

    value, _, _, _ = returned(admit_first=False)
    with pytest.raises(ValueError, match="all-refused"):
        _review(value, evidence_bytes=evidence_bytes, evidence_sha256=evidence_sha)

    value, _, _, _ = returned(admit_first=False)
    projected = projection()
    parameter_bytes, parameter_sha, _ = parameter_manifest(projected)
    with pytest.raises(ValueError, match="all-refused"):
        _review(
            value,
            parameter_bytes=parameter_bytes,
            parameter_sha256=parameter_sha,
        )
    with pytest.raises(ValueError, match="all-refused"):
        _review(value, receipt_sha256="a" * 64)
    schema_bytes, schema_sha = nfi_schema()
    with pytest.raises(ValueError, match="all-refused"):
        _review(value, schema_bytes=schema_bytes, schema_sha256=schema_sha)


@pytest.mark.parametrize(
    ("mutation", "match"),
    [
        (
            lambda row: _change_support(row, "pollen_support", latitude=0.0),
            "source location",
        ),
        (
            lambda row: _change_support(row, "vegetation_support", longitude=0.0),
            "source distance",
        ),
        (
            lambda row: row["paired_footprint"].update(
                reviewed_max_pair_distance_m=0.0
            ),
            "source distance",
        ),
        (
            lambda row: row["inventory_time_binding"].update(
                native_inventory_date="forged"
            ),
            "native date",
        ),
        (
            lambda row: row["pollen_collection_period"].update(
                younger_bp=100.0, older_bp=101.0
            ),
            "do not overlap",
        ),
        (
            lambda row: row["pollen_source_binding"].update(
                payload_access_status="opened"
            ),
            "pollen source binding",
        ),
        (
            lambda row: row["estimand"].update(support_role="regional_area_cover"),
            "point/plot",
        ),
        (
            lambda row: row["estimand"]["rows"][0].update(
                source_column="InventedMeasurement"
            ),
            "pinned NFI schema",
        ),
        (
            lambda row: row["estimand"]["rows"][0].update(taxon_id="taxon:forged"),
            "taxon and NFI source column",
        ),
        (_swap_estimand_columns, "taxon and NFI source column"),
        (
            lambda row: row["estimand"]["rows"][1].update(
                source_column=row["estimand"]["rows"][0]["source_column"]
            ),
            "taxon and NFI source column",
        ),
        (
            lambda row: row["estimand"]["rows"][0].update(unit="unit:arbitrary"),
            "governed NFI semantics",
        ),
        (
            lambda row: row["estimand"].update(estimand_id="nfi:contradictory"),
            "governed common measure",
        ),
        (lambda row: row.update(nfi_rights_evidence_reference_ids=[]), "canonical"),
        (lambda row: row.update(independence_status="assumed"), "explicitly"),
    ],
)
def test_pinned_evidence_semantics_are_complete(
    mutation: Callable[[dict[str, Any]], None], match: str
) -> None:
    value, receipt_sha, evidence_bytes, _ = returned(admit_first=True)
    assert evidence_bytes is not None
    manifest = _evidence(evidence_bytes)
    mutation(manifest["rows"][0])
    changed = json_bytes(manifest)
    with pytest.raises(ValueError, match=match):
        _review(value, receipt_sha, changed, sha256(changed).hexdigest())


def test_support_radius_is_reviewed_intent_not_inferred_from_distance() -> None:
    value, receipt_sha, evidence_bytes, _ = returned(admit_first=True)
    assert evidence_bytes is not None
    assert receipt_sha is not None
    manifest = _evidence(evidence_bytes)
    _change_support(manifest["rows"][0], "pollen_support", radius_m=1.0)
    changed = json_bytes(manifest)
    value["decisions"][0]["admission"] = admission(manifest["rows"][0], receipt_sha)
    result = _review(value, receipt_sha, changed, sha256(changed).hexdigest())
    assert result.cohort is not None and result.cohort.sites[0].support is not None
    assert result.cohort.sites[0].support.radius_m == 1.0


def test_support_fields_require_exact_footprint_digest() -> None:
    value, receipt_sha, evidence_bytes, _ = returned(admit_first=True)
    assert evidence_bytes is not None
    manifest = _evidence(evidence_bytes)
    manifest["rows"][0]["pollen_support"]["radius_m"] = 1.0
    changed = json_bytes(manifest)
    with pytest.raises(ValueError, match="footprint digest"):
        _review(value, receipt_sha, changed, sha256(changed).hexdigest())

    support = manifest["rows"][0]["pollen_support"]
    support["footprint_sha256"] = digest(
        {key: item for key, item in support.items() if key != "footprint_sha256"}
    )
    self_rehashed = json_bytes(manifest)
    with pytest.raises(ValueError, match="external trust anchor"):
        _review(value, receipt_sha, self_rehashed, sha256(changed).hexdigest())


def test_pollen_index_rejects_forgery_and_self_rehash() -> None:
    value, receipt_sha, evidence_bytes, evidence_sha = returned(admit_first=True)
    projected = projection()
    parameter_bytes, parameter_sha, parameter_rows = parameter_manifest(projected)
    mapping_bytes, mapping_sha = mapping_manifest(
        projected, parameter_sha, parameter_rows
    )
    index_bytes, index_sha, attestation_bytes, attestation_sha, _ = pollen_count_index(
        projected, mapping_sha, parameter_sha
    )
    index = _evidence(index_bytes)
    index["rows"][0]["sample_payload_size"] += 1
    forged_bytes = json_bytes(index)
    with pytest.raises(ValueError, match="external trust anchor"):
        _review(
            value,
            receipt_sha,
            evidence_bytes,
            evidence_sha,
            index_bytes=forged_bytes,
            index_sha256=index_sha,
        )
    row = index["rows"][0]
    row["index_row_sha256"] = digest(
        {key: item for key, item in row.items() if key != "index_row_sha256"}
    )
    self_rehashed = json_bytes(index)
    with pytest.raises(ValueError, match="ordered payload set"):
        _review(
            value,
            receipt_sha,
            evidence_bytes,
            evidence_sha,
            index_bytes=self_rehashed,
            index_sha256=sha256(self_rehashed).hexdigest(),
            attestation_bytes=attestation_bytes,
            attestation_sha256=attestation_sha,
            mapping_bytes=mapping_bytes,
            mapping_sha256=mapping_sha,
            parameter_bytes=parameter_bytes,
            parameter_sha256=parameter_sha,
        )


def test_pollen_index_rejects_duplicate_payload_digest_after_full_rehash() -> None:
    value, receipt_sha, evidence_bytes, evidence_sha = returned(admit_first=True)
    projected = projection()
    parameter_bytes, parameter_sha, parameter_rows = parameter_manifest(projected)
    mapping_bytes, mapping_sha = mapping_manifest(
        projected, parameter_sha, parameter_rows
    )
    index_bytes, _, attestation_bytes, _, _ = pollen_count_index(
        projected, mapping_sha, parameter_sha
    )
    index = _evidence(index_bytes)
    index["rows"][1]["sample_payload_sha256"] = index["rows"][0][
        "sample_payload_sha256"
    ]
    row = index["rows"][1]
    row["index_row_sha256"] = digest(
        {key: item for key, item in row.items() if key != "index_row_sha256"}
    )
    attestation = _evidence(attestation_bytes)
    attestation["ordered_payload_set_sha256"] = digest(
        [
            {
                key: item[key]
                for key in (
                    "pollen_sample",
                    "sample_payload_sha256",
                    "sample_payload_size",
                    "payload_schema_id",
                )
            }
            for item in index["rows"]
        ]
    )
    changed_attestation = json_bytes(attestation)
    attestation_sha = sha256(changed_attestation).hexdigest()
    index["producer_attestation_sha256"] = attestation_sha
    changed_index = json_bytes(index)
    with pytest.raises(ValueError, match="unique by sample"):
        _review(
            value,
            receipt_sha,
            evidence_bytes,
            evidence_sha,
            index_bytes=changed_index,
            index_sha256=sha256(changed_index).hexdigest(),
            attestation_bytes=changed_attestation,
            attestation_sha256=attestation_sha,
            mapping_bytes=mapping_bytes,
            mapping_sha256=mapping_sha,
            parameter_bytes=parameter_bytes,
            parameter_sha256=parameter_sha,
        )


@pytest.mark.parametrize(
    ("mutate", "match"),
    [
        (
            lambda value: value["source_table_schema"]["columns"][2].update(
                declared_type="INTEGER"
            ),
            "exact claim",
        ),
        (
            lambda value: value["source_table_schema"].update(
                primary_key=["samplename", "var_", "count"]
            ),
            "exact claim",
        ),
        (
            lambda value: value["query_contract"].update(order_by=["var_"]),
            "exact claim",
        ),
        (
            lambda value: value.update(noninteger_count_row_count=1),
            "exact claim",
        ),
        (
            lambda value: value.update(taxon_mapping_manifest_sha256="0" * 64),
            "exact claim",
        ),
        (
            lambda value: value.update(out_of_mapping_var_row_count=1),
            "exact claim",
        ),
        (
            lambda value: value.update(negative_count_row_count=1),
            "exact claim",
        ),
        (
            lambda value: value.update(nonpositive_mapped_denominator_sample_count=1),
            "exact claim",
        ),
    ],
)
def test_pollen_attestation_closes_ddl_query_and_result_checks(
    mutate: Callable[[dict[str, Any]], None], match: str
) -> None:
    value, receipt_sha, evidence_bytes, evidence_sha = returned(admit_first=True)
    projected = projection()
    parameter_bytes, parameter_sha, parameter_rows = parameter_manifest(projected)
    mapping_bytes, mapping_sha = mapping_manifest(
        projected, parameter_sha, parameter_rows
    )
    index_bytes, _, attestation_bytes, _, _ = pollen_count_index(
        projected, mapping_sha, parameter_sha
    )
    attestation = _evidence(attestation_bytes)
    mutate(attestation)
    changed_attestation = json_bytes(attestation)
    changed_attestation_sha = sha256(changed_attestation).hexdigest()
    index = _evidence(index_bytes)
    index["producer_attestation_sha256"] = changed_attestation_sha
    changed_index = json_bytes(index)
    with pytest.raises(ValueError, match=match):
        _review(
            value,
            receipt_sha,
            evidence_bytes,
            evidence_sha,
            index_bytes=changed_index,
            index_sha256=sha256(changed_index).hexdigest(),
            attestation_bytes=changed_attestation,
            attestation_sha256=changed_attestation_sha,
            mapping_bytes=mapping_bytes,
            mapping_sha256=mapping_sha,
            parameter_bytes=parameter_bytes,
            parameter_sha256=parameter_sha,
        )


def test_mapping_and_parameter_content_are_exactly_bound() -> None:
    value, receipt_sha, evidence_bytes, evidence_sha = returned(admit_first=True)
    projected = projection()
    parameter_bytes, parameter_sha, parameter_rows = parameter_manifest(projected)
    mapping_bytes, _mapping_sha = mapping_manifest(
        projected, parameter_sha, parameter_rows
    )

    mapping = _evidence(mapping_bytes)
    mapping["rows"][0]["original_varname"] = "forged"
    changed_mapping = json_bytes(mapping)
    with pytest.raises(ValueError, match="p_vars row digest"):
        _review(
            value,
            receipt_sha,
            evidence_bytes,
            evidence_sha,
            mapping_bytes=changed_mapping,
            mapping_sha256=sha256(changed_mapping).hexdigest(),
        )

    missing = _evidence(mapping_bytes)
    missing["rows"].pop()
    missing_bytes = json_bytes(missing)
    with pytest.raises(ValueError, match="object array"):
        _review(
            value,
            receipt_sha,
            evidence_bytes,
            evidence_sha,
            mapping_bytes=missing_bytes,
            mapping_sha256=sha256(missing_bytes).hexdigest(),
        )

    mismatched = _evidence(mapping_bytes)
    mismatched["rows"][1]["var_"] = mismatched["rows"][0]["var_"]
    native = {
        key: mismatched["rows"][1][key]
        for key in ("var_", "acc_var_", "original_varname", "acc_varname", "groupid")
    }
    mismatched["rows"][1]["p_vars_row_sha256"] = digest(
        {
            "pollen_source_sha256": projected["source_identities"]["empd2_source"],
            **native,
        }
    )
    mismatched_bytes = json_bytes(mismatched)
    with pytest.raises(ValueError, match="duplicated"):
        _review(
            value,
            receipt_sha,
            evidence_bytes,
            evidence_sha,
            mapping_bytes=mismatched_bytes,
            mapping_sha256=sha256(mismatched_bytes).hexdigest(),
        )

    for replacement in (0, 5231):
        outside = _evidence(mapping_bytes)
        row_index = 0 if replacement == 0 else -1
        outside["rows"][row_index]["var_"] = replacement
        native = {
            key: outside["rows"][row_index][key]
            for key in (
                "var_",
                "acc_var_",
                "original_varname",
                "acc_varname",
                "groupid",
            )
        }
        outside["rows"][row_index]["p_vars_row_sha256"] = digest(
            {
                "pollen_source_sha256": projected["source_identities"]["empd2_source"],
                **native,
            }
        )
        outside_bytes = json_bytes(outside)
        with pytest.raises(ValueError, match="1..5230 denominator"):
            _review(
                value,
                receipt_sha,
                evidence_bytes,
                evidence_sha,
                mapping_bytes=outside_bytes,
                mapping_sha256=sha256(outside_bytes).hexdigest(),
            )

    invalid_acc = _evidence(mapping_bytes)
    invalid_acc["rows"][0]["acc_var_"] = 5231
    native = {
        key: invalid_acc["rows"][0][key]
        for key in ("var_", "acc_var_", "original_varname", "acc_varname", "groupid")
    }
    invalid_acc["rows"][0]["p_vars_row_sha256"] = digest(
        {
            "pollen_source_sha256": projected["source_identities"]["empd2_source"],
            **native,
        }
    )
    invalid_acc_bytes = json_bytes(invalid_acc)
    with pytest.raises(ValueError, match="acc_var_"):
        _review(
            value,
            receipt_sha,
            evidence_bytes,
            evidence_sha,
            mapping_bytes=invalid_acc_bytes,
            mapping_sha256=sha256(invalid_acc_bytes).hexdigest(),
        )

    wrong_group_count = _evidence(mapping_bytes)
    wrong_group_count["rows"][1901]["acc_var_"] = 1902
    native = {
        key: wrong_group_count["rows"][1901][key]
        for key in ("var_", "acc_var_", "original_varname", "acc_varname", "groupid")
    }
    wrong_group_count["rows"][1901]["p_vars_row_sha256"] = digest(
        {
            "pollen_source_sha256": projected["source_identities"]["empd2_source"],
            **native,
        }
    )
    wrong_group_count_bytes = json_bytes(wrong_group_count)
    with pytest.raises(ValueError, match="1901 canonical"):
        _review(
            value,
            receipt_sha,
            evidence_bytes,
            evidence_sha,
            mapping_bytes=wrong_group_count_bytes,
            mapping_sha256=sha256(wrong_group_count_bytes).hexdigest(),
        )

    inconsistent_alias = _evidence(mapping_bytes)
    alias = inconsistent_alias["rows"][1901]
    alias.update(
        mapping_disposition="refused_unmapped",
        taxon_id=None,
        parameter_row_sha256=None,
        reason_codes=["outside-accepted-taxa"],
    )
    inconsistent_alias_bytes = json_bytes(inconsistent_alias)
    with pytest.raises(ValueError, match="alias class"):
        _review(
            value,
            receipt_sha,
            evidence_bytes,
            evidence_sha,
            mapping_bytes=inconsistent_alias_bytes,
            mapping_sha256=sha256(inconsistent_alias_bytes).hexdigest(),
        )

    absent_accepted_taxon = _evidence(mapping_bytes)
    for row in absent_accepted_taxon["rows"]:
        if row["acc_var_"] == 2:
            row.update(
                mapping_disposition="refused_unmapped",
                taxon_id=None,
                parameter_row_sha256=None,
                reason_codes=["outside-accepted-taxa"],
            )
    absent_accepted_taxon_bytes = json_bytes(absent_accepted_taxon)
    with pytest.raises(ValueError, match="canonical p_vars mappings"):
        _review(
            value,
            receipt_sha,
            evidence_bytes,
            evidence_sha,
            mapping_bytes=absent_accepted_taxon_bytes,
            mapping_sha256=sha256(absent_accepted_taxon_bytes).hexdigest(),
        )

    parameters = _evidence(parameter_bytes)
    parameters["rows"][0]["ppe_binding"]["normalized_value"] = 99.0
    changed_parameters = json_bytes(parameters)
    with pytest.raises(ValueError, match="pinned receipt"):
        _review(
            value,
            receipt_sha,
            evidence_bytes,
            evidence_sha,
            parameter_bytes=changed_parameters,
            parameter_sha256=sha256(changed_parameters).hexdigest(),
        )


def test_returned_document_changes_rebind_validation_and_cohort_manifest() -> None:
    first, receipt_sha, evidence_bytes, evidence_sha = returned(admit_first=True)
    first_result = _review(first, receipt_sha, evidence_bytes, evidence_sha)
    second = deepcopy(first)
    second["decisions"][0]["reason_codes"] = ["another_reviewed_reason"]
    second_result = _review(second, receipt_sha, evidence_bytes, evidence_sha)
    assert first_result.validation["returned_decisions_sha256"] == digest(first)
    assert second_result.validation["returned_decisions_sha256"] == digest(second)
    assert (
        first_result.validation["decision_manifest_sha256"]
        != (second_result.validation["decision_manifest_sha256"])
    )


def test_shared_nfi_observation_cannot_be_declared_twice() -> None:
    value, receipt_sha, evidence_bytes, _ = returned(admit_first=True)
    assert evidence_bytes is not None
    assert receipt_sha is not None
    manifest = _evidence(evidence_bytes)
    for index in (2, 3):
        decision = value["decisions"][index]
        decision["disposition"] = "declared_inclusion"
        decision["reason_codes"] = ["reviewed_identity_support_and_estimand"]
        decision["admission"] = admission(manifest["rows"][index], receipt_sha)
    with pytest.raises(ValueError, match="share one NFI observation"):
        _review(value, receipt_sha, evidence_bytes, sha256(evidence_bytes).hexdigest())


def test_same_physical_nfi_plot_across_years_has_one_group() -> None:
    value, receipt_sha, evidence_bytes, evidence_sha = returned(admit_first=True)
    assert evidence_bytes is not None
    assert receipt_sha is not None
    manifest = _evidence(evidence_bytes)
    second = value["decisions"][1]
    second["disposition"] = "declared_inclusion"
    second["reason_codes"] = ["reviewed_identity_support_and_estimand"]
    second["admission"] = admission(manifest["rows"][1], receipt_sha)
    result = _review(value, receipt_sha, evidence_bytes, evidence_sha)
    assert result.cohort is not None
    assert len({site.group_id for site in result.cohort.sites}) == 1


def test_shared_nfi_evidence_must_be_identical() -> None:
    value, receipt_sha, evidence_bytes, _ = returned(admit_first=True)
    assert evidence_bytes is not None
    manifest = _evidence(evidence_bytes)
    _change_support(manifest["rows"][3], "vegetation_support", radius_m=51.0)
    changed = json_bytes(manifest)
    with pytest.raises(ValueError, match="shared NFI observation evidence"):
        _review(value, receipt_sha, changed, sha256(changed).hexdigest())


def test_all_evidence_rows_must_share_one_exact_estimand() -> None:
    value, receipt_sha, evidence_bytes, _ = returned(admit_first=True)
    assert evidence_bytes is not None
    assert receipt_sha is not None
    manifest = _evidence(evidence_bytes)
    second_estimand = manifest["rows"][1]["estimand"]
    second_estimand["estimand_id"] = "nfi:point-plot-tree-stem-volume"
    for row in second_estimand["rows"]:
        suffix = "Birch" if row["taxon_id"] == "taxon:birch" else "Pine"
        row.update(
            source_column=f"Vol{suffix}",
            variable_id=f"variable:{suffix.lower()}-stem-volume",
            unit="unit:m3-per-ha",
        )
    second = value["decisions"][1]
    second["disposition"] = "declared_inclusion"
    second["reason_codes"] = ["reviewed_identity_support_and_estimand"]
    second["admission"] = admission(manifest["rows"][1], receipt_sha)
    changed = json_bytes(manifest)
    with pytest.raises(ValueError, match="one exact estimand"):
        _review(value, receipt_sha, changed, sha256(changed).hexdigest())


@pytest.mark.parametrize(
    ("kind", "field", "replacement"),
    [
        ("ppe_binding", "source_units", "ratio"),
        ("ppe_binding", "normalization_profile", "invented.v1"),
        ("ppe_binding", "normalized_value", 2.0),
        ("fall_speed_binding", "source_units", "cm/s"),
        ("fall_speed_binding", "normalization_profile", "invented.v1"),
        ("fall_speed_binding", "source_value_text", "99"),
    ],
)
def test_parameter_repin_cannot_change_units_profiles_or_values(
    kind: str, field: str, replacement: object
) -> None:
    projected = projection()
    content, _, _ = parameter_manifest(projected)
    manifest = _evidence(content)
    manifest["rows"][0][kind][field] = replacement
    row = manifest["rows"][0]
    row["parameter_row_sha256"] = digest(
        {key: item for key, item in row.items() if key != "parameter_row_sha256"}
    )
    changed = json_bytes(manifest)
    changed_sha = sha256(changed).hexdigest()
    receipt = returned(admit_first=True)[0]["taxon_ppe_receipt"]
    receipt["parameter_binding_sha256"] = changed_sha
    with pytest.raises((TypeError, ValueError)):
        authenticated_parameter_manifest(changed, changed_sha, projected, receipt)


def test_parameter_repin_cannot_mix_ppe_reference_scales() -> None:
    projected = projection()
    content, _, _ = parameter_manifest(projected)
    manifest = _evidence(content)
    row = manifest["rows"][1]
    row["ppe_binding"]["reference_taxon"] = "taxon:pine"
    row["parameter_row_sha256"] = digest(
        {key: item for key, item in row.items() if key != "parameter_row_sha256"}
    )
    changed = json_bytes(manifest)
    changed_sha = sha256(changed).hexdigest()
    receipt = returned(admit_first=True)[0]["taxon_ppe_receipt"]
    receipt["parameter_binding_sha256"] = changed_sha
    with pytest.raises(ValueError, match="manifest reference taxon"):
        authenticated_parameter_manifest(changed, changed_sha, projected, receipt)


def test_parameter_repin_cannot_change_accepted_taxon_rank() -> None:
    projected = projection()
    content, _, _ = parameter_manifest(projected)
    manifest = _evidence(content)
    row = manifest["rows"][0]
    row["accepted_taxon_rank"] = "species"
    row["parameter_row_sha256"] = digest(
        {key: item for key, item in row.items() if key != "parameter_row_sha256"}
    )
    changed = json_bytes(manifest)
    changed_sha = sha256(changed).hexdigest()
    receipt = returned(admit_first=True)[0]["taxon_ppe_receipt"]
    receipt["parameter_binding_sha256"] = changed_sha
    with pytest.raises(ValueError, match="genus rank"):
        authenticated_parameter_manifest(changed, changed_sha, projected, receipt)


def test_distinct_nfi_observations_freeze_distinct_pollen_channels() -> None:
    value, receipt_sha, evidence_bytes, evidence_sha = returned(admit_first=True)
    assert evidence_bytes is not None
    assert receipt_sha is not None
    manifest = _evidence(evidence_bytes)
    second = value["decisions"][2]
    second["disposition"] = "declared_inclusion"
    second["reason_codes"] = ["reviewed_identity_support_and_estimand"]
    second["admission"] = admission(manifest["rows"][2], receipt_sha)
    result = _review(value, receipt_sha, evidence_bytes, evidence_sha)
    assert result.cohort is not None
    scope = freeze_evaluation_scope(
        result.cohort, scope_id="scope:empd2-nfi-two", by_block=False
    )
    pollen = [
        channel.pollen_channels[0] for channel in scope.scope.observation_channels
    ]
    assert len({channel.input_id for channel in pollen}) == 2
    assert len({channel.source_sha256 for channel in pollen}) == 2


def test_outcome_or_nfi_measurement_fields_are_forbidden() -> None:
    value, receipt_sha, evidence_bytes, evidence_sha = returned(admit_first=True)
    value["decisions"][0]["admission"]["nfi_basal_area_value"] = 12.5
    with pytest.raises(ValueError, match="admission fields"):
        _review(value, receipt_sha, evidence_bytes, evidence_sha)


def test_proximity_does_not_auto_accept() -> None:
    value, _, _, _ = returned(admit_first=False)
    value["decisions"][0]["disposition"] = "declared_inclusion"
    with pytest.raises(ValueError, match="externally pinned"):
        _review(value)


def test_legacy_admitted_disposition_is_not_publicly_accepted() -> None:
    value, _, _, _ = returned(admit_first=False)
    value["decisions"][0]["disposition"] = "admitted"
    with pytest.raises(ValueError, match="declared_inclusion"):
        _review(value)
