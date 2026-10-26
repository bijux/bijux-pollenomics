"""Source evidence must establish each added zero without changing native data."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.abborrtjarnen_age_ppe import (
    chronology,
    count_profiles,
    inputs,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.abborrtjarnen_ppe_dependence.sources import (
    TAXA,
    TAXON_IDS,
)


def source_case(
    root: Path,
) -> tuple[
    dict[str, Any], list[dict[str, Any]], dict[str, Any], dict[str, Any], dict[str, Any]
]:
    raw, samples, accounts, zeros = [], [], [], []
    for i in range(107):
        omitted = i % 5 if i < 8 else None
        missing = [] if omitted is None else [TAXA[omitted]]
        values = [0 if j == omitted else 10 for j in range(5)]
        sample = {
            "sample_id": i,
            "depth_native": i,
            "missing_taxa": missing,
            "counts": None if missing else values,
            "reported_panel_subtotal": sum(values),
            "panel_mass": None if missing else sum(values),
            "all_reported_pollen_nisp": sum(values) + 2,
            "omitted_reported_pollen_nisp": 2,
        }
        samples.append(sample)
        accounts.append({k: v for k, v in sample.items() if k != "counts"})
        raw.append(
            {
                "sampleid": i,
                "depth": i,
                "datum": [
                    {
                        "element": "pollen",
                        "elementtype": "pollen",
                        "units": "NISP",
                        "value": values[j],
                        "variablename": name,
                        "taxonid": taxon,
                    }
                    for j, (name, taxon) in enumerate(zip(TAXA, TAXON_IDS, strict=True))
                    if j != omitted
                ],
            }
        )
        if omitted is not None:
            zeros.append(
                {
                    "native_sample_id": i,
                    "depth_native_exact": f"{i}/1",
                    "original_depth_token": str(i / 100),
                    "original_row_index": i,
                    "original_column": f"column_{omitted}",
                    "native_taxon_id": TAXON_IDS[omitted],
                    "taxon": TAXA[omitted],
                    "original_token": "0",
                    "original_status": "explicit_zero",
                    "original_integer_value": 0,
                    "original_invalid_reason": None,
                    "native_reported": False,
                    "native_value": None,
                    "comparison_status": "absent_native_datum",
                }
            )
    owners = (
        "native_sample_id",
        "depth_native_exact",
        "original_depth_token",
        "original_row_index",
        "original_column",
        "native_taxon_id",
        "taxon",
    )
    proof: dict[str, Any] = {
        "schema_version": "abborrtjarnen-original-count-correspondence.v1",
        "source_commit": "controlled-source",
        "status": "reported_counts_match",
        "candidate_classification_status": "enabled_reported_counts_match",
        "depth_binding": {
            **dict.fromkeys(
                (
                    "original_rows",
                    "native_samples",
                    "unique_original_depths",
                    "unique_native_depths",
                ),
                107,
            ),
            **{
                k: []
                for k in (
                    "duplicate_original_depths",
                    "duplicate_native_depths",
                    "original_only_depths",
                    "native_only_depths",
                )
            },
            "depth_pairs_sha256": "depth-data",
        },
        "comparison": {
            "slot_audit_sha256": "slot-data",
            "total_slots": 535,
            "native_reported_slots": 527,
            "reported_count_matches": 527,
            "native_absent_slots": 8,
            "reported_count_disagreements": 0,
            "reported_population_matches": True,
            "reported_count_precondition_passed": True,
        },
        "input_sha256": {f"source-store/input_{i}": str(i) for i in range(3)},
        "absence_candidates": zeros,
    }
    protocol = {
        "count_profile": count_profiles.SOURCE,
        "base_protocol": str(chronology.PROTOCOL),
        "source_count_commit": "controlled-source",
        "source_count_result": "artifacts/proof.json",
        "source_count_verification": "artifacts/verified.json",
        "depth_pairs_sha256": "depth-data",
        "slot_audit_sha256": "slot-data",
        "zero_owner_fields": list(owners),
        "expected_zero_owners_sha256": hashlib.sha256(
            json.dumps(
                [{k: c[k] for k in owners} for c in zeros],
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode()
        ).hexdigest(),
        "rights_and_correspondence": {
            "original": "local noncommercial controlled fixture"
        },
    }
    verified = {
        "status": "verified",
        "producer_source_commit": "controlled-source",
        "observer_source_commit": "controlled-source",
        "source_rows_checked": 107,
        "native_samples_checked": 107,
        "slots_checked": 535,
        "reported_checked": 527,
        "reported_disagreements": 0,
        "absent_native_checked": 8,
        "morphological_comments_checked": 5,
        "source_inputs_checked": 3,
        "model_fits": 0,
    }
    (root / "artifacts").mkdir()
    proof_body = json.dumps(proof).encode()
    (root / "artifacts/proof.json").write_bytes(proof_body)
    verified["result_sha256"] = hashlib.sha256(proof_body).hexdigest()
    verified_body = json.dumps(verified).encode()
    (root / "artifacts/verified.json").write_bytes(verified_body)
    protocol["repository_inputs"] = {
        name: {"bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}
        for name, body in [
            ("artifacts/proof.json", proof_body),
            ("artifacts/verified.json", verified_body),
        ]
    }
    path = root / count_profiles.PROTOCOL
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(protocol))
    case = {
        "samples": samples,
        "sample_accounts": accounts,
        "input_sha256": dict(proof["input_sha256"]),
    }
    return case, raw, proof, verified, protocol


def test_native_default_is_exact_identity_without_any_new_source_read() -> None:
    case = {"status": "strict-native"}
    assert (
        count_profiles.apply(case, [], Path("/not/a/source"), count_profiles.NATIVE)
        is case
    )


def test_only_recorded_zeros_extend_support_and_native_facts_survive(
    tmp_path: Path,
) -> None:
    case, raw, _, _, _ = source_case(tmp_path)
    native = copy.deepcopy(case)
    result = count_profiles.apply(case, raw, tmp_path, count_profiles.SOURCE)
    assert result["native_samples"] == native["samples"]
    assert len(result["samples"]) == 107
    for prior, active, account in zip(
        native["samples"], result["samples"], result["sample_accounts"], strict=True
    ):
        assert all(active[k] == v for k, v in prior.items() if k != "counts")
        assert all(account[k] == v for k, v in prior.items() if k != "counts")
        assert (
            not active["analytical_missing_taxa"]
            and active["analytical_panel_mass"] == prior["reported_panel_subtotal"]
        )
    old, old_counts = inputs.membership(result["native_samples"], [1750.0] * 107, 3)
    new, new_counts = inputs.membership(result["samples"], [1750.0] * 107, 3)
    assert old_counts is None and new_counts is not None
    assert (
        old["missing_members"] == new["native_missing_members"]
        and not new["missing_members"]
    )
    assert new["source_recorded_zero_sample_ids"] == list(range(8))
    assert new["panel_mass"] == new["reported_panel_subtotal"] == sum(new_counts)
    assert (
        inputs.membership(result["samples"], [-1.0] * 107, 3)[0]["status"]
        == "empty_native_window"
    )


@pytest.mark.parametrize(
    "corruption",
    [
        "status",
        "depth_population",
        "reported",
        "qualification",
        "positive",
        "blank",
        "owner",
        "duplicate",
        "source_hash",
        "native_depth",
        "native_missing",
        "changed_proof",
        "prepared_count",
        "prepared_owner",
        "reported_measurement",
    ],
)
def test_source_profile_refuses_unqualified_or_changed_measurements(
    tmp_path: Path, corruption: str
) -> None:
    case, raw, proof, verified, protocol = source_case(tmp_path)
    if corruption == "source_hash":
        case["input_sha256"]["source-store/input_0"] = "other"
    elif corruption == "native_depth":
        raw[0]["depth"] = 0.1
    elif corruption == "native_missing":
        raw[0]["datum"].pop()
    elif corruption == "changed_proof":
        (tmp_path / protocol["source_count_result"]).write_text("changed")
    elif corruption == "prepared_count":
        case["samples"][-1]["counts"][0] = 999
    elif corruption == "prepared_owner":
        case["sample_accounts"][0]["sample_id"] = 999
    elif corruption == "reported_measurement":
        raw[-1]["datum"][0]["value"] = 999
    else:
        if corruption == "status":
            proof["status"] = "refused"
        elif corruption == "depth_population":
            proof["depth_binding"]["unique_original_depths"] = 106
        elif corruption == "reported":
            proof["comparison"]["reported_count_matches"] = 526
        elif corruption == "qualification":
            verified["status"] = "unverified"
        elif corruption == "positive":
            proof["absence_candidates"][0]["original_integer_value"] = 1
        elif corruption == "blank":
            proof["absence_candidates"][0]["original_token"] = ""
        elif corruption == "owner":
            proof["absence_candidates"][0]["original_row_index"] = 99
        else:
            proof["absence_candidates"][-1] = proof["absence_candidates"][0]
        with pytest.raises(ValueError):
            count_profiles.qualified_zeros(proof, verified, protocol)
        return
    with pytest.raises(ValueError):
        count_profiles.apply(case, raw, tmp_path, count_profiles.SOURCE)
