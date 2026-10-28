"""Literal preservation and non-substitution controls on synthetic specimens."""

from __future__ import annotations

from copy import deepcopy
import json

import pytest

from .fixtures import body, csv_body, fixture
from .verification import compare_payloads, decode


def test_only69_display_labels_change_and_every_sample_support_stays_owned() -> None:
    facts = compare_payloads(*fixture())
    assert (
        facts["sample_owners_verified"] == facts["individual_supports_verified"] == 78
    )
    assert facts["localities_verified"] == 23
    assert facts["refusals_unchanged"] == 8
    assert (
        facts["json_hull_label_changes"]
        == facts["bundle_hull_label_changes"]
        == facts["csv_hull_label_changes"]
        == 69
    )


@pytest.mark.parametrize(
    "defect",
    [
        "sample_date",
        "sample_order",
        "refusal",
        "locality_order",
        "member_order",
        "coordinate",
        "hull_bound",
        "hull_text",
        "hull_mean",
        "support_source",
        "support_date",
        "new_empirical_metadata",
        "unchanged_label",
        "unknown_label",
        "new_bundle_section",
        "drop_support",
        "extra_support",
        "duplicate_locality",
        "changed_kind",
        "lost_source_metadata",
    ],
)
def test_all_nonlabel_changes_refuse(defect: str) -> None:
    normalization, baseline, candidate, canonical = fixture()
    local = json.loads(candidate["locality_json"])
    bundle = json.loads(candidate["bundle"])
    first = local["localities"][0]
    if defect == "sample_date":
        bundle["sample_records"][0]["chronology"]["time_mean_bp"] += 1
    elif defect == "sample_order":
        bundle["sample_records"].reverse()
    elif defect == "refusal":
        bundle["refusals"].pop()
    elif defect == "locality_order":
        local["localities"].reverse()
    elif defect == "member_order":
        first["sample_ids"].reverse()
        first["sample_chronologies"].reverse()
    elif defect == "coordinate":
        first["coordinates"]["latitude"] += 0.01
    elif defect == "hull_bound":
        first["chronology"]["time_start_bp"] += 1
    elif defect == "hull_text":
        first["chronology"]["original_text"] = "new field age"
    elif defect == "hull_mean":
        first["chronology"]["time_mean_bp"] += 1
    elif defect == "support_source":
        first["sample_chronologies"][0]["source_release"] = "other source"
    elif defect == "support_date":
        first["sample_chronologies"][0]["chronology"] = deepcopy(first["chronology"])
    elif defect == "new_empirical_metadata":
        first["sample_chronologies"][0]["calibration_status"] = "calibrated"
    elif defect == "unchanged_label":
        first["chronology"]["precision_posture"] = "sample_precise_interval"
    elif defect == "unknown_label":
        first["chronology"]["evidence_class"] = "field_qualified"
    elif defect == "new_bundle_section":
        bundle["scientific_admitted"] = True
    elif defect == "drop_support":
        first["sample_chronologies"].pop()
    elif defect == "extra_support":
        first["sample_chronologies"].append(deepcopy(first["sample_chronologies"][0]))
    elif defect == "duplicate_locality":
        local["localities"][-1] = deepcopy(first)
    elif defect == "changed_kind":
        bundle["refusals"][0]["record_kind"] = "locality_records"
    else:
        first.pop("interpretation_note")
    bundle["locality_records"] = local["localities"]
    candidate.update(
        locality_json=body(local),
        locality_csv=csv_body(local["localities"])
        if defect != "lost_source_metadata"
        else candidate["locality_csv"],
        bundle=body(bundle),
    )
    with pytest.raises((ValueError, KeyError)):
        compare_payloads(normalization, baseline, candidate, canonical)


def test_preexisting_hull_substitution_cannot_pass_as_preservation() -> None:
    normalization, baseline, candidate, canonical = fixture()
    for collection in (baseline, candidate):
        local = json.loads(collection["locality_json"])
        bundle = json.loads(collection["bundle"])
        support = local["localities"][0]["sample_chronologies"][0]
        # 1000 BP is inside the broad locality hull but outside this specimen's
        # [0,10] BP interval. Equal old/new corruption must still fail ownership.
        support["chronology"].update(
            original_text="1000-1010 BP",
            time_start_bp=1000,
            time_end_bp=1010,
            time_mean_bp=1005,
        )
        bundle["locality_records"] = local["localities"]
        collection.update(
            locality_json=body(local),
            locality_csv=csv_body(local["localities"]),
            bundle=body(bundle),
        )
    with pytest.raises(ValueError):
        compare_payloads(normalization, baseline, candidate, canonical)


def test_csv_must_preserve_source_columns_and_match_owned_support_json() -> None:
    normalization, baseline, candidate, canonical = fixture()
    candidate["locality_csv"] = candidate["locality_csv"].replace(
        b"native latitude", b"guessed latitude", 1
    )
    with pytest.raises(ValueError):
        compare_payloads(normalization, baseline, candidate, canonical)


@pytest.mark.parametrize(
    "body_bytes", [b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":Infinity}']
)
def test_duplicate_keys_and_nonfinite_json_refuse(body_bytes: bytes) -> None:
    with pytest.raises(ValueError):
        decode(body_bytes)
